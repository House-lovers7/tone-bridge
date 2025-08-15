"""
Base Adapter for Platform Integrations
Abstract base class that all platform adapters must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import logging

from app.models.internal_message import (
    InternalMessage, 
    PlatformResponse, 
    UIMessage,
    UIComponent,
    Platform,
    EventType,
    User,
    Channel
)

logger = logging.getLogger(__name__)

class PlatformAdapter(ABC):
    """
    Abstract base class for platform-specific adapters
    Each platform (Slack, Teams, Discord, etc.) must implement this interface
    """
    
    def __init__(self, platform: Platform, config: Dict[str, Any]):
        """
        Initialize the adapter
        
        Args:
            platform: The platform this adapter handles
            config: Platform-specific configuration
        """
        self.platform = platform
        self.config = config
        self.rate_limiter = RateLimiter(
            requests_per_second=config.get("rate_limit", 10)
        )
        self.logger = logging.getLogger(f"{__name__}.{platform.value}")
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with the platform
        
        Args:
            credentials: Platform-specific credentials
        
        Returns:
            True if authentication successful
        """
        pass
    
    @abstractmethod
    async def parse_event(self, raw_event: Dict[str, Any]) -> InternalMessage:
        """
        Parse a platform-specific event into an InternalMessage
        
        Args:
            raw_event: Raw event data from the platform
        
        Returns:
            Normalized InternalMessage
        """
        pass
    
    @abstractmethod
    async def format_response(self, ui_message: UIMessage) -> Dict[str, Any]:
        """
        Format a UIMessage into platform-specific response format
        
        Args:
            ui_message: Platform-agnostic UI message
        
        Returns:
            Platform-specific formatted response
        """
        pass
    
    @abstractmethod
    async def send_message(
        self, 
        channel_id: str, 
        ui_message: UIMessage,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to the platform
        
        Args:
            channel_id: Channel to send to
            ui_message: Message to send
            thread_id: Optional thread ID for replies
        
        Returns:
            Platform response
        """
        pass
    
    @abstractmethod
    async def update_message(
        self,
        channel_id: str,
        message_id: str,
        ui_message: UIMessage
    ) -> Dict[str, Any]:
        """
        Update an existing message
        
        Args:
            channel_id: Channel containing the message
            message_id: ID of message to update
            ui_message: New message content
        
        Returns:
            Platform response
        """
        pass
    
    @abstractmethod
    async def delete_message(
        self,
        channel_id: str,
        message_id: str
    ) -> bool:
        """
        Delete a message
        
        Args:
            channel_id: Channel containing the message
            message_id: ID of message to delete
        
        Returns:
            True if deletion successful
        """
        pass
    
    @abstractmethod
    async def get_user_info(self, user_id: str) -> User:
        """
        Get detailed user information
        
        Args:
            user_id: Platform-specific user ID
        
        Returns:
            User object with details
        """
        pass
    
    @abstractmethod
    async def get_channel_info(self, channel_id: str) -> Channel:
        """
        Get detailed channel information
        
        Args:
            channel_id: Platform-specific channel ID
        
        Returns:
            Channel object with details
        """
        pass
    
    # Common utility methods that can be overridden if needed
    
    async def handle_rate_limit(self):
        """Handle rate limiting"""
        await self.rate_limiter.acquire()
    
    def validate_event(self, raw_event: Dict[str, Any]) -> bool:
        """
        Validate that an event has required fields
        Can be overridden for platform-specific validation
        
        Args:
            raw_event: Raw event to validate
        
        Returns:
            True if event is valid
        """
        return raw_event is not None and isinstance(raw_event, dict)
    
    def map_ui_component_to_platform(self, component: UIComponent) -> Dict[str, Any]:
        """
        Map a generic UI component to platform-specific format
        Should be overridden by each platform adapter
        
        Args:
            component: Generic UI component
        
        Returns:
            Platform-specific component
        """
        # Default implementation - override in subclasses
        return {
            "type": component.type,
            "content": component.content,
            **component.metadata
        }
    
    async def handle_webhook(self, request_data: Dict[str, Any]) -> PlatformResponse:
        """
        Handle incoming webhook from platform
        
        Args:
            request_data: Webhook request data
        
        Returns:
            Response to send back to platform
        """
        try:
            # Validate the event
            if not self.validate_event(request_data):
                self.logger.warning(f"Invalid event received: {request_data}")
                return self._error_response("Invalid event format")
            
            # Parse to internal message
            internal_message = await self.parse_event(request_data)
            
            # Log the event
            self.logger.info(
                f"Received {internal_message.event_type} from {internal_message.user.username} "
                f"in {internal_message.channel.name or internal_message.channel.id}"
            )
            
            return PlatformResponse(
                platform=self.platform,
                channel_id=internal_message.channel.id,
                ui_message=UIMessage(
                    components=[
                        UIComponent(
                            type="text",
                            content="Message received and processed"
                        )
                    ]
                )
            )
            
        except Exception as e:
            self.logger.error(f"Error handling webhook: {str(e)}", exc_info=True)
            return self._error_response(f"Error processing event: {str(e)}")
    
    def _error_response(self, error_message: str) -> PlatformResponse:
        """Create an error response"""
        return PlatformResponse(
            platform=self.platform,
            channel_id="error",
            ui_message=UIMessage(
                components=[
                    UIComponent(
                        type="text",
                        content=f"Error: {error_message}",
                        style={"color": "red"}
                    )
                ],
                ephemeral=True
            )
        )

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, requests_per_second: int = 10):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait if necessary to respect rate limit"""
        async with self.lock:
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                await asyncio.sleep(sleep_time)
            
            self.last_request_time = asyncio.get_event_loop().time()

class AdapterRegistry:
    """Registry for platform adapters"""
    
    def __init__(self):
        self._adapters: Dict[Platform, PlatformAdapter] = {}
    
    def register(self, platform: Platform, adapter: PlatformAdapter):
        """Register an adapter for a platform"""
        self._adapters[platform] = adapter
        logger.info(f"Registered adapter for {platform.value}")
    
    def get(self, platform: Platform) -> Optional[PlatformAdapter]:
        """Get adapter for a platform"""
        return self._adapters.get(platform)
    
    def get_all(self) -> Dict[Platform, PlatformAdapter]:
        """Get all registered adapters"""
        return self._adapters.copy()
    
    async def initialize_all(self, configs: Dict[Platform, Dict[str, Any]]):
        """Initialize all adapters with their configs"""
        for platform, config in configs.items():
            adapter = self.get(platform)
            if adapter:
                try:
                    success = await adapter.authenticate(config.get("credentials", {}))
                    if success:
                        logger.info(f"Successfully authenticated {platform.value}")
                    else:
                        logger.warning(f"Failed to authenticate {platform.value}")
                except Exception as e:
                    logger.error(f"Error initializing {platform.value}: {str(e)}")

# Global adapter registry
adapter_registry = AdapterRegistry()