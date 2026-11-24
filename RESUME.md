# RESUME — Assistant Kiné (RAG + filtre « Zéro donnée patient »)

> Point de reprise autonome. Dernière mise à jour : **2026-11-24**.
> Ce dossier n'était pas versionné avant cette date → dépôt git créé le 2026-11-24.

## 1. Objectif

Un assistant Open WebUI pour kinésithérapeute libéral qui :
- répond aux **questions de gestion** (cotation NGAP, remboursement, accès direct, accords
  préalables, DPC, éthique) **avec les vrais chiffres** en dur ;
- **rédige courriers / comptes-rendus** en laissant des champs `[ ... ]` à compléter ;
- **ne reçoit JAMAIS une donnée patient** : un filtre de sortie masque toute donnée
  identifiante par `[A COMPLETER]`.

## 2. Pièce par pièce (ce qui est déployé et où)

| Composant | Identifiant | Source dans ce dossier |
|-----------|-------------|------------------------|
| Modèle OWUI | `assistant-kine` (base `IA`) | `_system_prompt_kine.md` (prompt) + `_model_kine.json` (méta) |
| Filtre outlet | `kine_zero_patient` | `_filtre_zero_donnee.py` |
| Base de connaissances | `2b0c338d-1040-4d25-bb77-30a6873b1c42` (« Connaissance Kiné ») | `corpus-rag/` (10 fichiers indexés) |
| Corpus source | — | `sources/NGAP-21062026.pdf` (228 p., ameli, 21/06/2026) |

### Corpus indexé (10 fichiers, chacun < 4 Ko — sinon reset embedding)
- `01-trames-courriers`, `02-education-patient`, `03-faq-admin-veille`
- `04a-ngap-calcul-regles-bilans`, `04b1-ngap-actes-rachis-membres`,
  `04b2-ngap-actes-neuro-resp-divers`, `04c-ngap-domicile-acces-erreurs`
- `05a-remboursement-prise-en-charge`, `05b-acces-direct-kine`, `05c-accords-prealables-apa`
- Sur disque mais NON indexés (remplacés) : `04b-ngap-actes-chapitre-II.md`,
  `04-nomenclature-actes-ngap.md`

## 3. Le filtre « Zéro donnée patient » — logique contextuelle

Filtre OWUI de type `filter`, événement `outlet` (s'exécute APRÈS le modèle, AVANT affichage).
Deux modes choisis selon la **présence d'une donnée patient dans le dernier message user** :

- **Mode agressif** (rédaction de courrier/CR) : masque tout (nom, âge, date chiffres OU
  lettres, EVA, amplitude, séances, %, cellules de tableau).
- **Mode non-agressif** (question de gestion) : ne masque que les motifs SÛRS, pour laisser
  apparaître les chiffres du référentiel (taux 60 %, tarifs, « 8 séances », dates de loi).

### Les 4 correctifs appliqués (relecture 2026-11-24) — NE PAS régresser
1. **Faux-positif déclencheur** : le détecteur `_PATIENT_DATA_RE` ne doit PAS contenir dates
   ni âges (sinon « loi du 19/05/2023 » déclenche le mode agressif). `_has_patient_data` ne
   scanne que le DERNIER message user (`reversed(messages)`).
2. **Fuite d'année** : le score `NN/MM` mordait `12/03` de `12/03/2026` → `/2026` restant.
   FIX = score NN/MM placé dans `_AMBIGUOUS_PATTERNS` APRÈS les motifs de date.
3. **EVA vs date** : motif EVA `\d{1,3}/(10|100|5)` mordait le mois de `05/10/2026`.
   FIX = lookahead `(?!\s*/)` (dans `_SAFE_PATTERNS` ET le détecteur).
4. **Date en toutes lettres** : le modèle réécrit « la séance du 12 mars 2026 » → fuite.
   FIX = motif agressif `\b\d{1,2}\s+(janvier|...|décembre)\b(?:\s*\d{2,4})?`.

## 4. Commandes de redéploiement

> open-webui n'a **aucun port hôte** : toute API passe par
> `docker exec open-webui sh -c 'curl http://localhost:8080/...'`.
> Token admin : `/tmp/owui_admin_token.txt` (expire → régénérer via signin, champ `token`).

### Redéployer le filtre
```bash
# corps = FunctionForm complet (id+name+content+meta+type). Renvoie content:"" ->
# vérifier via GET /functions/id/kine_zero_patient.
POST /api/v1/functions/id/kine_zero_patient/update
```
Le corps se construit en Python : lire la fonction via GET, remplacer `content` par le
fichier `_filtre_zero_donnee.py`, `docker cp` le JSON dans le conteneur, puis POST.

### Redéployer le prompt du modèle
Le prompt d'un modèle custom OWUI est dans **`meta.system_prompt`** (PAS `params.system`,
qui peut être `{}`). Corps = **ModelForm complet** `{id,name,base_model_id,meta,params}`
(422 si un champ manque) :
```bash
POST /api/v1/models/model/update?id=assistant-kine
```

### Ré-indexer le corpus
```bash
python3 _upload_05.py   # téléverse 05a/05b/05c (multipart -> file_id -> file/add)
```

## 5. Validation (3 tests UI, tous verts le 2026-11-24)
1. Question remboursement → 60/40/80/90/100 %, 1€/4€/50€, 9,95−1=8,95€, dates de loi : **tout en dur**.
2. Courrier « M. Dupont 45 ans 12/03/2026 EVA 7/10 amplitude 28/52 » → **tout masqué**, aucune fuite.
3. Question citant « loi du 19/05/2023 » → reste non-agressif, chiffres préservés.

⚠️ Pour vérifier l'effet du filtre outlet, se fier au **snapshot d'accessibilité** (DOM rendu),
PAS à `innerText` via Playwright (peut montrer le texte pré-filtre).

## 6. IDs / accès utiles
- KB : `2b0c338d-1040-4d25-bb77-30a6873b1c42`
- Modèle : `assistant-kine` · Filtre : `kine_zero_patient`
- Compte de test UI : `kine@giteexperience.com` (mot de passe NON stocké ici)
- Owner KB = admin test.qa (`98812e4c`) ; un **access_grant read** vers le user kine
  (`ecb710df`) est requis, sinon `query_knowledge_files` renvoie `[]`.

## 7. Ce qui reste à faire / pistes
- [ ] Étoffer le corpus (DPC, éthique Ordre, télétransmission) si besoin.
- [ ] Éventuellement passer le corpus en embedding 4 bits / reranker (projet séparé).
- [ ] Surveiller les faux négatifs du filtre (donnée patient non masquée) en usage réel.

## 8. Mémoire liée
L'état technique complet est aussi dans la mémoire repo Copilot :
`/memories/repo/owui-rag-kine-ngap.md` (rechargée automatiquement par l'agent).
