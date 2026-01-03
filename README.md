# Learning Progress Tracker

A small Python tool that analyzes your recent GitHub commits and logs "learning concepts" identified by Google Gemini.

## Overview

- The script scans your repositories for commits you authored in the last 24 hours.
- It extracts code diffs (patches) and sends them to Google Gemini to summarize technical concepts learned.
- The AI analysis is printed and appended to `LEARNING_LOG.md` with a date header.

What happens:

- The script authenticates to GitHub using `GITHUB_TOKEN`.
- It scans your repositories for commits authored by your account in the past 24 hours.
- For each commit found it collects file patches and builds a prompt.
- The prompt is sent to Google Gemini for analysis and the results are appended to `LEARNING_LOG.md`.
