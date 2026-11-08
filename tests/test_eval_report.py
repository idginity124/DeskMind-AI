import json
import pytest
from eval_report import read_report, render_report, main


def sample(*, recall=0.5):
    return {"questions": 2, "top_k": 3, "recall_at_k": recall,
            "hit_rate_at_k": 0.5, "mrr_at_k": 0.5, "mean_latency_ms": 12.2,
            "details": [{"question": "Why | now?", "retrieved": ["a|b.md", "b.md"],
                         "first_relevant_rank": 2, "elapsed_ms": 11.3},
                        {"question": "Missing answer", "retrieved": ["c.md"],
                         "first_relevant_rank": None, "elapsed_ms": 13.1}]}


def test_report_escapes_markdown_and_shows_misses():
    md = render_report(sample())
    assert "Why \\| now?" in md
    assert "a\\|b.md" in md
    assert "**not found**" in md
    assert "Recall@K" in md


def test_comparison_delta_and_warning():
    before = sample(recall=0.25)
    after = sample(recall=0.5)
    md = render_report(after, before)
    assert "+0.250" in md
    before["questions"] = 99
    assert "**Warning:**" in render_report(after, before)


@pytest.mark.parametrize("value", [-1, 1.3, float('nan'), True])
def test_rejects_invalid_recall(tmp_path, value):
    d = sample(recall=value)
    p = tmp_path / "invalid.json"
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError):
        read_report(p)


def test_json_to_md_roundtrip(tmp_path):
    src = tmp_path / "evaluation.json"
    dst = tmp_path / "reports" / "evaluation.md"
    src.write_text(json.dumps(sample()), encoding="utf-8")
    assert main([str(src), "--output", str(dst)]) == 0
    assert dst.is_file()
    assert "Why \\| now?" in dst.read_text()


def test_rejects_non_object(tmp_path):
    src = tmp_path / "input.json"
    src.write_text("[]")
    with pytest.raises(ValueError):
        read_report(src)
