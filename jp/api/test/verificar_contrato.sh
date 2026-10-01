#!/usr/bin/env bash
# =============================================================================
# verificar_contrato.sh — レスポンスの契約は保たれているか？
#
# ★ このスクリプトが存在する理由
#   teste_manual.sh は診断用フィールドを読むときに `.get(chave, '?')` を使う。
#   これは欠落に対しては頑健だが、黙って通ってしまう: キーがリネームされても
#   テストは '?' を表示して合格し、情報が消えたことに誰も
#   気づかない。
#
#   ここではその逆: 期待される各キーを明示的に検証し、
#   どれか 1 つでも欠けていればスクリプトは失敗する。
#
# 使い方
#     bash verificar_contrato.sh                 # teste_papeis.sh を読む
#     API=http://host:8000 CENA=/path/x.mp4 bash verificar_contrato.sh
# =============================================================================

AQUI="$(cd "$(dirname "$0")" && pwd)"
PAPEIS="${PAPEIS:-$AQUI/teste_papeis.sh}"

cV='\033[0;32m'; cR='\033[0;31m'; cF='\033[0m'
OK=0; ERRO=0

if [ -f "$PAPEIS" ]; then
    # shellcheck disable=SC1090
    . "$PAPEIS"
    CENA="${CENA:-$UNICA_PATH}"
    SID="${SID:-$UNICA_SID}"
    VID="${VID:-$UNICA_VID}"
    PID="${PID:-$PROGRAM_ID}"
fi
API="${API:-http://localhost:8000}"
[ -n "$CENA" ] || { echo "✗ CENA=<シーン動画のパス> を指定してください"; exit 1; }

echo "═══════════════════════════════════════════════════════════════════"
echo " 契約の検証 — $API"
echo "═══════════════════════════════════════════════════════════════════"

RESP=$(curl -s --max-time 900 -X POST "$API/caption" \
       -H 'Content-Type: application/json' \
       -d "{\"scene_id\":\"$SID\",\"video_id\":\"$VID\",\"program_id\":\"$PID\",\"scene_video_path\":\"$CENA\"}" 2>/dev/null)

[ -n "$RESP" ] || { printf "${cR}✗ API から応答がない${cF}\n"; exit 1; }

verificar() {  # verificar <ラベル> <d に対する python 式>
    local r
    r=$(echo "$RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
try:
    v = $2
    print('OK' if v is not None else 'AUSENTE')
except (KeyError, IndexError, TypeError):
    print('AUSENTE')
" 2>/dev/null)
    if [ "$r" = "OK" ]; then OK=$((OK+1)); printf "  ${cV}✓${cF} %s\n" "$1"
    else ERRO=$((ERRO+1)); printf "  ${cR}✗ %s — 欠落、またはリネームされている${cF}\n" "$1"; fi
}

echo
echo "  --- エンベロープ ---"
for c in state program_id summary items groups persisted seconds; do
    verificar "$c" "d['$c']"
done

echo
echo "  --- summary ---"
for c in total ok errors; do verificar "summary.$c" "d['summary']['$c']"; done

echo
echo "  --- items[0] ---"
for c in scene_id scene_caption_en keywords_en model_name model_version status; do
    verificar "items[0].$c" "d['items'][0]['$c']"
done
verificar "items[0].keywords_en[0].token"  "d['items'][0]['keywords_en'][0]['token']"
verificar "items[0].keywords_en[0].weight" "d['items'][0]['keywords_en'][0]['weight']"

echo
echo "  --- groups[0] ---"
for c in directory collection scenes from_cache cache_cleared annos exp_dir merge; do
    verificar "groups[0].$c" "d['groups'][0]['$c']"
done
verificar "groups[0].merge.merged" "d['groups'][0]['merge']['merged']"
verificar "groups[0].merge.total"  "d['groups'][0]['merge']['total']"

echo
echo "  --- persisted ---"
for c in written replaced total_in_program jsonl scenes_dir; do
    verificar "persisted.$c" "d['persisted']['$c']"
done

echo
echo "  --- 旧キーが復活してはならない ---"
antiga() {
    local r
    r=$(echo "$RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('PRESENTE' if '$2' in json.dumps(d) else 'ausente')
" 2>/dev/null)
    if [ "$r" = "ausente" ]; then OK=$((OK+1)); printf "  ${cV}✓${cF} '%s' は出現しない\n" "$2"
    else ERRO=$((ERRO+1)); printf "  ${cR}✗ '%s' が復活した — 契約がリグレッションしている${cF}\n" "$2"; fi
}
for k in '"diretorio"' '"estavam_em_cache"' '"cache_limpo"' '"fundidas"' '"gravadas"' '"job_id"' '"resumo"' '"erros"' '"segundos"'; do
    antiga "" "$(echo "$k" | tr -d '"')"
done

echo
echo "═══════════════════════════════════════════════════════════════════"
printf "  ${cV}OK %d 件${cF}   ${cR}問題 %d 件${cF}\n" "$OK" "$ERRO"
[ "$ERRO" -eq 0 ] && echo "  ✓ 契約は保たれている" || echo "  ✗ 契約が変わった — 利用側を更新してください"
exit $([ "$ERRO" -eq 0 ] && echo 0 || echo 1)
