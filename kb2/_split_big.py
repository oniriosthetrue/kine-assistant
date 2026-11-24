#!/usr/bin/env python3
"""Decoupe les gros .md en parties < MAX car., EN PRESERVANT LA CHAPITRATION.

Les gros fichiers font resetter l'appel d'embedding d'Open WebUI (batch trop
grand). On les scinde en plusieurs fiches pour rester sous le seuil.

Contrairement a un decoupage naive aux frontieres de paragraphes, ce splitter
est CONSCIENT DES TITRES : Open WebUI (markdown_header_text_splitter) ancre
chaque chunk sur le titre markdown precedent. Si une partie demarre en plein
milieu d'une sous-section sans son titre, le chunk perd son contexte de
chapitre. On rejoue donc, en tete de CHAQUE partie, le titre H1 du document
suivi du chemin de titres (## / ### ...) qui gouverne le contenu de la partie.

Decoupe de preference aux frontieres de sous-section ; ne coupe a l'interieur
d'une sous-section que si elle depasse seule MAX.

Usage :
    PY=/home/linus/mcp/docling/.venv/bin/python
    $PY _split_big.py <dossier_in> <dossier_out> [MAX=12000]
"""
import os
import re
import sys

MAX = 12000
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def parse_blocks(text: str):
    """Retourne (header, blocks) ou header = lignes H1+citation, et
    blocks = [{path:[(lvl,title)...], lines:[...]}] un bloc par sous-section.

    path = pile de titres en cours (anctres), lines = lignes du bloc Y COMPRIS
    sa propre ligne de titre.
    """
    lines = text.split("\n")
    # en-tete = H1 (niveau 1) SEUL + lignes de citation > + vides. On s'arrete
    # au premier titre de niveau >= 2 pour ne pas l'avaler dans l'en-tete
    # (sinon il serait reemis en tete de chaque partie).
    header = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = HEAD_RE.match(ln)
        if m and len(m.group(1)) > 1:
            break  # premier sous-titre -> fin de l'en-tete
        if ln.startswith("#") or ln.startswith(">") or ln == "":
            header.append(ln)
            i += 1
        else:
            break
    header_txt = "\n".join(header).strip()

    blocks = []
    stack = []  # [(level:int, title:str)]
    cur = {"path": [], "lines": []}
    for ln in lines[i:]:
        m = HEAD_RE.match(ln)
        if m:
            lvl = len(m.group(1))
            title = m.group(2).strip()
            # met a jour la pile des titres
            stack = [s for s in stack if s[0] < lvl]
            stack.append((lvl, title))
            if cur["lines"]:
                blocks.append(cur)
            cur = {"path": list(stack), "lines": [ln]}
        else:
            cur["lines"].append(ln)
    if cur["lines"]:
        blocks.append(cur)
    return header_txt, blocks


def block_text(block) -> str:
    return "\n".join(block["lines"]).strip()


def path_md(path, skip_own=True) -> str:
    """Rends le chemin de titres en markdown. skip_own evite de re-emettre
    le titre deja present en premiere ligne du bloc. Le H1 (lvl 1) est
    ignore car il est deja porte par l'en-tete du document."""
    items = path[:-1] if (skip_own and path) else path
    return "\n".join(
        "#" * lvl + " " + title for lvl, title in items if lvl > 1
    )


def split_file(path: str, outdir: str, maxc: int) -> int:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    base = os.path.splitext(os.path.basename(path))[0]
    if len(text) <= maxc:
        with open(os.path.join(outdir, os.path.basename(path)), "w",
                  encoding="utf-8") as fh:
            fh.write(text)
        return 1

    header, blocks = parse_blocks(text)

    # Rassemble les blocs en parties < maxc, en preferant couper entre blocs.
    parts = []          # chaque partie = liste de blocs
    cur = []
    cur_len = len(header) + 40  # marge pour l'en-tete rejouee
    for b in blocks:
        btxt = block_text(b)
        # bloc trop grand seul -> on le sous-decoupe a ses paragraphes en
        # conservant son chemin de titres comme ancre.
        if len(btxt) > maxc:
            if cur:
                parts.append(cur); cur = []; cur_len = len(header) + 40
            paras = b["lines"][1:]  # sans la ligne de titre
            sub = []
            sub_len = 0
            anchor = path_md(b["path"], skip_own=False)
            for p in "\n\n".join(paras).split("\n\n"):
                if sub_len + len(p) > maxc - len(anchor) and sub:
                    parts.append([{"path": b["path"], "lines": [anchor, "", "\n\n".join(sub)]}])
                    sub = []; sub_len = 0
                sub.append(p); sub_len += len(p) + 2
            if sub:
                cur = [{"path": b["path"], "lines": [anchor, "", "\n\n".join(sub)]}]
                cur_len = len(anchor) + sub_len
            continue
        if cur_len + len(btxt) > maxc and cur:
            parts.append(cur)
            cur = []
            cur_len = len(header) + 40
        cur.append(b)
        cur_len += len(btxt) + 2
    if cur:
        parts.append(cur)

    if len(parts) <= 1:
        with open(os.path.join(outdir, os.path.basename(path)), "w",
                  encoding="utf-8") as fh:
            fh.write(text)
        return 1

    n = 0
    for idx, part in enumerate(parts, 1):
        # ancre = chemin de titres du premier bloc (hors H1, hors son propre
        # titre que block_text reemet deja). Le H1 est porte par l'en-tete.
        first_path = part[0]["path"]
        anchor = path_md(first_path, skip_own=True)
        out_name = f"{base}__part{idx}.md"
        chunks = [header, f"_(partie {idx}/{len(parts)})_"]
        if anchor:
            chunks.append(anchor)
        for b in part:
            chunks.append(block_text(b))
        with open(os.path.join(outdir, out_name), "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(c for c in chunks if c) + "\n")
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
