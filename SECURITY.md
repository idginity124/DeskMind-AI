# Security policy and scope

**v1.0 local-first single-user release; single user; localhost only.**

Run `python -m uvicorn api:app --host 127.0.0.1 --port 8000`. Do not use `--host 0.0.0.0`, expose it behind a proxy, share its port, or deploy to public infrastructure without adding real authentication and network access controls.

Current guardrails:
- Accepted uploads: PDF/TXT/MD only, maximum 8 MB per file; PDFs <=100 pages; image-only PDFs rejected.
- Path traversal and hidden filenames are rejected; no client-supplied paths are used.
- Browser writes use a custom header and trusted localhost hosts to deter casual cross-origin requests.
- Local file changes build a replacement index in a staging directory and roll back on most application failures; this is not full power-loss durability.
- Index and API reads/writes are serialized in a single process to avoid Qdrant local path locking issues. **This is not a login system or secure authentication.**
- UI renders document text through `textContent`, not raw HTML, reducing reflected HTML injection risk.
- RAG prompts mark retrieved text untrusted; this alone cannot fully prevent prompt injection or hallucinations.

Known gaps: this is not cryptographically authenticated or suitable for public deployment; file content isn't malware scanned; PDF parsing can have security defects; there is no job queue or rate limiting; uploads rebuild the index; generated citations aren't verified; no encryption at rest, multi-user isolation, or adversarial pentest. Avoid processing untrusted sensitive files.

For vulnerabilities, use private GitHub reporting (if enabled) rather than posting secrets in a public issue.
