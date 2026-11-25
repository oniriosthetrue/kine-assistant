# Module 2 — Rédaction CR/courriers + filtre « zéro donnée patient »

**LE clou du spectacle.** On montre deux choses d'un coup :
1. l'assistant **rédige** une trame de compte-rendu pro à champs `[...]` à remplir ;
2. le **filtre de sécurité** masque **en direct** toute donnée patient qu'on essaierait de faire entrer.
C'est la **preuve visuelle** de l'angle « cet outil ne demande jamais une info patient ».

## Étape A — la trame à champs (prompt)

```
Rédige une trame de compte-rendu de fin de série pour une rééducation d'épaule post-opératoire,
en laissant des champs entre crochets pour ce que je devrai remplir.
```

**Résultat validé** : trame structurée (motif, bilan, actes, évolution, objectifs) avec
des champs `[...]` — `[DATE]`, `[EVA]/10`, `[NOM du prescripteur]`, etc. Rien de personnel :
juste un gabarit.

> Ce qu'on dit : « Il te prépare le squelette du CR. Tu remplis les crochets. Ça te fait
> gagner les 5 minutes de mise en forme à chaque fois. »

## Étape B — la preuve du filtre (le moment fort)

Taper **exprès** une demande qui contient une donnée patient, pour montrer qu'elle ressort masquée :

```
Rédige un CR pour M. Jean Dupont, 45 ans, vu le 12/03/2026, EVA 7/10 au départ puis 2/10 aujourd'hui.
```

**Résultat validé (réponse réelle)** : dans la réponse **finale**, toute la donnée patient
est devenue `[A COMPLETER]` :

| Saisi | Rendu final |
|---|---|
| `M. Jean Dupont, 45 ans` | `[A COMPLETER], [A COMPLETER]` |
| `12/03/2026` | `[A COMPLETER]` |
| `EVA 7/10 → 2/10` | `EVA [A COMPLETER] → [A COMPLETER]` |

> ⚠️ **Ne JAMAIS juger le filtre pendant la génération.** Le masque s'applique **après**
> la fin de la réponse (« Response complete »). Si on lit pendant le streaming, on voit
> encore le texte en clair → on croirait que le filtre a échoué. **Attendre la fin**, puis montrer.

## Ce qu'on dit au kiné (le moment fort)

> « Regarde ce que je viens de taper : un nom, un âge, une date, un EVA. Et regarde ce qui
> sort : tout est devenu `[A COMPLETER]`. L'outil **refuse** la donnée patient, même si j'essaie
> de la lui donner. C'est pour ça que je peux te dire, sans risque : **je ne suis pas hébergeur
> de données de santé**. On ne peut pas protéger ce qu'on n'a jamais reçu. »

## Limite / honnêteté à dire

> « Ça tient tant que **zéro** donnée n'entre. Le filtre + les conditions, c'est le bouclier.
> Et en déploiement **local**, sur ton PC, la donnée ne sort même pas de chez toi —
> là c'est inattaquable. »
