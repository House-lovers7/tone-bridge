from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import json
import hashlib
from app.core.redis_client import get_redis
from app.core.config import settings
from app.chains.transformation import (
    tone_transformation_chain,
    structure_transformation_chain,
    summarization_chain,
    terminology_chain
)

router = APIRouter()

class TransformRequest(BaseModel):
    text: str
    transformation_type: str
    target_tone: Optional[str] = None
    options: Optional[Dict[str, str]] = None

class TransformResponse(BaseModel):
    transformed_text: str
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/", response_model=TransformResponse)
async def transform_text(
    request: TransformRequest,
    redis_client = Depends(get_redis)
):
    """Transform text based on specified transformation type"""
    
    # Create cache key
    cache_key = f"transform:{request.transformation_type}:{request.target_tone or 'default'}:{hashlib.md5(request.text.encode()).hexdigest()}"
    
    # Check cache
    cached = await redis_client.get(cache_key)
    if cached:
        return TransformResponse(**json.loads(cached))
    
    try:
        # Select appropriate chain based on transformation type
        if request.transformation_type == "tone":
            if not request.target_tone:
                raise HTTPException(400, "target_tone is required for tone transformation")
            
            # Extract intensity level from options, default to 2 (moderate)
            intensity_level = int(request.options.get('intensity', '2')) if request.options else 2
            
            result = await tone_transformation_chain.ainvoke({
                "text": request.text,
                "target_tone": request.target_tone,
                "intensity_level": intensity_level
            })
            
        elif request.transformation_type == "structure":
            result = await structure_transformation_chain.ainvoke({
                "text": request.text,
                "options": request.options or {}
            })
            
        elif request.transformation_type == "summarize":
            result = await summarization_chain.ainvoke({
                "text": request.text,
                "max_length": request.options.get("max_length", 200) if request.options else 200
            })
            
        elif request.transformation_type == "terminology":
            result = await terminology_chain.ainvoke({
                "text": request.text,
                "domain": request.options.get("domain", "general") if request.options else "general"
            })
            
        else:
            raise HTTPException(400, f"Unknown transformation type: {request.transformation_type}")
        
        # Extract response
        response = TransformResponse(
            transformed_text=result.get("text", request.text),
            suggestions=result.get("suggestions", []),
            metadata=result.get("metadata", {})
        )
        
        # Cache the response
        await redis_client.setex(
            cache_key,
            settings.CACHE_TTL,
            json.dumps(response.dict())
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(500, f"Transformation failed: {str(e)}")