# GitPuller — Learning Progress Tracker

A tool that analyzes your recent GitHub commits with **Google Gemini AI** and tracks the technical concepts you're learning.

## Project Structure

```
gitpuller/
├── .github/                 # CI/CD workflows
├── frontend/                # Next.js dashboard
│   ├── app/                 # App Router pages & components
│   ├── lib/                 # Utility functions
│   ├── package.json
│   └── next.config.js       # Proxies /api/* to Python backend
│
└── backend/                 # Python AI engine
    ├── main.py              # CLI entry point
    ├── requirements.txt
    ├── .env                 # API keys (copy from .env.example)
    └── src/
        ├── core/            # Config & settings
        ├── db/              # SQLAlchemy engine & session
        ├── models/          # ORM models
        ├── schemas/         # Pydantic validation schemas
        ├── crud/            # Database CRUD operations
        ├── services/        # GitHub & Gemini integrations
        ├── agents/          # LangGraph AI workflows (planned)
        └── api/             # FastAPI routers (planned)
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # Fill in your API keys
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## How It Works

1. Authenticates to GitHub using your `GITHUB_TOKEN`
2. Scans your repositories for commits authored in the past 24 hours
3. Sends code diffs to **Google Gemini** for analysis
4. Extracts learning concepts and stores them in a SQLite database

## Tech Stack

| Layer    | Technology                                    |
|----------|-----------------------------------------------|
| Backend  | Python, SQLAlchemy, Pydantic, PyGithub        |
| AI       | Google Gemini (via `google-genai`)             |
| Frontend | Next.js 15, React 19, TypeScript              |
