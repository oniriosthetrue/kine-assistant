# Module 1 — Règlementaire NGAP expliqué

**Ce qu'on démontre** : l'assistant répond aux questions de cotation avec le **vrai
tarif/taux sourcé du NGAP ameli**, et surtout il **refuse d'inventer** : si une prémisse
est fausse, il la **corrige en le sourçant** au lieu de suivre la question aveuglément.
C'est le gap n°1 vs Doctolib (Doctolib émet la FSE, mais n'explique **pas** pourquoi
telle cotation — et ne corrige pas une erreur de code).

## Prompt à taper (copier-coller) — la « question piège »

```
Un patient a une AMK et une AMT sur la même séance. C'est quoi la différence de
cotation et de remboursement ? Et l'accès direct, ça marche pour quelles pathologies ?
```

> 🔑 **C'est volontairement une question piégée.** « AMT » **n'existe pas** dans la NGAP
> kiné, et l'accès direct **ne dépend pas** d'une liste de pathologies. Un ChatGPT nu
> inventerait une réponse cohérente. **Notre assistant, lui, démonte les deux erreurs.**
> C'est exactement ce qu'on veut montrer à un professionnel : il ne lui fera pas dire n'importe quoi.

## Ce qu'on dit au kiné (pendant les ~30-40 s)

> « Je lui pose une question avec une erreur dedans, exprès. Regarde s'il me suit
> docilement ou s'il me corrige. »

Pointer les **« Sources »** qui s'affichent (fichiers `04-ngap…`, `05b-acces-direct…` de KB1).

## Résultat validé (réponse réelle de la démo — 17 sources)

Le modèle **refuse les deux prémisses fausses** et redonne la vraie règle, tout sourcé :

1. **« AMT n'existe pas. »** La seule lettre-clé « AM… » en vigueur est **AMK**. Les codes
   disparus sont **AMS** (plus facturable depuis le 05/07/2024) et **AMC** (depuis le
   01/12/2024) — et il prévient de ne pas confondre « AMC » (acte) et « AMC » (mutuelle).
   → Donc « AMK + AMT sur la même séance » = situation qui n'existe pas.
2. **La vraie règle** : **une seule cotation par séance**, non cumulable sauf exceptions.
   Deux séances le même jour = 2 cotations plein tarif seulement si 2 prescriptions /
   2 articles / 2 régions / 2 séances distinctes.
3. **AMK chiffré** : sert au **BDK** (bilan-diagnostic kiné) et à la kiné-balnéo.
   BDK = **AMK 10,7 ≈ 23,65 €** (cas général) ou **AMK 10,8 ≈ 23,87 €** (affections
   neuro/musculaires). Tarif = coefficient × valeur de la lettre-clé (**AMK = 2,21 €**
   métropole, 2,43 € DROM). Rythme du BDK précisé (1ʳᵉ–10ᵉ, puis 30ᵉ, puis toutes les 20).
4. **Accès direct : ce n'est PAS une liste de pathologies.** Ça dépend du **lieu d'exercice**
   (loi Rist 2 du 19/05/2023) : établissements de santé/médico-sociaux, structures
   coordonnées (MSP/CDS/ESP/ESS), ou expérimentation **CPTS** (20 départements listés).
   Un kiné libéral **isolé** hors ces cadres **ne peut pas**. Sans diagnostic préalable :
   **8 séances max** puis réorientation médecin. Remboursement identique à l'ordonnance.

## Ce qu'on pointe à l'écran

- La **correction de la prémisse** (« AMT n'existe pas ») → l'argument anti-hallucination.
- Le **montant exact** du BDK et la valeur de la lettre-clé (pas « environ »).
- Le **bouton source** cliquable → « ça vient du NGAP, je peux te montrer d'où c'est tiré ».
- Les **17 sources** → « il n'a rien sorti de lui-même, tout est référencé ».

## Limite à dire

> « Les chiffres sont ceux du NGAP **à date** (21/06/2026). Quand la nomenclature bouge,
> on recharge la base — c'est une photo, pas du temps réel. Et lui il **éclaire** la
> cotation, il ne la **pose** pas : la FSE, c'est Doctolib. »

## Relances possibles (le kiné rebondit)

- « Détaille le remboursement d'un BDK jusqu'au reste à charge. »
- « Liste des actes cotables en AMK avec leurs coefficients. »
- « Qu'est-ce qui a changé depuis 2024 ? » (AMS/AMC supprimés).
