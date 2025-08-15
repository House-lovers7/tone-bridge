"""
Advanced Transformation API Endpoints
Handles new features: requirement structuring, background completion, priority scoring
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.chains.requirement_structuring import structure_requirements, generate_structured_summary
from app.chains.background_completion import complete_communication, analyze_background_completeness
from app.chains.priority_scoring import score_priority, batch_score_priorities, get_priority_emoji
from app.chains.tone_adjustment import ToneAdjuster

router = APIRouter(prefix="/api/v1/advanced", tags=["advanced"])

# Request/Response Models
class RequirementStructureRequest(BaseModel):
    text: str = Field(..., description="Text to structure into requirements")
    context: Optional[str] = Field(None, description="Additional context")
    generate_summary: bool = Field(True, description="Generate formatted summary")

class BackgroundCompletionRequest(BaseModel):
    text: str = Field(..., description="Text to analyze for missing background")
    auto_mode: bool = Field(False, description="Auto-complete vs generate questions")
    communication_type: str = Field("business", description="Type of communication")
    domain: str = Field("general", description="Domain context")
    recipient_role: Optional[str] = Field(None, description="Role of recipient")
    organization_context: Optional[str] = Field(None, description="Organization context")

class PriorityScoreRequest(BaseModel):
    text: str = Field(..., description="Text to score for priority")
    sender_role: Optional[str] = Field(None, description="Role of sender")
    context: Optional[str] = Field(None, description="Additional context")

class BatchPriorityRequest(BaseModel):
    messages: List[Dict[str, str]] = Field(..., description="List of messages to rank")
    context: Optional[str] = Field(None, description="Overall context")

class ToneAdjustmentRequest(BaseModel):
    text: str = Field(..., description="Text to transform")
    intensity: int = Field(2, ge=0, le=3, description="Transformation intensity (0-3)")
    target_tone: str = Field("warm", description="Target tone")
    preset: Optional[str] = Field(None, description="Preset configuration")
    generate_variations: bool = Field(False, description="Generate all intensity variations")

# Endpoints

@router.post("/structure-requirements")
async def structure_requirements_endpoint(request: RequirementStructureRequest):
    """
    Structure unstructured text into organized requirements with 4 quadrants
    """
    try:
        result = structure_requirements(request.text, request.context)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))
        
        # Generate formatted summary if requested
        if request.generate_summary and result["success"]:
            summary = generate_structured_summary(result["data"])
            result["data"]["formatted_summary"] = summary
        
        return {
            "success": True,
            "data": result["data"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complete-background")
async def complete_background_endpoint(request: BackgroundCompletionRequest):
    """
    Analyze and complete missing background information
    """
    try:
        result = complete_communication(
            text=request.text,
            auto_mode=request.auto_mode,
            communication_type=request.communication_type,
            domain=request.domain,
            recipient_role=request.recipient_role,
            organization_context=request.organization_context
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))
        
        return {
            "success": True,
            "data": result["data"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/score-priority")
async def score_priority_endpoint(request: PriorityScoreRequest):
    """
    Score message priority using Eisenhower Matrix
    """
    try:
        result = score_priority(
            text=request.text,
            sender_role=request.sender_role,
            context=request.context
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))
        
        # Add emoji representation
        priority_data = result["data"]
        priority_data["priority_emoji"] = get_priority_emoji(priority_data["priority_level"])
        
        return {
            "success": True,
            "data": priority_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-score-priorities")
async def batch_score_priorities_endpoint(request: BatchPriorityRequest):
    """
    Score and rank multiple messages by priority
    """
    try:
        result = batch_score_priorities(
            messages=request.messages,
            context=request.context
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))
        
        return {
            "success": True,
            "data": result["data"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adjust-tone")
async def adjust_tone_endpoint(request: ToneAdjustmentRequest):
    """
    Transform text with adjustable intensity slider
    """
    try:
        # Generate all variations if requested
        if request.generate_variations:
            result = ToneAdjuster.generate_intensity_variations(
                text=request.text,
                target_tone=request.target_tone
            )
        else:
            # Single transformation with specified intensity
            result = ToneAdjuster.transform_with_slider(
                text=request.text,
                intensity=request.intensity,
                target_tone=request.target_tone,
                preset=request.preset
            )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))
        
        return {
            "success": True,
            "data": result["data"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-detect-intensity")
async def auto_detect_intensity_endpoint(request: Dict[str, Any]):
    """
    Automatically detect appropriate transformation intensity
    """
    try:
        text = request.get("text", "")
        context = request.get("context", {})
        
        intensity = ToneAdjuster.auto_detect_intensity(text, context)
        
        return {
            "success": True,
            "data": {
                "recommended_intensity": intensity,
                "description": ToneAdjuster.INTENSITY_DESCRIPTIONS[intensity]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tone-presets")
async def get_tone_presets():
    """
    Get available tone transformation presets
    """
    return {
        "success": True,
        "data": {
            "presets": ToneAdjuster.PRESETS,
            "intensity_levels": ToneAdjuster.INTENSITY_DESCRIPTIONS
        }
    }

# Health check for new features
@router.get("/health")
async def health_check():
    """
    Check if advanced features are operational
    """
    return {
        "status": "healthy",
        "features": {
            "requirement_structuring": "active",
            "background_completion": "active",
            "priority_scoring": "active",
            "tone_adjustment": "active"
        }
    }