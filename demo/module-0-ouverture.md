# Module 0 — La question d'ouverture (le « waouh »)

**À jouer EN PREMIER**, avant le menu. Une vraie question de kiné, multi-sauts, qui
montre d'emblée que l'outil **raisonne** et pas juste « retrouve un texte ». Si ça
accroche le kiné dès la première minute, le reste de l'atelier se vend tout seul.

## Prompt à taper (copier-coller)

```
Un patient en ALD pour diabète vient pour une rééducation de genou. Je le facture à
100 % au titre de l'ALD ? Et si je fais aussi son bilan (BDK) le même jour, est-ce que
je peux cumuler le BDK avec la séance ? Détaille le remboursement jusqu'au reste à charge.
```

> 🔑 Pourquoi elle est forte : elle contient **trois sous-questions imbriquées**
> (ALD = 100 % ? + cumul BDK/séance ? + calcul reste à charge). Un moteur naïf répond
> à côté ou survend le 100 %. **Lui démêle les trois, correctement.**

## Ce qu'on dit au kiné (pendant la génération — c'est LONG, ~1-2 min)

> « Je lui mets une vraie question de cabinet, avec trois questions dans une seule.
> Regarde-le chercher — il va interroger la base plusieurs fois, comme toi tu irais
> vérifier dans le manuel et sur ameli. »

Pointer en direct : **« Exploring query_knowledge_files »** qui s'incrémente
(2 → 3 → 4 requêtes), puis **« 14 Sources »**.

## Résultat validé (réponse réelle de la démo — 4 requêtes, 14 sources)

1. **ALD ≠ tout à 100 %.** L'exonération ne porte **que sur les actes en rapport direct
   avec la pathologie exonérante** (le diabète). Une rééduc de genou **étrangère** au
   diabète se facture au **tarif opposable, remboursé 60 %** (ticket modérateur 40 %),
   comme un non-ALD. Le 100 % ne s'applique que si le genou est une **complication
   directe** du diabète. → *« on raisonne acte par acte / pathologie par pathologie »*.
2. **Cumul BDK + séance : ça dépend de quel « bilan ».**
   - **BDK du traitement** (AMK 10,7 ≈ 23,65 €) : émis **à l'occasion d'une séance** →
     **cumulable** (cas le plus probable).
   - **Bilan isolé de diagnostic** (Chap. I, AMK 5/8,5/10) : facturable **seulement en
     l'absence de traitement** → **NON cumulable** avec une séance le même jour.
3. **Tableau chiffré jusqu'au reste à charge** (hypothèse genou hors ALD, régime 60 %) :

   | Acte | Base | RO 60 % | Ticket 40 % | Franchise | RAC patient |
   |---|---|---|---|---|---|
   | Séance rééduc genou | 16,58 € | 9,95 € | 6,63 € | — | 6,63 € |
   | BDK (AMK 10,7) | 23,65 € | 14,19 € | 9,46 € | — | 9,46 € |
   | **Total journée** | **40,23 €** | **24,14 €** | **16,09 €** | **1 €** | **16,09 € + 1 €** |

   + précision : la complémentaire couvre le ticket modérateur **mais pas la franchise de 1 €**.

## Ce qu'on pointe à l'écran

- Le **raisonnement en 2 temps** (il ne tombe pas dans le piège « ALD = tout gratuit »).
- La **nuance BDK vs bilan isolé** → « il connaît la différence que beaucoup confondent ».
- Le **tableau** → « il te fait le calcul que tu ferais à la main, en 1 minute, sourcé ».

## ⚠️ Point de vigilance pour le live

C'est la réponse la plus **longue** de la démo (**~1-2 min**, 4 requêtes, 14 sources).
**À annoncer** (« là il bosse sérieusement, laisse-le finir ») et à **ne pas lancer en
parallèle** d'un autre module. Si le réseau est lent ce jour-là, avoir le module 1
(question piège AMT, plus rapide) en **roue de secours** pour l'ouverture.

## Limite à dire

> « Il raisonne juste, mais il **éclaire** — il ne pose pas la FSE, et il ne connaît pas
> ton patient. C'est toi qui tranche. Et les chiffres sont du NGAP à date. »
