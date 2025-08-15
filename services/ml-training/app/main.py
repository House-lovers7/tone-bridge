from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from app.models.schemas import (
    TrainingRequest,
    TrainingResponse,
    FeedbackData,
    ModelEvaluation,
    ABTestConfig,
    ABTestResult,
    ModelMetrics,
    TrainingStatus
)
from app.services.model_trainer import ModelTrainer
from app.services.feedback_collector import FeedbackCollector
from app.services.model_evaluator import ModelEvaluator
from app.services.ab_tester import ABTester
from app.services.model_registry import ModelRegistry
from app.database import init_db, get_db
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ML Training Service")
    await init_db()
    
    # Initialize services
    app.state.model_trainer = ModelTrainer()
    app.state.feedback_collector = FeedbackCollector()
    app.state.model_evaluator = ModelEvaluator()
    app.state.ab_tester = ABTester()
    app.state.model_registry = ModelRegistry()
    
    yield
    
    # Shutdown
    logger.info("Shutting down ML Training Service")

app = FastAPI(
    title="ToneBridge ML Training Service",
    description="Machine Learning model training and fine-tuning service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ml-training",
        "timestamp": datetime.utcnow().isoformat()
    }

# Training endpoints
@app.post("/train", response_model=TrainingResponse)
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
):
    """Start a new model training job"""
    try:
        trainer = app.state.model_trainer
        
        # Create training job
        job_id = await trainer.create_training_job(
            model_type=request.model_type,
            base_model=request.base_model,
            dataset_id=request.dataset_id,
            hyperparameters=request.hyperparameters,
            training_config=request.training_config
        )
        
        # Start training in background
        background_tasks.add_task(
            trainer.train_model,
            job_id=job_id
        )
        
        return TrainingResponse(
            job_id=job_id,
            status=TrainingStatus.PENDING,
            message="Training job created successfully",
            created_at=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/train/{job_id}/status")
async def get_training_status(job_id: str):
    """Get training job status"""
    try:
        trainer = app.state.model_trainer
        status = await trainer.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Training job not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train/{job_id}/stop")
async def stop_training(job_id: str):
    """Stop a training job"""
    try:
        trainer = app.state.model_trainer
        success = await trainer.stop_training(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Training job not found")
        
        return {"message": "Training stopped successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Feedback endpoints
@app.post("/feedback")
async def submit_feedback(feedback: FeedbackData):
    """Submit user feedback for model improvement"""
    try:
        collector = app.state.feedback_collector
        feedback_id = await collector.collect_feedback(
            user_id=feedback.user_id,
            session_id=feedback.session_id,
            input_text=feedback.input_text,
            output_text=feedback.output_text,
            transformation_type=feedback.transformation_type,
            rating=feedback.rating,
            corrections=feedback.corrections,
            metadata=feedback.metadata
        )
        
        return {
            "feedback_id": feedback_id,
            "message": "Feedback collected successfully"
        }
    except Exception as e:
        logger.error(f"Error collecting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/feedback/stats")
async def get_feedback_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get feedback statistics"""
    try:
        collector = app.state.feedback_collector
        stats = await collector.get_feedback_stats(start_date, end_date)
        return stats
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Evaluation endpoints
@app.post("/evaluate/{model_id}", response_model=ModelEvaluation)
async def evaluate_model(
    model_id: str,
    dataset_id: Optional[str] = None,
    metrics: Optional[List[str]] = None
):
    """Evaluate a trained model"""
    try:
        evaluator = app.state.model_evaluator
        
        evaluation = await evaluator.evaluate_model(
            model_id=model_id,
            dataset_id=dataset_id,
            metrics=metrics or ["accuracy", "f1", "perplexity", "bleu"]
        )
        
        return evaluation
    except Exception as e:
        logger.error(f"Error evaluating model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate/compare")
async def compare_models(
    model_ids: List[str],
    dataset_id: str,
    metrics: Optional[List[str]] = None
):
    """Compare multiple models"""
    try:
        evaluator = app.state.model_evaluator
        
        comparison = await evaluator.compare_models(
            model_ids=model_ids,
            dataset_id=dataset_id,
            metrics=metrics or ["accuracy", "f1", "perplexity", "bleu"]
        )
        
        return comparison
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# A/B Testing endpoints
@app.post("/ab-test", response_model=ABTestResult)
async def create_ab_test(config: ABTestConfig):
    """Create a new A/B test"""
    try:
        ab_tester = app.state.ab_tester
        
        test_id = await ab_tester.create_test(
            name=config.name,
            model_a_id=config.model_a_id,
            model_b_id=config.model_b_id,
            traffic_split=config.traffic_split,
            success_metrics=config.success_metrics,
            duration_hours=config.duration_hours
        )
        
        return ABTestResult(
            test_id=test_id,
            status="active",
            created_at=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ab-test/{test_id}/results")
async def get_ab_test_results(test_id: str):
    """Get A/B test results"""
    try:
        ab_tester = app.state.ab_tester
        results = await ab_tester.get_test_results(test_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting A/B test results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ab-test/{test_id}/stop")
async def stop_ab_test(test_id: str):
    """Stop an A/B test"""
    try:
        ab_tester = app.state.ab_tester
        success = await ab_tester.stop_test(test_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        return {"message": "A/B test stopped successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Model Registry endpoints
@app.get("/models")
async def list_models(
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """List available models"""
    try:
        registry = app.state.model_registry
        models = await registry.list_models(
            model_type=model_type,
            status=status,
            limit=limit,
            offset=offset
        )
        return models
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/{model_id}")
async def get_model_details(model_id: str):
    """Get model details"""
    try:
        registry = app.state.model_registry
        model = await registry.get_model(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    environment: str = "staging"
):
    """Deploy a model to production or staging"""
    try:
        registry = app.state.model_registry
        deployment_id = await registry.deploy_model(
            model_id=model_id,
            environment=environment
        )
        
        return {
            "deployment_id": deployment_id,
            "model_id": model_id,
            "environment": environment,
            "message": "Model deployed successfully"
        }
    except Exception as e:
        logger.error(f"Error deploying model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/{model_id}/rollback")
async def rollback_model(model_id: str):
    """Rollback a model deployment"""
    try:
        registry = app.state.model_registry
        success = await registry.rollback_model(model_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return {"message": "Model rolled back successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rolling back model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Metrics endpoints
@app.get("/metrics")
async def get_metrics(
    model_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get model performance metrics"""
    try:
        evaluator = app.state.model_evaluator
        metrics = await evaluator.get_metrics(
            model_id=model_id,
            start_date=start_date,
            end_date=end_date
        )
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dataset endpoints
@app.post("/datasets/upload")
async def upload_dataset(
    name: str,
    description: str,
    file_path: str,
    dataset_type: str = "training"
):
    """Upload a new dataset for training"""
    try:
        trainer = app.state.model_trainer
        dataset_id = await trainer.upload_dataset(
            name=name,
            description=description,
            file_path=file_path,
            dataset_type=dataset_type
        )
        
        return {
            "dataset_id": dataset_id,
            "message": "Dataset uploaded successfully"
        }
    except Exception as e:
        logger.error(f"Error uploading dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/datasets")
async def list_datasets(
    dataset_type: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """List available datasets"""
    try:
        trainer = app.state.model_trainer
        datasets = await trainer.list_datasets(
            dataset_type=dataset_type,
            limit=limit,
            offset=offset
        )
        return datasets
    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# RLHF endpoints
@app.post("/rlhf/start")
async def start_rlhf_training(
    model_id: str,
    reward_model_id: str,
    dataset_id: str,
    config: Optional[Dict[str, Any]] = None
):
    """Start RLHF (Reinforcement Learning from Human Feedback) training"""
    try:
        trainer = app.state.model_trainer
        job_id = await trainer.start_rlhf_training(
            model_id=model_id,
            reward_model_id=reward_model_id,
            dataset_id=dataset_id,
            config=config or {}
        )
        
        return {
            "job_id": job_id,
            "message": "RLHF training started successfully"
        }
    except Exception as e:
        logger.error(f"Error starting RLHF training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rlhf/{job_id}/status")
async def get_rlhf_status(job_id: str):
    """Get RLHF training status"""
    try:
        trainer = app.state.model_trainer
        status = await trainer.get_rlhf_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="RLHF job not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RLHF status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)