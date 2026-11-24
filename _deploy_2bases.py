#!/usr/bin/env python3
"""Deploie le modele assistant-kine avec 2 bases + routage.
Lit le modele courant, remplace meta.knowledge et meta.system_prompt, POST update.
Usage: docker exec -e TOK=... open-webui python /tmp/_deploy_2bases.py
"""
import json
import os
import urllib.request

TOK = os.environ["TOK"]
BASE = "http://localhost:8080/api/v1"
KB_ADMIN = "2b0c338d-1040-4d25-bb77-30a6873b1c42"
KB_PHYSIO = "e68519ab-dece-4221-901c-4c6b58010997"
MODEL_ID = "assistant-kine"


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOK}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())


# 1. lire le prompt depuis le fichier canonique
with open("/app/_system_prompt_kine.md", encoding="utf-8") as f:
    prompt = f.read()

# 2. lire le modele courant
m = req("GET", f"/models/model?id={MODEL_ID}")
meta = m["meta"]
params = m["params"]

# 3. appliquer les changements
meta["knowledge"] = [
    {"id": KB_ADMIN, "type": "collection"},
    {"id": KB_PHYSIO, "type": "collection"},
]
meta["system_prompt"] = prompt

# 4. construire le payload ModelForm
payload = {
    "id": MODEL_ID,
    "base_model_id": m.get("base_model_id"),
    "name": m["name"],
    "meta": meta,
    "params": params,
    "is_active": m.get("is_active", True),
    "access_grants": m.get("access_grants", []),
}

# 5. POST update
out = req("POST", "/models/model/update", payload)
print("OK update")
print("knowledge =", json.dumps(out["meta"]["knowledge"]))
print("prompt len =", len(out["meta"]["system_prompt"]))
