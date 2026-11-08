from fastapi.testclient import TestClient
from api import app, get_data_dir
import api


def test_health_when_index_missing(tmp_path):
    app.dependency_overrides[get_data_dir] = lambda: str(tmp_path)
    try:
        r = TestClient(app).get("/api/health")
        assert r.status_code == 200
        assert r.json()["indexed"] is False
    finally:
        app.dependency_overrides.clear()


def test_ask_endpoint_with_fake_answer(monkeypatch):
    monkeypatch.setattr(api, "ask", lambda question, **kwargs: {"answer": "test", "sources": []})
    r = TestClient(app).post("/api/ask", json={"question": "Nasılsın?"})
    assert r.status_code == 200
    assert r.json()["answer"] == "test"


def test_ask_api_rejects_blank():
    r = TestClient(app).post("/api/ask", json={"question": ""})
    assert r.status_code == 422


def test_frontpage_has_app_name():
    r = TestClient(app).get("/")
    assert r.status_code == 200
    assert "DeskMind AI" in r.text


def test_demo_index_endpoint(monkeypatch, tmp_path):
    app.dependency_overrides[get_data_dir] = lambda: str(tmp_path)
    try:
        monkeypatch.setattr(api, 'build_index', lambda docs, root: (
            ( __import__('pathlib').Path(root).mkdir(parents=True, exist_ok=True)),
            (__import__('pathlib').Path(root)/'index.json').write_text('{"model":"mock","dimension":2,"chunk_count":3}'),
            {'model':'mock','dimension':2,'chunk_count':3})[-1])
        c=TestClient(app)
        assert c.post('/api/demo/index').status_code == 403
        result = c.post('/api/demo/index', headers={'X-DeskMind-Client':'local-ui'})
        assert result.status_code == 200, result.text
        assert result.json()['chunk_count'] == 3
        assert c.get('/api/health?workspace=demo').json()['indexed'] is True
    finally:
        app.dependency_overrides.clear()
