"""Gemini AI service for analyzing code changes."""

import json
from typing import List, Dict
from google import genai
from app.core.config import settings


def analyze_commits_with_ai(push_data: List[Dict], api_key: str = None) -> List[Dict]:
    """
    Send code changes to Gemini AI for learning analysis.
    
    Args:
        push_data: List of dicts containing repo name, commits, and patches
        api_key: Gemini API key (defaults to settings.GEMINI_API_KEY)
        
    Returns:
        List of learning items as dicts with keys: repo, technology, concept, date
    """
    if api_key is None:
        api_key = settings.GEMINI_API_KEY
    
    try:
        # Initialize Gemini client
        client = genai.Client(api_key=api_key)
        
        # Handle empty data
        if not push_data:
            return []
        
        # Build the user prompt with code changes
        user_prompt = "Here is the code activity from the last 24 hours:\n\n"
        
        for push in push_data:
            user_prompt += f"### Repository: {push['repo']}\n\n"
            for commit in push['commits']:
                user_prompt += f"**Commit ({commit['sha']})**: {commit['message']}\n\n"
                if commit['patches']:
                    user_prompt += "**Code Changes:**\n```\n"
                    for patch in commit['patches']:
                        user_prompt += patch + "\n\n"
                    user_prompt += "```\n\n"
                else:
                    user_prompt += "_No code diffs available_\n\n"
        
        # System prompt that enforces JSON structure
        system_prompt = (
            "You are a Developer Learning Tracker. Analyze the code changes to identify "
            "new technical concepts learned. Return ONLY a JSON array with this exact structure: "
            '[{"repo": "repo_name", "technology": "tool_or_framework_used", "concept": "what_was_learned", "date": "YYYY-MM-DD"}]. '
            "Ignore basic typos or formatting changes. Focus on meaningful learning moments "
            "like new APIs, algorithms, design patterns, or technologies. Return an empty array [] if nothing meaningful."
        )
        
        print("\nAnalyzing with Gemini AI...")
        
        # Generate content with JSON mode
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[system_prompt, user_prompt],
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # Parse JSON response
        try:
            learning_data = json.loads(response.text)
            return learning_data if isinstance(learning_data, list) else []
        except json.JSONDecodeError:
            print(f"Warning: Could not parse JSON response: {response.text}")
            return []
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return []
