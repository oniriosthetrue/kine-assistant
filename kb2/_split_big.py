#!/usr/bin/env python3
"""Decoupe les gros .md en parties < MAX car. aux frontieres de paragraphes.

Les gros fichiers font resetter l'appel d'embedding d'Open WebUI (batch trop
grand). On les scinde en plusieurs fiches pour rester sous le seuil. Le contenu
est preserve a l'identique, seule la granularite change.

Usage :
    PY=/home/linus/mcp/docling/.venv/bin/python
    $PY _split_big.py <dossier_in> <dossier_out> [MAX=18000]
"""
import os
import re
import sys

MAX = 18000


def split_file(path: str, outdir: str, maxc: int) -> int:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    base = os.path.splitext(os.path.basename(path))[0]
    if len(text) <= maxc:
        with open(os.path.join(outdir, os.path.basename(path)), "w", encoding="utf-8") as fh:
            fh.write(text)
        return 1
    # extrait l'eventuel en-tete (titre + citation >) pour la reproduire
    lines = text.split("\n")
    header = []
    i = 0
    while i < len(lines) and (lines[i].startswith("#") or lines[i].startswith(">") or lines[i] == ""):
        header.append(lines[i]); i += 1
    header_txt = "\n".join(header).strip()
    body = "\n".join(lines[i:])
    paras = body.split("\n\n")
    parts, cur = [], ""
    for p in paras:
        if len(cur) + len(p) > maxc and cur:
            parts.append(cur); cur = p
        else:
            cur = (cur + "\n\n" + p).strip()
    if cur:
        parts.append(cur)
    n = 0
    for idx, part in enumerate(parts, 1):
        out = f"{base}__part{idx}.md"
        with open(os.path.join(outdir, out), "w", encoding="utf-8") as fh:
            fh.write(f"{header_txt}\n\n_(partie {idx}/{len(parts)})_\n\n{part}\n")
        n += 1
    return n


def main() -> None:
    src, out = sys.argv[1], sys.argv[2]
    maxc = int(sys.argv[3]) if len(sys.argv) > 3 else MAX
    os.makedirs(out, exist_ok=True)
    total = 0
    for f in sorted(os.listdir(src)):
        if f.endswith(".md"):
            n = split_file(os.path.join(src, f), out, maxc)
            if n > 1:
                print(f"{f} -> {n} parties")
            total += n
    print(f"total fiches produites : {total} -> {out}")


if __name__ == "__main__":
    main()
