# Repository Review

## État observé

Le repository fournit un moteur d’ingestion FastAPI fonctionnel et spécialisé sur l’extraction de tableaux PDF pour OpenWebUI.

## Points forts

- Pipeline d’extraction multi-stratégies robuste
- Bonne couverture des cas de fallback
- Métadonnées riches pour l’indexation RAG

## Écarts détectés

1. Documentation projet incomplète pour un usage portefeuille (overview/architecture/valeur/statut innovation manquants).
2. Mode d’exécution non standardisé en commande unique explicite.
3. README verbeux et partiellement redondant avec les autres artefacts.

## Actions réalisées dans cette révision

- Structuration de la documentation (`docs/overview.md`, `docs/architecture.md`, `USE_CASE.md`, `VALUE.md`, `INNOVATION_STATUS.md`)
- Réécriture du README en format opérationnel court + reproductible
- Ajout d’une commande standard `make run`

## Recommandations suivantes

- Ajouter des tests automatisés (unitaires sur normalisation / headers)
- Ajouter un échantillon PDF de test anonymisé + snapshots attendus
- Mettre en place CI (lint + tests + build)
