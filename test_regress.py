"""
Test de regression du filtre "Zero donnee patient".

Rejoue les 4 correctifs apportes a _filtre_zero_donnee.py + les 3 cas valides
en UI. Objectif : empecher toute regression si le filtre est modifie.

Lancement :  python3 test_regress.py
Sortie :     code 0 si tout passe, 1 sinon (avec le detail des echecs).
"""

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "filtre", os.path.join(HERE, "_filtre_zero_donnee.py")
)
filtre = importlib.util.module_from_spec(spec)
spec.loader.exec_module(filtre)

_scrub = filtre._scrub
_has = filtre._has_patient_data

FAILS = []


def check(label, cond):
    if not cond:
        FAILS.append(label)
        print(f"  [ECHEC] {label}")
    else:
        print(f"  [ok]    {label}")


def user(text):
    return [{"role": "user", "content": text}]


# --- FIX 1 : le declencheur ne doit PAS reagir aux dates/ages de referentiel --
print("FIX 1 - declencheur (faux-positifs)")
check("date officielle ne declenche pas",
      _has(user("Loi du 19/05/2023, nb de seances ?")) is False)
check("date mois=10 ne declenche pas",
      _has(user("Arrete du 05/10/2026, taux ?")) is False)
check("age de referentiel ne declenche pas",
      _has(user("A partir de 65 ans, quel accord ?")) is False)
check("civilite+nom declenche",
      _has(user("CR pour M. Jean Dupont")) is True)
check("EVA declenche",
      _has(user("CR EVA 7/10")) is True)
check("taille declenche",
      _has(user("patient 1m75")) is True)
check("etiquette nom: declenche",
      _has(user("nom: Durand")) is True)
check("dernier message seulement (pas de nom)",
      _has([{"role": "user", "content": "CR pour M. Dupont"},
            {"role": "assistant", "content": "..."},
            {"role": "user", "content": "et le taux de remboursement ?"}]) is False)

# --- FIX 5 : intention de redaction declenche (sans donnee patient codable) ---
print("FIX 5 - intention de redaction")
check("CR sans nom declenche",
      _has(user("Redige un CR pour la seance du 12/03/2026")) is True)
check("courrier sans nom declenche",
      _has(user("Prepare un courrier au medecin traitant")) is True)
check("compte-rendu declenche",
      _has(user("Fais un compte-rendu de fin de soins")) is True)
check("calcul (pas de doc) NE declenche PAS",
      _has(user("Fais-moi un calcul pour une seance a 16,89 EUR")) is False)
check("question taux NE declenche PAS",
      _has(user("Quel est le taux de remboursement ?")) is False)

# --- FIX 2 : fuite d'annee (le score NN/MM ne doit pas hacher 12/03) ---------
print("FIX 2 - fuite d'annee")
out = _scrub("Seance du 12/03/2026, 24 seances.", aggressive=True)
check("date complete entierement masquee", "/2026" not in out and "12/03" not in out)
check("aucune fuite d'annee residuelle", "2026" not in out)

# --- FIX 3 : motif EVA ne doit pas mordre le mois d'une date -----------------
print("FIX 3 - EVA vs date")
out = _scrub("ARrete du 05/10/2026 en vigueur.", aggressive=False)
check("date survit en non-agressif", "05/10/2026" in out)
out = _scrub("EVA evalue a 7/10.", aggressive=True)
check("EVA masque en agressif", "7/10" not in out)

# --- FIX 4 : date en toutes lettres masquee en mode agressif -----------------
print("FIX 4 - date en toutes lettres")
out = _scrub("Fin des soins le 12 mars 2026.", aggressive=True)
check("date en lettres masquee", "12 mars" not in out and "2026" not in out)
out = _scrub("Loi du 19 mai 2023.", aggressive=False)
check("date en lettres survit en non-agressif", "19 mai 2023" in out)

# --- Cas UI 1 : question remboursement => tout le referentiel en dur ---------
print("Cas UI 1 - remboursement (non-agressif, chiffres conserves)")
q = user("Quel taux de remboursement et quelle franchise ?")
check("remboursement = non-agressif", _has(q) is False)
txt = ("Taux 60 %, ticket 40 %, FSV 80 %, Alsace 90 %, ALD 100 %. "
       "Franchise 1 EUR, plafond 4 EUR / jour, 50 EUR / an. "
       "Seance 16,58 EUR -> 9,95 EUR -> AM verse 8,95 EUR.")
scrubbed = _scrub(txt, aggressive=False)
for keep in ["60 %", "40 %", "80 %", "90 %", "100 %", "50"]:
    check(f"'{keep}' conserve", keep in scrubbed)

# --- Cas UI 2 : courrier avec donnees patient => tout masque -----------------
print("Cas UI 2 - courrier (agressif, tout masque)")
q = user("Redige un courrier pour M. Jean Dupont, 45 ans, seance du 12/03/2026, "
         "EVA 7/10, amplitude 28/52.")
check("courrier = agressif", _has(q) is True)
courrier = ("Patient M. Jean Dupont, 45 ans, seance du 12/03/2026, "
            "EVA 7/10, amplitude 28/52.")
scrubbed = _scrub(courrier, aggressive=True)
for gone in ["Dupont", "45 ans", "12/03/2026", "7/10", "28/52", "2026"]:
    check(f"'{gone}' masque", gone not in scrubbed)

# --- Cas UI 3 : question citant une date officielle => non-agressif -----------
print("Cas UI 3 - question citant une date de loi")
q = user("Depuis la loi du 19/05/2023, combien de seances en acces direct ?")
check("question = non-agressif", _has(q) is False)
scrubbed = _scrub("Loi du 19/05/2023 : 8 seances sur 3 mois.", aggressive=False)
check("date de loi conservee", "19/05/2023" in scrubbed)
check("8 seances conserve", "8 seances" in scrubbed)

# --- Cas UI 4 : duree de referentiel en annees (DPC) => conservee ------------
print("Cas UI 4 - duree referentiel en annees (DPC)")
q = user("Le DPC est-il obligatoire ?")
check("question DPC = non-agressif", _has(q) is False)
scrubbed = _scrub("Obligatoire par cycle de 3 ans, au moins 1 action par an.",
                  aggressive=False)
check("cycle 3 ans conserve", "3 ans" in scrubbed)
check("age patient masque en agressif",
      "45 ans" not in _scrub("Patient age de 45 ans.", aggressive=True))

# --- Protection des champs [ ... ] (jamais touches) --------------------------
print("Protection des champs [ ... ]")
scrubbed = _scrub("Patient [A COMPLETER], EVA [A COMPLETER], pathologie [preciser].",
                  aggressive=True)
check("champs [ ... ] preserves", "[A COMPLETER]" in scrubbed and "[preciser]" in scrubbed)

print()
if FAILS:
    print(f"{len(FAILS)} ECHEC(S) :")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
print("TOUS LES TESTS PASSENT.")
sys.exit(0)
