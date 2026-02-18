# Project State

This state file captures the ingestion engine control flow and one critical end-to-end test sequence, aligned with `app.py`.

## A) Router / Decision Flow

```mermaid
flowchart TD
    A[PUT /process] --> B{Authorization header present?}
    B -- No --> B1[Return 401 Missing Bearer token]
    B -- Yes --> C{Bearer token matches ENGINE_API_KEY?}
    C -- No --> C1[Return 403 Invalid token]
    C -- Yes --> D{PDF by mime or filename?}

    D -- Yes --> E[Persist request body as temp PDF]
    E --> F[Extract tables via Camelot lattice]
    F --> G[Try Camelot stream]
    G --> H[Try pdfplumber table extraction]
    H --> I[Normalize + rebuild headers + de-duplicate]

    I --> J{Any valid table found?}
    J -- Yes --> K[Emit row-level docs + table markdown snapshot]
    K --> L[Chunk oversized docs with overlap]
    L --> M[Return OpenWebUI-compatible JSON payload]

    J -- No --> N[Fallback to pypdf text extraction]
    N --> O{Fallback text empty?}
    O -- No --> P[Chunk extracted text]
    O -- Yes --> Q[Create explicit OCR-needed message]
    P --> M
    Q --> M

    D -- No --> R[Decode utf-8 best effort]
    R --> S{Decoded text empty?}
    S -- Yes --> T[Create non-PDF fallback message]
    S -- No --> U[Chunk decoded text]
    T --> M
    U --> M
```

## B) Single Sequence for a Critical Test Case

### Critical case
**Authenticated upload of a table-heavy PDF where Camelot lattice fails but stream succeeds.**

```mermaid
sequenceDiagram
    autonumber
    participant Client as OpenWebUI / Client
    participant API as FastAPI /process
    participant Auth as Bearer Validator
    participant Lattice as Camelot Lattice
    participant Stream as Camelot Stream
    participant Normalize as DF Normalize + Header Rebuild
    participant Emit as Row + Snapshot Emitter

    Client->>API: PUT /process + Bearer token + PDF bytes
    API->>Auth: require_bearer(auth_header)
    Auth-->>API: OK

    API->>Lattice: read_pdf(flavor=lattice)
    Lattice-->>API: 0 usable tables

    API->>Stream: read_pdf(flavor=stream)
    Stream-->>API: Extracted tables

    API->>Normalize: normalize_df + rebuild_multi_header + hash-based dedupe
    Normalize-->>API: Clean structured tables

    API->>Emit: row-level docs + markdown snapshot docs
    Emit-->>API: documents[]

    API-->>Client: 200 OK + JSON documents for indexing
```

## C) Innovation Pipeline Traceability (Exploration → Service)

```mermaid
flowchart LR
    EX[Exploration] --> PC[POC]
    PC --> PI[Pilote]
    PI --> ST[Standard]
    ST --> SV[Service]
```

| Stage | Objective | Evidence to store | KPI examples |
| --- | --- | --- | --- |
| Exploration | Validate problem and feasibility | hypotheses, sample PDFs, target questions | baseline response quality |
| POC | Prove technical approach | extraction results, schema checks, quick benchmarks | parsing success rate |
| Pilote | Validate in near-real conditions | pilot dataset, incident log, user feedback | time saved per ingestion |
| Standard | Stabilize and document operation | runbook, controls, release notes | risk reduction (error rate) |
| Service | Operate with reliability targets | SLA/SLO, monitoring, ownership model | capacity created, cost avoided |
