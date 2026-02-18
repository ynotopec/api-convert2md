# Pitch métier – API Convert2MD

## Pitch 30 secondes (elevator pitch)

**API Convert2MD transforme vos PDFs tarifaires complexes en données fiables pour OpenWebUI, afin de réduire les erreurs de réponse et accélérer l’accès à l’information.**
Concrètement, là où un parsing PDF classique “casse” les tableaux, notre moteur reconstruit les entêtes et les lignes métier pour fournir des réponses précises sur les tarifs, options ou conditions. Résultat: moins de temps perdu, moins de risques opérationnels, plus de confiance dans les réponses IA.

---

## Le problème métier (langage terrain)

Aujourd’hui, les documents PDF complexes (grilles tarifaires, matrices de conditions, tableaux multi-entêtes) sont mal interprétés par les pipelines standards:
- colonnes mélangées,
- entêtes perdues,
- réponses RAG ambiguës ou erronées.

**Impact direct:** surcharge support, risques de mauvaise information tarifaire, faible adoption des assistants IA internes.

---

## La promesse de valeur

Avec API Convert2MD:
- **Fiabilité**: préservation de la sémantique tabulaire (entêtes + lignes métier)
- **Performance opérationnelle**: réduction du temps d’analyse documentaire
- **Réduction du risque**: moins d’erreurs tarifaires dans les réponses utilisateurs
- **Scalabilité**: même moteur réutilisable sur plusieurs domaines (finance, logistique, RH)

---

## Chiffres à mettre en avant (hypothèses actuelles)

- Temps d’analyse d’un PDF complexe: **45 min → 15 min**
- Gain estimé: **30 min / PDF (~67%)**
- Coût évité unitaire (60€/h): **30€ / PDF**
- À 100 PDF/mois: **~3 000€ / mois** de coût évité

---

## Argumentaire “Pourquoi maintenant ?”

- Les usages IA conversationnels se généralisent côté métiers.
- La valeur d’un assistant dépend d’abord de la qualité des données ingérées.
- Sans couche d’ingestion spécialisée PDF-tableaux, les erreurs persistent et freinent l’adoption.

**Convert2MD est le chaînon manquant entre documents complexes et réponses IA exploitables en production.**

---

## Objections fréquentes et réponses

**“On a déjà un parser PDF.”**  
Oui, mais les parseurs génériques traitent mal les tableaux multi-entêtes; notre moteur est conçu pour ce cas d’usage critique.

**“C’est un sujet technique, pas métier.”**  
C’est un sujet métier: chaque erreur tarifaire peut créer un coût (support, geste commercial, image).

**“Le ROI est-il rapide ?”**  
Oui, dès que le volume de PDFs est régulier: les gains de temps et la baisse d’erreurs sont mesurables dès les premières semaines.

---

## Proposition de cadrage (pilote 4 semaines)

1. Sélection d’un corpus cible (ex. 50 PDFs tarifaires)
2. Définition d’un jeu de questions métier de référence
3. Mesure avant/après sur 3 KPIs:
   - taux d’extraction tabulaire réussie,
   - exactitude des réponses,
   - temps moyen de traitement
4. Go/No-Go sur généralisation

---

## Formulation “prête à dire” en comité métier

> “Notre enjeu n’est pas d’ajouter une IA de plus, mais de fiabiliser les réponses sur nos documents les plus sensibles. Convert2MD nous permet de transformer des PDF tarifaires complexes en données réellement exploitables par OpenWebUI. On réduit les erreurs, on gagne du temps opérationnel et on sécurise l’adoption métier avec un ROI mesurable dès le pilote.”
