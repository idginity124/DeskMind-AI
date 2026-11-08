import pytest
from benchmark import evaluate


def test_retrieval_benchmark_metrics():
    cases = [
        {'question':'first','relevant_sources':['a.md']},
        {'question':'second','relevant_sources':['z.md']},
        {'question':'third','relevant_sources':['z.md']},
    ]
    def fake_search(q, k):
        return {
            'first': [{'source':'b.md'}, {'source':'a.md'}],
            'second': [{'source':'z.md'}, {'source':'a.md'}],
            'third': [{'source':'a.md'}, {'source':'b.md'}],
        }[q][:k]
    report = evaluate(cases, search=fake_search, top_k=2)
    assert report['hit_rate_at_k'] == pytest.approx(0.6667, abs=0.0001)
    assert report['mrr_at_k'] == 0.5
    assert report['questions'] == 3
    assert report['details'][0]['first_relevant_rank'] == 2


def test_empty_benchmark_rejected():
    with pytest.raises(ValueError):
        evaluate([], search=lambda *args: [])
