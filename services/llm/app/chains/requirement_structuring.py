"""
Requirement Structuring Chain
Transforms unstructured text into organized requirements with 4 quadrants:
- Background/Context
- Requests/Needs
- Constraints/Limitations
- Timeline/Deadline
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
    temperature=0.3,  # Lower temperature for more structured output
    openai_api_key=settings.OPENAI_API_KEY
)

# Output schema
class RequirementStructureOutput(BaseModel):
    background: str = Field(description="Background context and why this is needed")
    requests: List[str] = Field(description="Specific requests and needs")
    constraints: List[str] = Field(description="Constraints, limitations, and conditions")
    timeline: str = Field(description="Timeline, deadline, or urgency")
    missing_info: List[str] = Field(description="Information that seems to be missing")
    priority_indicators: List[str] = Field(description="Words or phrases indicating priority")
    metadata: Dict[str, Any] = Field(description="Additional analysis metadata")

# Requirement structuring prompt
requirement_structure_prompt = PromptTemplate(
    input_variables=["text", "context"],
    template="""You are an expert at analyzing and structuring requirements from unstructured communication.

Analyze the following text and structure it into clear requirements with 4 key components:

1. **Background/Context**: Why is this needed? What's the situation?
2. **Requests/Needs**: What specifically is being asked for?
3. **Constraints/Limitations**: What are the limitations, conditions, or restrictions?
4. **Timeline/Deadline**: When is this needed? What's the urgency?

Also identify:
- Missing information that would be helpful
- Priority indicators (urgent, ASAP, critical, etc.)

Input text:
{text}

Additional context (if any):
{context}

Provide your response in JSON format with:
- background: A clear summary of the background and context
- requests: List of specific requests (be precise and actionable)
- constraints: List of constraints and limitations
- timeline: Timeline or deadline information (or "Not specified" if missing)
- missing_info: List of important missing information
- priority_indicators: List of words/phrases indicating priority level
- metadata: Include structure_clarity_score (0-1), completeness_score (0-1)

Important guidelines:
- If information for a section is not present, indicate "Not specified" or provide an empty list
- Be precise and avoid assumptions
- Maintain the original intent while organizing the information
- For Japanese text, maintain cultural context and politeness levels

JSON Response:"""
)

# Enhanced prompt for incomplete requirements
requirement_completion_prompt = PromptTemplate(
    input_variables=["text", "missing_info"],
    template="""You are helping to complete incomplete requirements by generating clarifying questions.

Original text:
{text}

Missing information identified:
{missing_info}

Generate specific questions that would help gather the missing information.
Make questions clear, professional, and non-confrontational.

Provide your response in JSON format with:
- questions: List of clarifying questions to ask
- question_categories: Categorize each question (timeline, scope, resources, constraints, approval)
- suggested_defaults: Suggest reasonable defaults for missing information
- metadata: Include completeness_improvement_potential (0-1)

JSON Response:"""
)

# Create chains
json_parser = JsonOutputParser(pydantic_object=RequirementStructureOutput)

requirement_structuring_chain = LLMChain(
    llm=llm,
    prompt=requirement_structure_prompt,
    output_parser=json_parser
)

class RequirementCompletionOutput(BaseModel):
    questions: List[str] = Field(description="Clarifying questions to ask")
    question_categories: Dict[str, str] = Field(description="Category for each question")
    suggested_defaults: Dict[str, str] = Field(description="Suggested default values")
    metadata: Dict[str, Any] = Field(description="Additional metadata")

completion_json_parser = JsonOutputParser(pydantic_object=RequirementCompletionOutput)

requirement_completion_chain = LLMChain(
    llm=llm,
    prompt=requirement_completion_prompt,
    output_parser=completion_json_parser
)

def structure_requirements(text: str, context: Optional[str] = None) -> Dict[str, Any]:
    """
    Structure unstructured text into organized requirements
    
    Args:
        text: The unstructured input text
        context: Optional additional context
    
    Returns:
        Structured requirements with 4 quadrants
    """
    try:
        result = requirement_structuring_chain.invoke({
            "text": text,
            "context": context or "No additional context provided"
        })
        
        # If significant information is missing, generate completion questions
        if result.get("missing_info") and len(result["missing_info"]) > 0:
            completion_result = requirement_completion_chain.invoke({
                "text": text,
                "missing_info": ", ".join(result["missing_info"])
            })
            result["completion_suggestions"] = completion_result
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "background": "Error processing requirements",
                "requests": [],
                "constraints": [],
                "timeline": "Not specified",
                "missing_info": [],
                "priority_indicators": [],
                "metadata": {"error": True}
            }
        }

def generate_structured_summary(structured_data: Dict[str, Any]) -> str:
    """
    Generate a well-formatted summary from structured requirements
    
    Args:
        structured_data: The structured requirement data
    
    Returns:
        Formatted text summary
    """
    background = structured_data.get("background", "")
    requests = structured_data.get("requests", [])
    constraints = structured_data.get("constraints", [])
    timeline = structured_data.get("timeline", "Not specified")
    
    summary_parts = []
    
    if background:
        summary_parts.append(f"【背景】\n{background}")
    
    if requests:
        summary_parts.append(f"【要望】\n" + "\n".join([f"• {req}" for req in requests]))
    
    if constraints:
        summary_parts.append(f"【制約条件】\n" + "\n".join([f"• {const}" for const in constraints]))
    
    if timeline and timeline != "Not specified":
        summary_parts.append(f"【期限】\n{timeline}")
    
    return "\n\n".join(summary_parts)