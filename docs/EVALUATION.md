# Understanding DeskMind retrieval results

The app has a small, labeled set of questions in `eval/demo_questions.json`. These are **smoke tests**, not a broad language benchmark. The evaluation checks whether the correct *source file* is retrieved. It does not test answer factuality, hallucination rates, OCR quality, security or generalization.

## Run a local evaluation

First install the project and build the demo index:

```bash
.venv/bin/python semantic.py index --docs examples/docs
.venv/bin/python benchmark.py --dataset eval/demo_questions.json --data-dir .deskmind --top-k 3 > /tmp/deskmind-results.json
.venv/bin/python eval_report.py /tmp/deskmind-results.json --output /tmp/deskmind-evaluation.md
```

Open `/tmp/deskmind-evaluation.md` in any Markdown viewer. No cloud service or paid key is required for report generation.

## Compare after making a change

Save a baseline first:

```bash
cp /tmp/deskmind-results.json /tmp/deskmind-baseline.json
```

After changing chunking, embeddings or search parameters, rebuild the index, run the benchmark again, and compare:

```bash
.venv/bin/python benchmark.py --dataset eval/demo_questions.json --data-dir .deskmind --top-k 3 > /tmp/deskmind-results-new.json
.venv/bin/python eval_report.py /tmp/deskmind-results-new.json --baseline /tmp/deskmind-baseline.json --output /tmp/deskmind-comparison.md
```

The Markdown report shows Recall@K, hit rate, MRR, latency, and questions where no relevant source was found. A before/after score is only meaningful when the dataset, labels, environment, and Top-K are comparable. Even a positive difference on a four-question dataset could be noise. Don't present these demo results as a product accuracy percentage.

For an honest external evaluation, create a diverse set of queries and human-verified source labels, keep a held-out test split, run the same environment, and separately evaluate generated answer quality and citation faithfulness.
