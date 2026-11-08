# Changelog

## 1.0.0 — 2026-11-08
- Add browser-based personal library for text-based PDF, Markdown and TXT.
- Preserve source filenames and PDF page references in retrieval results.
- Add demo workspace initialization from the browser.
- Make personal upload and deletion transactional at the application/index level.
- Include multilingual semantic embeddings, Qdrant local storage, optional Ollama answers.
- Add defensive file validation, safe browser text rendering, localhost host checks.
- Add a reproducible, deliberately small retrieval smoke benchmark and tests.
- Add lightweight automated CI, CPU-first Linux setup and optional Docker recipe.

**Scope:** v1.0 is a local, single-user app. It is **not** a cloud service, an audited security product, or an empirically validated high-accuracy QA system. Image-only PDFs still require OCR. The local benchmark is not a general-purpose evaluation.
