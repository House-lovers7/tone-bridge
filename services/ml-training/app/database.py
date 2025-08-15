import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Boolean, Text, ForeignKey, Index
from sqlalchemy.sql import func
from redis import asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Global database objects
engine = None
async_session_maker = None
redis_client = None


class TrainingJob(Base):
    """Training job model"""
    __tablename__ = "training_jobs"
    
    id = Column(String, primary_key=True)
    model_type = Column(String, nullable=False)
    base_model = Column(String, nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")
    config = Column(JSON, nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    progress = Column(Float, default=0.0)
    metrics = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_training_jobs_status", "status"),
        Index("idx_training_jobs_created_at", "created_at"),
    )


class Model(Base):
    """Trained model registry"""
    __tablename__ = "models"
    
    id = Column(String, primary_key=True)
    training_job_id = Column(String, ForeignKey("training_jobs.id"), nullable=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    model_type = Column(String, nullable=False)
    base_model = Column(String, nullable=False)
    path = Column(String, nullable=False)
    metrics = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="draft")  # draft, staging, production, archived
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_models_status", "status"),
        Index("idx_models_model_type", "model_type"),
        Index("idx_models_created_at", "created_at"),
    )


class Dataset(Base):
    """Training dataset registry"""
    __tablename__ = "datasets"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String, nullable=False)  # training, validation, test, feedback
    file_path = Column(String, nullable=False)
    format = Column(String, nullable=False)  # json, csv, parquet, etc.
    size_mb = Column(Float, nullable=True)
    num_samples = Column(Integer, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_datasets_type", "type"),
        Index("idx_datasets_created_at", "created_at"),
    )


class Feedback(Base):
    """User feedback for model improvement"""
    __tablename__ = "feedback"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    session_id = Column(String, nullable=True)
    model_id = Column(String, ForeignKey("models.id"), nullable=True)
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=False)
    corrected_text = Column(Text, nullable=True)
    transformation_type = Column(String, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 rating
    feedback_type = Column(String, nullable=True)  # positive, negative, correction
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_feedback_user_id", "user_id"),
        Index("idx_feedback_rating", "rating"),
        Index("idx_feedback_created_at", "created_at"),
    )


class ABTest(Base):
    """A/B test configuration and results"""
    __tablename__ = "ab_tests"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    model_a_id = Column(String, ForeignKey("models.id"), nullable=False)
    model_b_id = Column(String, ForeignKey("models.id"), nullable=False)
    traffic_split = Column(Float, default=0.5)  # Percentage for model A
    success_metrics = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="active")  # active, paused, completed
    winner = Column(String, nullable=True)  # model_a or model_b
    results = Column(JSON, nullable=True)
    duration_hours = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("idx_ab_tests_status", "status"),
        Index("idx_ab_tests_created_at", "created_at"),
    )


class ModelMetrics(Base):
    """Model performance metrics over time"""
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String, ForeignKey("models.id"), nullable=False)
    metric_type = Column(String, nullable=False)  # accuracy, latency, throughput, etc.
    value = Column(Float, nullable=False)
    metadata = Column(JSON, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_model_metrics_model_id", "model_id"),
        Index("idx_model_metrics_type", "metric_type"),
        Index("idx_model_metrics_recorded_at", "recorded_at"),
    )


async def init_db():
    """Initialize database connections"""
    global engine, async_session_maker, redis_client
    
    try:
        # Create async engine
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Create session maker
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create tables (for development)
        if settings.ENVIRONMENT == "development":
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        
        # Initialize Redis client
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50
        )
        
        # Test connections
        async with async_session_maker() as session:
            result = await session.execute("SELECT 1")
            logger.info(f"Database connection successful: {result.scalar()}")
        
        await redis_client.ping()
        logger.info("Redis connection successful")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """Close database connections"""
    global engine, redis_client
    
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    return redis_client


# Direct PostgreSQL connection for raw queries
class PostgresConnection:
    """Direct PostgreSQL connection manager"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def init(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            min_size=10,
            max_size=20,
            command_timeout=60
        )
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def execute(self, query: str, *args):
        """Execute a query"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """Fetch multiple rows"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchone(self, query: str, *args):
        """Fetch a single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """Fetch a single value"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)


# Global PostgreSQL connection
pg_connection = PostgresConnection()


async def init_postgres():
    """Initialize PostgreSQL connection"""
    await pg_connection.init()
    logger.info("PostgreSQL connection pool initialized")


async def close_postgres():
    """Close PostgreSQL connection"""
    await pg_connection.close()
    logger.info("PostgreSQL connection pool closed")


# Utility functions for backwards compatibility
async def get_pg_connection():
    """Get PostgreSQL connection (for backwards compatibility)"""
    return pg_connection