"""
Background Completion Chain
Detects missing information and generates intelligent questions to complete context
"""

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.core.config import settings

# Initialize LLM
llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.4,  # Balanced for creative yet accurate questions
    openai_api_key=settings.OPENAI_API_KEY
)

# Output schemas
class MissingInfoAnalysis(BaseModel):
    missing_elements: List[str] = Field(description="List of missing information elements")
    confidence_level: float = Field(description="Confidence in the analysis (0-1)")
    context_gaps: Dict[str, str] = Field(description="Specific context gaps identified")
    completeness_score: float = Field(description="Overall completeness score (0-1)")

class BackgroundCompletionOutput(BaseModel):
    analysis: MissingInfoAnalysis = Field(description="Analysis of missing information")
    questions: List[Dict[str, str]] = Field(description="Generated questions with metadata")
    enhanced_text: str = Field(description="Text with placeholders for missing info")
    suggestions: List[str] = Field(description="Suggestions for improving communication")
    metadata: Dict[str, Any] = Field(description="Additional metadata")

# Background analysis prompt
background_analysis_prompt = PromptTemplate(
    input_variables=["text", "communication_type", "domain"],
    template="""You are an expert at analyzing business communication to identify missing context and information.

Analyze the following {communication_type} communication in the {domain} domain:

Text:
{text}

Identify:
1. Missing background information that would help understand the request better
2. Implicit assumptions that should be made explicit
3. Context gaps that could lead to misunderstanding
4. Information that the recipient would likely need to know

Consider common missing elements such as:
- Purpose and objectives
- Current situation/problem
- Previous attempts or history
- Stakeholders involved
- Success criteria
- Resources available
- Dependencies and blockers
- Business impact

Provide your response in JSON format with:
- missing_elements: List of missing information (be specific)
- confidence_level: Your confidence in this analysis (0-1)
- context_gaps: Dictionary mapping gap type to description
- completeness_score: Overall completeness (0-1, where 1 is perfectly complete)

JSON Response:"""
)

# Question generation prompt
question_generation_prompt = PromptTemplate(
    input_variables=["text", "missing_info", "recipient_role"],
    template="""You are helping to gather missing information through intelligent, non-intrusive questions.

Original message:
{text}

Missing information identified:
{missing_info}

Recipient role: {recipient_role}

Generate professional, contextual questions that:
1. Are specific and actionable
2. Don't sound accusatory or critical
3. Show understanding of the situation
4. Are appropriate for the recipient's role
5. Include why the information is helpful

For each missing element, create a question with:
- The question itself (natural, conversational)
- Category (background, requirements, constraints, resources, timeline, approval)
- Priority (high, medium, low)
- Why it matters (brief explanation)

Also enhance the original text by adding [NEEDS INFO: topic] placeholders where information is missing.

Provide your response in JSON format with:
- questions: List of dictionaries with 'question', 'category', 'priority', 'rationale'
- enhanced_text: Original text with [NEEDS INFO] placeholders
- suggestions: List of general communication improvement tips
- metadata: Include question_quality_score (0-1)

JSON Response:"""
)

# Auto-completion prompt for common scenarios
auto_completion_prompt = PromptTemplate(
    input_variables=["text", "scenario_type", "organization_context"],
    template="""You are an expert at intelligently filling in missing context based on common patterns.

Text:
{text}

Scenario type: {scenario_type}
Organization context: {organization_context}

Based on common patterns in {scenario_type} scenarios, provide intelligent defaults and assumptions for missing information.

Generate:
1. Likely background context
2. Probable objectives
3. Typical constraints in this scenario
4. Standard timelines for this type of request
5. Common stakeholders involved

Provide your response in JSON format with:
- inferred_background: Likely background context
- probable_objectives: List of probable objectives
- typical_constraints: Common constraints for this scenario
- suggested_timeline: Typical timeline
- likely_stakeholders: Probable stakeholders
- confidence_scores: Dictionary of confidence for each inference (0-1)
- disclaimer: Brief note about these being intelligent assumptions

JSON Response:"""
)

# Create chains
analysis_parser = JsonOutputParser(pydantic_object=MissingInfoAnalysis)
completion_parser = JsonOutputParser(pydantic_object=BackgroundCompletionOutput)

background_analysis_chain = LLMChain(
    llm=llm,
    prompt=background_analysis_prompt,
    output_parser=analysis_parser
)

question_generation_chain = LLMChain(
    llm=llm,
    prompt=question_generation_prompt
)

auto_completion_chain = LLMChain(
    llm=llm,
    prompt=auto_completion_prompt
)

def analyze_background_completeness(
    text: str,
    communication_type: str = "business",
    domain: str = "general"
) -> Dict[str, Any]:
    """
    Analyze text for missing background information
    
    Args:
        text: The text to analyze
        communication_type: Type of communication (business, technical, casual)
        domain: Domain context (IT, sales, marketing, etc.)
    
    Returns:
        Analysis of missing information
    """
    try:
        result = background_analysis_chain.invoke({
            "text": text,
            "communication_type": communication_type,
            "domain": domain
        })
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "missing_elements": [],
                "confidence_level": 0,
                "context_gaps": {},
                "completeness_score": 0
            }
        }

def generate_completion_questions(
    text: str,
    missing_info: List[str],
    recipient_role: str = "colleague"
) -> Dict[str, Any]:
    """
    Generate questions to gather missing information
    
    Args:
        text: Original text
        missing_info: List of missing information elements
        recipient_role: Role of the person asking questions
    
    Returns:
        Generated questions and enhanced text
    """
    try:
        result = question_generation_chain.invoke({
            "text": text,
            "missing_info": "\n".join(missing_info),
            "recipient_role": recipient_role
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
                "questions": [],
                "enhanced_text": text,
                "suggestions": [],
                "metadata": {}
            }
        }

def auto_complete_background(
    text: str,
    scenario_type: Optional[str] = None,
    organization_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Automatically infer and complete missing background based on patterns
    
    Args:
        text: Original text
        scenario_type: Type of scenario (feature_request, bug_report, etc.)
        organization_context: Organization-specific context
    
    Returns:
        Intelligent completions and inferences
    """
    # Detect scenario type if not provided
    if not scenario_type:
        scenario_type = _detect_scenario_type(text)
    
    try:
        result = auto_completion_chain.invoke({
            "text": text,
            "scenario_type": scenario_type,
            "organization_context": organization_context or "general business environment"
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
            "data": {}
        }

def _detect_scenario_type(text: str) -> str:
    """
    Simple heuristic to detect scenario type from text
    """
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["bug", "error", "broken", "fix"]):
        return "bug_report"
    elif any(word in text_lower for word in ["feature", "enhancement", "add", "implement"]):
        return "feature_request"
    elif any(word in text_lower for word in ["meeting", "discuss", "review"]):
        return "meeting_request"
    elif any(word in text_lower for word in ["approve", "approval", "permission"]):
        return "approval_request"
    elif any(word in text_lower for word in ["deadline", "urgent", "asap", "priority"]):
        return "urgent_task"
    else:
        return "general_request"

def complete_communication(
    text: str,
    auto_mode: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function to complete communication with missing background
    
    Args:
        text: Input text
        auto_mode: Whether to auto-complete or just generate questions
        **kwargs: Additional parameters
    
    Returns:
        Complete analysis and suggestions
    """
    # First, analyze what's missing
    analysis = analyze_background_completeness(
        text,
        kwargs.get("communication_type", "business"),
        kwargs.get("domain", "general")
    )
    
    if not analysis["success"]:
        return analysis
    
    missing_elements = analysis["data"]["missing_elements"]
    
    # Generate completion based on mode
    if auto_mode:
        # Auto-complete with intelligent defaults
        completion = auto_complete_background(
            text,
            kwargs.get("scenario_type"),
            kwargs.get("organization_context")
        )
    else:
        # Generate questions for manual completion
        completion = generate_completion_questions(
            text,
            missing_elements,
            kwargs.get("recipient_role", "colleague")
        )
    
    # Combine results
    return {
        "success": True,
        "data": {
            "analysis": analysis["data"],
            "completion": completion["data"] if completion["success"] else None,
            "mode": "auto" if auto_mode else "manual"
        }
    }