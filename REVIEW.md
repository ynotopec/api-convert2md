# Repository Review

## État observé

Le repository fournit un moteur d’ingestion FastAPI cohérent avec une extraction PDF orientée tableaux pour OpenWebUI.

## Alignement réalisé avec `app.py`

1. **Script d’exécution simplifié** : `run.sh` lance uniquement ce service FastAPI (suppression des variables et chemins hérités de projets Gradio/Streamlit qui ne concernaient pas `app.py`).
2. **Chargement d’environnement cohérent** : `.env` est optionnel, mais `ENGINE_API_KEY` est maintenant validée explicitement avant le démarrage, comme dans l’application.
3. **Documentation d’état corrigée** : le flux de fallback décrit désormais les comportements réels de `app.py` (message OCR si PDF sans texte, message non-PDF si corps vide), au lieu de mentionner un payload vide.

## Recommandations suivantes

- Ajouter des tests unitaires sur `normalize_df`, `rebuild_multi_header`, `chunk_text`.
- Ajouter un test API minimal (`/health` et `/process` avec faux payload texte).
- Épingler les versions sensibles (`camelot`, `pandas`, `opencv`) pour éviter les régressions silencieuses.
