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

## PDF processing speed

The default PDF table strategy is `fast`: the service tries extractors in order and stops as soon as one returns usable tables. This avoids waiting for slower fallback extractors on documents that Camelot can already parse.

For maximum recall, set `PDF_TABLE_STRATEGY=quality` to run every enabled extractor and de-duplicate the results. You can also reduce work further by selecting a subset/order of extractors, for example:

```bash
PDF_TABLE_STRATEGY=fast
PDF_TABLE_EXTRACTORS=camelot_lattice,pdfplumber
PDF_PAGES=1-10
```

## System packages

For best PDF table extraction, install Ghostscript on the host:

```bash
sudo apt-get install -y ghostscript
```
