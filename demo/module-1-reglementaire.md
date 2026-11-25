# Module 1 — Règlementaire NGAP expliqué

**Ce qu'on démontre** : l'assistant répond aux questions de cotation avec le **vrai
tarif/taux sourcé du NGAP ameli**, pas une réponse vague. C'est le gap n°1 vs Doctolib
(Doctolib émet la FSE, mais n'explique **pas** pourquoi telle cotation).

## Prompt à taper (copier-coller)

```
Un patient a une AMK et une AMT sur la même séance. C'est quoi la différence de
cotation et de remboursement ? Et l'accès direct, ça marche pour quelles pathologies ?
```

## Ce qu'on dit au kiné (pendant les ~30-40 s)

> « Là il va chercher dans le NGAP officiel. Regarde, il va te mettre la source en face. »

Pointer les **« Sources »** qui s'affichent (fichiers `01-ngap…`, `02-…` de KB1).

## Résultat validé (réponse réelle de la démo)

- Définit **AMK** (acte de rééducation motrice ou kinésithérapique de groupe/complexe)
  vs **AMT** (technique nouvelle à part entière), avec les **chiffres de cotation** exacts.
- Rappel : sur une même séance, les règles de cumul / non-cumul.
- **Accès direct** : liste les cas où le kiné peut traiter sans ordonnance (pathologies
  concernées), avec la source ameli.
- Chaque chiffre est **accompagné d'un lien « View source »** vers le fichier du NGAP.

## Ce qu'on pointe à l'écran

- Le **montant/taux exact** (pas « environ », pas « ça dépend »).
- Le **bouton source** cliquable → « ça vient du NGAP, je peux te montrer la page d'où c'est tiré ».

## Limite à dire

> « Les chiffres sont ceux du NGAP **à date** (21/06/2026). Quand la nomenclature bouge,
> on recharge la base — c'est une photo, pas du temps réel. Et lui il **éclaire** la
> cotation, il ne la **pose** pas : la FSE, c'est Doctolib. »
