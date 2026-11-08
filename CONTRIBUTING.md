# Contributing

Thanks for your interest in DeskMind!

## Before a pull request

1. Reproduce the bug or outline the proposed feature in an issue.
2. Install lightweight test dependencies: `python -m pip install -r requirements-dev.txt`.
3. Run `python -m pytest -q` and add focused tests for behavior changes.
4. Keep local documents, models, Qdrant data and API secrets out of commits.
5. Clearly distinguish tested functionality from planned features in descriptions and screenshots.

Priority areas: human-verifiable citations, evaluation datasets, incremental indexing, accessibility, robustness of local upload flows, translations and reproducible setup.

Please keep changes small and document security/privacy implications for any features exposing files or network services.
