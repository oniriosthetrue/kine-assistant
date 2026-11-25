# Dossier démo — Assistant Kiné

Démo **live, à la carte, sans aucune donnée patient** pour un atelier de 20-30 min.

- **`RUNBOOK.md`** — le guide de conduite (ouverture, menu, geste par module, clôture). À lire en entier avant l'atelier.
- **`module-1-reglementaire.md`** — NGAP expliqué (AMK/AMT, accès direct), sourcé ameli.
- **`module-2-physio.md`** — manuel physiologie/anatomie, réponses citées.
- **`module-3-redaction-filtre.md`** — trame CR à champs **+ preuve du filtre zéro donnée** (le clou).
- **`module-4-education.md`** — fiche d'éducation patient générique.
- **`module-5-dpc.md`** — obligations DPC, cycle triennal, sources.

## État de test (validé en live le 25/11/2026)

Les 5 modules ont été **testés en réel** sur `api.minervia.fr` (modèle « Assistant Kiné »).
Chaque fiche contient le **prompt exact** et le **résultat réellement observé**.

| Module | Routage | Sources | Verdict |
|---|---|---|---|
| 1 — Règlementaire | KB1 | ameli/NGAP (17) | ✅ refuse la prémisse fausse « AMT » + BDK chiffré |
| 2 — Physio | KB2 | OpenStax | ✅ structuré + honnête si hors-base |
| 3 — Rédaction + filtre | KB1 | trame | ✅ trame `[...]` + **filtre masque la donnée patient** |
| 4 — Éducation | KB1+KB2 | lombalgie | ✅ fiche générique, 6 sources, 0 patient |
| 5 — DPC | KB1 | 06-dpc | ✅ cycle de 3 ans en dur, ANDPC, mondpc.fr |

## 2 pièges à retenir le jour J

1. **Latence ~30-40 s** par réponse RAG → l'annoncer (« il cherche dans ses bouquins, c'est ce qui garantit que c'est sourcé »).
2. **Filtre (module 3)** : le masque s'applique **après** la fin de la réponse. Ne jamais juger pendant le streaming.
