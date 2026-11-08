"""Exercise the local library API without downloading a machine-learning model."""
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

import api
from api import app, get_data_dir
from semantic import read_chunks


@pytest.fixture()
def client(tmp_path, monkeypatch):
    app.dependency_overrides[get_data_dir] = lambda: str(tmp_path)

    def fake_build_index(docs, data_dir):
        doc_list = list(Path(docs).glob('*'))
        index = Path(data_dir)
        index.mkdir(parents=True, exist_ok=True)
        (index / 'index.json').write_text('{"model":"fake","chunk_count":2}', encoding='utf-8')
        return {"chunk_count": len(doc_list)}

    monkeypatch.setattr(api, 'build_index', fake_build_index)
    with TestClient(app) as c:
        yield c, tmp_path
    app.dependency_overrides.clear()


def test_workspace_starts_empty(client):
    c, _ = client
    r = c.get('/api/health?workspace=personal')
    assert r.status_code == 200
    assert r.json()['indexed'] is False
    assert c.get('/api/documents?workspace=personal').json()['documents'] == []


def test_upload_list_delete(client):
    c, _ = client
    headers = {'X-DeskMind-Client': 'local-ui'}
    res = c.put('/api/documents/test.txt', headers=headers, content='Anlamlı deneme metni'.encode())
    assert res.status_code == 200, res.text
    assert res.json()['indexed_chunks'] == 1
    docs = c.get('/api/documents?workspace=personal').json()['documents']
    assert [d['name'] for d in docs] == ['test.txt']
    assert c.get('/api/health?workspace=personal').json()['indexed'] is True
    assert c.put('/api/documents/test.txt', headers=headers, content=b'duplicate').status_code == 409
    assert c.delete('/api/documents/test.txt', headers=headers).status_code == 200
    assert c.get('/api/health?workspace=personal').json()['indexed'] is False


def test_upload_fails_closed_without_header(client):
    c, _ = client
    assert c.put('/api/documents/note.md', content=b'hello').status_code == 403
    assert c.delete('/api/documents/note.md').status_code == 403


def test_reject_bad_extension_and_bad_names(client):
    c, _ = client
    h = {'X-DeskMind-Client': 'local-ui'}
    for name in ('.hidden.txt', 'code.py', 'my\\secret.md'):
        assert c.put('/api/documents/'+name, headers=h, content=b'hi').status_code == 400


def test_reject_invalid_pdf_and_non_utf8(client):
    c, _ = client
    h = {'X-DeskMind-Client': 'local-ui'}
    assert c.put('/api/documents/test.pdf', headers=h, content=b'not pdf').status_code == 422
    assert c.put('/api/documents/test.md', headers=h, content=b'\xff\xfe').status_code == 422


def test_upload_limit(client):
    c, _ = client
    h = {'X-DeskMind-Client': 'local-ui'}
    assert c.put('/api/documents/too_big.txt', headers=h, content=b'X' * 8_000_001).status_code == 413


def test_scanned_pdf_rejected(client):
    from io import BytesIO
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    out = BytesIO()
    writer.write(out)
    c, _ = client
    res = c.put('/api/documents/scanned.pdf', headers={'X-DeskMind-Client': 'local-ui'}, content=out.getvalue())
    assert res.status_code == 422
    assert 'OCR' in res.json()['detail']


def test_pdf_page_tracking(tmp_path):
    # A text-extraction smoke test with a minimal handcrafted content stream.
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject, DictionaryObject
    w = PdfWriter()
    page = w.add_blank_page(width=300, height=300)
    font = DictionaryObject({NameObject('/Type'):NameObject('/Font'),
            NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    font_ref = w._add_object(font)
    fonts = DictionaryObject({NameObject('/F1'):font_ref})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):fonts})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 36 200 Td (Incident response playbook) Tj ET')
    page[NameObject('/Contents')] = w._add_object(stream)
    with (tmp_path/'manual.pdf').open('wb') as f: w.write(f)
    hits = read_chunks(tmp_path)
    assert hits[0]['source'] == 'manual.pdf'
    assert hits[0]['page'] == 1
    assert 'Incident' in hits[0]['text']


def test_failed_upload_keeps_old_library_and_index(client, monkeypatch):
    c, base = client
    headers = {'X-DeskMind-Client': 'local-ui'}
    assert c.put('/api/documents/original.txt', headers=headers, content=b'Original text').status_code == 200
    index = base/'workspaces'/'personal'/'index.json'
    old = index.read_bytes()

    def broken_reindex(*args, **kwargs):
        raise RuntimeError('Simulated model crash')

    monkeypatch.setattr(api, 'build_index', broken_reindex)
    result = c.put('/api/documents/new.txt', headers=headers, content=b'New text')
    assert result.status_code == 500
    assert index.read_bytes() == old
    docs = c.get('/api/documents?workspace=personal').json()['documents']
    assert [d['name'] for d in docs] == ['original.txt']
    assert not list((base/'workspaces'/'personal').glob('.deskmind-stage-*'))


def test_failed_delete_restores_document_and_index(client, monkeypatch):
    c, base = client
    headers = {'X-DeskMind-Client': 'local-ui'}
    for name in ('original.txt','second.txt'):
        assert c.put('/api/documents/' + name, headers=headers, content=b'Original text').status_code == 200
    index = base/'workspaces'/'personal'/'index.json'
    old = index.read_bytes()

    def broken_reindex(*args, **kwargs):
        raise RuntimeError('Simulated disk error')

    monkeypatch.setattr(api, 'build_index', broken_reindex)
    result = c.delete('/api/documents/original.txt', headers=headers)
    assert result.status_code == 500
    assert index.read_bytes() == old
    docs = c.get('/api/documents?workspace=personal').json()['documents']
    assert [d['name'] for d in docs] == ['original.txt','second.txt']


def test_index_swap_rebuild_then_commit(client):
    c, base = client
    headers = {'X-DeskMind-Client': 'local-ui'}
    assert c.put('/api/documents/first.txt', headers=headers, content=b'first').status_code == 200
    assert c.put('/api/documents/second.txt', headers=headers, content=b'second').status_code == 200
    assert c.delete('/api/documents/first.txt', headers=headers).status_code == 200
    info = c.get('/api/health?workspace=personal').json()
    assert info['indexed'] is True
    assert info['documents'] == 1
    assert not list((base/'workspaces'/'personal').glob('.deskmind-backup-*'))


def test_reject_symlink_library_entry(client):
    c, base = client
    docs = base/'workspaces'/'personal'/'documents'
    docs.mkdir(parents=True)
    (docs/'private.txt').symlink_to(base/'outside.txt')
    assert c.get('/api/documents?workspace=personal').json()['documents'] == []
    h = {'X-DeskMind-Client': 'local-ui'}
    assert c.put('/api/documents/private.txt', headers=h, content=b'test').status_code == 409
    assert c.delete('/api/documents/private.txt', headers=h).status_code == 404
