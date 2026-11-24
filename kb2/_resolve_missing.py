#!/usr/bin/env python3
"""Cherche les vrais noms d'articles FR pour les titres manquants."""
import time

import requests

API = "https://fr.wikipedia.org/w/api.php"
HDR = {"User-Agent": "kine-assistant-rag/1.0 (projet MinervIA)"}

CANDS = {
    "Fatigue musculaire": ["Fatigue (médecine)", "Courbature", "Fatigue musculaire"],
    "Atrophie musculaire": ["Atrophie musculaire", "Amyotrophie", "Fonte musculaire", "Atrophie"],
    "Tendinite de l'épaule": ["Tendinite de l'épaule", "Tendinite", "Coiffe des rotateurs", "Périarthrite scapulo-humérale"],
    "Prothèse totale de genou": ["Prothèse totale de genou", "Prothèse du genou", "Prothèse", "Arthroplastie"],
    "Tendinopathie d'Achille": ["Tendinopathie d'Achille", "Tendinite d'Achille", "Tendon calcanéen", "Tendon d'Achille"],
    "Syndrome de la coiffe des rotateurs": ["Syndrome de la coiffe des rotateurs", "Coiffe des rotateurs", "Conflit sous-acromial"],
    "Lésion médullaire": ["Lésion médullaire", "Lésion de la moelle épinière", "Moelle épinière", "Paraplégie"],
    "Rééducation après prothèse totale de la hanche": ["Rééducation après prothèse totale de la hanche", "Prothèse totale de hanche", "Rééducation"],
    "Échelle d'évaluation": ["Échelle d'évaluation", "Échelle d'évaluation de la douleur", "Échelle visuelle analogique"],
    "Renforcement musculaire": ["Renforcement musculaire", "Musculation", "Entraînement en résistance"],
}


def probe(title):
    backoff = 2.0
    for _ in range(6):
        r = requests.get(API, params={
            "action": "query", "prop": "extracts|info", "explaintext": 1,
            "exintro": 1, "inprop": "url", "redirects": 1, "titles": title,
            "format": "json",
        }, timeout=20, headers=HDR)
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", backoff)))
            backoff = min(backoff * 2, 60)
            continue
        break
    pages = r.json().get("query", {}).get("pages", {})
    for p in pages.values():
        if "missing" in p:
            return None
        return p.get("title"), len(p.get("extract", ""))
    return None


for orig, alts in CANDS.items():
    print(f"\n### {orig}")
    for a in alts:
        res = probe(a)
        if res is None:
            print(f"   [MISSING] {a}")
        else:
            print(f"   [{res[1]:5}] {res[0]}")
        time.sleep(1.5)
