# API Convert2MD – OpenWebUI External Ingestion Engine

Service FastAPI prêt à l’emploi pour brancher OpenWebUI sur un moteur d’extraction PDF orienté tableaux.

## Objectif

Convertir des PDFs complexes (grilles tarifaires, matrices, tableaux multi-entêtes) en documents structurés adaptés au RAG, avec une stratégie de fallback robuste.

## Fonctionnalités clés

- Extraction de tableaux : Camelot `lattice` → Camelot `stream` → `pdfplumber`
- Reconstruction automatique des entêtes multi-lignes
- Déduplication des tableaux via hash stable
- Emission de documents par ligne + snapshot markdown de tableau
- Fallback texte PDF via `pypdf`
- Endpoint compatible OpenWebUI `PUT /process`

## Démarrage rapide (≤ 10 minutes)

### 1) Prérequis

- Python 3.11+
- Ghostscript (requis/recommandé pour Camelot lattice)

### 2) Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 3) Configuration

```bash
export ENGINE_API_KEY="supersecret"
export PDF_PAGES="all"
```

### 4) Lancement

```bash
make run
```

Le service démarre sur `http://0.0.0.0:8088`.

## Exemple reproductible entrée / sortie

### Requête

```bash
curl -X PUT "http://localhost:8088/process" \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/pdf" \
  -H "X-Filename: tarifs.pdf" \
  --data-binary "@tarifs.pdf"
```

### Réponse (extrait)

```json
[
  {
    "page_content": "Pays: Argentine\nSMS envoyé | Forfait 2€: 0,27 €",
    "metadata": {
      "source": "tarifs.pdf",
      "page": 1,
      "extractor": "camelot_stream",
      "table_id": "p001_t001_1a2b3c4d",
      "format": "row_kv"
    }
  }
]
```

## Documentation

- Vue d’ensemble: `docs/overview.md`
- Architecture: `docs/architecture.md`
- Cas d’usage: `USE_CASE.md`
- Valeur métier: `VALUE.md`
- Pitch métier (prêt à présenter): `PITCH_METIER.md`
- Statut d’innovation: `INNOVATION_STATUS.md`

## API

- `GET /health` → `{"ok": true}`
- `PUT /process` → liste de documents OpenWebUI (`page_content`, `metadata`)

Authentification: header `Authorization: Bearer <ENGINE_API_KEY>`.

## Configuration OpenWebUI

### Option A — via variables d’environnement (Docker Compose)

Dans le service `open-webui`, ajoutez les variables suivantes :

```yaml
services:
  open-webui:
    environment:
      - CONTENT_EXTRACTION_ENGINE=external
      - EXTERNAL_DOCUMENT_LOADER_URL=http://ingestion-engine:8088
      - EXTERNAL_DOCUMENT_LOADER_API_KEY=supersecret
```

### Option B — via l’interface OpenWebUI (UI)

1. Ouvrir **Admin Panel**.
2. Aller dans **Settings** → **Documents** (ou **Files / Document Processing** selon la version).
3. Choisir **Content Extraction Engine** = `external`.
4. Renseigner **External Document Loader URL** = `http://ingestion-engine:8088`.
5. Renseigner **External Document Loader API Key** = `supersecret`.
6. Sauvegarder, puis tester l’import d’un PDF.

## Notes d’exploitation

- Variables de chunking : `MAX_DOC_CHARS`, `OVERLAP_CHARS`
- Limite fallback texte : `MAX_TEXT_PAGES`
- Tuning extraction : `CAMELOT_LATTICE_LINE_SCALE`, `CAMELOT_STREAM_EDGE_TOL`, `CAMELOT_STREAM_ROW_TOL`
- Parallélisme des extracteurs : `EXTRACTOR_WORKERS` (défaut: `3`)
