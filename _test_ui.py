import json, subprocess

KINE = open("/tmp/owui_kine_token.txt").read().strip()
QUESTIONS = [
    "Apres une prothese totale du genou, a partir de quelle seance de kine faut-il un accord prealable de la Securite sociale ?",
    "Un patient peut-il venir en kiné sans ordonnance ? Combien de séances et serai-je rembourse ?",
    "Une seance de kine est rembourse a 60%, mais il reste encore un reste a charge. Pourquoi ?",
]

def ask(q):
    payload = {"model": "assistant-kine", "messages": [{"role": "user", "content": q}], "stream": False}
    open("/tmp/_chat.json", "w").write(json.dumps(payload))
    subprocess.run(["docker", "cp", "/tmp/_chat.json", "open-webui:/tmp/_chat.json"], check=True)
    out = subprocess.run(
        ["docker", "exec", "open-webui", "sh", "-c",
         f"curl -s -X POST 'http://localhost:8080/api/chat/completions' "
         f"-H 'Authorization: Bearer {KINE}' -H 'Content-Type: application/json' "
         f"--data-binary @/tmp/_chat.json"],
        capture_output=True, text=True).stdout
    try:
        d = json.loads(out)
        return d["choices"][0]["message"]["content"]
    except Exception:
        return "PARSE_FAIL: " + out[:400]

for q in QUESTIONS:
    print("=" * 70)
    print("Q:", q)
    print("-" * 70)
    print(ask(q)[:1400])
    print()
