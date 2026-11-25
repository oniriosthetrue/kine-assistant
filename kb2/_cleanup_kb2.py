#!/usr/bin/env python3
"""Nettoyage KB2 : supprime doublons + fichiers en trop, rapporte les manquants.

Lit /tmp/kb2_idname.tsv (id<TAB>filename, 1 par ligne) et /tmp/expected.txt
(noms attendus = contenu de _all_split). Pour chaque nom attendu, garde 1 id et
supprime les extras. Supprime tout id dont le nom n'est PAS attendu. Affiche les
noms attendus sans aucun id (manquants) dans /tmp/to_reupload.txt.
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


def delete(fid):
    sh(f'docker exec {CONTAINER} sh -c \'curl -s -X DELETE '
       f'"{BASE}/knowledge/{KB2}/file/{fid}" -H "Authorization: Bearer {ADMIN}"\'')


def main() -> None:
    expected = {l.strip() for l in open("/tmp/expected.txt") if l.strip()}
    rows = []
    for line in open("/tmp/kb2_idname.tsv"):
        line = line.rstrip("\n")
        if "\t" not in line:
            continue
        fid, name = line.split("\t", 1)
        rows.append((fid, name))

    seen = {}
    to_delete = []
    for fid, name in rows:
        if name not in expected:
            to_delete.append((fid, name, "EXTRA"))
        elif name in seen:
            to_delete.append((fid, name, "DUP"))
        else:
            seen[name] = fid

    have = set(seen)
    missing = sorted(expected - have)

    dry = "--apply" not in sys.argv
    print(f"attendus={len(expected)}  presents_uniques={len(have)}  "
          f"a_supprimer={len(to_delete)}  manquants={len(missing)}")
    n_extra = sum(1 for _, _, r in to_delete if r == "EXTRA")
    n_dup = sum(1 for _, _, r in to_delete if r == "DUP")
    print(f"  extras={n_extra}  doublons={n_dup}")

    open("/tmp/to_reupload.txt", "w").write("\n".join(missing) + "\n")
    print("manquants ecrits dans /tmp/to_reupload.txt")

    if dry:
        print("DRY-RUN (relancer avec --apply pour supprimer)")
        return

    for fid, name, reason in to_delete:
        delete(fid)
    print(f"supprimes: {len(to_delete)}")


if __name__ == "__main__":
    main()
