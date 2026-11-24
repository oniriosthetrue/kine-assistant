#!/usr/bin/env python3
"""
Phase 1 - Recuperation des sources FR pour KB2 (Physiologie & Reeducation).

Source : Wikipédia FR via l'API "extracts" (texte brut propre, sans chrome,
licence CC-BY-SA 4.0). Ces fiches servent a la fois de contenu KB2 ET de
referentiel terminologique (glossaire FR canonique) pour la traduction FR
des sources anglaises (OpenStax A&P).

Usage :
    PY=/home/linus/mcp/docling/.venv/bin/python
    $PY _fetch_fr.py            # recupere tout
    $PY _fetch_fr.py --list     # affiche juste la liste des titres
Sortie : kb2/sources-fr/<slug>.md  (un fichier par article, en-tete + texte)
"""
import json
import os
import re
import sys
import time
import urllib.parse

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sources-fr")
API = "https://fr.wikipedia.org/w/api.php"

# Articles Wikipédia FR pertinents pour un assistant kinésithérapeute.
# Organises par theme. Le "titre" doit correspondre a l'intitule exact FR
# (l'API suit les redirects, donc les variantes sont tolerees).
TOPICS = {
    "physiologie": [
        "Muscle squelettique",
        "Contraction musculaire",
        "Système musculaire",
        "Unité motrice",
        "Fuseau neuromusculaire",
        "Organe tendineux de Golgi",
        "Proprioception",
        "Tendon",
        "Ligament",
        "Articulation",
        "Os",
        "Tissu osseux",
        "Système nerveux",
        "Système nerveux périphérique",
        "Nerf",
        "Système cardiovasculaire",
        "Cœur",
        "Débit cardiaque",
        "Système respiratoire",
        "Courbature",
        "Amyotrophie",
        "Hypertrophie musculaire",
        "Fibre musculaire",
        "Métabolisme anaérobie",
    ],
    "pathologies-rachis": [
        "Lombalgie",
        "Lombosciatique",
        "Hernie discale",
        "Sciatique",
        "Cruralgie",
        "Scoliose",
        "Spondylarthrite ankylosante",
        "Canal lombaire étroit",
    ],
    "pathologies-orthopedie": [
        "Entorse",
        "Entorse de la cheville",
        "Ligament croisé antérieur",
        "Coiffe des rotateurs",
        "Tendinopathie",
        "Tendinite",
        "Périarthrite scapulohumérale",
        "Épicondylite",
        "Canal carpien",
        "Arthrose",
        "Prothèse totale de hanche",
        "Prothèse du genou",
        "Ostéoporose",
        "Fracture",
        "Tendon calcanéen",
        "Épicondylite latérale",
        "Doigt à ressaut",
    ],
    "pathologies-neuro": [
        "Accident vasculaire cérébral",
        "Sclérose en plaques",
        "Maladie de Parkinson",
        "Paralysie cérébrale",
        "Myasthénie",
        "Syndrome de Guillain-Barré",
    ],
    "reeducation": [
        "Kinésithérapie",
        "Rééducation",
        "Massage",
        "Électrothérapie",
        "Ondes de choc",
        "Balnéothérapie",
        "Appareillage",
        "Prothèse",
        "Amputation",
        "Déambulateur",
        "Échelle d'évaluation de la douleur",
        "Musculation",
        "Étirement",
    ],
    "cardio-respiratoire": [
        "Insuffisance cardiaque",
        "Bronchopneumopathie chronique obstructive",
        "Asthme",
        "Essoufflement",
        "Réadaptation cardiaque",
        "Test d'effort",
        "Tension artérielle",
        "Fréquence cardiaque",
        "Insuffisance respiratoire",
        "Atelectasie",
        "Kinésithérapie respiratoire",
        "Diaphragme",
        "Ventilation",
        "Oxygénothérapie",
        "Tabagisme",
    ],
    "rhumatologie": [
        "Polyarthrite rhumatoïde",
        "Arthrite",
        "Goutte (maladie)",
        "Fibromyalgie",
        "Rhumatisme",
        "Cervicalgie",
        "Torticolis",
        "Bursite",
        "Fasciite plantaire",
        "Hallux valgus",
        "Pied plat",
        "Arthrose cervicale",
        "Arthropathie",
    ],
    "neuro-complement": [
        "Neuropathie périphérique",
        "Neuropathie diabétique",
        "Syndrome du défilé thoracobrachial",
        "Paraplégie",
        "Tétraplégie",
        "Ataxie",
        "Vertige",
        "Dystonie",
        "Vertige paroxystique positionnel bénin",
        "Dystrophie musculaire",
        "Sclérose latérale amyotrophique",
        "Myopathie",
        "Paralysie faciale",
        "Nerf sciatique",
        "Nerf médian",
        "Neurone",
        "Moelle épinière",
        "Cervelet",
        "Système vestibulaire",
        "Réflexe myotatique",
    ],
    "geriatrie": [
        "Chute (traumatologie)",
        "Sarcopénie",
        "Dénutrition",
        "Maladie d'Alzheimer",
        "Équilibre",
        "Syndrome de fragilité",
        "Gérontologie",
    ],
    "pediatrie": [
        "Torticolis congénital",
        "Pied bot",
        "Dysplasie de la hanche",
        "Maladie de Legg-Calvé-Perthes",
        "Enfant prématuré",
    ],
    "medecine-sport": [
        "Claquage musculaire",
        "Contusion",
        "Élongation musculaire",
        "Syndrome fémoro-patellaire",
        "Rééducation d'un ligament croisé antérieur opéré",
        "Commotion cérébrale",
        "Tendinopathie patellaire",
        "Syndrome de l'essuie-glace",
        "Syndrome de la bandelette ilio-tibiale",
        "Échauffement",
        "Exercice de récupération",
    ],
    "douleur": [
        "Douleur chronique",
        "Douleur neuropathique",
        "Nocicepteur",
        "Syndrome douloureux régional complexe",
        "Antalgique",
        "Stimulation musculaire électrique",
        "Membre fantôme",
    ],
    "lymphatique-oedeme": [
        "Système lymphatique",
        "Lymphœdème",
        "Drainage lymphatique manuel",
        "Bandage",
    ],
    "techniques-reeducation": [
        "Cryothérapie",
        "Thermothérapie",
        "Ultrasonothérapie",
        "Tapis de marche",
        "Posture",
        "Marche",
        "Locomotion",
        "Semelle orthopédique",
        "Orthèse",
        "Attelle",
        "Canne (marche)",
        "Béquilles",
        "Fauteuil roulant",
        "Kinésithérapie",
        "Gainage",
    ],
    "anatomie-complement": [
        "Colonne vertébrale",
        "Vertèbre",
        "Disque intervertébral",
        "Bassin (anatomie)",
        "Épaule",
        "Genou",
        "Cheville",
        "Hanche",
        "Poignet",
        "Main",
        "Pied",
        "Muscle",
        "Myocarde",
        "Synapse",
        "Fascia",
        "Aponévrose",
        "Bourse séreuse",
        "Cartilage",
        "Cartilage articulaire",
        "Ménisque",
        "Péroné",
        "Tibia",
        "Fémur",
        "Humérus",
        "Radius",
        "Cubitus",
        "Clavicule",
        "Scapula",
        "Sternum",
        "Côte (os)",
        "Crâne",
        "Rachis cervical",
        "Rachis lombaire",
        "Rachis thoracique",
        "Articulation sacro-iliaque",
    ],
}


def fetch_extract(title: str) -> tuple[str, str] | None:
    """Retourne (titre_normalise, texte_brut) ou None si introuvable.

    Gere le 429 (rate-limit Wikipedia) par backoff exponentiel.
    """
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "exsectionformat": "wiki",  # conserve les titres de section == X ==
        "format": "json",
        "redirects": 1,
        "titles": title,
    }
    backoff = 2.0
    for attempt in range(6):
        r = requests.get(API, params=params, timeout=30,
                         headers={"User-Agent": "kine-assistant-rag/1.0 (projet MinervIA)"})
        if r.status_code == 429:
            wait = float(r.headers.get("Retry-After", backoff))
            time.sleep(wait)
            backoff = min(backoff * 2, 60)
            continue
        break
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    for page in pages.values():
        if "extract" in page and page.get("title") != title or "extract" in page:
            text = page["extract"].strip()
            if len(text) < 200:  # ebauche / redirect vide
                return None
            return page["title"], text
    return None


def slugify(title: str) -> str:
    s = title.lower()
    s = s.replace("œ", "oe").replace("æ", "ae")
    s = re.sub(r"[àáâãä]", "a", s)
    s = re.sub(r"[èéêë]", "e", s)
    s = re.sub(r"[ìíîï]", "i", s)
    s = re.sub(r"[òóôõö]", "o", s)
    s = re.sub(r"[ùúûü]", "u", s)
    s = re.sub(r"[ÿý]", "y", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:60]


def wiki_to_md(text: str) -> str:
    """Convertit les titres de section wiki (== X ==) en markdown (## X).

    Le niveau wiki == correspond a H2 (le titre d'article est le H1),
    === -> H3, ==== -> H4. Exploite par le markdown_header_text_splitter
    d'Open WebUI pour aligner les frontieres de chunk sur les concepts.
    """
    def repl(m: re.Match) -> str:
        level = len(m.group(1))  # nb de = d'un cote
        title = m.group(2).strip()
        return "#" * min(level, 4) + " " + title

    return re.sub(r"(?m)^(=+)\s*(.+?)\s*\1\s*$", repl, text)


def clean_text(text: str) -> str:
    """Nettoie le texte brut Wikipédia pour le RAG."""
    # convertit les titres de section wiki en markdown (restaure la hierarchie)
    text = wiki_to_md(text)
    # supprime les references [1], [Note 2]...
    text = re.sub(r"\[(?:\d+|Note \d+|source needed|réf\. souhaitée)\]", "", text)
    # normalise les espaces
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> None:
    if "--list" in sys.argv:
        for theme, titles in TOPICS.items():
            print(f"\n[{theme}]")
            for t in titles:
                print("  -", t)
        return

    os.makedirs(OUT, exist_ok=True)
    total = sum(len(v) for v in TOPICS.values())
    done = ok = miss = skip = 0
    for theme, titles in TOPICS.items():
        for title in titles:
            done += 1
            # reprise : ignorer si deja present
            pre = os.path.join(OUT, f"{slugify(title)}.md")
            if os.path.exists(pre):
                skip += 1
                continue
            try:
                res = fetch_extract(title)
            except Exception as exc:  # noqa: BLE001
                print(f"[{done}/{total}] ERREUR {title!r}: {exc}")
                miss += 1
                continue
            if res is None:
                print(f"[{done}/{total}] MANQUE {title!r}")
                miss += 1
                time.sleep(0.3)
                continue
            norm, text = res
            text = clean_text(text)
            slug = slugify(norm)
            path = os.path.join(OUT, f"{slug}.md")
            header = (
                f"# {norm}\n\n"
                f"> Source : Wikipédia FR (article « {norm} »), licence CC-BY-SA 4.0.\n"
                f"> Thème : {theme}. Fiche de référence physiologie/rééducation.\n\n"
            )
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(header + text + "\n")
            ok += 1
            print(f"[{done}/{total}] OK {norm!r} -> {slug}.md ({len(text)} car.)")
            time.sleep(1.5)  # politesse API (eviter 429)
    print(f"\nTermine : {ok} nouvelles, {skip} deja presentes, {miss} manquantes -> {OUT}")


if __name__ == "__main__":
    main()
