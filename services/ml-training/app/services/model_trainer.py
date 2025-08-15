import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    AutoModelForSequenceClassification
)
from datasets import load_dataset, Dataset
from peft import LoraConfig, get_peft_model, TaskType
import mlflow
import wandb
from trl import PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead
from accelerate import Accelerator

from app.models.schemas import (
    TrainingStatus,
    TrainingJobStatus,
    TrainingConfig,
    RLHFConfig,
    ModelType,
    BaseModelType
)
from app.database import get_db
from app.utils.model_utils import (
    prepare_dataset,
    compute_metrics,
    get_model_path,
    save_model_checkpoint
)

logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self):
        self.jobs = {}
        self.accelerator = Accelerator()
        self.setup_mlflow()
        self.setup_wandb()
        
    def setup_mlflow(self):
        """Initialize MLflow tracking"""
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
        mlflow.set_experiment("tonebridge-training")
        
    def setup_wandb(self):
        """Initialize Weights & Biases tracking"""
        if os.getenv("WANDB_API_KEY"):
            wandb.init(project="tonebridge", entity=os.getenv("WANDB_ENTITY"))
    
    async def create_training_job(
        self,
        model_type: ModelType,
        base_model: BaseModelType,
        dataset_id: str,
        hyperparameters: Optional[TrainingConfig] = None,
        training_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new training job"""
        job_id = str(uuid.uuid4())
        
        self.jobs[job_id] = {
            "id": job_id,
            "status": TrainingStatus.PENDING,
            "model_type": model_type,
            "base_model": base_model,
            "dataset_id": dataset_id,
            "hyperparameters": hyperparameters or TrainingConfig(),
            "training_config": training_config or {},
            "created_at": datetime.utcnow(),
            "progress": 0
        }
        
        # Store in database
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO training_jobs 
                (id, model_type, base_model, dataset_id, status, config, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                job_id, model_type.value, base_model.value, dataset_id, 
                TrainingStatus.PENDING.value, json.dumps(training_config), 
                datetime.utcnow()
            )
        
        logger.info(f"Created training job: {job_id}")
        return job_id
    
    async def train_model(self, job_id: str):
        """Train a model asynchronously"""
        try:
            self.jobs[job_id]["status"] = TrainingStatus.RUNNING
            self.jobs[job_id]["started_at"] = datetime.utcnow()
            
            # Get job details
            job = self.jobs[job_id]
            model_type = job["model_type"]
            base_model = job["base_model"]
            dataset_id = job["dataset_id"]
            config = job["hyperparameters"]
            
            # Load dataset
            dataset = await self.load_dataset(dataset_id)
            
            # Select and load base model
            model, tokenizer = await self.load_base_model(base_model)
            
            # Apply LoRA for efficient fine-tuning
            if config.gradient_checkpointing:
                model = self.apply_lora(model, model_type)
            
            # Prepare training arguments
            training_args = self.prepare_training_args(job_id, config)
            
            # Create trainer
            trainer = self.create_trainer(
                model=model,
                tokenizer=tokenizer,
                dataset=dataset,
                training_args=training_args,
                model_type=model_type
            )
            
            # Start training with MLflow tracking
            with mlflow.start_run(run_name=f"training_{job_id}"):
                mlflow.log_params({
                    "model_type": model_type.value,
                    "base_model": base_model.value,
                    "epochs": config.epochs,
                    "batch_size": config.batch_size,
                    "learning_rate": config.learning_rate
                })
                
                # Training loop with progress updates
                for epoch in range(config.epochs):
                    trainer.train()
                    
                    # Update progress
                    progress = ((epoch + 1) / config.epochs) * 100
                    self.jobs[job_id]["progress"] = progress
                    self.jobs[job_id]["current_epoch"] = epoch + 1
                    
                    # Evaluate
                    eval_results = trainer.evaluate()
                    mlflow.log_metrics(eval_results, step=epoch)
                    
                    # Save checkpoint
                    if (epoch + 1) % config.save_steps == 0:
                        checkpoint_path = f"checkpoints/{job_id}/epoch_{epoch+1}"
                        trainer.save_model(checkpoint_path)
                        
                    # Update job status in database
                    await self.update_job_status(job_id, progress, eval_results)
            
            # Save final model
            model_path = f"models/{job_id}"
            trainer.save_model(model_path)
            tokenizer.save_pretrained(model_path)
            
            # Register model
            model_id = await self.register_model(job_id, model_path, eval_results)
            
            # Update job completion
            self.jobs[job_id]["status"] = TrainingStatus.COMPLETED
            self.jobs[job_id]["completed_at"] = datetime.utcnow()
            self.jobs[job_id]["model_id"] = model_id
            
            logger.info(f"Training completed for job: {job_id}")
            
        except Exception as e:
            logger.error(f"Training failed for job {job_id}: {e}")
            self.jobs[job_id]["status"] = TrainingStatus.FAILED
            self.jobs[job_id]["error_message"] = str(e)
            await self.update_job_status(job_id, self.jobs[job_id]["progress"], 
                                        {"error": str(e)})
    
    async def load_dataset(self, dataset_id: str) -> Dataset:
        """Load dataset from database or file"""
        async with get_db() as db:
            result = await db.fetchone(
                "SELECT file_path, format FROM datasets WHERE id = $1",
                dataset_id
            )
            
        if not result:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        file_path, format = result
        
        if format == "json":
            dataset = load_dataset("json", data_files=file_path)
        elif format == "csv":
            dataset = load_dataset("csv", data_files=file_path)
        elif format == "parquet":
            dataset = load_dataset("parquet", data_files=file_path)
        else:
            dataset = load_dataset(file_path)
        
        return dataset["train"]
    
    async def load_base_model(self, base_model: BaseModelType):
        """Load base model and tokenizer"""
        model_map = {
            BaseModelType.GPT4: "gpt2-xl",  # Placeholder
            BaseModelType.GPT35_TURBO: "gpt2-large",  # Placeholder
            BaseModelType.CLAUDE_3: "EleutherAI/gpt-neo-2.7B",  # Placeholder
            BaseModelType.CLAUDE_2: "EleutherAI/gpt-neo-1.3B",  # Placeholder
            BaseModelType.GEMINI_PRO: "google/flan-t5-large",
            BaseModelType.GEMINI_ULTRA: "google/flan-t5-xl",
            BaseModelType.LLAMA_2: "meta-llama/Llama-2-7b-hf",
            BaseModelType.MISTRAL: "mistralai/Mistral-7B-v0.1",
        }
        
        model_name = model_map.get(base_model, "gpt2")
        
        # Load model and tokenizer
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.pad_token = tokenizer.eos_token
        
        return model, tokenizer
    
    def apply_lora(self, model, model_type: ModelType):
        """Apply LoRA for efficient fine-tuning"""
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=8,  # Low rank
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj"],
            inference_mode=False
        )
        
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        
        return model
    
    def prepare_training_args(self, job_id: str, config: TrainingConfig):
        """Prepare training arguments"""
        return TrainingArguments(
            output_dir=f"./outputs/{job_id}",
            num_train_epochs=config.epochs,
            per_device_train_batch_size=config.batch_size,
            per_device_eval_batch_size=config.batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            warmup_steps=config.warmup_steps,
            learning_rate=config.learning_rate,
            weight_decay=config.weight_decay,
            adam_epsilon=config.adam_epsilon,
            max_grad_norm=config.max_grad_norm,
            logging_dir=f"./logs/{job_id}",
            logging_steps=config.logging_steps,
            save_steps=config.save_steps,
            eval_steps=config.eval_steps,
            save_total_limit=config.save_total_limit,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="loss",
            fp16=config.fp16 and torch.cuda.is_available(),
            gradient_checkpointing=config.gradient_checkpointing,
            deepspeed=config.deepspeed,
            report_to=["mlflow", "wandb"] if os.getenv("WANDB_API_KEY") else ["mlflow"],
            push_to_hub=False
        )
    
    def create_trainer(self, model, tokenizer, dataset, training_args, model_type):
        """Create trainer instance"""
        # Tokenize dataset
        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                padding="max_length",
                max_length=training_args.max_length if hasattr(training_args, 'max_length') else 512
            )
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )
        
        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            eval_dataset=tokenized_dataset,  # Should use separate validation set
            data_collator=data_collator,
            tokenizer=tokenizer,
            compute_metrics=compute_metrics
        )
        
        return trainer
    
    async def start_rlhf_training(
        self,
        model_id: str,
        reward_model_id: str,
        dataset_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start RLHF training"""
        job_id = str(uuid.uuid4())
        rlhf_config = RLHFConfig(**config) if config else RLHFConfig()
        
        # Create RLHF job
        self.jobs[job_id] = {
            "id": job_id,
            "type": "rlhf",
            "status": TrainingStatus.PENDING,
            "model_id": model_id,
            "reward_model_id": reward_model_id,
            "dataset_id": dataset_id,
            "config": rlhf_config,
            "created_at": datetime.utcnow()
        }
        
        # Run RLHF training in background
        asyncio.create_task(self._run_rlhf_training(job_id))
        
        return job_id
    
    async def _run_rlhf_training(self, job_id: str):
        """Run RLHF training"""
        try:
            job = self.jobs[job_id]
            job["status"] = TrainingStatus.RUNNING
            
            # Load models
            model = AutoModelForCausalLMWithValueHead.from_pretrained(job["model_id"])
            ref_model = AutoModelForCausalLMWithValueHead.from_pretrained(job["model_id"])
            reward_model = AutoModelForSequenceClassification.from_pretrained(job["reward_model_id"])
            tokenizer = AutoTokenizer.from_pretrained(job["model_id"])
            
            # Load dataset
            dataset = await self.load_dataset(job["dataset_id"])
            
            # PPO configuration
            ppo_config = PPOConfig(
                batch_size=job["config"].batch_size,
                mini_batch_size=job["config"].mini_batch_size,
                gradient_accumulation_steps=job["config"].gradient_accumulation_steps,
                learning_rate=job["config"].learning_rate,
                kl_penalty="kl",
                init_kl_coef=job["config"].kl_penalty,
                horizon=10000,
                gamma=job["config"].gamma,
                lam=job["config"].lam,
                cliprange=job["config"].cliprange,
                cliprange_value=job["config"].cliprange_value,
                vf_coef=job["config"].vf_coef,
                ppo_epochs=job["config"].ppo_epochs
            )
            
            # Create PPO trainer
            ppo_trainer = PPOTrainer(
                config=ppo_config,
                model=model,
                ref_model=ref_model,
                tokenizer=tokenizer
            )
            
            # Training loop
            for step in range(job["config"].max_steps):
                # Sample batch
                batch = dataset.select(range(ppo_config.batch_size))
                
                # Generate responses
                query_tensors = tokenizer(batch["prompt"], return_tensors="pt", padding=True)
                response_tensors = ppo_trainer.generate(query_tensors, **generation_kwargs)
                
                # Compute rewards
                rewards = self.compute_rewards(response_tensors, reward_model, tokenizer)
                
                # Update policy
                stats = ppo_trainer.step(query_tensors, response_tensors, rewards)
                
                # Update job progress
                job["current_step"] = step
                job["reward_mean"] = stats["ppo/mean_scores"]
                job["kl_divergence"] = stats["objective/kl"]
                
                # Log metrics
                if step % 100 == 0:
                    logger.info(f"RLHF Step {step}: Reward={stats['ppo/mean_scores']:.3f}, KL={stats['objective/kl']:.3f}")
                    
                    if wandb.run:
                        wandb.log(stats, step=step)
            
            # Save final model
            model_path = f"models/rlhf_{job_id}"
            ppo_trainer.save_model(model_path)
            
            job["status"] = TrainingStatus.COMPLETED
            job["completed_at"] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"RLHF training failed for job {job_id}: {e}")
            job["status"] = TrainingStatus.FAILED
            job["error_message"] = str(e)
    
    def compute_rewards(self, response_tensors, reward_model, tokenizer):
        """Compute rewards using reward model"""
        # Decode responses
        responses = tokenizer.batch_decode(response_tensors, skip_special_tokens=True)
        
        # Get reward scores
        inputs = tokenizer(responses, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = reward_model(**inputs)
            rewards = outputs.logits.squeeze()
        
        return rewards
    
    async def update_job_status(self, job_id: str, progress: float, metrics: Dict):
        """Update job status in database"""
        async with get_db() as db:
            await db.execute(
                """
                UPDATE training_jobs 
                SET status = $1, progress = $2, metrics = $3, updated_at = $4
                WHERE id = $5
                """,
                self.jobs[job_id]["status"].value, progress, 
                json.dumps(metrics), datetime.utcnow(), job_id
            )
    
    async def register_model(self, job_id: str, model_path: str, metrics: Dict) -> str:
        """Register trained model"""
        model_id = str(uuid.uuid4())
        
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO models 
                (id, training_job_id, path, metrics, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                model_id, job_id, model_path, json.dumps(metrics), datetime.utcnow()
            )
        
        return model_id
    
    async def get_job_status(self, job_id: str) -> Optional[TrainingJobStatus]:
        """Get training job status"""
        if job_id not in self.jobs:
            # Try to load from database
            async with get_db() as db:
                result = await db.fetchone(
                    "SELECT * FROM training_jobs WHERE id = $1",
                    job_id
                )
                if result:
                    return TrainingJobStatus(
                        job_id=result["id"],
                        status=TrainingStatus(result["status"]),
                        progress=result.get("progress", 0),
                        metrics=result.get("metrics"),
                        started_at=result.get("started_at"),
                        completed_at=result.get("completed_at")
                    )
            return None
        
        job = self.jobs[job_id]
        return TrainingJobStatus(
            job_id=job_id,
            status=job["status"],
            progress=job.get("progress", 0),
            current_epoch=job.get("current_epoch"),
            total_epochs=job.get("hyperparameters", {}).epochs if "hyperparameters" in job else None,
            current_step=job.get("current_step"),
            metrics=job.get("metrics"),
            error_message=job.get("error_message"),
            started_at=job.get("started_at"),
            completed_at=job.get("completed_at")
        )
    
    async def stop_training(self, job_id: str) -> bool:
        """Stop a training job"""
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = TrainingStatus.STOPPED
            await self.update_job_status(job_id, self.jobs[job_id].get("progress", 0), 
                                        {"stopped": True})
            return True
        return False
    
    async def upload_dataset(
        self,
        name: str,
        description: str,
        file_path: str,
        dataset_type: str
    ) -> str:
        """Upload and register a dataset"""
        dataset_id = str(uuid.uuid4())
        
        # Get file info
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        file_format = file_path.split('.')[-1]
        
        # Count samples (simplified)
        num_samples = 0
        if file_format == "json":
            with open(file_path) as f:
                data = json.load(f)
                num_samples = len(data) if isinstance(data, list) else 1
        
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO datasets 
                (id, name, description, type, file_path, format, size_mb, num_samples, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                dataset_id, name, description, dataset_type, file_path, 
                file_format, file_size, num_samples, datetime.utcnow()
            )
        
        return dataset_id
    
    async def list_datasets(
        self,
        dataset_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict]:
        """List available datasets"""
        async with get_db() as db:
            query = "SELECT * FROM datasets"
            params = []
            
            if dataset_type:
                query += " WHERE type = $1"
                params.append(dataset_type)
            
            query += f" ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
            
            results = await db.fetch(query, *params)
            
        return [dict(r) for r in results]
    
    async def get_rlhf_status(self, job_id: str) -> Optional[Dict]:
        """Get RLHF training status"""
        if job_id in self.jobs and self.jobs[job_id].get("type") == "rlhf":
            job = self.jobs[job_id]
            return {
                "job_id": job_id,
                "status": job["status"].value,
                "current_step": job.get("current_step", 0),
                "total_steps": job.get("config", {}).max_steps,
                "reward_mean": job.get("reward_mean"),
                "kl_divergence": job.get("kl_divergence"),
                "started_at": job.get("started_at"),
                "completed_at": job.get("completed_at")
            }
        return None