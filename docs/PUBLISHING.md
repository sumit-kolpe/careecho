# Publish on GitHub

The repository is prepared locally. Creating a public remote is a separate step
requiring your GitHub account. Use GitHub's **New repository** page and create an
empty repository named `careecho` without initializing a README or license.

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
