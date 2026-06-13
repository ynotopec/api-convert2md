# API Convert2MD

Minimal token-protected FastAPI service that converts uploaded documents to Markdown and keeps OpenWebUI External Document Loader compatibility.

## Features

- Idempotent install/start scripts: safe to run repeatedly.
- `uv` dependency management.
- Virtual environment at `~/venv/api-convert2md` by default.
- Token API with `Authorization: Bearer <API_TOKEN>`.
- Popular multipart API: `POST /v1/convert` (alias: `POST /convert`).
- OpenWebUI-compatible API: `PUT /process`.
- CPU-first deployment compatible with NVIDIA H100/DGX Spark hosts; GPU presence is not required.

## Start

```bash
cp .env.example .env
# edit .env and set API_TOKEN
./install.sh
source ./run.sh 0.0.0.0 8088
```

Health check:

```bash
curl http://127.0.0.1:8088/health
```

Convert a file:

```bash
curl -X POST http://127.0.0.1:8088/v1/convert \
  -H "Authorization: Bearer $API_TOKEN" \
  -F "file=@document.pdf"
```

OpenWebUI:

```bash
CONTENT_EXTRACTION_ENGINE=external
EXTERNAL_DOCUMENT_LOADER_URL=http://127.0.0.1:8088
EXTERNAL_DOCUMENT_LOADER_API_KEY=$API_TOKEN
```

## systemd example

Use `run.sh` directly from systemd; it uses `exec` when not sourced.

```ini
[Service]
WorkingDirectory=/workspace/api-convert2md
EnvironmentFile=/workspace/api-convert2md/.env
ExecStart=/workspace/api-convert2md/run.sh 0.0.0.0 8088
Restart=always
```

## System packages

For best PDF table extraction, install Ghostscript on the host:

```bash
sudo apt-get install -y ghostscript
```
