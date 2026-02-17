"""LLM service for analyzing code changes.

Uses LangChain's .with_structured_output() to guarantee the LLM
always returns data matching our Pydantic schema. No more manual
JSON parsing or silent failures.

Currently uses Google's model by default, but because we use LangChain
as an abstraction layer, you can swap in any provider (OpenAI, Anthropic,
Mistral, etc.) by changing the import and constructor below.

KEY CONCEPT — .with_structured_output():
  Instead of telling the LLM "return JSON" and hoping for the best,
  we pass a Pydantic model definition. LangChain:
    1. Converts the schema into the LLM's function-calling format
    2. Sends it alongside the prompt
    3. Auto-parses the response into a validated Pydantic object
    4. Raises a clear error if validation fails
"""

import logging
from typing import List, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.config import settings
from src.schemas.learning import LearningCreate, LearningAnalysis

# Use a logger instead of print() — FastAPI captures these properly
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System prompt — tells the LLM what role to play and how to think
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a Developer Learning Tracker. Analyze the code changes to identify "
    "new technical concepts the developer learned. Focus on meaningful learning moments "
    "like new APIs, algorithms, design patterns, or technologies. "
    "Ignore basic typos, formatting changes, or trivial edits. "
    "If nothing meaningful was learned, return an empty list."
)


def _build_user_prompt(push_data: List[Dict]) -> str:
    """
    Build the user-facing prompt from GitHub push data.
    
    Separated into its own function so it can be tested independently.
    """
    prompt = "Here is the code activity from the last 24 hours:\n\n"

    for push in push_data:
        prompt += f"### Repository: {push['repo']}\n\n"
        for commit in push["commits"]:
            prompt += f"**Commit ({commit['sha']})**: {commit['message']}\n\n"
            if commit["patches"]:
                prompt += "**Code Changes:**\n```\n"
                for patch in commit["patches"]:
                    prompt += patch + "\n\n"
                prompt += "```\n\n"
            else:
                prompt += "_No code diffs available_\n\n"

    return prompt


def analyze_commits_with_ai(push_data: List[Dict]) -> List[LearningCreate]:
    """
    Send code changes to the configured LLM for learning analysis.

    Returns a list of validated LearningCreate objects — guaranteed to match
    the schema or an empty list on failure.

    Args:
        push_data: List of dicts containing repo name, commits, and patches

    Returns:
        List[LearningCreate]: Validated learning items (never raw dicts)
    """
    if not push_data:
        return []

    try:
        # 1. Initialize the LLM via LangChain
        #    To swap providers, change the import and this constructor.
        #    e.g. ChatOpenAI(model="gpt-4o", api_key=settings.OPENAI_API_KEY)
        llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.LLM_API_KEY,
            temperature=0,  # Deterministic output for structured data
        )

        # 2. Bind our Pydantic schema — this is the "bulletproof" part
        #    The LLM is now forced to return a LearningAnalysis object.
        #    LangChain handles JSON parsing + Pydantic validation internally.
        structured_llm = llm.with_structured_output(LearningAnalysis)

        # 3. Build messages
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_build_user_prompt(push_data)),
        ]

        # 4. Invoke — returns a LearningAnalysis object, NOT a string
        logger.info("Analyzing commits with LLM (structured output)...")
        result: LearningAnalysis = structured_llm.invoke(messages)

        logger.info(f"LLM returned {len(result.learnings)} learning items")
        return result.learnings

    except Exception as e:
        # Log the error but don't crash the API — return empty gracefully
        logger.error(f"LLM analysis failed: {e}")
        return []
