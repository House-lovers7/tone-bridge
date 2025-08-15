import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from enum import Enum


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )
    
    # Environment
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ToneBridge ML Training Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    
    # Server Settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8004)
    WORKERS: int = Field(default=1)
    
    # Database
    POSTGRES_HOST: str = Field(default="postgres")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="tonebridge")
    POSTGRES_PASSWORD: str = Field(default="password")
    POSTGRES_DB: str = Field(default="tonebridge_db")
    DATABASE_URL: Optional[str] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return (
            f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_HOST')}:"
            f"{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
        )
    
    # Redis
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        password = values.get("REDIS_PASSWORD")
        if password:
            return f"redis://:{password}@{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
    
    # Model Settings
    MODEL_CACHE_DIR: str = Field(default="/app/models")
    DATASET_CACHE_DIR: str = Field(default="/app/datasets")
    CHECKPOINT_DIR: str = Field(default="/app/checkpoints")
    OUTPUT_DIR: str = Field(default="/app/outputs")
    LOG_DIR: str = Field(default="/app/logs")
    
    # Training Settings
    DEFAULT_BATCH_SIZE: int = Field(default=8)
    DEFAULT_LEARNING_RATE: float = Field(default=5e-5)
    DEFAULT_EPOCHS: int = Field(default=3)
    DEFAULT_WARMUP_STEPS: int = Field(default=500)
    DEFAULT_LOGGING_STEPS: int = Field(default=10)
    DEFAULT_SAVE_STEPS: int = Field(default=500)
    DEFAULT_EVAL_STEPS: int = Field(default=500)
    MAX_SEQ_LENGTH: int = Field(default=512)
    GRADIENT_CHECKPOINTING: bool = Field(default=True)
    FP16_TRAINING: bool = Field(default=True)
    
    # LoRA Settings
    LORA_R: int = Field(default=8, description="LoRA rank")
    LORA_ALPHA: int = Field(default=32, description="LoRA alpha")
    LORA_DROPOUT: float = Field(default=0.1, description="LoRA dropout")
    LORA_TARGET_MODULES: List[str] = Field(
        default=["q_proj", "v_proj", "k_proj", "o_proj"],
        description="Target modules for LoRA"
    )
    
    # RLHF Settings
    PPO_BATCH_SIZE: int = Field(default=128)
    PPO_MINI_BATCH_SIZE: int = Field(default=4)
    PPO_GRADIENT_ACCUMULATION: int = Field(default=1)
    PPO_EPOCHS: int = Field(default=4)
    KL_PENALTY: float = Field(default=0.1)
    REWARD_MODEL_PATH: Optional[str] = None
    
    # MLflow Settings
    MLFLOW_TRACKING_URI: str = Field(default="http://localhost:5000")
    MLFLOW_EXPERIMENT_NAME: str = Field(default="tonebridge-training")
    MLFLOW_ARTIFACT_LOCATION: str = Field(default="/app/mlflow-artifacts")
    
    # Weights & Biases Settings
    WANDB_API_KEY: Optional[str] = None
    WANDB_PROJECT: str = Field(default="tonebridge")
    WANDB_ENTITY: Optional[str] = None
    
    # Model Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None
    
    # Model Registry
    MODEL_REGISTRY_BUCKET: Optional[str] = None
    MODEL_REGISTRY_PATH: str = Field(default="/app/model-registry")
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-here")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:8080",
        ]
    )
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PORT: int = Field(default=9090)
    
    # GPU Settings
    CUDA_VISIBLE_DEVICES: Optional[str] = None
    DEVICE_MAP: str = Field(default="auto")
    MAX_MEMORY: Optional[dict] = None
    
    # Performance
    NUM_WORKERS: int = Field(default=4)
    MAX_CONCURRENT_JOBS: int = Field(default=2)
    JOB_TIMEOUT_HOURS: int = Field(default=24)
    
    # Storage
    USE_S3: bool = Field(default=False)
    S3_BUCKET: Optional[str] = None
    S3_REGION: str = Field(default="us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.MODEL_CACHE_DIR,
            self.DATASET_CACHE_DIR,
            self.CHECKPOINT_DIR,
            self.OUTPUT_DIR,
            self.LOG_DIR,
            self.MODEL_REGISTRY_PATH,
            self.MLFLOW_ARTIFACT_LOCATION,
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    class Config:
        """Pydantic config"""
        case_sensitive = True
        validate_assignment = True


# Create global settings instance
settings = Settings()

# Create directories on initialization
settings.create_directories()