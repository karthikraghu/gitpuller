"""GitHub service for fetching commit data.

Fetches recent commits from all repos the authenticated user has access to,
filters out non-useful files (lockfiles, build artifacts, media), and
returns only the patches that contain human-authored code worth analyzing.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from github import Github, GithubException, Auth
from src.core.config import settings
from src.core.filters import is_worth_analyzing

# Use logger instead of print() — consistent with the rest of the backend
logger = logging.getLogger(__name__)


def fetch_recent_commits(github_token: str = None) -> List[Dict]:
    """
    Fetch commits authored by the authenticated user in the last 24 hours.

    The pipeline:
      1. Authenticate with GitHub
      2. Scan repos for recent commits
      3. For each commit, extract file patches
      4. FILTER out files that aren't worth analyzing (lockfiles, media, etc.)
      5. Return only meaningful code diffs

    Args:
        github_token: GitHub authentication token (defaults to settings.GITHUB_TOKEN)

    Returns:
        List of dicts containing repo name, commits, and filtered code patches
    """
    if github_token is None:
        github_token = settings.GITHUB_TOKEN

    try:
        # Authenticate with GitHub
        auth = Auth.Token(github_token)
        g = Github(auth=auth, timeout=settings.REQUEST_TIMEOUT)
        user = g.get_user()
        logger.info(f"Authenticated as: {user.login}")

        # Calculate 24 hours ago
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        push_data = []
        processed_repos = 0
        total_skipped = 0  # Track how many files we filter out

        logger.info("Scanning repositories for commits in the last 24 hours...")

        for repo in user.get_repos():
            if processed_repos >= settings.MAX_REPOS:
                logger.info(f"Reached max_repos limit ({settings.MAX_REPOS})")
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
                            # ── FILTER 1: Skip files with no new code ────
                            # Renames and deletions don't teach you anything new.
                            if file.status in ("renamed", "removed"):
                                continue

                            # ── FILTER 2: Skip junk files via AI-Ignore ──
                            # This is where pathspec does the heavy lifting.
                            # Lockfiles, build artifacts, media, etc. are
                            # caught here BEFORE they ever reach the LLM.
                            if not is_worth_analyzing(file.filename):
                                logger.debug(f"  Skipped: {file.filename}")
                                total_skipped += 1
                                continue

                            # File passed both filters — include its patch
                            if file.patch:
                                patches.append(
                                    f"File: {file.filename}\n{file.patch}"
                                )

                        commits_data.append({
                            "message": detailed.commit.message,
                            "sha": sha[:7],
                            "patches": patches
                        })
                        commit_count += 1

                    except GithubException:
                        continue

                if commits_data:
                    push_data.append({
                        "repo": repo.full_name,
                        "commits": commits_data
                    })
                    logger.info(
                        f"  {repo.full_name}: {len(commits_data)} commits"
                    )

            except GithubException:
                continue
            except Exception:
                continue

        if total_skipped > 0:
            logger.info(f"AI-Ignore filter skipped {total_skipped} files total")

        print(f"DEBUG: Retrieved GitHub data: {push_data}")
        return push_data

    except GithubException as e:
        logger.error(f"GitHub API Error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []
