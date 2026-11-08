"""DeskMind local API. Single-user only: bind to 127.0.0.1, never public network."""
from __future__ import annotations

import os
import shutil
import tempfile
import threading
import uuid
from io import BytesIO
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.concurrency import run_in_threadpool

from semantic import ask, build_index, load_model_info

app = FastAPI(title="DeskMind AI", version="1.0.0", docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]", "testserver"])


@app.middleware("http")
async def local_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
DATA_DIR = os.environ.get("DESKMIND_DATA_DIR", ".deskmind")
MAX_BYTES = 8_000_000
# Qdrant local mode uses a per-path lock. Serialize reads and writes for a single user.
LIBRARY_LOCK = threading.RLock()
ALLOWED = {".pdf", ".md", ".txt"}
Workspace = Literal["demo", "personal"]


class AskBody(BaseModel):
    question: str = Field(min_length=2, max_length=1500)
    top_k: int = Field(default=4, ge=1, le=10)
    ollama_model: str | None = Field(default=None, max_length=200)
    workspace: Workspace = "demo"


def get_data_dir() -> str:
    """Dependency override allows isolated tests and configurable data locations."""
    return DATA_DIR


def workspace_dirs(data_dir: str, workspace: Workspace) -> tuple[Path, Path]:
    base = Path(data_dir).resolve()
    if workspace == "demo":
        return base, Path(__file__).resolve().parent / "examples" / "docs"
    index = base / "workspaces" / "personal"
    return index, index / "documents"


def documents_in(folder: Path) -> list[dict]:
    if not folder.is_dir():
        return []
    return [{"name": p.name, "bytes": p.stat().st_size, "type": p.suffix[1:].upper()}
            for p in sorted(folder.iterdir()) if p.is_file() and not p.is_symlink()
            and p.suffix.lower() in ALLOWED]


def valid_name(filename: str) -> str:
    if (not filename or filename in {".", ".."} or filename.startswith(".")
            or "/" in filename or "\\" in filename or "\x00" in filename
            or len(filename) > 150 or Path(filename).suffix.lower() not in ALLOWED):
        raise HTTPException(status_code=400, detail="Sadece .pdf/.txt/.md uzantılı, güvenli dosya adları kabul edilir")
    return filename


def validate_document(name: str, data: bytes) -> None:
    if not data or len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Dosya boş veya 8 MB sınırını aşıyor")
    if name.lower().endswith(".pdf"):
        if not data.startswith(b"%PDF-"):
            raise HTTPException(status_code=422, detail="Geçerli PDF dosyası değil")
        from pypdf import PdfReader
        try:
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                raise HTTPException(status_code=422, detail="Şifreli PDF desteklenmiyor")
            if len(reader.pages) > 100:
                raise HTTPException(status_code=413, detail="PDF 100 sayfayı aşamaz")
            if not any((page.extract_text() or "").strip() for page in reader.pages):
                raise HTTPException(status_code=422, detail="PDF metin içermiyor; taranan dosyalar için OCR gerekli")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=422, detail="PDF okunamadı veya şifreli") from exc
    else:
        try:
            if not data.decode("utf-8-sig").strip():
                raise HTTPException(status_code=422, detail="Boş metin belgesi")
        except UnicodeError as exc:
            raise HTTPException(status_code=422, detail="Metin dosyaları UTF-8 olmalı") from exc


def swap_index(docs: Path, index: Path) -> dict:
    """Rebuild into a separate Qdrant directory, then swap with rollback.

    A failed model download, PDF parse or disk write must NOT destroy the
    previous searchable index. This routine runs under LIBRARY_LOCK.
    """
    index.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".deskmind-stage-", dir=index))
    backup = Path(tempfile.mkdtemp(prefix=".deskmind-backup-", dir=index))
    names = ("qdrant", "index.json")
    installed = []
    previous = []
    try:
        result = build_index(str(docs), str(stage))
        if not (stage / "index.json").is_file():
            raise RuntimeError("New index metadata was not produced")
        try:
            for name in names:
                old_path = index / name
                if old_path.exists():
                    old_path.rename(backup / name)
                    previous.append(name)
            for name in names:
                new_path = stage / name
                if new_path.exists():
                    new_path.rename(index / name)
                    installed.append(name)
        except Exception:
            for name in installed:
                new_path = index / name
                if new_path.is_dir():
                    shutil.rmtree(new_path)
                else:
                    new_path.unlink(missing_ok=True)
            for name in previous:
                (backup / name).rename(index / name)
            raise
        return result
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)


def clear_index(index: Path) -> None:
    """Remove current index after final document was moved aside."""
    index.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix=".deskmind-clear-", dir=index))
    moved = []
    try:
        for name in ("qdrant", "index.json"):
            if (index / name).exists():
                (index / name).rename(backup / name)
                moved.append(name)
    except Exception:
        for name in moved:
            (backup / name).rename(index / name)
        raise
    finally:
        shutil.rmtree(backup, ignore_errors=True)


def add_document(data_dir: str, filename: str, data: bytes) -> dict:
    """Transactional upload. Called on threadpool, never blocks event loop."""
    with LIBRARY_LOCK:
        index, docs = workspace_dirs(data_dir, "personal")
        docs.mkdir(parents=True, exist_ok=True)
        dest = docs / filename
        if dest.exists() or dest.is_symlink():
            raise HTTPException(status_code=409, detail="Aynı isimde belge mevcut; önce sil veya yeniden adlandır")
        tmp_path = docs / f".incoming-{uuid.uuid4().hex}"
        try:
            tmp_path.write_bytes(data)
            tmp_path.rename(dest)
            try:
                result = swap_index(docs, index)
            except Exception:
                dest.unlink(missing_ok=True)
                raise
            return {"ok": True, "filename": filename, "indexed_chunks": result["chunk_count"]}
        finally:
            tmp_path.unlink(missing_ok=True)


def remove_document(data_dir: str, filename: str) -> dict:
    """Transactional delete; restore the file on reindex failure."""
    with LIBRARY_LOCK:
        index, docs = workspace_dirs(data_dir, "personal")
        dest = docs / filename
        if not dest.is_file() or dest.is_symlink():
            raise HTTPException(status_code=404, detail="Belge bulunamadı")
        index.mkdir(parents=True, exist_ok=True)
        tombstone = index / f".removed-{uuid.uuid4().hex}"
        dest.rename(tombstone)
        try:
            remaining = documents_in(docs)
            if remaining:
                swap_index(docs, index)
            else:
                clear_index(index)
        except Exception:
            tombstone.rename(dest)
            raise
        # Remove the temporarily retained original only after successful commit.
        tombstone.unlink()
        return {"ok": True, "remaining": len(remaining)}


@app.get("/", response_class=HTMLResponse)
def home():
    return (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health(data_dir: Annotated[str, Depends(get_data_dir)], workspace: Workspace = "demo"):
    index, docs = workspace_dirs(data_dir, workspace)
    with LIBRARY_LOCK:
        try:
            info = load_model_info(index)
            return {"indexed": True, "info": info, "workspace": workspace, "documents": len(documents_in(docs))}
        except FileNotFoundError:
            return {"indexed": False, "info": None, "workspace": workspace, "documents": len(documents_in(docs))}


@app.get("/api/documents")
def get_documents(data_dir: Annotated[str, Depends(get_data_dir)], workspace: Workspace = "personal"):
    _, docs = workspace_dirs(data_dir, workspace)
    return {"workspace": workspace, "documents": documents_in(docs)}


@app.put("/api/documents/{filename}")
async def put_document(filename: str, request: Request, data_dir: Annotated[str, Depends(get_data_dir)]):
    """Raw upload avoids multipart parser. Browser uses PUT with a custom header.

    Cross-origin requests cannot pass the preflight, and TrustedHost blocks DNS rebinding.
    This remains a localhost-only prototype without multi-user authorization.
    """
    valid_name(filename)
    if request.headers.get("X-DeskMind-Client") != "local-ui":
        raise HTTPException(status_code=403, detail="Yerel arayüz gerekli")
    size_header = request.headers.get("content-length")
    if size_header is not None and (not size_header.isascii() or not size_header.isdecimal()):
        raise HTTPException(status_code=400, detail="Geçersiz dosya uzunluğu")
    if size_header is not None and int(size_header) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Dosya 8 MB sınırını aşıyor")
    parts = bytearray()
    async for block in request.stream():
        parts.extend(block)
        if len(parts) > MAX_BYTES:
            raise HTTPException(status_code=413, detail="Dosya 8 MB sınırını aşıyor")
    validate_document(filename, bytes(parts))
    try:
        return await run_in_threadpool(add_document, data_dir, filename, bytes(parts))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"İndeksleme başarısız: {type(exc).__name__}") from exc


@app.delete("/api/documents/{filename}")
def delete_document(filename: str, data_dir: Annotated[str, Depends(get_data_dir)], request: Request):
    valid_name(filename)
    if request.headers.get("X-DeskMind-Client") != "local-ui":
        raise HTTPException(status_code=403, detail="Yerel arayüz gerekli")
    try:
        return remove_document(data_dir, filename)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Silme veya indeksleme başarısız: {type(exc).__name__}") from exc


@app.post("/api/demo/index")
async def create_demo_index(request: Request, data_dir: Annotated[str, Depends(get_data_dir)]):
    """Prepare the bundled example library on first launch, on request."""
    if request.headers.get("X-DeskMind-Client") != "local-ui":
        raise HTTPException(status_code=403, detail="Yerel arayüz gerekli")

    def run():
        with LIBRARY_LOCK:
            index, docs = workspace_dirs(data_dir, "demo")
            return swap_index(docs, index)

    try:
        result = await run_in_threadpool(run)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Demo indekslenemedi: {type(exc).__name__}") from exc
    return {"ok": True, **result}


@app.post("/api/ask")
def ask_api(body: AskBody, data_dir: Annotated[str, Depends(get_data_dir)]):
    index, _ = workspace_dirs(data_dir, body.workspace)
    try:
        with LIBRARY_LOCK:
            return ask(body.question, data_dir=str(index), top_k=body.top_k,
                       ollama_model=body.ollama_model or None)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (ConnectionError, OSError) as exc:
        raise HTTPException(status_code=502, detail="Ollama servisine ulaşılamıyor. Modeli ve servisi kontrol et.") from exc
