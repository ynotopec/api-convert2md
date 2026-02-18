# OpenWebUI Generic External Ingestion Engine

Generic, production-ready **External Content Extraction Engine** for OpenWebUI.

This service replaces the default internal PDF parsing with a **robust, structure-aware ingestion pipeline** designed for complex tables (tariffs, matrices, multi-level headers, telecom grids, etc.).

It prevents common RAG hallucinations caused by:

- Lost table headers
- Flattened DataFrames
- Mixed tables in the same chunk
- Numeric columns without semantic labels

---

# ✨ Features

- ✅ Camelot (lattice → stream) + pdfplumber fallback
- ✅ Automatic multi-row header reconstruction (generic)
- ✅ Table de-duplication via stable `hash_df`
- ✅ Row-level document emission (best RAG precision)
- ✅ Markdown snapshot fallback per table
- ✅ Automatic chunking with overlap
- ✅ PDF text fallback (pypdf)
- ✅ No document-specific hardcoding
- ✅ No per-PDF code modification required

---

# 🧠 Why This Exists

OpenWebUI’s default PDF ingestion:

```

PDF → text extraction → chunking → embedding

```

For complex tables, this causes:

- headers separated from data
- values without column meaning
- LLM “guessing” semantics (e.g., inventing Fixe/Mobile labels)

This engine instead performs:

```

PDF → structured table extraction → header reconstruction →
row-level documents → precise metadata → embedding

````

Result: reliable answers for queries like:

> "Quels sont les tarifs concernant l’Argentine ?"

---

# 📦 Installation

## 1️⃣ Clone repository

```bash
git clone https://github.com/your-org/openwebui-external-ingestion.git
cd openwebui-external-ingestion
````

## 2️⃣ Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### System dependency (for Camelot lattice)

On Linux:

```bash
sudo apt install ghostscript
```

---

# 🔧 requirements.txt

```txt
fastapi
uvicorn[standard]
pandas
tabulate
pypdf
camelot-py[cv]
pdfplumber
opencv-python
```

---

# 🚀 Run the Engine

```bash
export ENGINE_API_KEY="supersecret"
export PDF_PAGES="all"

uvicorn app:app --host 0.0.0.0 --port 8088
```

Test:

```bash
curl -X PUT "http://localhost:8088/process" \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/pdf" \
  -H "X-Filename: tarifs.pdf" \
  --data-binary "@tarifs.pdf"
```

---

# 🔌 OpenWebUI Configuration

This engine works with OpenWebUI’s **External Content Extraction Engine**.

## Option A — Docker (Recommended)

If OpenWebUI runs in Docker:

### docker-compose example

```yaml
services:
  openwebui:
    image: ghcr.io/open-webui/open-webui:latest
    environment:
      - CONTENT_EXTRACTION_ENGINE=external
      - EXTERNAL_DOCUMENT_LOADER_URL=http://ingestion-engine:8088
      - EXTERNAL_DOCUMENT_LOADER_API_KEY=supersecret
    depends_on:
      - ingestion-engine

  ingestion-engine:
    build: .
    environment:
      - ENGINE_API_KEY=supersecret
      - PDF_PAGES=all
      - MAX_DOC_CHARS=6000
      - OVERLAP_CHARS=800
    ports:
      - "8088:8088"
```

---

## Option B — OpenWebUI Local + Engine Local

If both run locally (no Docker):

Set OpenWebUI environment variables:

```bash
export CONTENT_EXTRACTION_ENGINE=external
export EXTERNAL_DOCUMENT_LOADER_URL=http://localhost:8088
export EXTERNAL_DOCUMENT_LOADER_API_KEY=supersecret
```

Restart OpenWebUI.

---

# 📂 How It Works Internally

## 1️⃣ Extraction Order

1. Camelot (lattice)
2. Camelot (stream)
3. pdfplumber

## 2️⃣ Header Reconstruction

Automatically detects multi-line headers and rebuilds column names:

Example reconstructed column:

```
SMS envoyé | Forfait 2€
```

No schema hardcoding.

## 3️⃣ Row-Level Emission

If first column looks like an entity (e.g. country/destination):

Each row becomes a separate document:

```
Pays: Argentine
SMS envoyé | Forfait 2€: 0,27 €
SMS envoyé | Forfait Free 5G: 0,27 €
...
```

This dramatically improves retrieval precision.

## 4️⃣ Table Snapshot

A Markdown snapshot is also stored for full-context retrieval.

---

# ⚙️ Environment Variables

| Variable                   | Default    | Description                    |
| -------------------------- | ---------- | ------------------------------ |
| ENGINE_API_KEY             | (required) | Must match OpenWebUI key       |
| PDF_PAGES                  | all        | Pages to parse                 |
| MAX_DOC_CHARS              | 6000       | Max document size              |
| OVERLAP_CHARS              | 800        | Chunk overlap                  |
| MAX_TEXT_PAGES             | 200        | Fallback text extraction limit |
| MAX_HEADER_ROWS            | 4          | Header detection depth         |
| CAMELOT_LATTICE_LINE_SCALE | 40         | Lattice tuning                 |
| CAMELOT_STREAM_EDGE_TOL    | 200        | Stream tuning                  |
| CAMELOT_STREAM_ROW_TOL     | 10         | Stream tuning                  |

---

# 🔍 Troubleshooting

## ❌ “No tables found in table area”

Normal Camelot warning. Automatically handled.

## ❌ Wrong answers after engine update

Delete old Knowledge Base and re-upload PDFs.

Old chunks remain indexed otherwise.

## ❌ Scanned PDF

If text extraction is empty, PDF likely requires OCR.

---

# 🧪 Recommended RAG Settings (OpenWebUI)

* Chunk size: 1000–1500 tokens
* Overlap: 200–300
* Recursive chunking: enabled
* Avoid aggressive separators

---

# 🏗 Design Philosophy

* No per-document hacks
* No schema hardcoding
* Automatic structure detection
* RAG-first document design
* Production-safe behavior

---

# 📈 Result

Before:

```
Argentine | 0,27 | 0,27 | 1,05 | ...
```

LLM invents meaning.

After:

```
Pays: Argentine
SMS envoyé | Forfait 2€: 0,27 €
...
```

LLM answers correctly without hallucination.

---

# 📜 License

MIT

---

# 🤝 Contributions

Pull requests welcome.

Focus areas:

* OCR integration
* XLSX ingestion
* Advanced header detection
* SQL output mode
* Performance optimization for 100k+ row tables

---

```
---

# 🗺️ Project State Artifacts

A current project state file is available in `STATE.md`, including:

- Router / decision flow for the `/process` ingestion path
- A single critical end-to-end sequence test case


