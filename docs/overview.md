# Overview technique

## Ce que fait le service

Ce projet expose une API FastAPI qui reçoit un document binaire (principalement PDF) et renvoie une liste de documents textuels structurés compatibles avec le format attendu par OpenWebUI.

## Pipeline d’ingestion

1. Vérification du token Bearer (`ENGINE_API_KEY`)
2. Détection du type de contenu et branche PDF/non-PDF
3. Extraction de tableaux par ordre de priorité :
   - Camelot lattice
   - Camelot stream
   - pdfplumber
4. Normalisation des DataFrames et reconstruction des entêtes multi-lignes
5. Déduplication des tableaux (hash)
6. Emission documentaire :
   - documents par ligne (quand colonne entité détectée)
   - snapshot markdown du tableau
7. Chunking des documents longs
8. Fallback extraction texte (`pypdf`) si aucun tableau exploitable

## Entrées / sorties

- Entrée : `PUT /process` avec bytes du fichier + headers (`Authorization`, `Content-Type`, `X-Filename`)
- Sortie : `JSON[]` avec objets `{page_content, metadata}`

## Points forts

- Générique (pas de logique spécifique à un PDF)
- Robuste aux structures tabulaires complexes
- Compatible RAG et indexation vectorielle
- Facile à intégrer dans OpenWebUI
