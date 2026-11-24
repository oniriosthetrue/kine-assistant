import json, subprocess, os

COL = "2b0c338d-1040-4d25-bb77-30a6873b1c42"
ADMIN = open("/tmp/owui_admin_token.txt").read().strip()
BASE = "http://localhost:8080/api/v1"
SRC = "/home/linus/communication/kin\u00e9/corpus-rag"
FILES = ["05a-remboursement-prise-en-charge.md",
         "05b-acces-direct-kine.md",
         "05c-accords-prealables-apa.md"]

def sh(c):
    return subprocess.run(c, shell=True, capture_output=True, text=True).stdout

# 1. copy files into container
for f in FILES:
    subprocess.run(["docker", "cp", os.path.join(SRC, f), f"open-webui:/tmp/{f}"], check=True)

# 2. upload each file (multipart) -> file_id, then add to collection
for f in FILES:
    up = sh(f'docker exec open-webui sh -c \'curl -s -X POST "{BASE}/files/" '
            f'-H "Authorization: Bearer {ADMIN}" -F "file=@/tmp/{f}"\'')
    try:
        fid = json.loads(up)["id"]
    except Exception as e:
        print(f"UPLOAD FAIL {f}: {up[:300]}"); continue
    body = json.dumps({"file_id": fid})
    open("/tmp/_add_body.json", "w").write(body)
    subprocess.run(["docker", "cp", "/tmp/_add_body.json", "open-webui:/tmp/_add_body.json"], check=True)
    add = sh(f'docker exec open-webui sh -c \'curl -s -X POST '
             f'"{BASE}/knowledge/{COL}/file/add" -H "Authorization: Bearer {ADMIN}" '
             f'-H "Content-Type: application/json" --data-binary @/tmp/_add_body.json\'')
    ok = "error" not in add.lower()
    print(f"{f}: file_id={fid} add_ok={ok}")
    if not ok:
        print("   ", add[:300])

# 3. list collection files to confirm
lst = sh(f'docker exec open-webui sh -c \'curl -s "{BASE}/knowledge/{COL}/files" '
         f'-H "Authorization: Bearer {ADMIN}"\'')
data = json.loads(lst).get("data", [])
print("\n--- FICHIERS DANS LA KB ---")
for it in data:
    print(" -", it.get("filename") or it.get("name"))
