# Démo live — Assistant Kiné (MinervIA)

> Runbook d'atelier **20-30 min**, piloté par Nicolas. Format « à la carte » :
> on ouvre, on montre l'angle, puis **le kiné choisit** les modules qu'il veut voir.
> Tous les modules sont prêts à enchaîner. 100 % live, aucune donnée patient.

---

## 0. Avant l'atelier (J-1, ~10 min)

- [ ] Stack vLLM + Open WebUI démarrés (`api.minervia.fr` accessible).
- [ ] Se connecter au compte de démo, modèle **« Assistant Kiné »** sélectionné.
- [ ] Ouvrir un onglet vierge, historique vidé (nouvelle conversation propre).
- [ ] Avoir sous la main : la **feuille A4** (`feuille-a4-kine.pdf`) à remettre, et ce runbook.
- [ ] Lancer **une** question au hasard pour vérifier que ça répond (latence réseau du jour).

> ⏱️ **Latence** : chaque réponse RAG met **~30-40 s** (le modèle rappelle les bases,
> cite ses sources). C'est normal et même bon signe — le kiné voit les « Sources »
> s'afficher. Prévenir : « là il va chercher dans ses bouquins, ça prend une vingtaine
> de secondes, c'est ce qui garantit que c'est sourcé et pas inventé. »

---

## 1. Ouverture — l'angle (2-3 min, à dire, pas à montrer)

Phrase d'accroche (l'angle unique, ne jamais en dévier) :

> « Cet outil ne te demande **jamais** une info patient. Jamais un nom, jamais un âge,
> jamais un diagnostic. Et c'est exactement pour ça qu'il est simple côté données :
> on ne peut pas perdre, pirater ou revendre ce qu'on n'a **jamais reçu**. »

Puis la frontière Doctolib (le kiné est déjà dessus — ne jamais le concurrencer) :

> « Doctolib, c'est tes **mains** : il exécute (RDV, rappels, FSE, paiement).
> Lui, c'est ta **tête** : il t'explique le règlementaire, il rédige, il t'enseigne.
> Zéro chevauchement. Il n'émet **aucune** FSE — il t'éclaire la cotation, il ne cotte pas. »

**Le chiffre à construire AVEC lui** (pas à imposer) :
> « Combien d'heures par semaine tu passes sur tout ce qui n'est **pas** une séance ?
> C'est ça, le temps qu'on va te rendre. »

---

## 2. Menu à la carte — le kiné choisit

Proposer le menu, laisser le kiné pointer ce qui le démange. Chaque module a sa fiche.
**Les numéros suivent l'ordre de passage conseillé.**

| # | Module | Ce que ça répond | Fiche |
|---|--------|------------------|-------|
| 1 | **Ouverture (waouh)** | ALD + cumul BDK + reste à charge (raisonnement) | `module-1-ouverture.md` |
| 2 | **Rédaction CR / courriers** + **filtre zéro donnée** | trame à champs `[...]`, et la preuve que rien ne sort | `module-2-redaction-filtre.md` |
| 3 | **Règlementaire NGAP** | « AMK ou AMT ? » (piège), accès direct, accord préalable | `module-3-reglementaire.md` |
| 4 | **Manuel physio / anatomie** | biomécanique, mécanisme d'une patho, **cité** | `module-4-physio.md` |
| 5 | **Éducation patient** | fiche d'info générique à remettre | `module-5-education.md` |
| 6 | **DPC / veille** | obligations, cycle, sources | `module-6-dpc.md` |

> Ordre conseillé si le kiné hésite : **1 → 2 → 3 → 4 → 5 → 6**.
> Le module 1 (ouverture) accroche dès la 1ʳᵉ minute ; le module 2 est le clou
> (on voit le filtre masquer une donnée patient en direct).

---

## 3. Conduite de chaque module (le même geste)

1. **Nouvelle conversation** (propre à chaque module).
2. **Taper le prompt** exact de la fiche (copier-coller depuis la fiche).
3. **Pendant les ~30-40 s**, commenter à voix haute : « il rappelle la base documentaire,
   il va te citer d'où ça vient ». Pointer les **« N Sources »** qui apparaissent.
4. **Lire la réponse ensemble**, pointer ce qui compte (le tarif exact, la source, le `[...]`).
5. Enchaîner ou rebondir sur une question du kiné.

> ⚠️ **Filtre (module 2)** : ne **jamais** juger le filtre pendant la génération.
> Le masque s'applique **après** la fin (« Response complete »). Attendre la fin,
> puis montrer que le nom/âge/EVA sont devenus `[A COMPLETER]`.

---

## 4. Clôture — la porte d'entrée (2-3 min)

Rappeler les 5 messages-clés, puis proposer la suite **sans engagement** :

> « On ne part pas sur un contrat. On part sur un **atelier d'écoute** puis un
> **pilote gratuit** : tu l'utilises sur tes vraies questions — sans jamais y mettre
> un patient — pendant quelques semaines, et on voit si ça te rend du temps. »

Limites à assumer à la fin (ça crée la confiance, pas l'inverse) :
- Pas de diagnostic, pas de plan individualisé → ça reste **ton** acte, sous **ta** responsabilité.
- Ne remplace ni le toucher, ni l'observation, ni le lien.
- Rien ne part sans **ta** relecture.
- NGAP = à date (re-chargé quand la nomenclature bouge).
- Base physio = **pédagogique**, pas une reco de prise en charge.

Remettre la **feuille A4**. Noter les modules qui l'ont fait réagir → ce sont les usages
à creuser dans le pilote.

---

## Notes techniques (rappel, ne pas montrer)

- Modèle `assistant-kine` (base `IA`), prompt routage 2 bases, filtre sortie `kine_zero_patient`.
- KB1 « Connaissance Kiné » (règlementaire/DPC, sourcé ameli) · KB2 « Physiologie & Rééducation » (630 sources).
- Le RAG ne marche **que dans l'UI** (mode agent), pas en curl → toujours démontrer via le navigateur.
- Déploiement cible = **local** (PC du kiné) pour l'argument HDS inattaquable. La démo tourne en hébergé par simplicité.
