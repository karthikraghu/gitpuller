"""
Learning Progress Tracker
A Python tool to track learning progress using Gemini AI and GitHub integration.
"""

import os
from datetime import datetime, timedelta, timezone
from github import Github, GithubException
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def fetch_recent_push_events(github_token, max_repos=50, max_commits_per_repo=10, request_timeout=10):
    """
    Fetch commits authored by the authenticated user across their repositories in the last 24 hours.
    Returns a list of repos with commits and diffs.

    Args:
        github_token: GitHub token string
        max_repos: Maximum number of repositories to scan
        max_commits_per_repo: Maximum commits to fetch per repo
        request_timeout: Timeout in seconds for GitHub API requests
    """
    try:
        g = Github(github_token, timeout=request_timeout)
        user = g.get_user()
        print(f"Authenticated as: {user.login}")

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        push_data = []
        processed_repos = 0

        print("\nScanning your repositories for commits in the last 24 hours...")

        for repo in user.get_repos():
            if processed_repos >= max_repos:
                print(f"Reached max_repos limit ({max_repos}); stopping repo scan.")
                break

            processed_repos += 1
            commits_data = []
            try:
                commits = repo.get_commits(since=cutoff_time, author=user.login)
                commit_count = 0
                for commit in commits:
                    if commit_count >= max_commits_per_repo:
                        break

                    sha = commit.sha
                    try:
                        detailed = repo.get_commit(sha)
                        patches = []
                        for file in getattr(detailed, "files", []):
                            if file.patch:
                                patches.append(f"File: {file.filename}\n{file.patch}")

                        commits_data.append({
                            "message": detailed.commit.message,
                            "sha": sha[:7],
                            "patches": patches
                        })
                        commit_count += 1
                    except GithubException as e:
                        print(f"  Could not fetch details for commit {sha[:7]} in {repo.full_name}: {e}")
                        continue

                if commits_data:
                    push_data.append({
                        "repo": repo.full_name,
                        "commits": commits_data
                    })
                    print(f"  Found {len(commits_data)} commits in {repo.full_name}")

            except GithubException as e:
                print(f"  Could not access repo {repo.full_name}: {e}")
                continue

        return push_data

    except GithubException as e:
        print(f"GitHub API Error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def analyze_with_gemini(push_data, api_key):
    """
    Send the collected code changes to Gemini AI for analysis.
    Returns the AI-generated learning summary.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Build the prompt with collected data
        if not push_data:
            return "No code activity found in the last 24 hours."
        
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
        
        system_prompt = (
            "You are a Developer Learning Tracker. Analyze the code changes to identify "
            "new technical concepts learned. Group the output by Repository. "
            "Ignore basic typos or formatting changes. Focus on meaningful learning moments "
            "like new APIs, algorithms, design patterns, or technologies."
        )
        
        print("\nAnalyzing with Gemini AI...")
        
        response = model.generate_content(
            [system_prompt, user_prompt],
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2048,
            )
        )
        
        return response.text
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return f"Error analyzing with AI: {e}"


def save_to_log(analysis):
    """
    Append the analysis to LEARNING_LOG.md with today's date as a header.
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = "LEARNING_LOG.md"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n## {today}\n\n")
            f.write(analysis)
            f.write("\n\n---\n")
        
        print(f"\nAnalysis saved to {log_file}")
        
    except Exception as e:
        print(f"Could not save to log file: {e}")


def main():
    """
    Main entry point for the Learning Progress Tracker.
    """
    print("=" * 60)
    print("GitHub Learning Progress Tracker")
    print("=" * 60)
    
    # Load API keys from environment
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not github_token:
        print("Error: GITHUB_TOKEN not found in .env file")
        return
    
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY not found in .env file")
        return
    
    # Step 1: Fetch GitHub activity (only your commits, across your repos)
    push_data = fetch_recent_push_events(github_token, max_repos=50, max_commits_per_repo=10, request_timeout=10)
    
    if not push_data:
        print("\nNo push events found in the last 24 hours.")
        return
    
    # Step 2: Analyze with Gemini AI
    analysis = analyze_with_gemini(push_data, gemini_api_key)
    
    # Step 3: Display results
    print("\n" + "=" * 60)
    print("LEARNING ANALYSIS")
    print("=" * 60)
    print(analysis)
    
    # Step 4: Save to log file
    save_to_log(analysis)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
