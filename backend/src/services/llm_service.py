"""LLM service for analyzing code changes.

Uses LangChain's .with_structured_output() to guarantee the LLM
always returns data matching our Pydantic schema. No more manual
JSON parsing or silent failures.

Provider and model are configured entirely via .env — no code changes
needed to switch between Groq, OpenRouter, OpenAI, etc.

KEY CONCEPT — OpenAI-Compatible APIs:
  Many LLM providers (Groq, OpenRouter, Together, etc.) expose an API
  that follows the same format as OpenAI's. This means LangChain's
  ChatOpenAI class works with ALL of them — you just change the base_url.

KEY CONCEPT — Structured Output Methods:
  .with_structured_output() has two methods:

  "function_calling" (default):
    → Sends the Pydantic schema as a "tool" definition
    → LLM responds with a tool call containing structured JSON
    → Most reliable, but NOT all models support it
    → Works with: GPT-4o, Claude 3.5, Llama 3.3 on Groq

  "json_mode":
    → Sets response_format to {"type": "json_object"}
    → LangChain embeds the schema description in the prompt
    → Parses the raw JSON response into a Pydantic object
    → Less strict, but MUCH more widely supported
    → Works with: almost every model on every provider

  Which to use? Start with "json_mode" (safe default). Switch to
  "function_calling" only when your model explicitly supports it.
"""

import logging
from typing import List, Dict

from langchain_openai import ChatOpenAI
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

    The LLM provider, model, and structured output method are all read from
    settings (which come from .env). To switch models, just edit .env and
    restart — no code changes needed.

    Args:
        push_data: List of dicts containing repo name, commits, and patches

    Returns:
        List[LearningCreate]: Validated learning items (never raw dicts)
    """
    if not push_data:
        return []

    try:
        # 1. Initialize the LLM via LangChain
        #    ChatOpenAI works with ANY OpenAI-compatible API.
        #    The base_url tells it WHERE to send requests.
        #    Change it in .env to switch providers instantly.
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=0,  # Deterministic output for structured data
        )

        # 2. Bind our Pydantic schema with the configured method
        #    "json_mode"         → widely supported, embeds schema in prompt
        #    "function_calling"  → more reliable, but fewer models support it
        #    Configured via LLM_STRUCTURED_METHOD in .env
        method = settings.LLM_STRUCTURED_METHOD
        logger.info(
            f"Using model={settings.LLM_MODEL}, "
            f"method={method}, "
            f"base_url={settings.LLM_BASE_URL}"
        )
        structured_llm = llm.with_structured_output(
            LearningAnalysis, method=method
        )

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
