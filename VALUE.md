# Valeur métier

## 🎯 Problème métier ciblé

Réduire les erreurs de réponse sur documents tarifaires PDF en préservant la sémantique des tableaux durant l’indexation.

## ⏱ Temps économisé (hypothèses)

- Temps moyen d’analyse manuelle d’un PDF complexe: **45 min**
- Avec ingestion structurée: **15 min** (contrôle rapide)
- Gain: **30 min / PDF** (~67%)

## 💰 Coût évité / réduit (hypothèses)

- Coût chargé analyste: **60€/h**
- Gain unitaire: **30€ / PDF**
- À 100 PDFs/mois: **~3 000€/mois** de coût évité

## 🛡 Risque diminué

- Diminution du risque d’erreurs tarifaires liées à des réponses RAG imprécises
- Réduction des incidents de support causés par une mauvaise interprétation de colonnes

## 🚀 Capacité nouvelle créée

- Interrogation fiable de documents tabulaires complexes dans OpenWebUI
- Réutilisation multi-domaines (finance, logistique, RH) sans re-développement par document

## KPIs recommandés

- Taux d’extraction tabulaire réussie (% fichiers)
- Taux de réponses exactes sur jeu de questions de référence
- Temps moyen d’onboarding d’un nouveau PDF
- Volume de PDFs ingérés / semaine

## Hypothèses explicites

- PDFs majoritairement non-scannés
- Questions utilisateurs orientées données tabulaires
- Intégration OpenWebUI correctement paramétrée

## Conditions de validité

- Monitoring régulier du taux de fallback texte
- Jeu de validation maintenu lors de changements de dépendances
