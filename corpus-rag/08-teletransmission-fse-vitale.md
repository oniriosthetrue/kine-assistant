# Télétransmission des feuilles de soins (VITALE / SCOR)

Cadre : télétransmission obligatoire des **feuilles de soins électroniques (FSE)** via le
**CVS** (Compte Rendu Régulé) et le protocole **SCOR**, avec la carte **VITALE**. Sources :
ameli.fr (professionnels de santé), GIE SESAM-Vitale.

## Principe

- Le kiné libéral conventionné doit **télétransmettre** les feuilles de soins à la CPAM
  (et, le cas échéant, à la complémentaire via **téléséisme**/NOEMIE).
- La **FSE** est lue à partir de la **carte Vitale** du patient (tiers payant) : le kiné
  n'a pas à ressaisir l'identité ni le numéro de sécurité sociale.
- Le **CVS** (Compte Rendu Régulé) est le flux normalisé envoyé à l'Assurance Maladie.

## Matériel et logiciel

- **Lecteur de cartes Vitale** (ex. Lecteur CP2000 ou équivalent) + **carte CPS** du
  professionnel (Certificat de Professionnel de Santé) pour signer les flux.
- **Logiciel de facturation** agréé (respectant la norme **SCOR**) : génère la FSE, gère
  le téléversement, les rejets et les retours de la CPAM.
- La **signature électronique** (certificat **CPS**) authentifie chaque envoi.

## Tiers payant et télétransmission

- Le kiné applique le **tiers payant** : le patient ne paie que la **participation
  forfaitaire** de **1 €** par acte (non remboursable) et l'éventuel dépassement.
- La télétransmission déclenche le **remboursement** direct du kiné par la CPAM (et la
  complémentaire si télétransmission NOEMIE).
- **Délai** : la FSE doit être télétransmise dans un délai raisonnable après la séance
  (règle usuelle : sans retard, en pratique sous quelques jours).

## Rejets courants

- Carte Vitale non à jour / droits fermés → patient renvoyé vers sa CPAM.
- Absence d'**accord préalable** quand il est requis → rejet (voir accords préalables).
- Code NGAP erroné ou non télétransmissible → rejet à corriger.

## À retenir pour l'assistant

- « Comment je transmets mes feuilles ? » → **Télétransmission FSE via lecteur Vitale +
  logiciel SCOR + carte CPS**, obligatoire pour un kiné conventionné.
- « Le patient paie-t-il ? » → **Tiers payant** : il ne règle que la **participation
  forfaitaire** (et dépassement éventuel).
- Ne jamais inventer un montant de participation forfaitaire : le vérifier (ameli).
