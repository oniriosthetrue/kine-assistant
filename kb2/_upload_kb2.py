#!/usr/bin/env python3
"""
Uploade tous les .md d'un dossier vers une base de connaissances Open WebUI.

Motif repris de _upload_05.py : docker cp -> POST /files/ (multipart) ->
file_id -> POST /knowledge/{KB}/file/add. Reprenable : saute les fichiers
deja presents dans la KB (comparaison par nom).

Usage :
    PY=/home/linus/mcp/docling/.venv/bin/python
    $PY _upload_kb2.py sources-fr
    $PY _upload_kb2.py _out/fr
"""
import json
import os
import subprocess
import sys

KB2 = "e68519ab-dece-4221-901c-4c6b58010997"
ADMIN = open("/tmp/owui_admin_token.txt").read().strip()
BASE = "http://localhost:8080/api/v1"
CONTAINER = "open-webui"
HERE = os.path.dirname(os.path.abspath(__file__))


def sh(c):
    return subprocess.run(c, shell=True, capture_output=True, text=True).stdout


def existing_files():
    lst = sh(f'docker exec {CONTAINER} sh -c \'curl -s "{BASE}/knowledge/{KB2}/files" '
             f'-H "Authorization: Bearer {ADMIN}"\'')
    try:
        data = json.loads(lst)
    except Exception:
        return set()
    items = data.get("items") or data.get("data") or []
    return {it.get("filename") or it.get("name") for it in items}


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: _upload_kb2.py <dossier>"); sys.exit(1)
    src = os.path.join(HERE, sys.argv[1])
    files = sorted(f for f in os.listdir(src) if f.endswith(".md"))
    have = existing_files()
    print(f"{len(files)} fichiers dans {src}, {len(have)} deja dans la KB2")
    up = add_ok = skip = 0
    for f in files:
        if f in have:
            skip += 1
            continue
        subprocess.run(["docker", "cp", os.path.join(src, f),
                        f"{CONTAINER}:/tmp/{f}"], check=True)
        resp = sh(f'docker exec {CONTAINER} sh -c \'curl -s -X POST "{BASE}/files/" '
                  f'-H "Authorization: Bearer {ADMIN}" -F "file=@/tmp/{f}"\'')
        try:
            fid = json.loads(resp)["id"]
        except Exception:
            print(f"UPLOAD FAIL {f}: {resp[:200]}"); continue
        up += 1
        open("/tmp/_add_body.json", "w").write(json.dumps({"file_id": fid}))
        subprocess.run(["docker", "cp", "/tmp/_add_body.json",
                        f"{CONTAINER}:/tmp/_add_body.json"], check=True)
        r = sh(f'docker exec {CONTAINER} sh -c \'curl -s -X POST '
               f'"{BASE}/knowledge/{KB2}/file/add" -H "Authorization: Bearer {ADMIN}" '
               f'-H "Content-Type: application/json" --data-binary @/tmp/_add_body.json\'')
        ok = "error" not in r.lower()
        add_ok += ok
        if not ok:
            print(f"ADD FAIL {f}: {r[:200]}")
    print(f"\nuploades={up} ajoutes={add_ok} ignores={skip}")
    print(f"total dans KB2 = {len(existing_files())}")


if __name__ == "__main__":
    main()
