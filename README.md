# GitPuller — Learning Progress Tracker

A tool that analyzes your recent GitHub commits with **AI** and tracks the technical concepts you're learning.

## Quick Start


## How It Works

1. Authenticates to GitHub using your `GITHUB_TOKEN`
2. Scans your repositories for commits authored in the past 24 hours
3. Sends code diffs to an **LLM** for analysis
4. Extracts learning concepts and stores them in a SQLite database

## Tech Stack

| Layer    | Technology                                    |
|----------|-----------------------------------------------|
| Backend  | Python, SQLAlchemy, Pydantic, PyGithub        |
| AI       | LangChain (provider-agnostic LLM abstraction)  |
| Frontend | Next.js 15, React 19, TypeScript              |
