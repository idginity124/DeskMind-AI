"""Render human-readable retrieval evaluation reports from benchmark.py JSON.

Works offline and uses only the Python standard library.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

_METRICS = (
    ("recall_at_k", "Recall@K"),
    ("hit_rate_at_k", "Hit rate@K"),
    ("mrr_at_k", "MRR@K"),
    ("mean_latency_ms", "Mean latency (ms)"),
)


def read_report(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"{path}: expected a JSON object")
    for k in ("questions", "top_k"):
        if type(obj.get(k)) is not int or obj[k] < 1:
            raise ValueError(f"{path}: {k} must be a positive integer")
    for key, _ in _METRICS:
        value = obj.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{path}: {key} must be a finite number")
        if key != "mean_latency_ms" and not 0 <= value <= 1:
            raise ValueError(f"{path}: {key} must be between 0 and 1")
        if key == "mean_latency_ms" and value < 0:
            raise ValueError(f"{path}: latency cannot be negative")
    details = obj.get("details", [])
    if not isinstance(details, list):
        raise ValueError(f"{path}: details must be an array")
    for row in details:
        if not isinstance(row, dict) or not isinstance(row.get("question"), str) or not isinstance(row.get("retrieved"), list):
            raise ValueError(f"{path}: malformed detail row")
        if not all(isinstance(x, str) for x in row["retrieved"]):
            raise ValueError(f"{path}: retrieved filenames must be strings")
        rank = row.get("first_relevant_rank")
        if rank is not None and (type(rank) is not int or not 1 <= rank <= obj["top_k"]):
            raise ValueError(f"{path}: invalid first_relevant_rank")
    return obj


def _cell(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ").replace("`", "\\`")


def _fmt(value: float, key: str) -> str:
    return f"{value:.1f} ms" if key == "mean_latency_ms" else f"{value:.3f}"


def render_report(current: dict[str, Any], baseline: dict[str, Any] | None = None) -> str:
    lines = ["# Retrieval evaluation report", "", "> These metrics cover retrieval only, not the correctness of generated answers.", "", f"**Questions:** {current['questions']} · **Top-K:** {current['top_k']}", ""]
    if baseline:
        lines += [f"**Baseline:** {baseline['questions']} questions · Top-{baseline['top_k']}", ""]
        if baseline["questions"] != current["questions"] or baseline["top_k"] != current["top_k"]:
            lines += ["> **Warning:** baseline and current run use different question counts or Top-K. Compare with care.", ""]
    lines += ["## Summary", "", "| Metric | Current | Baseline | Change |", "| --- | ---: | ---: | ---: |"]
    for key, title in _METRICS:
        curr = current[key]
        prior = baseline[key] if baseline else None
        change = "—" if prior is None else f"{curr - prior:+.3f}" if key != "mean_latency_ms" else f"{curr - prior:+.1f} ms"
        lines.append(f"| {title} | {_fmt(curr, key)} | {_fmt(prior, key) if prior is not None else '—'} | {change} |")
    lines += ["", "## Per-question retrieval", "", "| Question | First relevant rank | Retrieved sources | Time |", "| --- | ---: | --- | ---: |"]
    details = current.get("details", [])
    if not details:
        lines.append("| No per-question details in input | — | — | — |")
    for item in details:
        rank = item.get("first_relevant_rank")
        elapsed = item.get("elapsed_ms", "—")
        if isinstance(elapsed, (int, float)) and not isinstance(elapsed, bool):
            elapsed = f"{elapsed:.1f} ms"
        lines.append(f"| {_cell(item['question'])} | {rank if rank is not None else '**not found**'} | {_cell(', '.join(item['retrieved']) or '—')} | {_cell(elapsed)} |")
    lines += ["", "## How to read this report", "", "- **Recall@K:** fraction of labeled relevant sources retrieved in the top K.", "- **Hit rate@K:** fraction of questions for which at least one relevant source is retrieved.", "- **MRR@K:** rewards the first relevant source appearing earlier in the ranking.", "- **Latency:** average measured retrieval time for these questions and this machine.", "", "A high score on a small hand-written test set does not guarantee useful performance on new documents. Use the same dataset, indexing settings, model and machine to make a meaningful before/after comparison.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert benchmark.py JSON output to an inspectable Markdown report")
    parser.add_argument("results", type=Path, help="Current benchmark JSON file")
    parser.add_argument("--baseline", type=Path, help="Optional previous run for comparison")
    parser.add_argument("--output", type=Path, help="Write Markdown to this location (default: print)")
    args = parser.parse_args(argv)
    current = read_report(args.results)
    baseline = read_report(args.baseline) if args.baseline else None
    output = render_report(current, baseline)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Wrote report to {args.output}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
