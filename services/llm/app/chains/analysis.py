from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Dict, Any
from app.core.config import settings

# Initialize LLM
llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.3,  # Lower temperature for analysis
    openai_api_key=settings.OPENAI_API_KEY
)

# Output schemas
class AnalysisOutput(BaseModel):
    result: Any = Field(description="The analysis result")
    confidence: float = Field(description="Confidence score 0-1")
    details: Dict[str, Any] = Field(description="Additional details")

# Tone analysis prompt
tone_analysis_prompt = PromptTemplate(
    input_variables=["text"],
    template="""Analyze the tone of the following text and categorize it.

Text:
{text}

Possible tones:
- technical: Heavy use of jargon, very detailed, engineering-focused
- casual: Informal, conversational
- formal: Professional, structured, business-like
- aggressive: Demanding, pushy, confrontational
- passive: Indirect, hesitant, overly polite
- neutral: Balanced, factual
- warm: Friendly, empathetic, supportive

Provide your response in JSON format with:
- tone: The primary tone detected
- confidence: Your confidence score (0-1)
- secondary_tones: List of other tones present

JSON Response:"""
)

# Clarity analysis prompt
clarity_analysis_prompt = PromptTemplate(
    input_variables=["text"],
    template="""Analyze the clarity of the following text on a scale of 0-1.

Text:
{text}

Consider:
1. Sentence structure complexity
2. Use of jargon or technical terms
3. Logical flow
4. Ambiguity in meaning
5. Accessibility to general audience

Provide your response in JSON format with:
- clarity_score: Overall clarity score (0-1, where 1 is perfectly clear)
- issues: List of clarity issues found
- improvements: Specific suggestions to improve clarity

JSON Response:"""
)

# Structure analysis prompt
structure_analysis_prompt = PromptTemplate(
    input_variables=["text"],
    template="""Analyze the structure and organization of the following text.

Text:
{text}

Evaluate:
1. Information hierarchy
2. Logical flow
3. Use of formatting (if any)
4. Presence of key components (intro, body, conclusion, action items)

Provide your response in JSON format with:
- structure: Object describing the structure found
- suggestions: List of structural improvements
- technical_terms: List of technical terms found with definitions
- key_points: List of main points extracted

JSON Response:"""
)

# Priority detection prompt
priority_detection_prompt = PromptTemplate(
    input_variables=["text"],
    template="""Analyze the urgency and priority level of the following message.

Text:
{text}

Look for:
1. Time-sensitive language (ASAP, urgent, deadline, etc.)
2. Impact indicators (critical, blocking, major issue)
3. Escalation language
4. Specific deadlines mentioned

Classify priority as:
- critical: Immediate action required, blocking issues
- high: Important, needs attention soon
- medium: Standard priority, regular workflow
- low: Informational, no immediate action needed

Provide your response in JSON format with:
- priority: The detected priority level
- indicators: List of phrases/words that indicate this priority
- deadline: Any specific deadline mentioned (or null)
- recommended_response_time: Suggested response timeframe

JSON Response:"""
)

# Create chains
tone_analysis_chain = LLMChain(
    llm=llm,
    prompt=tone_analysis_prompt,
    output_parser=JsonOutputParser()
)

clarity_analysis_chain = LLMChain(
    llm=llm,
    prompt=clarity_analysis_prompt,
    output_parser=JsonOutputParser()
)

structure_analysis_chain = LLMChain(
    llm=llm,
    prompt=structure_analysis_prompt,
    output_parser=JsonOutputParser()
)

priority_detection_chain = LLMChain(
    llm=llm,
    prompt=priority_detection_prompt,
    output_parser=JsonOutputParser()
)