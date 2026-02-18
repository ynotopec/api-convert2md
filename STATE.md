# Project State

This state file captures the ingestion engine control flow and one critical end-to-end test sequence.

## A) Router / Decision Flow

```mermaid
flowchart TD
    A[PUT /process] --> B{Authorization header present?}
    B -- No --> B1[Return 401 Missing Bearer token]
    B -- Yes --> C{Bearer token matches ENGINE_API_KEY?}
    C -- No --> C1[Return 403 Invalid token]
    C -- Yes --> D[Persist request body as temp PDF]

    D --> E[Extract tables via Camelot lattice]
    E --> F{Any valid tables?}
    F -- No --> G[Try Camelot stream]
    F -- Yes --> H[Normalize + rebuild headers + de-duplicate]

    G --> I{Any valid tables?}
    I -- No --> J[Try pdfplumber table extraction]
    I -- Yes --> H

    J --> K{Any valid tables?}
    K -- Yes --> H
    K -- No --> L[Fallback to pypdf text extraction]

    H --> M[Emit row-level docs when first column is entity-like]
    M --> N[Also emit markdown snapshot docs]
    N --> O[Chunk docs with overlap limits]
    O --> P[Return OpenWebUI-compatible JSON payload]

    L --> Q{Fallback text available?}
    Q -- No --> Q1[Return empty documents payload]
    Q -- Yes --> O
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

## Notes

- The extraction strategy is intentionally **ordered** to prioritize structure quality before fallback text parsing.
- The critical case above validates the main reliability promise of the service: preserving table semantics even when one parser mode fails.
