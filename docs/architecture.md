# Architecture

## Schéma global

```mermaid
flowchart TD
    A[Client/OpenWebUI] -->|PUT /process + Bearer| B[FastAPI app.py]
    B --> C{Fichier PDF ?}

    C -- Oui --> D[Extraction tables]
    D --> D1[Camelot lattice]
    D --> D2[Camelot stream]
    D --> D3[pdfplumber]

    D1 --> E[Normalisation DataFrame]
    D2 --> E
    D3 --> E

    E --> F[Reconstruction multi-header]
    F --> G[Déduplication hash_df]
    G --> H[Emission docs ligne + markdown]
    H --> I[Chunking]
    I --> J[JSONResponse OpenWebUI]

    C -- Non ou échec tables --> K[Fallback texte pypdf / utf-8]
    K --> I
```

## Composants

- **API layer**: FastAPI, endpoints `/health` et `/process`
- **Extraction layer**: Camelot, pdfplumber, pypdf
- **Transformation layer**: pandas (normalisation, entêtes, déduplication)
- **Emission layer**: génération des objets documents et chunking

## Déploiement minimal

- Un conteneur ou process Python
- Variables d’environnement pour clé API et paramètres d’extraction
- Exposition HTTP (port 8088 par défaut)
