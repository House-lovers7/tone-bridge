from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, validator


class ModelType(str, Enum):
    """Model types for different transformation tasks"""
    TONE_ADJUSTMENT = "tone_adjustment"
    STRUCTURE = "structure"
    SUMMARIZATION = "summarization"
    TERMINOLOGY = "terminology"
    REQUIREMENT_STRUCTURING = "requirement_structuring"
    BACKGROUND_COMPLETION = "background_completion"
    PRIORITY_SCORING = "priority_scoring"
    GENERAL = "general"


class BaseModelType(str, Enum):
    """Base model providers"""
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"
    CLAUDE_3 = "claude-3"
    CLAUDE_2 = "claude-2"
    GEMINI_PRO = "gemini-pro"
    GEMINI_ULTRA = "gemini-ultra"
    LLAMA_2 = "llama-2"
    MISTRAL = "mistral"
    CUSTOM = "custom"


class TrainingStatus(str, Enum):
    """Training job status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    PAUSED = "paused"


class DatasetType(str, Enum):
    """Dataset types"""
    TRAINING = "training"
    VALIDATION = "validation"
    TEST = "test"
    FEEDBACK = "feedback"


class ModelStatus(str, Enum):
    """Model deployment status"""
    DRAFT = "draft"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class FeedbackType(str, Enum):
    """Feedback types"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    CORRECTION = "correction"
    NEUTRAL = "neutral"


# Training Configuration Schemas
class TrainingConfig(BaseModel):
    """Training hyperparameters configuration"""
    epochs: int = Field(default=3, ge=1, le=100)
    batch_size: int = Field(default=8, ge=1, le=128)
    learning_rate: float = Field(default=5e-5, ge=1e-8, le=1e-2)
    warmup_steps: int = Field(default=500, ge=0)
    weight_decay: float = Field(default=0.01, ge=0.0, le=1.0)
    adam_epsilon: float = Field(default=1e-8)
    max_grad_norm: float = Field(default=1.0, ge=0.0)
    gradient_accumulation_steps: int = Field(default=1, ge=1)
    logging_steps: int = Field(default=10, ge=1)
    save_steps: int = Field(default=500, ge=1)
    eval_steps: int = Field(default=500, ge=1)
    save_total_limit: int = Field(default=3, ge=1)
    fp16: bool = Field(default=True)
    gradient_checkpointing: bool = Field(default=True)
    deepspeed: Optional[Dict[str, Any]] = None
    max_seq_length: int = Field(default=512, ge=32, le=4096)
    
    @validator('learning_rate')
    def validate_learning_rate(cls, v):
        if v <= 0:
            raise ValueError("Learning rate must be positive")
        return v


class LoRAConfig(BaseModel):
    """LoRA configuration for parameter-efficient fine-tuning"""
    r: int = Field(default=8, description="LoRA rank", ge=1, le=128)
    lora_alpha: int = Field(default=32, ge=1)
    lora_dropout: float = Field(default=0.1, ge=0.0, le=1.0)
    target_modules: List[str] = Field(
        default=["q_proj", "v_proj", "k_proj", "o_proj"],
        description="Target modules for LoRA"
    )
    bias: str = Field(default="none", pattern="^(none|all|lora_only)$")
    task_type: str = Field(default="CAUSAL_LM")
    inference_mode: bool = Field(default=False)


class RLHFConfig(BaseModel):
    """RLHF (Reinforcement Learning from Human Feedback) configuration"""
    batch_size: int = Field(default=128, ge=1)
    mini_batch_size: int = Field(default=4, ge=1)
    gradient_accumulation_steps: int = Field(default=1, ge=1)
    ppo_epochs: int = Field(default=4, ge=1)
    learning_rate: float = Field(default=1e-5, ge=1e-8)
    kl_penalty: float = Field(default=0.1, ge=0.0)
    gamma: float = Field(default=0.99, ge=0.0, le=1.0)
    lam: float = Field(default=0.95, ge=0.0, le=1.0)
    cliprange: float = Field(default=0.2, ge=0.0)
    cliprange_value: float = Field(default=0.2, ge=0.0)
    vf_coef: float = Field(default=0.5, ge=0.0)
    max_steps: int = Field(default=10000, ge=1)


# Request/Response Schemas
class TrainingRequest(BaseModel):
    """Training job request"""
    model_type: ModelType
    base_model: BaseModelType
    dataset_id: str
    hyperparameters: Optional[TrainingConfig] = None
    lora_config: Optional[LoRAConfig] = None
    training_config: Optional[Dict[str, Any]] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class TrainingResponse(BaseModel):
    """Training job response"""
    job_id: str
    status: TrainingStatus
    message: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None


class TrainingJobStatus(BaseModel):
    """Training job status details"""
    job_id: str
    status: TrainingStatus
    progress: float = Field(ge=0.0, le=100.0)
    current_epoch: Optional[int] = None
    total_epochs: Optional[int] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    metrics: Optional[Dict[str, float]] = None
    loss: Optional[float] = None
    learning_rate: Optional[float] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_time_remaining: Optional[int] = None  # seconds


class FeedbackData(BaseModel):
    """User feedback data"""
    user_id: str
    session_id: Optional[str] = None
    input_text: str = Field(min_length=1, max_length=10000)
    output_text: str = Field(min_length=1, max_length=10000)
    corrected_text: Optional[str] = Field(default=None, max_length=10000)
    transformation_type: ModelType
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    feedback_type: Optional[FeedbackType] = None
    corrections: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ModelEvaluation(BaseModel):
    """Model evaluation results"""
    model_id: str
    dataset_id: str
    metrics: Dict[str, float]
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    perplexity: Optional[float] = None
    bleu_score: Optional[float] = None
    rouge_scores: Optional[Dict[str, float]] = None
    inference_time_ms: Optional[float] = None
    evaluated_at: datetime
    num_samples: int
    errors: Optional[List[Dict[str, Any]]] = None


class ABTestConfig(BaseModel):
    """A/B test configuration"""
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    model_a_id: str
    model_b_id: str
    traffic_split: float = Field(default=0.5, ge=0.0, le=1.0)
    success_metrics: List[str] = Field(min_items=1)
    minimum_sample_size: int = Field(default=1000, ge=100)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)
    duration_hours: Optional[int] = Field(default=24, ge=1)
    auto_conclude: bool = Field(default=True)


class ABTestResult(BaseModel):
    """A/B test results"""
    test_id: str
    status: str
    model_a_metrics: Dict[str, float]
    model_b_metrics: Dict[str, float]
    winner: Optional[str] = None
    confidence: Optional[float] = None
    p_value: Optional[float] = None
    sample_size_a: int
    sample_size_b: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class ModelMetrics(BaseModel):
    """Model performance metrics"""
    model_id: str
    latency_p50: float
    latency_p95: float
    latency_p99: float
    throughput: float  # requests per second
    error_rate: float
    memory_usage_mb: float
    gpu_utilization: Optional[float] = None
    cost_per_1k_tokens: Optional[float] = None
    total_requests: int
    total_tokens: int
    recorded_at: datetime


class DatasetUpload(BaseModel):
    """Dataset upload request"""
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    type: DatasetType
    format: str = Field(pattern="^(json|csv|parquet|txt|jsonl)$")
    tags: Optional[List[str]] = None


class DatasetInfo(BaseModel):
    """Dataset information"""
    id: str
    name: str
    description: Optional[str] = None
    type: DatasetType
    format: str
    file_path: str
    size_mb: float
    num_samples: int
    columns: Optional[List[str]] = None
    statistics: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ModelDeployRequest(BaseModel):
    """Model deployment request"""
    model_id: str
    environment: str = Field(default="staging", pattern="^(staging|production)$")
    replicas: int = Field(default=1, ge=1, le=10)
    cpu_request: str = Field(default="1", pattern="^[0-9]+m?$")
    memory_request: str = Field(default="2Gi", pattern="^[0-9]+[KMGi]+$")
    gpu_request: Optional[int] = Field(default=None, ge=0, le=8)
    auto_scaling: bool = Field(default=True)
    min_replicas: int = Field(default=1, ge=1)
    max_replicas: int = Field(default=10, ge=1, le=100)
    target_cpu_utilization: int = Field(default=70, ge=10, le=90)


class ModelInfo(BaseModel):
    """Model information"""
    id: str
    name: str
    version: str
    model_type: ModelType
    base_model: BaseModelType
    status: ModelStatus
    training_job_id: Optional[str] = None
    metrics: Optional[ModelEvaluation] = None
    config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    deployed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    model_id: str
    dataset_id: str
    output_format: str = Field(default="json", pattern="^(json|csv|parquet)$")
    batch_size: int = Field(default=32, ge=1, le=1000)
    max_length: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    num_return_sequences: int = Field(default=1, ge=1, le=10)


class FeedbackStats(BaseModel):
    """Feedback statistics"""
    total_feedback: int
    average_rating: Optional[float] = None
    rating_distribution: Dict[int, int]
    feedback_by_type: Dict[str, int]
    feedback_by_transformation: Dict[str, int]
    most_common_corrections: List[Dict[str, Any]]
    trend_data: Optional[List[Dict[str, Any]]] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None