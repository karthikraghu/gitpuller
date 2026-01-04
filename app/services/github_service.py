"""GitHub service for fetching commit data."""

from datetime import datetime, timedelta, timezone
from typing import List, Dict
from github import Github, GithubException, Auth
from app.core.config import settings


def fetch_recent_commits(github_token: str = None) -> List[Dict]:
    """
    Fetch commits authored by the authenticated user in the last 24 hours.
    
    Args:
        github_token: GitHub authentication token (defaults to settings.GITHUB_TOKEN)
        
    Returns:
        List of dicts containing repo name, commits, and code patches
    """
    if github_token is None:
        github_token = settings.GITHUB_TOKEN
    
    try:
        # Authenticate with GitHub
        auth = Auth.Token(github_token)
        g = Github(auth=auth, timeout=settings.REQUEST_TIMEOUT)
        user = g.get_user()
        print(f"Authenticated as: {user.login}")

        # Calculate 24 hours ago
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        push_data = []
        processed_repos = 0

        print("\nScanning your repositories for commits in the last 24 hours...")

        for repo in user.get_repos():
            if processed_repos >= settings.MAX_REPOS:
                print(f"Reached max_repos limit ({settings.MAX_REPOS}); stopping repo scan.")
                break

            processed_repos += 1
            commits_data = []
            
            try:
                commits = repo.get_commits(since=cutoff_time, author=user.login)
                commit_count = 0
                
                for commit in commits:
                    if commit_count >= settings.MAX_COMMITS_PER_REPO:
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
                        
                    except GithubException:
                        # Silently ignore inaccessible commits
                        continue

                if commits_data:
                    push_data.append({
                        "repo": repo.full_name,
                        "commits": commits_data
                    })
                    print(f"  Found {len(commits_data)} commits in {repo.full_name}")

            except GithubException:
                # Silently ignore inaccessible repos
                continue
            except Exception:
                # Silently ignore other errors
                continue

        return push_data

    except GithubException as e:
        print(f"GitHub API Error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []
