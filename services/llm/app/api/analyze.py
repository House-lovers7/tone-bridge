from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from app.chains.analysis import (
    tone_analysis_chain,
    clarity_analysis_chain,
    structure_analysis_chain,
    priority_detection_chain
)

router = APIRouter()

class AnalyzeRequest(BaseModel):
    text: str

class AnalyzeResponse(BaseModel):
    tone: str
    clarity: float
    structure: Dict[str, Any]
    suggestions: List[str]
    priority: str
    terms_found: List[Dict[str, str]] = []

@router.post("/", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """Analyze text for tone, clarity, structure, and priority"""
    
    try:
        # Run all analysis chains in parallel
        import asyncio
        
        tone_task = tone_analysis_chain.ainvoke({"text": request.text})
        clarity_task = clarity_analysis_chain.ainvoke({"text": request.text})
        structure_task = structure_analysis_chain.ainvoke({"text": request.text})
        priority_task = priority_detection_chain.ainvoke({"text": request.text})
        
        results = await asyncio.gather(
            tone_task,
            clarity_task,
            structure_task,
            priority_task
        )
        
        tone_result = results[0]
        clarity_result = results[1]
        structure_result = results[2]
        priority_result = results[3]
        
        # Combine results
        response = AnalyzeResponse(
            tone=tone_result.get("tone", "neutral"),
            clarity=clarity_result.get("clarity_score", 0.5),
            structure=structure_result.get("structure", {}),
            suggestions=structure_result.get("suggestions", []),
            priority=priority_result.get("priority", "medium"),
            terms_found=structure_result.get("technical_terms", [])
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")