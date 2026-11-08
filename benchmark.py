"""Tiny *curated* retrieval smoke benchmark, not a production quality claim.

Usage: python benchmark.py --dataset eval/demo_questions.json --data-dir .deskmind
This script uses the REAL embedding model and Qdrant index when executed.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from semantic import retrieve


def evaluate(cases: list[dict], *, search, top_k: int = 3) -> dict:
    if not cases:
        raise ValueError("No benchmark questions provided")
    details = []
    total_rr = 0.0
    hit_count = 0
    recall_total = 0.0
    durations = []
    for case in cases:
        started = time.perf_counter()
        hits = search(case['question'], top_k)
        duration = (time.perf_counter() - started) * 1000
        durations.append(duration)
        relevant = set(case['relevant_sources'])
        rank = next((i for i, h in enumerate(hits, start=1) if h['source'] in relevant), None)
        hit_count += bool(rank)
        recall_total += len(relevant & {h['source'] for h in hits}) / len(relevant)
        total_rr += (1 / rank) if rank else 0
        details.append({
            'question': case['question'],
            'retrieved': [h['source'] for h in hits],
            'first_relevant_rank': rank,
            'elapsed_ms': round(duration, 1),
        })
    n = len(cases)
    return {'questions': n, 'top_k': top_k, 'recall_at_k': round(recall_total / n, 4), 'hit_rate_at_k': round(hit_count / n, 4),
            'mrr_at_k': round(total_rr / n, 4),
            'mean_latency_ms': round(sum(durations) / n, 1), 'details': details}


def main():
    parser = argparse.ArgumentParser(description='Evaluate retrieval on labeled questions')
    parser.add_argument('--dataset', default='eval/demo_questions.json')
    parser.add_argument('--data-dir', default='.deskmind')
    parser.add_argument('--top-k', type=int, default=3)
    args = parser.parse_args()
    cases = json.loads(Path(args.dataset).read_text(encoding='utf-8'))
    report = evaluate(cases, search=lambda question, k: retrieve(question,
                                   data_dir=args.data_dir, top_k=k), top_k=args.top_k)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
