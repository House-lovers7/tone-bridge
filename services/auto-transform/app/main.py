"""
Auto-transformation Service
Detects and applies automatic transformations based on configured rules
"""

import asyncio
import json
import re
from datetime import datetime, time
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from sqlalchemy import create_engine, select, and_, or_
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import redis
from textblob import TextBlob
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="ToneBridge Auto-Transform Service",
    description="Automatic message transformation based on rules and triggers",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = "postgresql://tonebridge:password@postgres:5432/tonebridge"
REDIS_URL = "redis://redis:6379"
LLM_SERVICE_URL = "http://llm-service:8000"
GATEWAY_URL = "http://gateway:8080"

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Models
class AutoTransformConfig(BaseModel):
    tenant_id: str
    enabled: bool = False
    default_transformation_type: str = "soften"
    default_intensity: int = 2
    min_message_length: int = 50
    max_processing_delay_ms: int = 500
    require_confirmation: bool = True
    show_preview: bool = True
    preserve_original: bool = True

class TransformRule(BaseModel):
    rule_name: str
    description: Optional[str]
    enabled: bool = True
    priority: int = 0
    trigger_type: str  # 'keyword', 'sentiment', 'recipient', 'channel', 'time', 'pattern'
    trigger_value: Dict[str, Any]
    transformation_type: str
    transformation_intensity: int = 2
    transformation_options: Dict[str, Any] = {}
    platforms: List[str] = []
    channels: List[str] = []
    user_roles: List[str] = []

class MessageContext(BaseModel):
    message: str
    user_id: str
    tenant_id: str
    platform: str
    channel_id: Optional[str] = None
    recipient_ids: List[str] = []
    metadata: Dict[str, Any] = {}

class TransformationResult(BaseModel):
    should_transform: bool
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    transformation_type: str
    transformation_intensity: int
    transformation_options: Dict[str, Any] = {}
    confidence: float = 0.0
    reason: Optional[str] = None

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rule evaluation engine
class RuleEngine:
    """Evaluates transformation rules against message context"""
    
    @staticmethod
    async def evaluate_rules(context: MessageContext, rules: List[Dict]) -> Optional[TransformationResult]:
        """Evaluate all rules and return the highest priority match"""
        matches = []
        
        for rule in rules:
            if not rule['enabled']:
                continue
                
            # Check platform and channel constraints
            if rule['platforms'] and context.platform not in rule['platforms']:
                continue
            if rule['channels'] and context.channel_id not in rule['channels']:
                continue
            
            # Evaluate trigger
            match_result = await RuleEngine._evaluate_trigger(
                context, 
                rule['trigger_type'], 
                rule['trigger_value']
            )
            
            if match_result['matches']:
                matches.append({
                    'rule': rule,
                    'confidence': match_result['confidence'],
                    'reason': match_result['reason']
                })
        
        if not matches:
            return None
        
        # Sort by priority (descending) and confidence (descending)
        matches.sort(key=lambda x: (x['rule']['priority'], x['confidence']), reverse=True)
        best_match = matches[0]
        
        return TransformationResult(
            should_transform=True,
            rule_id=best_match['rule']['id'],
            rule_name=best_match['rule']['rule_name'],
            transformation_type=best_match['rule']['transformation_type'],
            transformation_intensity=best_match['rule']['transformation_intensity'],
            transformation_options=best_match['rule']['transformation_options'],
            confidence=best_match['confidence'],
            reason=best_match['reason']
        )
    
    @staticmethod
    async def _evaluate_trigger(context: MessageContext, trigger_type: str, trigger_value: Dict) -> Dict:
        """Evaluate a specific trigger condition"""
        
        if trigger_type == 'keyword':
            return RuleEngine._check_keywords(context.message, trigger_value.get('keywords', []))
        
        elif trigger_type == 'sentiment':
            return RuleEngine._check_sentiment(context.message, trigger_value)
        
        elif trigger_type == 'recipient':
            return RuleEngine._check_recipients(context.recipient_ids, trigger_value)
        
        elif trigger_type == 'channel':
            return RuleEngine._check_channel(context.channel_id, trigger_value)
        
        elif trigger_type == 'time':
            return RuleEngine._check_time(trigger_value)
        
        elif trigger_type == 'pattern':
            return RuleEngine._check_patterns(context.message, trigger_value.get('patterns', []))
        
        return {'matches': False, 'confidence': 0.0, 'reason': 'Unknown trigger type'}
    
    @staticmethod
    def _check_keywords(message: str, keywords: List[str]) -> Dict:
        """Check if message contains any keywords"""
        message_lower = message.lower()
        found_keywords = [kw for kw in keywords if kw.lower() in message_lower]
        
        if found_keywords:
            confidence = min(1.0, len(found_keywords) / len(keywords))
            return {
                'matches': True,
                'confidence': confidence,
                'reason': f"Contains keywords: {', '.join(found_keywords)}"
            }
        
        return {'matches': False, 'confidence': 0.0, 'reason': 'No keywords found'}
    
    @staticmethod
    def _check_sentiment(message: str, config: Dict) -> Dict:
        """Check message sentiment using TextBlob"""
        try:
            blob = TextBlob(message)
            polarity = blob.sentiment.polarity
            threshold = config.get('threshold', 0)
            operator = config.get('operator', 'less_than')
            
            matches = False
            if operator == 'less_than' and polarity < threshold:
                matches = True
            elif operator == 'greater_than' and polarity > threshold:
                matches = True
            elif operator == 'equals' and abs(polarity - threshold) < 0.1:
                matches = True
            
            if matches:
                confidence = abs(polarity - threshold) / 2  # Normalize to 0-1
                return {
                    'matches': True,
                    'confidence': min(1.0, confidence),
                    'reason': f"Sentiment polarity {polarity:.2f} {operator} {threshold}"
                }
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
        
        return {'matches': False, 'confidence': 0.0, 'reason': 'Sentiment check failed'}
    
    @staticmethod
    def _check_recipients(recipient_ids: List[str], config: Dict) -> Dict:
        """Check if recipients match criteria"""
        target_roles = config.get('roles', [])
        target_ids = config.get('ids', [])
        
        # Check direct ID matches
        if target_ids:
            matching_ids = set(recipient_ids) & set(target_ids)
            if matching_ids:
                return {
                    'matches': True,
                    'confidence': 0.9,
                    'reason': f"Recipient match: {', '.join(matching_ids)}"
                }
        
        # Check role matches (would need role lookup in production)
        if target_roles:
            # Placeholder for role checking
            return {
                'matches': True,
                'confidence': 0.8,
                'reason': f"Recipient role match: {', '.join(target_roles)}"
            }
        
        return {'matches': False, 'confidence': 0.0, 'reason': 'No recipient match'}
    
    @staticmethod
    def _check_channel(channel_id: Optional[str], config: Dict) -> Dict:
        """Check if channel matches criteria"""
        if not channel_id:
            return {'matches': False, 'confidence': 0.0, 'reason': 'No channel specified'}
        
        channel_type = config.get('type')
        channel_ids = config.get('ids', [])
        
        if channel_ids and channel_id in channel_ids:
            return {
                'matches': True,
                'confidence': 1.0,
                'reason': f"Channel match: {channel_id}"
            }
        
        if channel_type:
            # Check channel type (would need channel lookup in production)
            if channel_type == 'support' and 'support' in channel_id.lower():
                return {
                    'matches': True,
                    'confidence': 0.8,
                    'reason': f"Channel type match: {channel_type}"
                }
        
        return {'matches': False, 'confidence': 0.0, 'reason': 'No channel match'}
    
    @staticmethod
    def _check_time(config: Dict) -> Dict:
        """Check if current time matches criteria"""
        now = datetime.now()
        current_time = now.time()
        
        after_str = config.get('after')
        before_str = config.get('before')
        
        if after_str:
            after_time = time.fromisoformat(after_str)
            if current_time < after_time:
                return {'matches': False, 'confidence': 0.0, 'reason': 'Before time window'}
        
        if before_str:
            before_time = time.fromisoformat(before_str)
            if current_time > before_time:
                return {'matches': False, 'confidence': 0.0, 'reason': 'After time window'}
        
        return {
            'matches': True,
            'confidence': 0.9,
            'reason': f"Within time window: {now.strftime('%H:%M')}"
        }
    
    @staticmethod
    def _check_patterns(message: str, patterns: List[str]) -> Dict:
        """Check if message matches regex patterns"""
        for pattern_str in patterns:
            try:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                if pattern.search(message):
                    return {
                        'matches': True,
                        'confidence': 0.9,
                        'reason': f"Pattern match: {pattern_str}"
                    }
            except re.error:
                logger.error(f"Invalid regex pattern: {pattern_str}")
        
        return {'matches': False, 'confidence': 0.0, 'reason': 'No pattern match'}

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auto-transform"}

@app.post("/evaluate")
async def evaluate_message(context: MessageContext, db: Session = Depends(get_db)):
    """Evaluate if a message should be auto-transformed"""
    try:
        # Check if auto-transform is enabled for tenant
        cache_key = f"auto_transform:config:{context.tenant_id}"
        cached_config = redis_client.get(cache_key)
        
        if cached_config:
            config = json.loads(cached_config)
        else:
            # Load from database
            result = db.execute(
                select('*').select_from('auto_transform_configs')
                .where('tenant_id' == context.tenant_id)
            ).first()
            
            if not result or not result['enabled']:
                return {"should_transform": False, "reason": "Auto-transform disabled"}
            
            config = dict(result)
            # Cache for 5 minutes
            redis_client.setex(cache_key, 300, json.dumps(config, default=str))
        
        # Check message length threshold
        if len(context.message) < config['min_message_length']:
            return {"should_transform": False, "reason": "Message too short"}
        
        # Load rules
        rules_cache_key = f"auto_transform:rules:{context.tenant_id}"
        cached_rules = redis_client.get(rules_cache_key)
        
        if cached_rules:
            rules = json.loads(cached_rules)
        else:
            # Load from database
            results = db.execute(
                select('*').select_from('auto_transform_rules')
                .where(and_(
                    'config_id' == config['id'],
                    'enabled' == True
                ))
                .order_by('priority DESC')
            ).fetchall()
            
            rules = [dict(r) for r in results]
            # Cache for 5 minutes
            redis_client.setex(rules_cache_key, 300, json.dumps(rules, default=str))
        
        if not rules:
            return {"should_transform": False, "reason": "No active rules"}
        
        # Evaluate rules
        result = await RuleEngine.evaluate_rules(context, rules)
        
        if result:
            # Log the evaluation
            db.execute(
                """
                INSERT INTO auto_transform_logs 
                (tenant_id, rule_id, user_id, original_message, platform, 
                 channel_id, status, triggered_at)
                VALUES (:tenant_id, :rule_id, :user_id, :message, :platform,
                        :channel_id, 'triggered', NOW())
                """,
                {
                    'tenant_id': context.tenant_id,
                    'rule_id': result.rule_id,
                    'user_id': context.user_id,
                    'message': context.message,
                    'platform': context.platform,
                    'channel_id': context.channel_id
                }
            )
            db.commit()
            
            return result.dict()
        
        return {"should_transform": False, "reason": "No matching rules"}
        
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transform")
async def auto_transform(
    context: MessageContext,
    transformation: TransformationResult,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Apply auto-transformation to a message"""
    try:
        # Call LLM service to transform
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLM_SERVICE_URL}/api/v1/transform",
                json={
                    "text": context.message,
                    "transformation_type": transformation.transformation_type,
                    "intensity": transformation.transformation_intensity,
                    "options": transformation.transformation_options
                }
            )
            response.raise_for_status()
            transform_result = response.json()
        
        if not transform_result.get('success'):
            raise Exception("Transformation failed")
        
        transformed_text = transform_result['data']['transformed_text']
        
        # Update log
        db.execute(
            """
            UPDATE auto_transform_logs 
            SET transformed_message = :transformed,
                processed_at = NOW(),
                status = 'transformed'
            WHERE tenant_id = :tenant_id 
              AND user_id = :user_id
              AND status = 'triggered'
              AND triggered_at > NOW() - INTERVAL '1 minute'
            """,
            {
                'transformed': transformed_text,
                'tenant_id': context.tenant_id,
                'user_id': context.user_id
            }
        )
        db.commit()
        
        # Track metrics in background
        background_tasks.add_task(
            track_metrics,
            context.tenant_id,
            transformation.rule_id,
            'success'
        )
        
        return {
            "success": True,
            "original": context.message,
            "transformed": transformed_text,
            "rule_applied": transformation.rule_name,
            "confidence": transformation.confidence
        }
        
    except Exception as e:
        logger.error(f"Transformation error: {e}")
        
        # Log failure
        db.execute(
            """
            UPDATE auto_transform_logs 
            SET status = 'failed',
                error_message = :error,
                processed_at = NOW()
            WHERE tenant_id = :tenant_id 
              AND user_id = :user_id
              AND status = 'triggered'
              AND triggered_at > NOW() - INTERVAL '1 minute'
            """,
            {
                'error': str(e),
                'tenant_id': context.tenant_id,
                'user_id': context.user_id
            }
        )
        db.commit()
        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config/{tenant_id}")
async def get_config(tenant_id: str, db: Session = Depends(get_db)):
    """Get auto-transform configuration for a tenant"""
    result = db.execute(
        select('*').select_from('auto_transform_configs')
        .where('tenant_id' == tenant_id)
    ).first()
    
    if not result:
        return {"enabled": False}
    
    return dict(result)

@app.put("/config/{tenant_id}")
async def update_config(
    tenant_id: str,
    config: AutoTransformConfig,
    db: Session = Depends(get_db)
):
    """Update auto-transform configuration"""
    try:
        # Check if config exists
        existing = db.execute(
            select('id').select_from('auto_transform_configs')
            .where('tenant_id' == tenant_id)
        ).first()
        
        if existing:
            # Update
            db.execute(
                """
                UPDATE auto_transform_configs 
                SET enabled = :enabled,
                    default_transformation_type = :type,
                    default_intensity = :intensity,
                    min_message_length = :min_length,
                    max_processing_delay_ms = :max_delay,
                    require_confirmation = :require_confirm,
                    show_preview = :show_preview,
                    preserve_original = :preserve,
                    updated_at = NOW()
                WHERE tenant_id = :tenant_id
                """,
                {
                    'enabled': config.enabled,
                    'type': config.default_transformation_type,
                    'intensity': config.default_intensity,
                    'min_length': config.min_message_length,
                    'max_delay': config.max_processing_delay_ms,
                    'require_confirm': config.require_confirmation,
                    'show_preview': config.show_preview,
                    'preserve': config.preserve_original,
                    'tenant_id': tenant_id
                }
            )
        else:
            # Insert
            db.execute(
                """
                INSERT INTO auto_transform_configs 
                (tenant_id, enabled, default_transformation_type, 
                 default_intensity, min_message_length, max_processing_delay_ms,
                 require_confirmation, show_preview, preserve_original)
                VALUES (:tenant_id, :enabled, :type, :intensity, :min_length,
                        :max_delay, :require_confirm, :show_preview, :preserve)
                """,
                {
                    'tenant_id': tenant_id,
                    'enabled': config.enabled,
                    'type': config.default_transformation_type,
                    'intensity': config.default_intensity,
                    'min_length': config.min_message_length,
                    'max_delay': config.max_processing_delay_ms,
                    'require_confirm': config.require_confirmation,
                    'show_preview': config.show_preview,
                    'preserve': config.preserve_original
                }
            )
        
        db.commit()
        
        # Clear cache
        redis_client.delete(f"auto_transform:config:{tenant_id}")
        
        return {"success": True, "message": "Configuration updated"}
        
    except Exception as e:
        logger.error(f"Config update error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rules/{tenant_id}")
async def get_rules(tenant_id: str, db: Session = Depends(get_db)):
    """Get all auto-transform rules for a tenant"""
    # Get config first
    config = db.execute(
        select('id').select_from('auto_transform_configs')
        .where('tenant_id' == tenant_id)
    ).first()
    
    if not config:
        return []
    
    rules = db.execute(
        select('*').select_from('auto_transform_rules')
        .where('config_id' == config['id'])
        .order_by('priority DESC')
    ).fetchall()
    
    return [dict(r) for r in rules]

@app.post("/rules/{tenant_id}")
async def create_rule(
    tenant_id: str,
    rule: TransformRule,
    db: Session = Depends(get_db)
):
    """Create a new auto-transform rule"""
    try:
        # Get config
        config = db.execute(
            select('id').select_from('auto_transform_configs')
            .where('tenant_id' == tenant_id)
        ).first()
        
        if not config:
            # Create default config
            result = db.execute(
                """
                INSERT INTO auto_transform_configs (tenant_id)
                VALUES (:tenant_id)
                RETURNING id
                """,
                {'tenant_id': tenant_id}
            ).first()
            config_id = result['id']
        else:
            config_id = config['id']
        
        # Insert rule
        result = db.execute(
            """
            INSERT INTO auto_transform_rules 
            (config_id, rule_name, description, enabled, priority,
             trigger_type, trigger_value, transformation_type, 
             transformation_intensity, transformation_options,
             platforms, channels, user_roles)
            VALUES (:config_id, :name, :desc, :enabled, :priority,
                    :trigger_type, :trigger_value, :trans_type,
                    :trans_intensity, :trans_options,
                    :platforms, :channels, :roles)
            RETURNING id
            """,
            {
                'config_id': config_id,
                'name': rule.rule_name,
                'desc': rule.description,
                'enabled': rule.enabled,
                'priority': rule.priority,
                'trigger_type': rule.trigger_type,
                'trigger_value': json.dumps(rule.trigger_value),
                'trans_type': rule.transformation_type,
                'trans_intensity': rule.transformation_intensity,
                'trans_options': json.dumps(rule.transformation_options),
                'platforms': rule.platforms,
                'channels': rule.channels,
                'roles': rule.user_roles
            }
        ).first()
        
        db.commit()
        
        # Clear cache
        redis_client.delete(f"auto_transform:rules:{tenant_id}")
        
        return {"success": True, "rule_id": str(result['id'])}
        
    except Exception as e:
        logger.error(f"Rule creation error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates")
async def get_templates(db: Session = Depends(get_db)):
    """Get available rule templates"""
    templates = db.execute(
        select('*').select_from('auto_transform_templates')
        .order_by('category', 'template_name')
    ).fetchall()
    
    return [dict(t) for t in templates]

@app.post("/apply-template/{tenant_id}/{template_id}")
async def apply_template(
    tenant_id: str,
    template_id: str,
    db: Session = Depends(get_db)
):
    """Apply a template to create a new rule"""
    try:
        # Get template
        template = db.execute(
            select('*').select_from('auto_transform_templates')
            .where('id' == template_id)
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        rule_config = json.loads(template['rule_config'])
        
        # Create rule from template
        rule = TransformRule(
            rule_name=f"{template['template_name']} (from template)",
            description=template['description'],
            **rule_config
        )
        
        return await create_rule(tenant_id, rule, db)
        
    except Exception as e:
        logger.error(f"Template application error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def track_metrics(tenant_id: str, rule_id: str, status: str):
    """Track auto-transform metrics"""
    try:
        # Increment counters in Redis
        today = datetime.now().strftime('%Y-%m-%d')
        redis_client.hincrby(f"auto_transform:metrics:{tenant_id}:{today}", status, 1)
        if rule_id:
            redis_client.hincrby(f"auto_transform:rule_usage:{tenant_id}:{today}", rule_id, 1)
    except Exception as e:
        logger.error(f"Metrics tracking error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)