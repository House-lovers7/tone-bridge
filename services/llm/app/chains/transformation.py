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
    temperature=0.7,
    openai_api_key=settings.OPENAI_API_KEY
)

# Output schemas
class ToneTransformOutput(BaseModel):
    text: str = Field(description="The transformed text")
    suggestions: List[str] = Field(description="Additional suggestions for improvement")
    metadata: Dict[str, Any] = Field(description="Additional metadata")

# Tone transformation prompt with adjustable intensity
tone_prompt = PromptTemplate(
    input_variables=["text", "target_tone", "intensity_level"],
    template="""You are an expert communication specialist helping bridge the gap between engineers and non-engineers.

Transform the following text to have a {target_tone} tone with intensity level {intensity_level} while preserving the core message and intent.

Intensity levels (0-3):
- 0: Keep original tone (minimal changes, only fix obvious issues)
- 1: Light adjustment (subtle improvements, maintain original style)
- 2: Moderate transformation (clear tone shift, balanced approach)
- 3: Full transformation (complete tone overhaul, maximum adjustment)

Target tones can include:
- warm: Add empathy, friendliness, and human touch
- professional: Formal, clear, and business-appropriate
- casual: Relaxed, conversational, approachable
- technical: Precise, detailed, engineering-focused
- executive: High-level, strategic, decision-oriented

Apply the intensity level to determine how much to transform:
- Level 0: Only fix grammatical errors and clarify ambiguities
- Level 1: Add minimal courtesy phrases, slight softening
- Level 2: Restructure for better flow, add appropriate emotional context
- Level 3: Complete rewrite with maximum tone adjustment

Original text:
{text}

Provide your response in JSON format with:
- text: The transformed message
- suggestions: List of 2-3 additional improvement suggestions
- metadata: Include detected_tone (original tone), transformation_score (0-1), intensity_applied (0-3)

JSON Response:"""
)

# Structure transformation prompt
structure_prompt = PromptTemplate(
    input_variables=["text", "options"],
    template="""You are an expert at structuring communication for clarity and impact.

Restructure the following text to be more organized and easier to understand.
Focus on:
1. Clear hierarchy of information
2. Logical flow
3. Proper use of bullet points or numbered lists
4. Clear sections if needed

Original text:
{text}

Options: {options}

Provide your response in JSON format with:
- text: The restructured message
- suggestions: List of structural improvements made
- metadata: Include structure_score (0-1), key_points extracted

JSON Response:"""
)

# Summarization prompt
summarization_prompt = PromptTemplate(
    input_variables=["text", "max_length"],
    template="""You are an expert at creating concise, impactful summaries.

Summarize the following text to approximately {max_length} words while preserving key information and action items.

Original text:
{text}

Provide your response in JSON format with:
- text: The summary
- suggestions: List of key points preserved
- metadata: Include compression_ratio, preserved_action_items

JSON Response:"""
)

# Terminology transformation prompt
terminology_prompt = PromptTemplate(
    input_variables=["text", "domain"],
    template="""You are an expert at translating technical jargon into accessible language and vice versa.

Transform technical terms in the following text to be more accessible to a {domain} audience.
Domains can be: general (non-technical), business, technical, executive

Original text:
{text}

Provide your response in JSON format with:
- text: The transformed text with terminology adjusted
- suggestions: List of term replacements made
- metadata: Include terms_replaced (list of [original, replacement] pairs)

JSON Response:"""
)

# Create chains with JSON output parser
json_parser = JsonOutputParser(pydantic_object=ToneTransformOutput)

tone_transformation_chain = LLMChain(
    llm=llm,
    prompt=tone_prompt,
    output_parser=json_parser
)

structure_transformation_chain = LLMChain(
    llm=llm,
    prompt=structure_prompt,
    output_parser=json_parser
)

summarization_chain = LLMChain(
    llm=llm,
    prompt=summarization_prompt,
    output_parser=json_parser
)

terminology_chain = LLMChain(
    llm=llm,
    prompt=terminology_prompt,
    output_parser=json_parser
)