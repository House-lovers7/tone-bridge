"""
Priority Scoring Chain
Automatically determines urgency and importance of messages
"""

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.config import settings

# Initialize LLM
llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.2,  # Low temperature for consistent scoring
    openai_api_key=settings.OPENAI_API_KEY
)

# Output schemas
class PriorityScoreOutput(BaseModel):
    urgency_score: float = Field(description="Urgency score (0-100)")
    importance_score: float = Field(description="Importance score (0-100)")
    priority_level: str = Field(description="Priority level: critical, high, medium, low")
    priority_matrix_quadrant: str = Field(description="Eisenhower matrix quadrant")
    urgency_indicators: List[str] = Field(description="Words/phrases indicating urgency")
    importance_indicators: List[str] = Field(description="Words/phrases indicating importance")
    recommended_response_time: str = Field(description="Recommended response timeframe")
    escalation_needed: bool = Field(description="Whether escalation is recommended")
    reasoning: str = Field(description="Explanation of the scoring")
    metadata: Dict[str, Any] = Field(description="Additional metadata")

class ActionRecommendationOutput(BaseModel):
    recommended_actions: List[Dict[str, str]] = Field(description="Recommended actions with priorities")
    delegation_suggestions: List[str] = Field(description="Tasks that could be delegated")
    scheduling_recommendation: str = Field(description="When to handle this")
    resources_needed: List[str] = Field(description="Resources required")
    potential_blockers: List[str] = Field(description="Potential blockers to address")

# Priority scoring prompt
priority_scoring_prompt = PromptTemplate(
    input_variables=["text", "sender_role", "context", "current_time"],
    template="""You are an expert at assessing message priority using the Eisenhower Matrix and other priority frameworks.

Analyze the following message for urgency and importance:

Message:
{text}

Sender role: {sender_role}
Additional context: {context}
Current time: {current_time}

Assess the message using these criteria:

URGENCY (Time-sensitive):
- Explicit deadlines mentioned
- Time-sensitive language (ASAP, urgent, immediately, today, etc.)
- Business impact if delayed
- External dependencies waiting
- Compliance or legal deadlines

IMPORTANCE (Value/Impact):
- Strategic alignment with goals
- Business value or revenue impact
- Number of stakeholders affected
- Long-term consequences
- Risk mitigation importance

Score both dimensions 0-100 and classify into Eisenhower Matrix:
- Q1 (Do First): Urgent & Important - Crisis, deadlines, problems
- Q2 (Schedule): Not Urgent & Important - Planning, prevention, improvement
- Q3 (Delegate): Urgent & Not Important - Interruptions, some calls
- Q4 (Eliminate): Not Urgent & Not Important - Time wasters, trivia

Provide your response in JSON format with:
- urgency_score: 0-100 (100 = requires immediate action)
- importance_score: 0-100 (100 = critical business impact)
- priority_level: "critical" (Q1, >80 both), "high" (Q1/Q2, >60), "medium" (Q2/Q3, 40-60), "low" (Q4, <40)
- priority_matrix_quadrant: "Q1", "Q2", "Q3", or "Q4"
- urgency_indicators: List of specific words/phrases indicating urgency
- importance_indicators: List of specific words/phrases indicating importance
- recommended_response_time: Specific timeframe (e.g., "within 2 hours", "by end of day", "this week")
- escalation_needed: true/false
- reasoning: Brief explanation of the scoring
- metadata: Include confidence_score (0-1), has_deadline (true/false), deadline_date (if applicable)

JSON Response:"""
)

# Action recommendation prompt
action_recommendation_prompt = PromptTemplate(
    input_variables=["text", "priority_scores", "available_time"],
    template="""Based on the priority assessment, recommend specific actions for handling this request.

Original message:
{text}

Priority assessment:
{priority_scores}

Available time: {available_time}

Provide actionable recommendations considering:
1. The priority quadrant and scores
2. Optimal handling approach
3. Resource allocation
4. Delegation opportunities
5. Scheduling strategy

Provide your response in JSON format with:
- recommended_actions: List of actions with priority order and estimated time
- delegation_suggestions: What could be delegated and to whom (by role)
- scheduling_recommendation: Specific scheduling advice
- resources_needed: Required resources or people
- potential_blockers: Issues to address proactively

JSON Response:"""
)

# Batch priority scoring prompt for multiple messages
batch_scoring_prompt = PromptTemplate(
    input_variables=["messages", "context"],
    template="""Analyze and rank multiple messages by priority.

Messages to analyze:
{messages}

Context: {context}

For each message:
1. Score urgency and importance
2. Assign to Eisenhower quadrant
3. Recommend handling order

Provide a ranked list with reasoning for the order.

JSON Response with:
- ranked_messages: List ordered by priority with scores
- handling_order: Specific sequence recommendation
- batch_insights: Overall patterns noticed
- time_allocation: Suggested time allocation per item

JSON Response:"""
)

# Create chains
json_parser = JsonOutputParser(pydantic_object=PriorityScoreOutput)
action_parser = JsonOutputParser(pydantic_object=ActionRecommendationOutput)

priority_scoring_chain = LLMChain(
    llm=llm,
    prompt=priority_scoring_prompt,
    output_parser=json_parser
)

action_recommendation_chain = LLMChain(
    llm=llm,
    prompt=action_recommendation_prompt,
    output_parser=action_parser
)

batch_scoring_chain = LLMChain(
    llm=llm,
    prompt=batch_scoring_prompt
)

def score_priority(
    text: str,
    sender_role: Optional[str] = None,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Score the priority of a message
    
    Args:
        text: The message to analyze
        sender_role: Role of the sender (CEO, customer, colleague, etc.)
        context: Additional context about the situation
    
    Returns:
        Priority scores and classification
    """
    try:
        result = priority_scoring_chain.invoke({
            "text": text,
            "sender_role": sender_role or "unknown",
            "context": context or "No additional context",
            "current_time": datetime.now().isoformat()
        })
        
        # Generate action recommendations for high priority items
        if result.get("priority_level") in ["critical", "high"]:
            actions = action_recommendation_chain.invoke({
                "text": text,
                "priority_scores": str(result),
                "available_time": "standard working hours"
            })
            result["action_recommendations"] = actions
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "urgency_score": 50,
                "importance_score": 50,
                "priority_level": "medium",
                "priority_matrix_quadrant": "Q2",
                "urgency_indicators": [],
                "importance_indicators": [],
                "recommended_response_time": "within 24 hours",
                "escalation_needed": False,
                "reasoning": "Error in priority assessment",
                "metadata": {"error": True}
            }
        }

def batch_score_priorities(
    messages: List[Dict[str, str]],
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Score and rank multiple messages by priority
    
    Args:
        messages: List of messages with metadata
        context: Overall context
    
    Returns:
        Ranked list with priority scores
    """
    try:
        # Format messages for analysis
        formatted_messages = "\n\n".join([
            f"Message {i+1} (from: {msg.get('sender', 'unknown')}):\n{msg['text']}"
            for i, msg in enumerate(messages)
        ])
        
        result = batch_scoring_chain.invoke({
            "messages": formatted_messages,
            "context": context or "Standard business context"
        })
        
        # Parse the string result to JSON
        import json
        parsed_result = json.loads(result["text"])
        
        return {
            "success": True,
            "data": parsed_result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "ranked_messages": [],
                "handling_order": [],
                "batch_insights": "",
                "time_allocation": {}
            }
        }

def get_priority_emoji(priority_level: str) -> str:
    """
    Get emoji representation for priority level
    """
    return {
        "critical": "🔴",
        "high": "🟠", 
        "medium": "🟡",
        "low": "🟢"
    }.get(priority_level, "⚪")

def get_matrix_explanation(quadrant: str) -> str:
    """
    Get explanation for Eisenhower Matrix quadrant
    """
    explanations = {
        "Q1": "Do First - Urgent and Important: Handle immediately",
        "Q2": "Schedule - Important but not Urgent: Plan and schedule",
        "Q3": "Delegate - Urgent but not Important: Delegate if possible",
        "Q4": "Eliminate - Neither Urgent nor Important: Consider declining"
    }
    return explanations.get(quadrant, "Unknown priority")

def calculate_response_deadline(
    urgency_score: float,
    importance_score: float,
    has_explicit_deadline: bool = False,
    deadline_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate recommended response deadline based on scores
    
    Args:
        urgency_score: Urgency score (0-100)
        importance_score: Importance score (0-100)
        has_explicit_deadline: Whether message contains explicit deadline
        deadline_date: Explicit deadline if mentioned
    
    Returns:
        Response deadline recommendation
    """
    if has_explicit_deadline and deadline_date:
        return {
            "deadline": deadline_date,
            "type": "explicit",
            "flexibility": "low"
        }
    
    # Calculate based on scores
    combined_score = (urgency_score * 0.6 + importance_score * 0.4)
    
    if combined_score >= 80:
        deadline = datetime.now() + timedelta(hours=2)
        response_time = "within 2 hours"
    elif combined_score >= 60:
        deadline = datetime.now() + timedelta(hours=8)
        response_time = "by end of day"
    elif combined_score >= 40:
        deadline = datetime.now() + timedelta(days=2)
        response_time = "within 2 days"
    else:
        deadline = datetime.now() + timedelta(days=7)
        response_time = "within a week"
    
    return {
        "deadline": deadline.isoformat(),
        "response_time": response_time,
        "type": "calculated",
        "flexibility": "medium" if combined_score < 60 else "low"
    }