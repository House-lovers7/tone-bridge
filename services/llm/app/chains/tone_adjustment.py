"""
Tone Adjustment Module
Provides fine-grained control over tone transformation intensity
"""

from typing import Dict, Any, Optional, List
from app.chains.transformation import tone_transformation_chain

class ToneAdjuster:
    """
    Manages tone transformation with adjustable intensity levels
    """
    
    # Preset configurations for different scenarios
    PRESETS = {
        "engineer_to_business": {
            "target_tone": "warm",
            "default_intensity": 2,
            "description": "Transform technical language to business-friendly"
        },
        "casual_to_formal": {
            "target_tone": "professional",
            "default_intensity": 2,
            "description": "Elevate casual text to professional level"
        },
        "direct_to_diplomatic": {
            "target_tone": "warm",
            "default_intensity": 3,
            "description": "Soften direct communication"
        },
        "verbose_to_concise": {
            "target_tone": "executive",
            "default_intensity": 2,
            "description": "Streamline to executive summary"
        }
    }
    
    # Intensity level descriptions
    INTENSITY_DESCRIPTIONS = {
        0: "原文維持 (Preserve Original)",
        1: "軽微な調整 (Light Touch)",
        2: "バランス調整 (Balanced)",
        3: "完全変換 (Full Transform)"
    }
    
    @staticmethod
    def transform_with_slider(
        text: str,
        intensity: int = 2,
        target_tone: str = "warm",
        preset: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transform text with intensity slider control
        
        Args:
            text: Input text to transform
            intensity: Transformation intensity (0-3)
            target_tone: Target tone type
            preset: Optional preset configuration
        
        Returns:
            Transformed text with metadata
        """
        # Validate intensity
        intensity = max(0, min(3, intensity))
        
        # Apply preset if specified
        if preset and preset in ToneAdjuster.PRESETS:
            preset_config = ToneAdjuster.PRESETS[preset]
            if target_tone == "warm":  # Use preset's target if not overridden
                target_tone = preset_config["target_tone"]
            if intensity == 2:  # Use preset's intensity if default
                intensity = preset_config["default_intensity"]
        
        try:
            # Call the transformation chain with intensity
            result = tone_transformation_chain.invoke({
                "text": text,
                "target_tone": target_tone,
                "intensity_level": intensity
            })
            
            # Add intensity description to result
            result["intensity_description"] = ToneAdjuster.INTENSITY_DESCRIPTIONS[intensity]
            result["preset_used"] = preset
            
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {
                    "text": text,  # Return original on error
                    "error_message": "Transformation failed"
                }
            }
    
    @staticmethod
    def generate_intensity_variations(
        text: str,
        target_tone: str = "warm"
    ) -> Dict[str, Any]:
        """
        Generate all intensity variations for comparison
        
        Args:
            text: Input text
            target_tone: Target tone
        
        Returns:
            All intensity variations for preview
        """
        variations = {}
        
        for intensity in range(4):
            try:
                result = ToneAdjuster.transform_with_slider(
                    text=text,
                    intensity=intensity,
                    target_tone=target_tone
                )
                
                if result["success"]:
                    variations[intensity] = {
                        "text": result["data"]["text"],
                        "description": ToneAdjuster.INTENSITY_DESCRIPTIONS[intensity]
                    }
                else:
                    variations[intensity] = {
                        "text": text,
                        "description": f"Error at level {intensity}"
                    }
            except Exception as e:
                variations[intensity] = {
                    "text": text,
                    "description": f"Error: {str(e)}"
                }
        
        return {
            "success": True,
            "data": {
                "original": text,
                "variations": variations,
                "target_tone": target_tone
            }
        }
    
    @staticmethod
    def auto_detect_intensity(
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Automatically detect appropriate intensity level based on text analysis
        
        Args:
            text: Input text
            context: Optional context (sender, recipient, urgency, etc.)
        
        Returns:
            Recommended intensity level (0-3)
        """
        # Simple heuristic for auto-detection
        # In production, this could use ML or more sophisticated analysis
        
        intensity = 2  # Default to balanced
        
        # Check for aggressive or very direct language
        aggressive_indicators = ["immediately", "must", "asap", "now", "!!!"]
        if any(indicator in text.lower() for indicator in aggressive_indicators):
            intensity = 3  # Needs full transformation
        
        # Check for already polite language
        polite_indicators = ["please", "thank you", "would you", "could you", "kindly"]
        polite_count = sum(1 for indicator in polite_indicators if indicator in text.lower())
        if polite_count >= 2:
            intensity = 1  # Already fairly polite
        
        # Context-based adjustments
        if context:
            # Urgent messages might need less transformation
            if context.get("urgency") == "high":
                intensity = max(0, intensity - 1)
            
            # Messages to executives might need more formality
            if context.get("recipient_role") == "executive":
                intensity = min(3, intensity + 1)
        
        return intensity
    
    @staticmethod
    def get_transformation_explanation(
        original: str,
        transformed: str,
        intensity: int
    ) -> str:
        """
        Generate explanation of what changed and why
        
        Args:
            original: Original text
            transformed: Transformed text
            intensity: Applied intensity level
        
        Returns:
            Human-readable explanation
        """
        if intensity == 0:
            return "最小限の変更のみ実施（文法修正など）"
        elif intensity == 1:
            return "軽微な調整を実施（丁寧語の追加など）"
        elif intensity == 2:
            return "バランスの取れた変換を実施（構造改善と感情表現の追加）"
        else:
            return "完全な書き換えを実施（トーンと構造の全面的な変更）"

# Convenience functions for common use cases
def soften_message(text: str, intensity: int = 2) -> Dict[str, Any]:
    """Quick function to soften a message"""
    return ToneAdjuster.transform_with_slider(
        text=text,
        intensity=intensity,
        target_tone="warm"
    )

def formalize_message(text: str, intensity: int = 2) -> Dict[str, Any]:
    """Quick function to make a message more formal"""
    return ToneAdjuster.transform_with_slider(
        text=text,
        intensity=intensity,
        target_tone="professional"
    )

def executive_summary(text: str, intensity: int = 2) -> Dict[str, Any]:
    """Quick function to create executive-level communication"""
    return ToneAdjuster.transform_with_slider(
        text=text,
        intensity=intensity,
        target_tone="executive"
    )