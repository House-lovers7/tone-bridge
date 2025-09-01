from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from app.api import health, transform, analyze, advanced_transform
from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import init_redis

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await init_redis()
    yield
    # Shutdown
    # Add cleanup code here if needed

app = FastAPI(
    title="ToneBridge LLM Service",
    description="LLM service for message transformation and analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(transform.router, prefix="/transform", tags=["transform"])
app.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
app.include_router(advanced_transform.router, tags=["advanced"])


@app.get("/")
async def root():
    return {"message": "ToneBridge LLM Service", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
