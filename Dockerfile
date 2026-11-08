# CPU-only container, local single-user use. Docker's first build is large due to PyTorch.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/app/.cache/huggingface
WORKDIR /app
COPY requirements-rag.txt ./
RUN python -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && python -m pip install --no-cache-dir -r requirements-rag.txt
COPY . .
RUN useradd --uid 10001 --create-home deskmind \
 && mkdir -p /app/.deskmind /app/.cache/huggingface \
 && chown -R deskmind:deskmind /app/.deskmind /app/.cache
USER deskmind
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
