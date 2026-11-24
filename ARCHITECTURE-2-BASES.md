# Architecture 2 bases — Assistant Kiné

Conception retenue le 2026-11-24 (choix « C »). Objectif : enrichir l'assistant
avec du savoir de **physiologie / rééducation** sans dégrader le retrieval
**administratif NGAP** déjà validé.

## Principe

Deux collections de connaissances **séparées**, attachées à **un seul modèle**
(`assistant-kine`). Le routage se fait par le **system_prompt** : à chaque
question, le modèle doit interroger **une seule** base et passer son identifiant
dans le paramètre `knowledge_ids` de l'outil `query_knowledge_files`.

```
Question → assistant-kine → routage (prompt)
   ├─ gestion / cotation / courrier  → KB1 Administratif  2b0c338d-1040-4d25-bb77-30a6873b1c42
   ├─ physiologie / anatomie / rééduc → KB2 Physiologie    e68519ab-dece-4221-901c-4c6b58010997
   └─ donnée patient / diagnostic     → refus poli (règle d'or)
```

## Vérité technique (vérifiée dans `tools/builtin.py`, OWUI 0.13.4)

- L'outil RAG réel de l'agent est `query_knowledge_files(query, knowledge_ids?, count)`.
- Si le modèle a N collections attachées, l'agent **fusionne** les collections par
  défaut (`collection_names = [toutes]`). Il **peut** cibler une base en passant
  `knowledge_ids=[id]` — c'est le levier exploité par le prompt.
- `search_knowledge_files(query, knowledge_id?)` = recherche par **nom de fichier**,
  scopée aux KB attachées.
- Conséquence : **1 modèle + 2 KB + directive de prompt** suffisent. Pas de 2ᵉ modèle.

## Frontière clinique retenue

La base 2 **élargit** le périmètre de l'assistant (le prompt refusait le clinique
avant ce changement). Frontière validée par le user :

> L'assistant peut **expliquer** la physiologie, l'anatomie, la logique d'une
> rééducation et **éduquer** de façon générique — mais ne **pose jamais de
> diagnostic** et n'établit **jamais** un plan individualisé pour un patient donné.

La **règle d'or « aucune donnée patient »** s'applique aux deux bases. La base 2
ne contient que du savoir **général**, jamais de cas clinique nominatif.

## État déployé (2026-11-24)

| Élément | Valeur |
|---------|--------|
| KB1 Administratif | `2b0c338d-1040-4d25-bb77-30a6873b1c42` (13 fichiers, inchangée) |
| KB2 Physiologie & Rééducation | `e68519ab-dece-4221-901c-4c6b58010997` (**vide**, conteneur seul) |
| Modèle | `assistant-kine`, `meta.knowledge` = [KB1, KB2] |
| Prompt | `_system_prompt_kine_v2.md` (6166 car., section « BASES ET ROUTAGE ») |
| Déploiement | `_deploy_2bases.py` (lit le modèle, remplace knowledge+prompt, POST update) |

Les deux KB donnent `read` à l'utilisateur kiné `ecb710df`.

## Validation UI (agent mode, seul chemin qui compte)

- **Non-régression NGAP** : « tarif séance 30 min + taux remboursement » → sources
  `04a-ngap-*` / `05a-remboursement-*`, tarif = coefficient × 2,21 €, taux 60/80/90/100 %. **OK.**
- **Question physiologie** (base 2 vide) : le modèle répond sur son savoir et
  déclare honnêtement que « les documents ne traitent pas de la physiologie fine…
  ils portent sur la NGAP ». **Aucune pollution NGAP.** **OK.**
- `test_regress.py` (filtre zéro donnée patient) : tous tests passent.

## Limite connue / prochaine étape

Tant que la base 2 est **vide**, l'agent fait une recherche fusionnée qui retombe
sur la base admin seule → pas de dilution, mais le **routage explicite**
(`knowledge_ids=[KB2]`) n'est pleinement observable qu'une fois la base 2 peuplée.

**Prochaine étape (hors périmètre de cette tâche C)** : alimenter la base 2.
Sources candidates : OpenStax Anatomy & Physiology 2e (CC-BY, RAG-ready, anglais),
fiches françaises CMPPRF/HAS pour la rééduc courante. Ne pas indexer sans accord explicite.

## Rollback

Réattacher uniquement KB1 au modèle et restaurer l'ancien prompt :
`meta.knowledge = [{id:2b0c338d…, type:collection}]`, `system_prompt` = version
précédente (git). La KB2 vide peut rester ou être supprimée sans impact.
