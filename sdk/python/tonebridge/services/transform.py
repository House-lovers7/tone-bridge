"""
Transform Service
Handles text transformation operations
"""

from typing import Optional, Dict, Any, List, Union
from ..types import (
    TransformationType,
    TransformOptions,
    TransformRequest,
    TransformResponse,
    BatchTransformRequest,
)
from ..constants import (
    API_ENDPOINTS,
    DEFAULT_INTENSITY,
    MAX_TEXT_LENGTH,
)
from ..exceptions import ValidationError


class TransformService:
    """Service for text transformation operations"""
    
    def __init__(self, client):
        """
        Initialize transform service
        
        Args:
            client: ToneBridgeClient instance
        """
        self.client = client
    
    def transform(
        self,
        text: str,
        transformation_type: Union[TransformationType, str],
        intensity: int = DEFAULT_INTENSITY,
        options: Optional[TransformOptions] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Transform text
        
        Args:
            text: Text to transform
            transformation_type: Type of transformation
            intensity: Transformation intensity (0-3)
            options: Transformation options
            metadata: Additional metadata
            
        Returns:
            Transformation response
            
        Example:
            >>> result = client.transform.transform(
            ...     "This needs to be fixed",
            ...     TransformationType.SOFTEN,
            ...     intensity=2
            ... )
        """
        self._validate_transform_request(text, transformation_type, intensity)
        
        request_data = {
            "text": text,
            "transformation_type": transformation_type.value if isinstance(transformation_type, TransformationType) else transformation_type,
            "intensity": intensity,
        }
        
        if options:
            request_data["options"] = options.__dict__ if hasattr(options, '__dict__') else options
        
        if metadata:
            request_data["metadata"] = metadata
        
        return self.client.request("POST", API_ENDPOINTS["TRANSFORM"], json=request_data)
    
    def soften(
        self,
        text: str,
        intensity: int = DEFAULT_INTENSITY,
        options: Optional[TransformOptions] = None,
    ) -> Dict[str, Any]:
        """
        Soften harsh language
        
        Args:
            text: Text to soften
            intensity: Transformation intensity (0-3)
            options: Transformation options
            
        Returns:
            Transformation response
        """
        return self.transform(text, TransformationType.SOFTEN, intensity, options)
    
    def clarify(
        self,
        text: str,
        intensity: int = DEFAULT_INTENSITY,
        options: Optional[TransformOptions] = None,
    ) -> Dict[str, Any]:
        """
        Clarify confusing text
        
        Args:
            text: Text to clarify
            intensity: Transformation intensity (0-3)
            options: Transformation options
            
        Returns:
            Transformation response
        """
        return self.transform(text, TransformationType.CLARIFY, intensity, options)
    
    def structure(
        self,
        text: str,
        intensity: int = DEFAULT_INTENSITY,
        options: Optional[TransformOptions] = None,
    ) -> Dict[str, Any]:
        """
        Structure unorganized text
        
        Args:
            text: Text to structure
            intensity: Transformation intensity (0-3)
            options: Transformation options
            
        Returns:
            Transformation response
        """
        return self.transform(text, TransformationType.STRUCTURE, intensity, options)
    
    def summarize(
        self,
        text: str,
        intensity: int = DEFAULT_INTENSITY,
        options: Optional[TransformOptions] = None,
    ) -> Dict[str, Any]:
        """
        Summarize long text
        
        Args:
            text: Text to summarize
            intensity: Transformation intensity (0-3)
            options: Transformation options
            
        Returns:
            Transformation response
        """
        return self.transform(text, TransformationType.SUMMARIZE, intensity, options)
    
    def transform_terminology(
        self,
        text: str,
        options: Optional[TransformOptions] = None,
    ) -> Dict[str, Any]:
        """
        Transform technical terminology to non-technical
        
        Args:
            text: Text with technical terms
            options: Transformation options
            
        Returns:
            Transformation response
        """
        return self.transform(text, TransformationType.TERMINOLOGY, DEFAULT_INTENSITY, options)
    
    def structure_requirements(
        self,
        text: str,
        options: Optional[TransformOptions] = None,
    ) -> Dict[str, Any]:
        """
        Structure requirements into 4 quadrants
        
        Args:
            text: Unstructured requirements
            options: Transformation options
            
        Returns:
            Structured requirements
        """
        request_data = {"text": text}
        if options:
            request_data["options"] = options.__dict__ if hasattr(options, '__dict__') else options
        
        return self.client.request(
            "POST",
            API_ENDPOINTS["STRUCTURE_REQUIREMENTS"],
            json=request_data
        )
    
    def complete_background(
        self,
        text: str,
        options: Optional[TransformOptions] = None,
    ) -> Dict[str, Any]:
        """
        Complete missing background information
        
        Args:
            text: Text with potentially missing background
            options: Transformation options
            
        Returns:
            Text with completed background
        """
        request_data = {"text": text}
        if options:
            request_data["options"] = options.__dict__ if hasattr(options, '__dict__') else options
        
        return self.client.request(
            "POST",
            API_ENDPOINTS["COMPLETE_BACKGROUND"],
            json=request_data
        )
    
    def adjust_tone(
        self,
        text: str,
        intensity: int,
        target_tone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Adjust tone with specific intensity
        
        Args:
            text: Text to adjust
            intensity: Tone adjustment intensity (0-3)
            target_tone: Target tone
            
        Returns:
            Tone-adjusted text
        """
        return self.client.request(
            "POST",
            API_ENDPOINTS["ADJUST_TONE"],
            json={
                "text": text,
                "intensity": intensity,
                "target_tone": target_tone,
            }
        )
    
    def auto_detect_intensity(
        self,
        text: str,
        transformation_type: Union[TransformationType, str],
    ) -> Dict[str, Any]:
        """
        Auto-detect optimal transformation intensity
        
        Args:
            text: Text to analyze
            transformation_type: Type of transformation
            
        Returns:
            Optimal intensity and confidence
        """
        return self.client.request(
            "POST",
            API_ENDPOINTS["AUTO_DETECT_INTENSITY"],
            json={
                "text": text,
                "transformation_type": transformation_type.value if isinstance(transformation_type, TransformationType) else transformation_type,
            }
        )
    
    def get_tone_presets(self) -> List[Dict[str, Any]]:
        """
        Get available tone presets
        
        Returns:
            List of tone presets
        """
        return self.client.request("GET", API_ENDPOINTS["TONE_PRESETS"])
    
    def batch_transform(
        self,
        items: List[Dict[str, Any]],
        parallel: bool = True,
        stop_on_error: bool = False,
    ) -> Dict[str, Any]:
        """
        Batch transform multiple texts
        
        Args:
            items: List of transform requests
            parallel: Process in parallel
            stop_on_error: Stop on first error
            
        Returns:
            Batch transformation results
        """
        if not items:
            raise ValidationError("No items to transform")
        
        # Validate each item
        for item in items:
            self._validate_transform_request(
                item.get("text", ""),
                item.get("transformation_type", ""),
                item.get("intensity", DEFAULT_INTENSITY)
            )
        
        return self.client.request(
            "POST",
            API_ENDPOINTS["BATCH_TRANSFORM"],
            json={
                "items": items,
                "parallel": parallel,
                "stop_on_error": stop_on_error,
            }
        )
    
    def custom_transform(
        self,
        text: str,
        instructions: str,
        options: Optional[TransformOptions] = None,
    ) -> Dict[str, Any]:
        """
        Transform with custom instructions
        
        Args:
            text: Text to transform
            instructions: Custom transformation instructions
            options: Transformation options
            
        Returns:
            Custom transformation result
        """
        transform_options = options or TransformOptions()
        transform_options.custom_instructions = instructions
        
        return self.transform(
            text,
            TransformationType.CUSTOM,
            DEFAULT_INTENSITY,
            transform_options
        )
    
    def get_history(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get transformation history
        
        Args:
            limit: Number of items to retrieve
            offset: Offset for pagination
            
        Returns:
            Transformation history
        """
        return self.client.request(
            "GET",
            API_ENDPOINTS["HISTORY"],
            params={"limit": limit, "offset": offset}
        )
    
    def _validate_transform_request(
        self,
        text: str,
        transformation_type: Union[TransformationType, str],
        intensity: int,
    ) -> None:
        """Validate transform request parameters"""
        if not text:
            raise ValidationError("Text is required")
        
        if len(text) > MAX_TEXT_LENGTH:
            raise ValidationError(f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters")
        
        if not transformation_type:
            raise ValidationError("Transformation type is required")
        
        if intensity < 0 or intensity > 3:
            raise ValidationError("Intensity must be between 0 and 3")