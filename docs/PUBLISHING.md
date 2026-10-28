# GitHub repository

The public repository is [sumit-kolpe/careecho](https://github.com/sumit-kolpe/careecho).
It was published on October 28, 2026. Review automated checks on the
[Actions page](https://github.com/sumit-kolpe/careecho/actions).

## Publish a separate copy

To publish your own copy, use GitHub's **New repository** page and create an
empty repository without initializing a README or license. The commands below
are for a new local checkout with no existing remote.

From this project directory:

```bash
git status --short
git add .
git diff --cached --stat
git commit -m "Build CareEcho teach-back research prototype"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/careecho.git
git push -u origin main
```

Review staged files before committing. `.venv`, `.env`, caches, `private_data`, and
`outputs` are excluded; synthetic fixtures and checked-in reports are intentional.
Do not include real recordings or API keys. Authentication uses your own GitHub setup.

Suggested description: **Evidence-linked discharge teach-back review with local
Whisper, structured LLM outputs, and health-access barrier detection.**

Suggested topics: `python`, `healthcare`, `speech-recognition`, `whisper`, `nlp`,
`health-literacy`, `streamlit`, `responsible-ai`.

Before applying, replace any personal placeholders, run the demo yourself, check
GitHub Actions on the pushed commit, and add a short screen recording or screenshot
showing a synthetic case. You can link the repository directly in the application.
