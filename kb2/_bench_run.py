#!/usr/bin/env python3
"""Runner du benchmark de retrieval KB2.

Pour chaque requete (/tmp/bench_queries.json), interroge Open WebUI
POST /retrieval/query/collection (via docker exec curl), recupere les noms des
fichiers retournes, et calcule le rang du fichier attendu.

Metriques : hit@1, hit@3, hit@5, MRR (strict = nom exact du fichier attendu),
plus hit@5 "same-doc" (une autre part du meme document compte comme succes
semantique).
"""
import json, subprocess, sys, time

KB = "e68519ab-dece-4221-901c-4c6b58010997"
TOK = open("/tmp/owui_admin_token.txt").read().strip()
QUERIES = json.load(open("/tmp/bench_queries.json", encoding="utf-8"))
K = 10
OUT = "/tmp/bench_results.json"

def base(name):
    # enleve .md puis tout suffixe __partN / __kbN -> nom du document logique
    n = name[:-3] if name.endswith(".md") else name
    n = n.split("__part")[0]
    n = n.split("__kb")[0]
    return n

def retrieve(query):
    payload = json.dumps({"query": query, "collection_names": [KB], "k": K, "hybrid": False})
    cmd = ["docker", "exec", "open-webui", "sh", "-c",
           f"curl -s -X POST 'http://localhost:8080/api/v1/retrieval/query/collection' "
           f"-H 'Authorization: Bearer {TOK}' -H 'Content-Type: application/json' "
           f"--data-binary @/tmp/_bench_body.json"]
    # ecrire le body dans le conteneur
    open("/tmp/_bench_body.json", "w", encoding="utf-8").write(payload)
    subprocess.run(["docker", "cp", "/tmp/_bench_body.json", "open-webui:/tmp/_bench_body.json"],
                   check=True, capture_output=True)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    try:
        d = json.loads(r.stdout)
    except Exception:
        return None
    metas = d.get("metadatas") or [[]]
    names = [m.get("name") for m in metas[0] if m.get("name")]
    return names

results = []
t0 = time.time()
for i, item in enumerate(QUERIES, 1):
    q, exp = item["query"], item["expected"]
    names = None
    for attempt in range(3):
        try:
            names = retrieve(q)
            if names is not None:
                break
        except Exception as e:
            pass
        time.sleep(2)
    if names is None:
        names = []
    # rang strict (nom exact)
    rank = 0
    for j, n in enumerate(names, 1):
        if n == exp:
            rank = j
            break
    # rang "same-doc" (autre part du meme document)
    rank_doc = 0
    eb = base(exp)
    for j, n in enumerate(names, 1):
        if base(n) == eb:
            rank_doc = j
            break
    results.append({"query": q, "expected": exp, "top": names[:K],
                    "rank": rank, "rank_doc": rank_doc})
    if i % 10 == 0:
        print(f"  {i}/{len(QUERIES)}  ({time.time()-t0:.0f}s)", flush=True)

json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# --- scoring ---
n = len(results)
def hit_at(k, key):
    return sum(1 for r in results if 0 < r[key] <= k)
mrr = sum(1.0 / r["rank"] for r in results if r["rank"] > 0) / n
mrr_doc = sum(1.0 / r["rank_doc"] for r in results if r["rank_doc"] > 0) / n

print("\n================ BENCHMARK RETRIEVAL KB2 ================")
print(f"Requetes evaluees        : {n}")
print(f"Temps total              : {time.time()-t0:.0f}s")
print(f"--- STRICT (nom de fichier exact) ---")
print(f"Hit@1                    : {hit_at(1,'rank')/n:.1%}  ({hit_at(1,'rank')}/{n})")
print(f"Hit@3                    : {hit_at(3,'rank')/n:.1%}  ({hit_at(3,'rank')}/{n})")
print(f"Hit@5                    : {hit_at(5,'rank')/n:.1%}  ({hit_at(5,'rank')}/{n})")
print(f"Hit@10                   : {hit_at(10,'rank')/n:.1%}  ({hit_at(10,'rank')}/{n})")
print(f"MRR                      : {mrr:.3f}")
print(f"--- SEMANTIQUE (autre part du meme document = succes) ---")
print(f"Hit@1 (doc)              : {hit_at(1,'rank_doc')/n:.1%}")
print(f"Hit@3 (doc)              : {hit_at(3,'rank_doc')/n:.1%}")
print(f"Hit@5 (doc)              : {hit_at(5,'rank_doc')/n:.1%}")
print(f"MRR (doc)                : {mrr_doc:.3f}")
miss = [r for r in results if r["rank_doc"] == 0]
print(f"\nRequetes sans AUCUN résultat du bon document : {len(miss)}")
for r in miss[:15]:
    print(f"  ATTENDU {r['expected']}  |  recu: {r['top'][:3]}")
