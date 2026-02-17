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

        # -------------------------------------------------------------------
        # DATA PREPARATION: Flatten & Batch
        # -------------------------------------------------------------------
        # Flatten: [(repo_name, commit_dict), ...]
        all_commits = []
        for push in push_data:
            repo_name = push["repo"]
            for commit in push["commits"]:
                all_commits.append((repo_name, commit))

        total_commits = len(all_commits)
        BATCH_SIZE = 5
        all_learnings = []

        logger.info(f"Analyzing {total_commits} commits in batches of {BATCH_SIZE}...")

        # Process in batches
        for i in range(0, total_commits, BATCH_SIZE):
            batch = all_commits[i : i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (total_commits + BATCH_SIZE - 1) // BATCH_SIZE

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} commits)...")

            # Reconstruct mini-push_data for this batch
            # We group by repo again to keep the prompt clean and robust
            mini_push_data = []
            current_repo = None
            current_commits = []

            # Sort by repo to group them easily (optional but cleaner)
            batch.sort(key=lambda x: x[0])

            for repo_name, commit in batch:
                # If it's a new repo in this batch, start a new entry
                if repo_name != current_repo:
                    if current_repo is not None:
                        mini_push_data.append({
                            "repo": current_repo,
                            "commits": current_commits
                        })
                    current_repo = repo_name
                    current_commits = []
                
                current_commits.append(commit)
            
            # Don't forget the last group
            if current_repo:
                mini_push_data.append({
                    "repo": current_repo,
                    "commits": current_commits
                })

                # ---------------------------------------------------------------
            # LLM INVOCATION
            # ---------------------------------------------------------------
            try:
                user_prompt_content = _build_user_prompt(mini_push_data)
                
                # DEBUG PROMPT
                logger.info("========== DEBUG: PROMPT START ==========")
                logger.info(f"Prompt Length: {len(user_prompt_content)} characters")
                logger.info(f"Prompt Preview (first 500 chars):\n{user_prompt_content[:500]}...")
                logger.info("========== DEBUG: PROMPT END ============")

                messages = [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=user_prompt_content),
                ]

                result: LearningAnalysis = structured_llm.invoke(messages)
                if result and result.learnings:
                    logger.info(f"  Batch {batch_num} found {len(result.learnings)} items")
                    all_learnings.extend(result.learnings)
                else:
                    logger.debug(f"  Batch {batch_num} returned no items")

            except Exception as e:
                logger.error(f"  Batch {batch_num} failed: {e}")
                # Continue to next batch instead of failing everything
                continue

        logger.info(f"Total learning items found across all batches: {len(all_learnings)}")
        return all_learnings

    except Exception as e:
        # Log the error but don't crash the API — return empty gracefully
        logger.error(f"LLM analysis setup failed: {e}")
        return []
