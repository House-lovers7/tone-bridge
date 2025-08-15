"""
Auto-Transform Service
Handles automatic transformation rules and configurations
"""

from typing import Optional, Dict, Any, List, Union
from ..types import (
    AutoTransformConfig,
    AutoTransformRule,
    MessageContext,
    TransformationResult,
    TransformationType,
    TriggerType,
)
from ..constants import API_ENDPOINTS
from ..exceptions import ValidationError


class AutoTransformService:
    """Service for auto-transform operations"""
    
    def __init__(self, client):
        """
        Initialize auto-transform service
        
        Args:
            client: ToneBridgeClient instance
        """
        self.client = client
        self.base_endpoint = "/auto-transform"
    
    def get_config(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get auto-transform configuration
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Configuration dictionary
        """
        endpoint = f"{self.base_endpoint}/config"
        if tenant_id:
            endpoint = f"{endpoint}/{tenant_id}"
        
        return self.client.request("GET", endpoint)
    
    def update_config(
        self,
        config: Union[AutoTransformConfig, Dict[str, Any]],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update auto-transform configuration
        
        Args:
            config: Configuration to update
            tenant_id: Tenant ID
            
        Returns:
            Updated configuration
        """
        endpoint = f"{self.base_endpoint}/config"
        if tenant_id:
            endpoint = f"{endpoint}/{tenant_id}"
        
        config_data = config.__dict__ if hasattr(config, '__dict__') else config
        return self.client.request("PUT", endpoint, json=config_data)
    
    def enable(self, tenant_id: Optional[str] = None) -> None:
        """
        Enable auto-transform
        
        Args:
            tenant_id: Tenant ID
        """
        self.update_config({"enabled": True}, tenant_id)
    
    def disable(self, tenant_id: Optional[str] = None) -> None:
        """
        Disable auto-transform
        
        Args:
            tenant_id: Tenant ID
        """
        self.update_config({"enabled": False}, tenant_id)
    
    def evaluate(
        self,
        context: Union[MessageContext, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate if message should be auto-transformed
        
        Args:
            context: Message context
            
        Returns:
            Transformation evaluation result
        """
        context_data = context.__dict__ if hasattr(context, '__dict__') else context
        self._validate_message_context(context_data)
        
        return self.client.request(
            "POST",
            f"{self.base_endpoint}/evaluate",
            json=context_data
        )
    
    def transform(
        self,
        context: Union[MessageContext, Dict[str, Any]],
        transformation: Union[TransformationResult, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Apply auto-transformation
        
        Args:
            context: Message context
            transformation: Transformation result from evaluation
            
        Returns:
            Transformation result
        """
        context_data = context.__dict__ if hasattr(context, '__dict__') else context
        transformation_data = transformation.__dict__ if hasattr(transformation, '__dict__') else transformation
        
        return self.client.request(
            "POST",
            f"{self.base_endpoint}/transform",
            json={
                "context": context_data,
                "transformation": transformation_data,
            }
        )
    
    def get_rules(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all rules
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List of rules
        """
        endpoint = f"{self.base_endpoint}/rules"
        if tenant_id:
            endpoint = f"{endpoint}/{tenant_id}"
        
        return self.client.request("GET", endpoint)
    
    def get_rule(
        self,
        rule_id: str,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get rule by ID
        
        Args:
            rule_id: Rule ID
            tenant_id: Tenant ID
            
        Returns:
            Rule dictionary
        """
        endpoint = f"{self.base_endpoint}/rules/{rule_id}"
        if tenant_id:
            endpoint = f"{self.base_endpoint}/rules/{tenant_id}/{rule_id}"
        
        return self.client.request("GET", endpoint)
    
    def create_rule(
        self,
        rule: Union[AutoTransformRule, Dict[str, Any]],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new rule
        
        Args:
            rule: Rule to create
            tenant_id: Tenant ID
            
        Returns:
            Created rule information
        """
        rule_data = rule.__dict__ if hasattr(rule, '__dict__') else rule
        self._validate_rule(rule_data)
        
        endpoint = f"{self.base_endpoint}/rules"
        if tenant_id:
            endpoint = f"{endpoint}/{tenant_id}"
        
        return self.client.request("POST", endpoint, json=rule_data)
    
    def update_rule(
        self,
        rule_id: str,
        updates: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a rule
        
        Args:
            rule_id: Rule ID
            updates: Updates to apply
            tenant_id: Tenant ID
            
        Returns:
            Updated rule
        """
        endpoint = f"{self.base_endpoint}/rules/{rule_id}"
        if tenant_id:
            endpoint = f"{self.base_endpoint}/rules/{tenant_id}/{rule_id}"
        
        return self.client.request("PUT", endpoint, json=updates)
    
    def delete_rule(
        self,
        rule_id: str,
        tenant_id: Optional[str] = None,
    ) -> None:
        """
        Delete a rule
        
        Args:
            rule_id: Rule ID
            tenant_id: Tenant ID
        """
        endpoint = f"{self.base_endpoint}/rules/{rule_id}"
        if tenant_id:
            endpoint = f"{self.base_endpoint}/rules/{tenant_id}/{rule_id}"
        
        self.client.request("DELETE", endpoint)
    
    def enable_rule(
        self,
        rule_id: str,
        tenant_id: Optional[str] = None,
    ) -> None:
        """
        Enable a rule
        
        Args:
            rule_id: Rule ID
            tenant_id: Tenant ID
        """
        self.update_rule(rule_id, {"enabled": True}, tenant_id)
    
    def disable_rule(
        self,
        rule_id: str,
        tenant_id: Optional[str] = None,
    ) -> None:
        """
        Disable a rule
        
        Args:
            rule_id: Rule ID
            tenant_id: Tenant ID
        """
        self.update_rule(rule_id, {"enabled": False}, tenant_id)
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """
        Get available templates
        
        Returns:
            List of templates
        """
        return self.client.request("GET", f"{self.base_endpoint}/templates")
    
    def apply_template(
        self,
        template_id: str,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Apply a template
        
        Args:
            template_id: Template ID
            tenant_id: Tenant ID
            
        Returns:
            Applied rule information
        """
        endpoint = f"{self.base_endpoint}/apply-template/{template_id}"
        if tenant_id:
            endpoint = f"{self.base_endpoint}/apply-template/{tenant_id}/{template_id}"
        
        return self.client.request("POST", endpoint)
    
    def create_keyword_rule(
        self,
        name: str,
        keywords: List[str],
        transformation_type: Union[TransformationType, str],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create keyword-based rule
        
        Args:
            name: Rule name
            keywords: Keywords to trigger on
            transformation_type: Transformation to apply
            tenant_id: Tenant ID
            
        Returns:
            Created rule information
        """
        rule = {
            "rule_name": name,
            "enabled": True,
            "priority": 0,
            "trigger_type": TriggerType.KEYWORD.value,
            "trigger_value": {"keywords": keywords},
            "transformation_type": transformation_type.value if isinstance(transformation_type, TransformationType) else transformation_type,
            "transformation_intensity": 2,
        }
        
        return self.create_rule(rule, tenant_id)
    
    def create_sentiment_rule(
        self,
        name: str,
        threshold: float,
        operator: str,
        transformation_type: Union[TransformationType, str],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create sentiment-based rule
        
        Args:
            name: Rule name
            threshold: Sentiment threshold
            operator: Comparison operator
            transformation_type: Transformation to apply
            tenant_id: Tenant ID
            
        Returns:
            Created rule information
        """
        rule = {
            "rule_name": name,
            "enabled": True,
            "priority": 0,
            "trigger_type": TriggerType.SENTIMENT.value,
            "trigger_value": {"threshold": threshold, "operator": operator},
            "transformation_type": transformation_type.value if isinstance(transformation_type, TransformationType) else transformation_type,
            "transformation_intensity": 2,
        }
        
        return self.create_rule(rule, tenant_id)
    
    def create_time_rule(
        self,
        name: str,
        after: str,
        before: str,
        transformation_type: Union[TransformationType, str],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create time-based rule
        
        Args:
            name: Rule name
            after: Start time (HH:MM)
            before: End time (HH:MM)
            transformation_type: Transformation to apply
            tenant_id: Tenant ID
            
        Returns:
            Created rule information
        """
        rule = {
            "rule_name": name,
            "enabled": True,
            "priority": 0,
            "trigger_type": TriggerType.TIME.value,
            "trigger_value": {"after": after, "before": before},
            "transformation_type": transformation_type.value if isinstance(transformation_type, TransformationType) else transformation_type,
            "transformation_intensity": 2,
        }
        
        return self.create_rule(rule, tenant_id)
    
    def get_statistics(
        self,
        tenant_id: Optional[str] = None,
        period: int = 30,
    ) -> Dict[str, Any]:
        """
        Get rule statistics
        
        Args:
            tenant_id: Tenant ID
            period: Period in days
            
        Returns:
            Statistics dictionary
        """
        endpoint = f"{self.base_endpoint}/statistics"
        if tenant_id:
            endpoint = f"{endpoint}/{tenant_id}"
        
        return self.client.request("GET", endpoint, params={"period": period})
    
    def _validate_message_context(self, context: Dict[str, Any]) -> None:
        """Validate message context"""
        if not context.get("message"):
            raise ValidationError("Message is required")
        if not context.get("user_id"):
            raise ValidationError("User ID is required")
        if not context.get("tenant_id"):
            raise ValidationError("Tenant ID is required")
        if not context.get("platform"):
            raise ValidationError("Platform is required")
    
    def _validate_rule(self, rule: Dict[str, Any]) -> None:
        """Validate rule"""
        if not rule.get("rule_name"):
            raise ValidationError("Rule name is required")
        if not rule.get("trigger_type"):
            raise ValidationError("Trigger type is required")
        if not rule.get("trigger_value"):
            raise ValidationError("Trigger value is required")
        if not rule.get("transformation_type"):
            raise ValidationError("Transformation type is required")