# DeskMind AI quickstart

DeskMind is a private local document Q&A prototype. Upload your own PDF, TXT or Markdown notes in the Personal workspace. The Demo workspace is read-only and includes example texts. Ask questions and verify the cited passages.

The app uses multilingual embeddings and Qdrant for semantic retrieval. An Ollama model is optional for generated answers; without Ollama it returns the nearest source excerpt. Text-only PDFs work, but image-only scanned PDFs need OCR.
