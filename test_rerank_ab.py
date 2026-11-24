#!/usr/bin/env python3
"""Test A/B reranker sur le corpus kiné.

Embedding seul (cosine) vs Embedding + Rerank 4B.
Metrique : hit@3 (le chunk "gold" est-il dans le top 3, = rag.top_k OWUI).
Lit le corpus, interroge le service embedding (localhost:8001).
"""
import json
import math
import os
import re
import sys
import urllib.request

BASE = "http://localhost:8001"
EMB_MODEL = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL = "Qwen/Qwen3-Reranker-4B"
CORPUS = os.path.join(os.path.dirname(__file__), "corpus-rag")
TOP_K = 3          # = rag.top_k OWUI
RECALL_K = 15      # candidats envoyes au reranker


def post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def embed(texts):
    out = post("/v1/embeddings", {"model": EMB_MODEL, "input": texts})
    return [d["embedding"] for d in out["data"]]


def rerank(query, docs, top_n):
    out = post("/v1/rerank", {"model": RERANK_MODEL, "query": query,
                              "documents": docs, "top_n": top_n})
    return out["results"]  # [{index, relevance_score}]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def chunk_file(path):
    """Decoupe un .md en chunks au niveau des titres ## / ### / ---."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # decoupe sur les frontieres de section
    parts = re.split(r"\n(?=#{2,3} )|\n---\n", text)
    chunks = []
    for p in parts:
        p = p.strip()
        if len(p) >= 80:  # ignore les micro-fragments
            chunks.append(p)
    return chunks


# (question, prefix_fichier_gold)
QUESTIONS = [
    ("J'ai traite 27 seances une prothese totale de genou, est-ce que je peux continuer sans rien demander ?", "05c"),
    ("Une patiente en acces direct sans aucun diagnostic medical, combien de seances max ?", "04c"),
    ("Le forfait deplacement, c'est 2,50 euros ou 4 euros ?", "04c"),
    ("Puis-je facturer AMS pour un bilan ?", "04a"),
    ("Le bilan-diagnostic, a quelle frequence je le facture ?", "04a"),
    ("Cotation d'une reeduc apres ligamentoplastie LCA, accord quand ?", "05c"),
    ("Un supplement balneo, ca se cote comment ?", "04c"),
    ("Je fais 2 territoires le meme jour, je cote 2 actes ?", "04a"),
    ("Renouveler une ordonnance de 8 mois, j'ai le droit ?", "04c"),
    ("Telesoin, meme prix qu'en cabinet ?", "04c"),
    ("Lombalgie : accord des 16 seances, toujours ?", "05c"),
    ("Majoration dimanche, je la mets automatiquement ?", "04c"),
]


def main():
    files = sorted(f for f in os.listdir(CORPUS) if f.endswith(".md"))
    chunks, meta = [], []
    for fn in files:
        for c in chunk_file(os.path.join(CORPUS, fn)):
            chunks.append(c)
            meta.append(fn)
    print(f"Corpus : {len(files)} fichiers -> {len(chunks)} chunks\n")

    print("Embedding des chunks...", flush=True)
    chunk_vecs = embed(chunks)

    emb_hits = 0
    rer_hits = 0
    rows = []
    for q, gold in QUESTIONS:
        qv = embed([q])[0]
        scores = [(i, cosine(qv, chunk_vecs[i])) for i in range(len(chunks))]
        scores.sort(key=lambda x: -x[1])
        # --- Embedding seul : top_k ---
        emb_top = [i for i, _ in scores[:TOP_K]]
        emb_ok = any(meta[i].startswith(gold) for i in emb_top)
        emb_hits += emb_ok
        # --- Rerank sur les RECALL_K meilleurs candidats ---
        cand = [i for i, _ in scores[:RECALL_K]]
        rr = rerank(q, [chunks[i] for i in cand], TOP_K)
        rer_top = [cand[r["index"]] for r in rr]
        rer_ok = any(meta[i].startswith(gold) for i in rer_top)
        rer_hits += rer_ok
        rows.append((q, gold, emb_ok, rer_ok,
                     meta[emb_top[0]], meta[rer_top[0]]))

    print(f"{'Q':<58} {'gold':<5} {'EMB':<4} {'RER':<4}")
    print("-" * 82)
    for q, gold, e, r, emeta, rmeta in rows:
        qq = (q[:55] + "...") if len(q) > 58 else q
        print(f"{qq:<58} {gold:<5} {'OK' if e else 'KO':<4} {'OK' if r else 'KO':<4}"
              f"   emb->{emeta[:18]:<18} rer->{rmeta[:18]}")
    n = len(QUESTIONS)
    print("-" * 82)
    print(f"hit@{TOP_K}  embedding seul : {emb_hits}/{n} = {emb_hits/n:.0%}")
    print(f"hit@{TOP_K}  + rerank 4B    : {rer_hits}/{n} = {rer_hits/n:.0%}")
    delta = rer_hits - emb_hits
    print(f"delta : {delta:+d} question(s)")


if __name__ == "__main__":
    main()
