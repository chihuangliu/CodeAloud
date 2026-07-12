FROM python:3.12-slim
RUN pip install uv
WORKDIR /app
# the package must be present for uv to build/install it (editable) during sync
COPY pyproject.toml uv.lock ./
COPY code_aloud ./code_aloud
# backend image only needs the shared core + the `backend` group (fastapi/uvicorn/redis)
RUN uv sync --frozen --no-default-groups --group backend
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "code_aloud.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
