# GitHub publication — DeskMind AI

**Existing public repository:** https://github.com/idginity124/-DeskMind-AI

The repository name starts with a hyphen (`-`). Use the exact GitHub URL below; do not remove or rename the prefix accidentally.

## Publish from the extracted project (Bash or Fish)

```bash
cd /path/to/DeskMind-AI
git init -b main
git add .
git status --short
git commit -m "release: DeskMind AI v1.0 local document assistant"
git remote add origin https://github.com/idginity124/-DeskMind-AI.git
git push -u origin main
```

If `main` already has a README commit, fetch and reconcile with it before pushing; avoid force-pushing other work. Authenticate through Git Credential Manager or GitHub CLI, **not by pasting tokens into chat**. Private data in `.deskmind/`, `.venv/`, `.env` and user PDFs must not be committed.

## Verify the release

1. Check that README images, Turkish translation and local links render on GitHub.
2. Confirm GitHub Actions workflow `.github/workflows/tests.yml` passes.
3. Review repository's public files to ensure no secrets or personal documents were included.
4. Add topics: `rag`, `local-ai`, `python`, `fastapi`, `qdrant`, `sentence-transformers`, `ollama`, `pdf`, `ai-engineering`.
5. Publish a source release/tag if desired, with an accurate description of local-only scope.

Releasing source is not equivalent to providing prebuilt binaries. The first model download requires internet and users install Python dependencies locally.
