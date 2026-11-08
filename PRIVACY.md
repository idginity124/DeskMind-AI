# Privacy

DeskMind is designed as a **single-user, local-first** desktop/browser application.

- Uploaded documents live in `.deskmind/workspaces/personal/documents` by default. Their embeddings and text payloads are in the Qdrant local index next to that folder.
- The app does **not** require a cloud account and does **not** send your documents to a hosted LLM API. The optional Ollama endpoint is hardcoded to `127.0.0.1:11434`.
- Initial embedding model downloads require network access to the model host. Check your local environment and dependency policies before using proprietary documents.
- Documents are not encrypted at rest. Treat the `.deskmind/` folder as sensitive, limit filesystem access and back it up appropriately.
- Deleting documents removes them from the active index; it is **not** a secure deletion guarantee for storage media or backups.
- `.deskmind/` is excluded from Git. Never commit document data, downloaded model weights, `.env` files or API keys.
- No telemetry/analytics code is included in the application itself.

This is an experimental application, not an audited privacy product. Please review `SECURITY.md` before using sensitive information.
