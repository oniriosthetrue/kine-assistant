#!/usr/bin/env python3
"""
Phase 2 - Traduction FR des chapitres OpenStax A&P (source anglaise),
pilotee par le glossaire FR canonique (GLOSSAIRE-FR.md).

Lit les chunks OpenStax (chunks_openstax_anatomy.jsonl), les regroupe par
section, et traduit chaque section (titre + corps) en francais via le LLM
local en imposant le glossaire. Sortie : une fiche markdown par section dans
_out/fr/.

Reprebable : saute les sections deja traduites.
Concurrent : N requetes LLM en parallele (vLLM sert le batch).

Usage :
    PY=/home/linus/mcp/docling/.venv/bin/python
    $PY _translate_en.py --chapters 10 --limit 3   # test : 3 sections du ch.10
    $PY _translate_en.py --chapters 6,7,8,9,10,11,12,13,14,15,18,19,20 --workers 4

NE PAS LANCER sans accord explicite : mobilise le GPU de la stack qwen.
"""
import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNKS = "/tmp/chunks_anatomy.jsonl"
GLOSSARY = os.path.join(HERE, "GLOSSAIRE-FR.md")
OUT = os.path.join(HERE, "_out", "fr")

LLM_URL = os.environ.get("LLM_URL", "http://localhost:8000/v1/chat/completions")
LLM_MODEL = os.environ.get("LLM_MODEL", "flash-next-v2")

SYSTEM = (
    "Tu es un traducteur expert en anatomie et physiologie humaines, "
    "specialiste du vocabulaire medical francais utilise par les "
    "kinesitherapeutes (HAS, ameli, dictionnaire de l'Academie nationale de "
    "medecine).\n\n"
    "Tu dois TRADUIRE en francais le texte anglais fourni, en respectant "
    "STRICTEMENT le glossaire terminologique ci-dessous. Regles :\n"
    "1. Employer EXCLUSIVEMENT la colonne FR du glossaire pour tout terme qui "
    "y figure. Ne jamais paraphraser ni inventer un equivalent.\n"
    "2. Abréviation FR entre parentheses a la premiere occurrence seulement.\n"
    "3. Ne pas traduire les termes latins deja en usage FR (sarcomere, osteon, "
    "troponine...). Noms propres inchanges (Ranvier, Havers, Krebs...).\n"
    "4. Traduire fidelement, SANS ajouter ni omettre d'information.\n"
    "5. francais scientifique neutre, tournures courtes, aucun anglicisme.\n"
    "6. Rendre UNIQUEMENT la traduction francaise, sans commentaire, sans "
    "preambule, sans titre.\n\n"
    "=== GLOSSAIRE TERMINOLOGIQUE FR (referrentiel obligatoire) ===\n"
)

_print_lock = threading.Lock()
_counter = {"done": 0, "fail": 0}


def load_glossary() -> str:
    with open(GLOSSARY, encoding="utf-8") as fh:
        return fh.read()


def load_sections(chapters: list[int]) -> dict:
    """Retourne {section_key: {meta, blocks}} en ignorant les chunks overlap.

    Chaque section est decomposee en BLOCS ordonnes par sous-section
    (champ subsection_title + source_level de la source OpenStax), afin de
    restaurer la hierarchie de titres markdown a la traduction. Les chunks
    consecutifs d'une meme sous-section sont fusionnes en un seul bloc.
    """
    sections: dict[str, dict] = {}
    with open(CHUNKS, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if d["chapter_num"] not in chapters:
                continue
            if d.get("is_overlap"):
                continue
            key = f"ch{d['chapter_num']:02d}_sec{d['section_num']}"
            sec = sections.setdefault(key, {
                "chapter_num": d["chapter_num"],
                "chapter_title": d["chapter_title"],
                "section_num": d["section_num"],
                "section_title": d.get("section_title", ""),
                "blocks": [],  # [{level, title, parts[]}]
            })
            txt = d.get("text", "").strip()
            if not txt:
                continue
            sub = (d.get("subsection_title") or "").strip()
            level = d.get("source_level") or 2
            cur = sec["blocks"][-1] if sec["blocks"] else None
            if cur is not None and cur["title"] == sub and cur["level"] == level:
                cur["parts"].append(txt)
            else:
                sec["blocks"].append(
                    {"level": level, "title": sub, "parts": [txt]}
                )
    for sec in sections.values():
        for b in sec["blocks"]:
            b["text"] = "\n\n".join(b["parts"])
        sec["text"] = "\n\n".join(b["text"] for b in sec["blocks"])
    return sections


def slugify(s: str) -> str:
    s = s.lower().replace("œ", "oe")
    s = re.sub(r"[àáâãä]", "a", s); s = re.sub(r"[èéêë]", "e", s)
    s = re.sub(r"[ìíîï]", "i", s); s = re.sub(r"[òóôõö]", "o", s)
    s = re.sub(r"[ùúûü]", "u", s); s = re.sub(r"[ÿý]", "y", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:50]


def strip_reasoning(text: str) -> str:
    text = re.sub(r"<\|think\|.*?<\|/think\|>", "", text, flags=re.DOTALL)
    text = re.sub(r"<think>.*?<\/think>", "", text, flags=re.DOTALL)
    return text.strip()


def _chat(prompt: str, max_tokens: int) -> str:
    for attempt in range(4):
        try:
            r = requests.post(
                LLM_URL,
                json={
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": max_tokens,
                },
                timeout=300,
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            if not content:
                # modele de raisonnement : tokens epuises par le raisonnement
                raise ValueError("content None (tokens reasoning epuises)")
            return strip_reasoning(content)
        except Exception as exc:  # noqa: BLE001
            with _print_lock:
                print(f"    retry {attempt+1}: {exc}", file=sys.stderr)
            time.sleep(3)
    return ""


def translate_title(title: str, glossary: str) -> str:
    if not title:
        return ""
    prompt = (
        "Traduis en francais ce titre de section d'anatomie/physiologie, en "
        "respectant le glossaire. Rends UNIQUEMENT le titre traduit, sans "
        "guillemets ni point final.\n\n"
        f"{SYSTEM}{glossary}\n\nTitre anglais : {title}\nTitre francais :"
    )
    out = _chat(prompt, 1024)
    return out.strip().strip('"').rstrip(".")


def translate_body(text: str, glossary: str) -> str:
    chunks = []
    if len(text) <= 6000:
        chunks = [text]
    else:
        paras = text.split("\n\n")
        cur = ""
        for p in paras:
            if len(cur) + len(p) > 5500 and cur:
                chunks.append(cur)
                cur = p
            else:
                cur = (cur + "\n\n" + p).strip()
        if cur:
            chunks.append(cur)

    out = []
    for ch in chunks:
        prompt = (
            f"{SYSTEM}{glossary}\n\n"
            f"=== TEXTE ANGLAIS A TRADUIRE ===\n{ch}\n\n"
            "=== TRADUCTION FRANCAISE ===\n"
        )
        res = _chat(prompt, 8192)
        out.append(res if res else "[TRADUCTION ECHOUEE]")
    return "\n\n".join(out)


def process(key: str, sec: dict, glossary: str) -> None:
    slug = f"{key}-{slugify(sec['section_title'] or sec['chapter_title'])}"
    path = os.path.join(OUT, f"{slug}.md")
    if os.path.exists(path):
        return
    t0 = time.time()
    fr_title = translate_title(sec["section_title"] or sec["chapter_title"], glossary)
    # Traduit chaque bloc (sous-section) separement et injecte son titre
    # markdown. Le niveau wiki source_level 2 -> ##, 3 -> ### (H1 = titre
    # de section). Exploite par le markdown_header_text_splitter d'OWUI.
    body_parts = []
    failed = False
    for b in sec["blocks"]:
        fr_sub = translate_title(b["title"], glossary) if b["title"] else ""
        fr_block = translate_body(b["text"], glossary)
        if "[TRADUCTION ECHOUEE]" in fr_block:
            failed = True
        md_level = "#" * min(max(b["level"], 2), 4)
        if fr_sub:
            body_parts.append(f"{md_level} {fr_sub}\n\n{fr_block}")
        else:
            body_parts.append(fr_block)
    fr_body = "\n\n".join(body_parts)
    header = (
        f"# {fr_title or sec['section_title']}\n\n"
        f"> OpenStax Anatomy & Physiology 2e (CC-BY-4.0), ch. "
        f"{sec['chapter_num']} « {sec['chapter_title']} », section "
        f"{sec['section_num']}. Traduit de l'anglais par traduction "
        f"assistee (glossaire FR canonique MinervIA).\n\n"
    )
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(header + fr_body + "\n")
    os.replace(tmp, path)
    with _print_lock:
        _counter["done"] += 1
        if failed:
            _counter["fail"] += 1
        print(f"[{_counter['done']}] {key} {fr_title!r} "
              f"({time.time()-t0:.0f}s){'' if not failed else ' ECHEC'}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapters", required=True,
                    help="liste de numeros de chapitres, ex: 6,9,10,11")
    ap.add_argument("--limit", type=int, default=0, help="max de sections (test)")
    ap.add_argument("--workers", type=int, default=4, help="requetes LLM paralleles")
    args = ap.parse_args()

    chapters = [int(c) for c in args.chapters.split(",")]
    glossary = load_glossary()
    sections = load_sections(chapters)
    keys = sorted(k for k in sections if len(sections[k]["text"]) >= 150)
    todo = [k for k in keys
            if not os.path.exists(os.path.join(
                OUT, f"{k}-{slugify(sections[k]['section_title'] or sections[k]['chapter_title'])}.md"))]
    if args.limit:
        todo = todo[: args.limit]

    os.makedirs(OUT, exist_ok=True)
    print(f"{len(todo)} sections a traiter (chapitres {chapters}, "
          f"{args.workers} workers)", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(process, k, sections[k], glossary) for k in todo]
        for _ in as_completed(futs):
            pass
    print(f"\nTermine en {time.time()-t0:.0f}s : {_counter['done']} traitees, "
          f"{_counter['fail']} echecs -> {OUT}")


if __name__ == "__main__":
    main()
