# Cas d’usage réel

## Contexte

Une équipe support télécom interroge des grilles tarifaires PDF via OpenWebUI.

## Problème

Le parsing texte brut des PDFs sépare les entêtes des valeurs et dégrade la qualité des réponses RAG (hallucinations, confusion colonnes/forfaits).

## Solution apportée par ce service

Le moteur extrait la structure tabulaire, reconstruit les entêtes multi-lignes et indexe des documents par ligne entité (ex: pays), ce qui améliore la précision de recherche.

## Scénario concret

Question utilisateur: *« Quels sont les tarifs SMS vers l’Argentine ? »*

Résultat attendu:
- récupération de la ligne `Argentine`
- restitution des colonnes tarifaires avec leur contexte d’entête

## Conditions de succès

- PDF textuel (ou qualité suffisante pour extraction de tables)
- token API configuré côté OpenWebUI
- dépendances Camelot/ghostscript présentes
