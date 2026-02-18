#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenWebUI External Content Ingestion Engine (External Document Loader)

OpenWebUI calls:
  PUT {EXTERNAL_DOCUMENT_LOADER_URL}/process
Headers:
  Authorization: Bearer <EXTERNAL_DOCUMENT_LOADER_API_KEY>
  Content-Type: <mime>
  X-Filename: <filename>
Body:
  raw file bytes

Response JSON expected by OpenWebUI:
  - either {"page_content": "...", "metadata": {...}}
  - or a list of such objects (recommended)

This engine is GENERIC (no per-PDF code changes):
- Extract tables: Camelot lattice -> Camelot stream -> pdfplumber
- De-duplicate tables by hash_df (fast, stable)
- Rebuild multi-row headers generically (no hardcoded schema)
- Emits "records" per row (best for RAG precision) + fallback markdown
- Fallback to PDF text extraction (pypdf) if no tables or low-quality tables
- Suppresses noisy Camelot warnings

Deps:
  pip install fastapi uvicorn[standard] pandas tabulate pypdf camelot-py[cv] pdfplumber opencv-python
System (may be needed for camelot lattice):
  ghostscript

Run:
  export ENGINE_API_KEY="supersecret"
  uvicorn app:app --host 0.0.0.0 --port 8088

OpenWebUI env:
  CONTENT_EXTRACTION_ENGINE=external
  EXTERNAL_DOCUMENT_LOADER_URL=http://ingestion-engine:8088
  EXTERNAL_DOCUMENT_LOADER_API_KEY=supersecret
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse


# -----------------------------
# Quiet Camelot warnings
# -----------------------------
warnings.filterwarnings(
    "ignore",
    message=r"No tables found in table area.*",
    category=UserWarning,
    module=r"camelot\..*",
)

# -----------------------------
# Config (env)
# -----------------------------
ENGINE_API_KEY = os.getenv("ENGINE_API_KEY", "")
PDF_PAGES = os.getenv("PDF_PAGES", "all")  # "all" or "1-5" etc.

# Chunking / emission
MAX_DOC_CHARS = int(os.getenv("MAX_DOC_CHARS", "6000"))         # per document content
OVERLAP_CHARS = int(os.getenv("OVERLAP_CHARS", "800"))          # overlap if chunking a long doc
MAX_TEXT_PAGES = int(os.getenv("MAX_TEXT_PAGES", "200"))

# Multi-header reconstruction
MAX_HEADER_ROWS = int(os.getenv("MAX_HEADER_ROWS", "4"))

# Camelot tuning
CAMELOT_LATTICE_LINE_SCALE = int(os.getenv("CAMELOT_LATTICE_LINE_SCALE", "40"))
CAMELOT_STREAM_EDGE_TOL = int(os.getenv("CAMELOT_STREAM_EDGE_TOL", "200"))
CAMELOT_STREAM_ROW_TOL = int(os.getenv("CAMELOT_STREAM_ROW_TOL", "10"))

# Heuristics thresholds
MIN_ROWS_FOR_TABLE = int(os.getenv("MIN_ROWS_FOR_TABLE", "2"))
MIN_COLS_FOR_TABLE = int(os.getenv("MIN_COLS_FOR_TABLE", "2"))


# -----------------------------
# Auth
# -----------------------------
def require_bearer(auth_header: Optional[str]) -> None:
    if not ENGINE_API_KEY:
        raise HTTPException(500, "ENGINE_API_KEY is not set on the ingestion engine")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(401, "Missing Bearer token")
    token = auth_header.split(" ", 1)[1].strip()
    if token != ENGINE_API_KEY:
        raise HTTPException(403, "Invalid token")


# -----------------------------
# DataFrame cleaning / header rebuild (generic)
# -----------------------------
def _strip_cell(x) -> str:
    if x is None:
        return ""
    s = str(x).replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # ensure string-ish column names
    df.columns = [_strip_cell(c) if _strip_cell(c) else f"col_{i}" for i, c in enumerate(df.columns)]

    # normalize cells
    for c in df.columns:
        df[c] = df[c].map(_strip_cell)

    # drop empty rows
    mask_nonempty = df.apply(lambda row: any(v != "" for v in row.values), axis=1)
    df = df.loc[mask_nonempty].reset_index(drop=True)

    # dedupe column names
    cols, seen = [], {}
    for c in df.columns:
        k = c if c else "col"
        seen[k] = seen.get(k, 0) + 1
        cols.append(k if seen[k] == 1 else f"{k}_{seen[k]}")
    df.columns = cols

    return df

_NUMERICISH_RE = re.compile(r"^\s*[-+]?[\d\s.,]+(?:€|%|eur|mo|mn|min)?\s*$", re.IGNORECASE)

def _is_numericish(s: str) -> bool:
    s = (s or "").strip()
    if not s:
        return False
    if s.lower() in {"inclus", "illimité", "illimite", "n/a", "na", "—", "-", "x"}:
        return True
    return bool(_NUMERICISH_RE.match(s))

def rebuild_multi_header(df: pd.DataFrame, max_header_rows: int = 4) -> pd.DataFrame:
    """
    Generic multi-row header reconstruction:
    - Detect up to N header rows at top (mostly non-numeric cells)
    - Forward-fill header cells horizontally (handles merged-like blanks)
    - Build new column names by joining header levels with " | "
    - Remove header rows from body

    If detection fails, returns df unchanged.
    """
    if df.empty or len(df) < 2:
        return df

    # detect header rows
    header_rows: List[int] = []
    for i in range(min(max_header_rows, len(df))):
        row = df.iloc[i].fillna("").astype(str).map(_strip_cell)
        if len(row) == 0:
            break

        nonempty = sum(1 for v in row.values if v)
        if nonempty == 0:
            # allow completely empty header row (rare), but stop
            break

        numericish = sum(1 for v in row.values if _is_numericish(v))
        # header row: more text than numeric-ish
        if numericish <= len(row) * 0.5:
            header_rows.append(i)
        else:
            break

    if not header_rows:
        return df

    header_df = df.iloc[header_rows].fillna("").astype(str)
    header_df = header_df.applymap(_strip_cell) if hasattr(header_df, "applymap") else header_df  # safe, optional

    # forward fill horizontally to propagate group headings
    header_df = header_df.replace("", pd.NA).ffill(axis=1).fillna("")

    new_cols = []
    for col in header_df.columns:
        parts = []
        for i in header_rows:
            v = _strip_cell(header_df.loc[i, col])
            if v:
                parts.append(v)
        name = " | ".join(parts) if parts else str(col)
        name = re.sub(r"\s+", " ", name).strip()
        new_cols.append(name if name else str(col))

    body = df.iloc[max(header_rows) + 1 :].reset_index(drop=True)
    if body.empty:
        return df

    body.columns = new_cols

    # dedupe any identical new col names
    cols, seen = [], {}
    for c in body.columns:
        k = c if c else "col"
        seen[k] = seen.get(k, 0) + 1
        cols.append(k if seen[k] == 1 else f"{k} ({seen[k]})")
    body.columns = cols

    return body

def hash_df(df: pd.DataFrame) -> str:
    """
    Fast stable hash of DF content (columns + values).
    No applymap. Vectorized cleaning.
    """
    if df is None or df.empty:
        return ""

    d = df.fillna("").astype(str).copy()
    # normalize cells vectorized per column
    for col in d.columns:
        d[col] = (
            d[col]
            .str.replace("\u00a0", " ", regex=False)
            .str.replace(r"[ \t]+", " ", regex=True)
            .str.strip()
        )

    header = "|".join(map(str, d.columns))
    body = "\n".join("|".join(row) for row in d.values)
    raw = header + "\n" + body
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def df_to_markdown_table(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


# -----------------------------
# PDF extractors
# -----------------------------
@dataclass
class ExtractedTable:
    page: int
    source: str
    df: pd.DataFrame
    df_hash: str

def extract_with_camelot(pdf_path: Path, pages: str, flavor: str) -> List[Tuple[int, pd.DataFrame]]:
    import camelot  # lazy import

    kwargs = {}
    if flavor == "lattice":
        kwargs = dict(line_scale=CAMELOT_LATTICE_LINE_SCALE)
    elif flavor == "stream":
        kwargs = dict(strip_text="\n", edge_tol=CAMELOT_STREAM_EDGE_TOL, row_tol=CAMELOT_STREAM_ROW_TOL)

    tables = camelot.read_pdf(str(pdf_path), pages=pages, flavor=flavor, **kwargs)

    out: List[Tuple[int, pd.DataFrame]] = []
    for t in tables:
        try:
            page = int(getattr(t, "page", "0"))
        except Exception:
            page = 0
        df = t.df
        df = normalize_df(df)
        df = rebuild_multi_header(df, max_header_rows=MAX_HEADER_ROWS)
        df = normalize_df(df)
        if df.shape[0] >= MIN_ROWS_FOR_TABLE and df.shape[1] >= MIN_COLS_FOR_TABLE:
            out.append((page, df))
    return out

def extract_with_pdfplumber(pdf_path: Path) -> List[Tuple[int, pd.DataFrame]]:
    import pdfplumber  # lazy import

    out: List[Tuple[int, pd.DataFrame]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for p_idx, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables() or []
            for tab in tables:
                if not tab:
                    continue
                df = pd.DataFrame(tab)
                df = normalize_df(df)
                df = rebuild_multi_header(df, max_header_rows=MAX_HEADER_ROWS)
                df = normalize_df(df)
                if df.shape[0] >= MIN_ROWS_FOR_TABLE and df.shape[1] >= MIN_COLS_FOR_TABLE:
                    out.append((p_idx, df))
    return out

def extract_tables_optimum(pdf_path: Path, pages: str = "all") -> List[ExtractedTable]:
    extracted: List[ExtractedTable] = []
    seen_hashes: set[str] = set()

    def add(src: str, tables: List[Tuple[int, pd.DataFrame]]):
        nonlocal extracted, seen_hashes
        for page, df in tables:
            if df is None or df.empty:
                continue
            h = hash_df(df)
            if not h or h in seen_hashes:
                continue
            seen_hashes.add(h)
            extracted.append(ExtractedTable(page=page, source=src, df=df, df_hash=h))

    # priority order
    try:
        add("camelot_lattice", extract_with_camelot(pdf_path, pages=pages, flavor="lattice"))
    except Exception:
        pass
    try:
        add("camelot_stream", extract_with_camelot(pdf_path, pages=pages, flavor="stream"))
    except Exception:
        pass
    try:
        add("pdfplumber", extract_with_pdfplumber(pdf_path))
    except Exception:
        pass

    # stable ordering
    extracted.sort(key=lambda t: (t.page, t.source, t.df_hash))
    return extracted

def extract_text_pypdf(pdf_path: Path, max_pages: int) -> str:
    from pypdf import PdfReader  # lazy import

    reader = PdfReader(str(pdf_path))
    texts = []
    for i, page in enumerate(reader.pages[:max_pages], start=1):
        t = (page.extract_text() or "").strip()
        if t:
            texts.append(f"## page {i}\n\n{t}\n")
    return "\n\n---\n\n".join(texts).strip()


# -----------------------------
# Emission strategy for RAG (generic)
# -----------------------------
def _row_to_kv_lines(row: dict, max_key_len: int = 80) -> List[str]:
    lines = []
    for k, v in row.items():
        key = str(k).strip()
        if not key:
            continue
        if len(key) > max_key_len:
            key = key[:max_key_len] + "…"
        val = _strip_cell(v)
        if val == "":
            continue
        lines.append(f"{key}: {val}")
    return lines

def table_to_documents(
    df: pd.DataFrame,
    filename: str,
    page: int,
    source: str,
    table_id: str,
) -> List[dict]:
    """
    Generic conversion:
    - If first column looks like an entity column (e.g., country/destination),
      emit one document per row (best retrieval for "Argentine ?").
    - Always include a compact markdown snapshot as fallback.
    """
    docs: List[dict] = []

    # Identify candidate entity column: first column, mostly text, not numeric-ish
    entity_col = df.columns[0] if len(df.columns) > 0 else None
    if entity_col is not None:
        col_vals = df[entity_col].fillna("").astype(str).map(_strip_cell).tolist()
        nonempty = [v for v in col_vals if v]
        textlike = sum(1 for v in nonempty if not _is_numericish(v))
        entity_ok = (len(nonempty) >= 3) and (textlike >= int(0.7 * len(nonempty)))
    else:
        entity_ok = False

    # 1) Row-level documents (preferred)
    if entity_ok:
        records = df.to_dict(orient="records")
        for idx, row in enumerate(records, start=1):
            entity = _strip_cell(row.get(entity_col, ""))
            if not entity:
                continue
            kv_lines = _row_to_kv_lines(row)
            if not kv_lines:
                continue

            content = f"{entity_col}: {entity}\n" + "\n".join(kv_lines)
            docs.append({
                "page_content": content,
                "metadata": {
                    "source": filename,
                    "page": page,
                    "extractor": source,
                    "table_id": table_id,
                    "row_index": idx,
                    "entity": entity,
                    "entity_col": str(entity_col),
                    "format": "row_kv",
                },
            })

    # 2) Table snapshot (fallback / context)
    md = (
        f"## {filename} — table\n"
        f"- page: {page}\n"
        f"- extractor: {source}\n"
        f"- table_id: {table_id}\n\n"
        f"{df_to_markdown_table(df)}\n"
    )
    docs.append({
        "page_content": md,
        "metadata": {
            "source": filename,
            "page": page,
            "extractor": source,
            "table_id": table_id,
            "format": "table_markdown",
        },
    })

    return docs

def chunk_text(text: str, max_chars: int, overlap: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    out = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        out.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return out


# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="OpenWebUI External Ingestion Engine", version="2.0.0")

@app.get("/health")
def health():
    return {"ok": True}

@app.put("/process")
async def process(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    content_type: Optional[str] = Header(default=None),
    x_filename: Optional[str] = Header(default=None),
):
    require_bearer(authorization)

    data = await request.body()
    if not data:
        raise HTTPException(400, "Empty body")

    filename = (x_filename or "uploaded").strip()
    mime = (content_type or "").lower()

    # PDF pathway
    if ("pdf" in mime) or filename.lower().endswith(".pdf"):
        with tempfile.TemporaryDirectory() as td:
            pdf_path = Path(td) / "doc.pdf"
            pdf_path.write_bytes(data)

            tables = extract_tables_optimum(pdf_path, pages=PDF_PAGES)

            # If no tables -> fallback to text
            if not tables:
                text = extract_text_pypdf(pdf_path, max_pages=MAX_TEXT_PAGES)
                if not text:
                    text = (
                        f"{filename}\n\n"
                        f"(No tables detected and text extraction is empty. "
                        f"This PDF may be scanned; OCR may be required.)"
                    )
                parts = chunk_text(text, MAX_DOC_CHARS, OVERLAP_CHARS)
                return JSONResponse([{
                    "page_content": p,
                    "metadata": {
                        "source": filename,
                        "content_type": mime or "application/pdf",
                        "engine": "fallback_text",
                        "chunk": i,
                        "chunks_total": len(parts),
                    },
                } for i, p in enumerate(parts, start=1)])

            # Convert tables -> documents (row-level + table snapshot)
            docs: List[dict] = []
            for t_idx, t in enumerate(tables, start=1):
                table_id = f"p{t.page:03d}_t{t_idx:03d}_{t.df_hash[:8]}"
                docs.extend(table_to_documents(t.df, filename, t.page, t.source, table_id))

            # Chunk any oversized docs (rare but possible for big markdown snapshots)
            final_docs: List[dict] = []
            for d in docs:
                content = d["page_content"]
                parts = chunk_text(content, MAX_DOC_CHARS, OVERLAP_CHARS)
                if len(parts) == 1:
                    final_docs.append(d)
                else:
                    for i, p in enumerate(parts, start=1):
                        md = dict(d["metadata"])
                        md.update({"chunk": i, "chunks_total": len(parts)})
                        final_docs.append({"page_content": p, "metadata": md})

            return JSONResponse(final_docs)

    # Non-PDF fallback: best effort utf-8 text
    try:
        text = data.decode("utf-8", errors="ignore").strip()
    except Exception:
        text = ""
    if not text:
        text = f"{filename}\n\n(Non-PDF format not handled; empty text.)"
    parts = chunk_text(text, MAX_DOC_CHARS, OVERLAP_CHARS)
    return JSONResponse([{
        "page_content": p,
        "metadata": {
            "source": filename,
            "content_type": mime or "application/octet-stream",
            "engine": "basic_text",
            "chunk": i,
            "chunks_total": len(parts),
        },
    } for i, p in enumerate(parts, start=1)])


"""
Quick test (without OpenWebUI):
  curl -X PUT "http://localhost:8088/process" \
    -H "Authorization: Bearer supersecret" \
    -H "Content-Type: application/pdf" \
    -H "X-Filename: tarifs.pdf" \
    --data-binary "@tarifs.pdf"
"""
