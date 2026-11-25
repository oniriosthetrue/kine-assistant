#!/usr/bin/env python3
"""Genere ~100 requetes de retrieval avec ground truth.

Pour chaque fichier de _all_split (echantillon), extrait une phrase distinctive
du CORPS (jamais le titre / les en-tetes) -> la requete. Ground truth = nom du
fichier source. Ecrit /tmp/bench_queries.json (liste de {query, expected}).
"""
import os, re, json, random

SRC = "/home/linus/communication/kiné/kb2/_all_split"
OUT = "/tmp/bench_queries.json"
N = 100
random.seed(42)

def clean_phrase(s):
    s = re.sub(r"\[\[.*?\]\]", "", s)        # liens wiki
    s = re.sub(r"\[.*?\]\(.*?\)", "", s)      # liens md
    s = re.sub(r"[|*_`>#]", "", s)            # markdown
    s = re.sub(r"\s+", " ", s).strip()
    return s

def pick_sentence(text):
    """Cherche une phrase informative du corps (60-220 car.), ni titre ni liste."""
    lines = text.splitlines()
    # ignorer les lignes d'en-tete / meta
    body = []
    for ln in lines:
        t = ln.strip()
        if not t: continue
        if t.startswith("#"): continue
        if t.startswith("<!--"): continue
        if t.startswith("|"): continue          # tableaux
        if t.startswith("-") or t.startswith("*"): continue  # listes
        if re.match(r"^\d+\.", t): continue
        body.append(t)
    # decouper en phrases
    sents = []
    for ln in body:
        for sp in re.split(r"(?<=[.!?])\s+", ln):
            c = clean_phrase(sp)
            if 60 <= len(c) <= 220 and sum(ch.isalpha() for ch in c) > 40:
                sents.append(c)
    if not sents:
        return None
    # preferer une phrase du milieu (plus "contenu" qu'une intro)
    mid = len(sents) // 2
    cand = sents[mid:mid+5] or sents
    return random.choice(cand)

files = sorted(f for f in os.listdir(SRC) if f.endswith(".md"))
random.shuffle(files)

queries = []
for f in files:
    if len(queries) >= N:
        break
    txt = open(os.path.join(SRC, f), encoding="utf-8").read()
    q = pick_sentence(txt)
    if q:
        queries.append({"query": q, "expected": f})

json.dump(queries, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(queries)} requetes -> {OUT}")
for x in queries[:5]:
    print(" -", x["expected"], "::", x["query"][:70])
