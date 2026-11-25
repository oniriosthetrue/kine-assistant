#!/usr/bin/env bash
# Orchestrateur KB2 : enchaîne automatiquement la suite du peuplement.
# 1. attend la fin de la traduction batch1 (GPU)
# 2. lance batch2 (chapitres restants) puis attend
# 3. attend la fin du fetch Wikipédia enrichi
# 4. split tout (sources-fr + _out/fr) a 12k
# 5. purge KB2 (supprime les 156 anciens fichiers)
# 6. re-upload l'ensemble
# S'ARRETE avant la validation UI (faite a la main dans le navigateur).
set -uo pipefail
cd /home/linus/communication/kiné/kb2
PY=/home/linus/mcp/docling/.venv/bin/python
KB=e68519ab-dece-4221-901c-4c6b58010997
TOK=$(cat /tmp/owui_admin_token.txt)
BASE=http://localhost:8080/api/v1
log(){ echo "[$(date +%H:%M:%S)] $*"; }

wait_for(){ # attend qu'aucun process ne matche le motif
  local pat="$1" label="$2"
  while pgrep -f "$pat" >/dev/null; do sleep 30; done
  log "$label terminee"
}

log "=== ETAPE 1 : attente fin traduction batch1 ==="
wait_for "_translate_en.py" "traduction batch1"
log "batch1 : $(ls _out/fr/*.md | wc -l) sections"

log "=== ETAPE 2 : traduction batch2 (chapitres restants) ==="
$PY _translate_en.py --chapters 1,2,3,4,5,16,17,21,22,23,24,25,26,27 --workers 4 \
  >> /tmp/translate_full.log 2>&1
log "batch2 terminee : $(ls _out/fr/*.md | wc -l) sections au total"

log "=== ETAPE 3 : attente fin fetch Wikipédia ==="
wait_for "_fetch_fr.py" "fetch Wikipédia"
log "sources-fr : $(ls sources-fr/*.md | wc -l) fiches"

log "=== ETAPE 4 : split a 12k (sources-fr + _out/fr) ==="
rm -rf _all_src _all_split && mkdir -p _all_src
cp sources-fr/*.md _all_src/ && cp _out/fr/*.md _all_src/
log "fiches combinees : $(ls _all_src/*.md | wc -l)"
$PY _split_big.py _all_src _all_split 12000
log "apres split : $(ls _all_split/*.md | wc -l) fichiers"

log "=== ETAPE 5 : purge KB2 ==="
> /tmp/kb2_ids.txt
for p in $(seq 1 20); do
  docker exec open-webui sh -c "curl -s -H 'Authorization: Bearer $TOK' '$BASE/knowledge/$KB/files?page=$p&content=false'" \
    | $PY -c "import sys,json; d=json.load(sys.stdin); [print(it['id']) for it in (d.get('items') or [])]" >> /tmp/kb2_ids.txt
  [ "$(wc -l < /tmp/kb2_ids.txt)" -ge "$(docker exec open-webui sh -c "curl -s -H 'Authorization: Bearer $TOK' '$BASE/knowledge/$KB/files?page=1&content=false'" | $PY -c 'import sys,json;print(json.load(sys.stdin).get("total",0))')" ] && break
done
N=$(sort -u /tmp/kb2_ids.txt | wc -l)
log "suppression de $N fichiers..."
while read -r fid; do
  docker exec open-webui sh -c "curl -s -X POST -H 'Authorization: Bearer $TOK' -H 'Content-Type: application/json' -d '{\"file_id\":\"$fid\"}' '$BASE/knowledge/$KB/file/remove'" >/dev/null
done < <(sort -u /tmp/kb2_ids.txt)
log "purge faite"

log "=== ETAPE 6 : re-upload ==="
$PY _upload_kb2.py _all_split 2>&1 | grep -v "Successfully copied" | tail -5

log "=== VERIFICATION FINALE ==="
> /tmp/kb2_have_final.txt
for p in $(seq 1 20); do
  docker exec open-webui sh -c "curl -s -H 'Authorization: Bearer $TOK' '$BASE/knowledge/$KB/files?page=$p&content=false'" \
    | $PY -c "import sys,json; d=json.load(sys.stdin); [print(it.get('filename') or it.get('name')) for it in (d.get('items') or [])]" >> /tmp/kb2_have_final.txt
done
TOT=$(docker exec open-webui sh -c "curl -s -H 'Authorization: Bearer $TOK' '$BASE/knowledge/$KB/files?page=1&content=false'" | $PY -c 'import sys,json;print(json.load(sys.stdin).get("total",0))')
log "TOTAL dans KB2 = $TOT"
miss=0
for f in $(ls _all_src); do
  base="${f%.md}"
  grep -qx "$f" /tmp/kb2_have_final.txt || grep -q "^${base}__part" /tmp/kb2_have_final.txt || { echo "MANQUANT: $f"; miss=$((miss+1)); }
done
log "contenus non couverts: $miss"
log "=== ORCHESTRATION TERMINEE - pret pour validation UI ==="
