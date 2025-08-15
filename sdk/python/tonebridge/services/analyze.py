"""
Analyze Service
Handles text analysis operations
"""

from typing import Optional, Dict, Any, List, Union
from ..types import (
    AnalysisType,
    Priority,
    AnalyzeRequest,
    AnalyzeResponse,
)
from ..constants import API_ENDPOINTS, MAX_TEXT_LENGTH
from ..exceptions import ValidationError


class AnalyzeService:
    """Service for text analysis operations"""
    
    def __init__(self, client):
        """
        Initialize analyze service
        
        Args:
            client: ToneBridgeClient instance
        """
        self.client = client
    
    def analyze(
        self,
        text: str,
        analysis_types: Optional[List[Union[AnalysisType, str]]] = None,
        include_suggestions: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze text
        
        Args:
            text: Text to analyze
            analysis_types: Types of analysis to perform
            include_suggestions: Include improvement suggestions
            metadata: Additional metadata
            
        Returns:
            Analysis results
            
        Example:
            >>> result = client.analyze.analyze(
            ...     "This is urgent!",
            ...     analysis_types=[AnalysisType.TONE, AnalysisType.PRIORITY],
            ...     include_suggestions=True
            ... )
        """
        self._validate_analyze_request(text)
        
        request_data = {
            "text": text,
            "include_suggestions": include_suggestions,
        }
        
        if analysis_types:
            request_data["analysis_types"] = [
                t.value if isinstance(t, AnalysisType) else t
                for t in analysis_types
            ]
        
        if metadata:
            request_data["metadata"] = metadata
        
        return self.client.request("POST", API_ENDPOINTS["ANALYZE"], json=request_data)
    
    def analyze_tone(self, text: str) -> str:
        """
        Analyze text tone
        
        Args:
            text: Text to analyze
            
        Returns:
            Tone of the text
        """
        result = self.analyze(text, analysis_types=[AnalysisType.TONE])
        return result.get("data", {}).get("tone", "unknown")
    
    def analyze_clarity(self, text: str) -> float:
        """
        Analyze text clarity
        
        Args:
            text: Text to analyze
            
        Returns:
            Clarity score (0-100)
        """
        result = self.analyze(text, analysis_types=[AnalysisType.CLARITY])
        return result.get("data", {}).get("clarity_score", 0.0)
    
    def analyze_priority(self, text: str) -> Dict[str, str]:
        """
        Analyze text priority
        
        Args:
            text: Text to analyze
            
        Returns:
            Priority and quadrant information
        """
        result = self.analyze(text, analysis_types=[AnalysisType.PRIORITY])
        data = result.get("data", {})
        return {
            "priority": data.get("priority", "medium"),
            "quadrant": data.get("priority_quadrant"),
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze text sentiment
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment polarity and subjectivity
        """
        result = self.analyze(text, analysis_types=[AnalysisType.SENTIMENT])
        return result.get("data", {}).get("sentiment", {})
    
    def comprehensive_analysis(
        self,
        text: str,
        include_suggestions: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis with all types
        
        Args:
            text: Text to analyze
            include_suggestions: Include improvement suggestions
            
        Returns:
            Comprehensive analysis results
        """
        return self.analyze(
            text,
            analysis_types=[
                AnalysisType.TONE,
                AnalysisType.CLARITY,
                AnalysisType.PRIORITY,
                AnalysisType.SENTIMENT,
                AnalysisType.STRUCTURE,
                AnalysisType.COMPLETENESS,
            ],
            include_suggestions=include_suggestions,
        )
    
    def score_priority(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Score priority using Eisenhower Matrix
        
        Args:
            text: Text to score
            context: Additional context
            
        Returns:
            Priority score and quadrant information
        """
        request_data = {"text": text}
        if context:
            request_data["context"] = context
        
        return self.client.request(
            "POST",
            API_ENDPOINTS["SCORE_PRIORITY"],
            json=request_data
        )
    
    def batch_score_priorities(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Batch score priorities for multiple messages
        
        Args:
            messages: List of messages to score
            
        Returns:
            List of priority scores
        """
        return self.client.request(
            "POST",
            API_ENDPOINTS["BATCH_SCORE_PRIORITIES"],
            json={"messages": messages}
        )
    
    def check_needs_transformation(self, text: str) -> Dict[str, Any]:
        """
        Check if text needs transformation
        
        Args:
            text: Text to check
            
        Returns:
            Recommendation for transformation
        """
        analysis = self.comprehensive_analysis(text, include_suggestions=True)
        data = analysis.get("data", {})
        
        needs_transformation = (
            data.get("clarity_score", 100) < 70 or
            data.get("tone") in ["harsh", "technical"] or
            data.get("sentiment", {}).get("polarity", 0) < -0.3
        )
        
        reasons = []
        if data.get("clarity_score", 100) < 70:
            reasons.append("Low clarity score")
        if data.get("tone") == "harsh":
            reasons.append("Harsh tone detected")
        if data.get("tone") == "technical":
            reasons.append("Technical language detected")
        if data.get("sentiment", {}).get("polarity", 0) < -0.3:
            reasons.append("Negative sentiment")
        
        recommended_type = "soften"
        if data.get("clarity_score", 100) < 60:
            recommended_type = "clarify"
        elif data.get("tone") == "technical":
            recommended_type = "terminology"
        
        return {
            "needs_transformation": needs_transformation,
            "recommended_type": recommended_type if needs_transformation else None,
            "confidence": 0.8 if needs_transformation else 0.2,
            "reasons": reasons,
        }
    
    def get_suggestions(self, text: str) -> List[str]:
        """
        Get improvement suggestions for text
        
        Args:
            text: Text to get suggestions for
            
        Returns:
            List of suggestions
        """
        result = self.analyze(text, include_suggestions=True)
        return result.get("data", {}).get("suggestions", [])
    
    def _validate_analyze_request(self, text: str) -> None:
        """Validate analyze request parameters"""
        if not text:
            raise ValidationError("Text is required")
        
        if len(text) > MAX_TEXT_LENGTH:
            raise ValidationError(f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters")