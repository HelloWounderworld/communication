#!/usr/bin/env bash
# =============================================================================
# teste_manual.sh — POST /caption と POST /caption/batch の組み合わせテスト
#
# 前提条件
#   1. teste_config.sh を記入する
#   2. bash preparar_teste.sh
#   3. モデルを読み込んだ状態でサービスが稼働している
#
# 使い方
#     bash teste_manual.sh          # 全ケースを直列で
#     bash teste_manual.sh 7        # ケース 7 のみ
#
# ★ 直列実行
#   各リクエストは、前のリクエストのレスポンスが返ってから送信される。
#   並列性はない: `curl` はブロッキングで、ケースは順番に実行される。
#   いくつかのケースは前のケースに依存する（6 のキャッシュは 5 から来る。
#   7 の force は 6 が前提）。そのため、ケースを単独で実行すると、
#   通しで実行した場合と結果が異なることがある。
#
# ★ 必須の 2 形式のみ
#     POST /caption        { scene_id, video_id, program_id, scene_video_path }
#     POST /caption/batch  { items: [ {...}, ... ] }
#   追加フィールド（force, assincrono, callback_url）はテストに必要な箇所だけ。
# =============================================================================

AQUI="$(cd "$(dirname "$0")" && pwd)"
PAPEIS="${PAPEIS:-$AQUI/teste_papeis.sh}"
SO="${1:-}"

# ⚠️ 色名は 2 文字: R/A/V だと $R（レスポンス本文）や、スクリプト内で使う
# $A・$V と衝突する。最終サマリーの表示が崩れていた原因はこれ。
cV='\033[0;32m'; cR='\033[0;31m'; cA='\033[0;33m'; cC='\033[0;36m'; cF='\033[0m'
OK=0; ERRO=0; PULO=0

[ -f "$PAPEIS" ] || { printf "${cR}✗ %s が見つからない${cF}\n  実行してください: bash preparar_teste.sh\n" "$PAPEIS"; exit 1; }
# shellcheck disable=SC1090
. "$PAPEIS"

t()    { echo; echo "═══════════════════════════════════════════════════════════════════"; echo " $1"; echo "═══════════════════════════════════════════════════════════════════"; }
pula() { [ -n "$SO" ] && [ "$SO" != "$1" ]; }
ok()   { OK=$((OK+1));     printf "  ${cV}✓${cF} %s\n" "$1"; }
nok()  { ERRO=$((ERRO+1)); printf "  ${cR}✗${cF} %s\n       %s\n" "$1" "$2"; }
skip() { PULO=$((PULO+1)); printf "  ${cA}○${cF} %s\n       スキップ: %s\n" "$1" "$2"; }
det()  { printf "       ${cC}%s${cF}\n" "$1"; }

# ⚠️ これらの関数は $HTTP と $R を設定するので、$( ) なしで呼ぶ — コマンド
# 置換の中ではサブシェルで実行され、変数がここまで
# 伝わらない。
_B=$(mktemp); trap 'rm -f "$_B"' EXIT

POST() {  # POST <ルート> <json>
    HTTP=$(curl -s -o "$_B" -w '%{http_code}' --max-time "$TIMEOUT" \
           -X POST "$API$1" -H 'Content-Type: application/json' -d "$2" 2>/dev/null)
    R=$(cat "$_B")
}
GET() {
    HTTP=$(curl -s -o "$_B" -w '%{http_code}' --max-time "$TIMEOUT" "$API$1" 2>/dev/null)
    R=$(cat "$_B")
}
J() { echo "$1" | python3 -c "import sys,json;d=json.load(sys.stdin);print($2)" 2>/dev/null; }

# item <sid> <vid> <path> [program_id]
item() {
    printf '{"scene_id":"%s","video_id":"%s","program_id":"%s","scene_video_path":"%s"}' \
           "$1" "$2" "${4:-$PROGRAM_ID}" "$3"
}

# =============================================================================
t "設定"
printf "  %-16s %s\n" "API"        "$API"
printf "  %-16s %s\n" "program_id" "$PROGRAM_ID"
printf "  %-16s %s シーン / %s ディレクトリ\n" "シーン" "$N_CENAS" "$N_DIRS"
echo
printf "  %-11s %-20s %s\n" "ロール" "scene_id" "video_id"
echo "  ────────────────────────────────────────────────"
printf "  %-11s %-20s %s\n" "UNICA"   "${UNICA_SID:-—}"   "${UNICA_VID:-—}"
printf "  %-11s %-20s %s\n" "LOTE_A1" "${LOTE_A1_SID:-—}" "${LOTE_A1_VID:-—}"
printf "  %-11s %-20s %s\n" "LOTE_A2" "${LOTE_A2_SID:-—}" "${LOTE_A2_VID:-—}"
printf "  %-11s %-20s %s\n" "LOTE_B1" "${LOTE_B1_SID:-—}" "${LOTE_B1_VID:-—}"
printf "  %-11s %-20s %s\n" "CURTA"   "${CURTA_SID:-—}"   "${CURTA_DUR:+${CURTA_DUR}s}"
printf "  %-11s %-20s %s\n" "ISOLAM." "${ISO_SID:-—}"     "${PROGRAM_ID_2:-—}"

# =============================================================================
t "プリフライト"
command -v curl >/dev/null || { printf "  ${cR}✗ curl が見つからない${cF}\n"; exit 1; }
GET /health
if [ "$HTTP" != "200" ]; then
    printf "  ${cR}✗ %s の API が応答しない (HTTP %s)${cF}\n" "$API" "$HTTP"
    echo "    これはシーンとは無関係 — GET /health だけの問題。"
    echo "    確認してください: サービスは稼働しているか？ ポートは正しいか？ (teste_config.sh)"
    exit 1
fi
PRONTO=$(J "$R" "d['models']['ready']")
GPU0=$(J "$R" "d['models']['gpu'].get('allocated_mb','—')")
echo "  API              : ok"
echo "  models.ready     : $PRONTO"
echo "  gpu.allocated_mb : $GPU0"
[ "$PRONTO" = "True" ] || { printf "\n  ${cR}✗ モデルが読み込まれていない${cF} — REFCAP_CARREGAR_MODELOS=0 を付けずに起動してください\n"; exit 1; }

# =============================================================================
t "ブロック 1 — POST /caption  (単一シーン形式)"

# --- 1. 基本ケース ---
if ! pula 1; then
    if [ -z "$UNICA_SID" ]; then skip "1. 単一シーン" "シーンなし"
    else
        POST /caption "$(item "$UNICA_SID" "$UNICA_VID" "$UNICA_PATH")"
        S=$(J "$R" "d['items'][0]['status']"); CAP=$(J "$R" "d['items'][0]['scene_caption_en']")
        if [ "$HTTP" = "200" ] && [ "$S" = "success" ] && [ -n "$CAP" ]; then
            ok "1. POST /caption — $UNICA_SID"
            det "state   : $(J "$R" "d['state']")"
            det "summary : $(J "$R" "json.dumps(d['summary'])")"
            det "キャプション: $CAP"
            det "keywords: $(J "$R" "', '.join(k['token'] for k in d['items'][0]['keywords_en'])")"
        else nok "1. POST /caption" "HTTP=$HTTP status=$S"; fi
    fi
fi

# --- 2. 1 秒未満のシーン（viddataset のパッチ） ---
if ! pula 2; then
    if [ -z "$CURTA_SID" ]; then skip "2. ★ 1 秒未満のシーン" "データセットに該当なし"
    else
        POST /caption "$(item "$CURTA_SID" "$CURTA_VID" "$CURTA_PATH")"
        S=$(J "$R" "d['items'][0]['status']")
        if [ "$HTTP" = "200" ] && [ "$S" = "success" ]; then
            ok "2. ★ ${CURTA_DUR}s のシーン — max(1,int(duration)) パッチ"
            det "キャプション: $(J "$R" "d['items'][0]['scene_caption_en']")"
        else nok "2. 短いシーン" "HTTP=$HTTP status=$S — パッチは適用されているか？"; fi
    fi
fi

# --- 3. 存在しないパス ---
if ! pula 3; then
    POST /caption "$(item "cena_fantasma" "vidX" "/caminho/que/nao/existe/x.mp4")"
    E=$(J "$R" "d['items'][0]['error_code']")
    if [ "$HTTP" = "200" ] && [ "$E" = "FILE_NOT_FOUND" ]; then
        ok "3. 存在しないパス → FILE_NOT_FOUND"
        det "HTTP 200 で、エラーは item の中にある — 4xx ではない"
    else nok "3. FILE_NOT_FOUND" "HTTP=$HTTP error_code=$E"; fi
fi

# --- 4. シーンのないディレクトリ ---
if ! pula 4; then
    POST /caption "$(item "cena_ausente" "vidX" "$DIR_VAZIO")"
    E=$(J "$R" "d['items'][0]['error_code']")
    [ "$E" = "SCENE_NOT_FOUND" ] && ok "4. 空ディレクトリ → SCENE_NOT_FOUND" \
        || nok "4. SCENE_NOT_FOUND" "error_code=$E"
fi

# --- 5. ★ 削除されたフォールバック ---
if ! pula 5; then
    if [ -z "$DIR_COM_VIDEO" ]; then skip "5. ★ フォールバック削除" "参照用ディレクトリなし"
    else
        POST /caption "$(item "id_inexistente_ali" "vidX" "$DIR_COM_VIDEO")"
        E=$(J "$R" "d['items'][0]['error_code']")
        if [ "$E" = "SCENE_NOT_FOUND" ]; then
            ok "5. ★ フォールバック削除 — 誤った動画にキャプションを付けない"
            det "動画が存在するディレクトリに対し、存在しない scene_id を要求した"
        else nok "5. フォールバック削除" "error_code=$E — 拒否されるべき"; fi
    fi
fi

# =============================================================================
t "ブロック 2 — キャッシュ  (直列: 6 は 1 に、7 は 6 に依存)"

# --- 6. 再処理: スキップされるべき ---
if ! pula 6; then
    if [ -z "$UNICA_SID" ]; then skip "6. 再処理（キャッシュ）" "シーンなし"
    else
        T0=$(date +%s%N)
        POST /caption "$(item "$UNICA_SID" "$UNICA_VID" "$UNICA_PATH")"
        T1=$(date +%s%N); MS_CACHE=$(( (T1-T0)/1000000 ))
        S=$(J "$R" "d['items'][0]['status']")
        EM=$(J "$R" "d['groups'][0].get('from_cache','?')")
        if [ "$S" = "success" ]; then
            ok "6. force なしで再処理 — ${MS_CACHE}ms"
            det "estavam_em_cache: $EM   ← 1 = BLIP は再実行されていない"
        else nok "6. 再処理" "status=$S"; fi
    fi
fi

# --- 7. force: 再処理されるべき ---
if ! pula 7; then
    if [ -z "$UNICA_SID" ]; then skip "7. force" "シーンなし"
    else
        P=$(python3 -c "
import json
d = json.loads('''$(item "$UNICA_SID" "$UNICA_VID" "$UNICA_PATH")''')
d['force'] = True
print(json.dumps(d))")
        T0=$(date +%s%N); POST /caption "$P"; T1=$(date +%s%N)
        MS_FORCE=$(( (T1-T0)/1000000 ))
        S=$(J "$R" "d['items'][0]['status']")
        if [ "$S" = "success" ]; then
            ok "7. force: true — ${MS_FORCE}ms"
            det "cache_cleared: $(J "$R" "d['groups'][0].get('cache_cleared')")"
            if [ -n "$MS_CACHE" ] && [ "$MS_FORCE" -gt "$MS_CACHE" ]; then
                det "★ ${MS_FORCE}ms > ${MS_CACHE}ms — 実際に再処理された"
            elif [ -n "$MS_CACHE" ]; then
                printf "       ${cA}⚠️  %sms が %sms より大きくない — キャッシュは本当にクリアされたか？${cF}\n" "$MS_FORCE" "$MS_CACHE"
            fi
        else nok "7. force" "status=$S"; fi
    fi
fi

# =============================================================================
t "ブロック 3 — POST /caption/batch  (items 形式)"

# --- 8. 同一ディレクトリのバッチ: 1 グループ ---
if ! pula 8; then
    if [ -z "$LOTE_A1_SID" ] || [ -z "$LOTE_A2_SID" ]; then
        skip "8. バッチ — 同一ディレクトリ" "同じ video_id に 2 シーン必要"
    else
        POST /caption/batch "{\"items\":[$(item "$LOTE_A1_SID" "$LOTE_A1_VID" "$LOTE_A1_PATH"),$(item "$LOTE_A2_SID" "$LOTE_A2_VID" "$LOTE_A2_PATH")]}"
        T=$(J "$R" "d['summary']['total']"); O=$(J "$R" "d['summary']['ok']"); G=$(J "$R" "len(d['groups'])")
        if [ "$HTTP" = "200" ] && [ "$O" = "2" ] && [ "$G" = "1" ]; then
            ok "8. 同一ディレクトリの 2 シーンのバッチ"
            det "グループ数: $G  ← 想定どおり build() は 1 回のみ"
        else nok "8. 同一ディレクトリのバッチ" "HTTP=$HTTP total=$T ok=$O グループ数=$G (期待値: 1 グループ)"; fi
    fi
fi

# --- 9. ★ 異なるディレクトリのバッチ: N グループ ---
if ! pula 9; then
    if [ -z "$LOTE_B1_SID" ]; then
        skip "9. ★ バッチ — 異なるディレクトリ" "ディレクトリが 1 つだけ（VIDEO_IDS を 2 つ指定してください）"
    else
        POST /caption/batch "{\"items\":[$(item "$LOTE_A1_SID" "$LOTE_A1_VID" "$LOTE_A1_PATH"),$(item "$LOTE_B1_SID" "$LOTE_B1_VID" "$LOTE_B1_PATH")]}"
        O=$(J "$R" "d['summary']['ok']"); G=$(J "$R" "len(d['groups'])")
        if [ "$HTTP" = "200" ] && [ "$O" = "2" ] && [ "$G" = "2" ]; then
            ok "9. ★ 2 ディレクトリのバッチ → 2 回の build"
            det "$(J "$R" "chr(10).join('       %s シーン（%s）' % (g['scenes'], g['directory']) for g in d['groups'])")"
        else nok "9. グルーピング" "HTTP=$HTTP ok=$O グループ数=$G (期待値: 2)"; fi
    fi
fi

# --- 10. 1 シーンだけのバッチ ---
if ! pula 10; then
    if [ -z "$UNICA_SID" ]; then skip "10. 1 件のバッチ" "シーンなし"
    else
        POST /caption/batch "{\"items\":[$(item "$UNICA_SID" "$UNICA_VID" "$UNICA_PATH")]}"
        O=$(J "$R" "d['summary']['ok']")
        [ "$HTTP" = "200" ] && [ "$O" = "1" ] && ok "10. 1 シーンのみのバッチ（境界ケース）" \
            || nok "10. 1 件のバッチ" "HTTP=$HTTP ok=$O"
    fi
fi

# --- 11. ★ 部分エラー: 1 件の不正が他を巻き込まない ---
if ! pula 11; then
    if [ -z "$LOTE_A1_SID" ]; then skip "11. ★ 部分エラー" "シーンなし"
    else
        POST /caption/batch "{\"items\":[$(item "$LOTE_A1_SID" "$LOTE_A1_VID" "$LOTE_A1_PATH"),$(item "ruim" "vidX" "/nada/x.mp4"),$(item "$UNICA_SID" "$UNICA_VID" "$UNICA_PATH")]}"
        O=$(J "$R" "d['summary']['ok']"); E=$(J "$R" "d['summary']['errors']")
        if [ "$HTTP" = "200" ] && [ "$O" = "2" ] && [ "$E" = "1" ]; then
            ok "11. ★ 部分エラーでバッチ全体は失敗しない"
            det "ok=$O errors=$E、かつ HTTP 200 — 500 ではない"
            det "不正な item: $(J "$R" "[i['error_code'] for i in d['items'] if i['status']=='error'][0]")"
        else nok "11. 部分エラー" "HTTP=$HTTP ok=$O errors=$E"; fi
    fi
fi

# --- 12. ★ 同一バッチ内の重複シーン ---
if ! pula 12; then
    if [ -z "$UNICA_SID" ]; then skip "12. バッチ内の重複シーン" "シーンなし"
    else
        POST /caption/batch "{\"items\":[$(item "$UNICA_SID" "$UNICA_VID" "$UNICA_PATH"),$(item "$UNICA_SID" "$UNICA_VID" "$UNICA_PATH")]}"
        T=$(J "$R" "d['summary']['total']")
        if [ "$HTTP" = "200" ]; then
            ok "12. バッチ内で同じシーンを重複（境界ケース）"
            det "total=$T — 重複があってもパイプラインは壊れない"
        else nok "12. 重複シーン" "HTTP=$HTTP"; fi
    fi
fi

# --- 13. 全シーンを一度に ---
if ! pula 13; then
    ITENS=$(python3 - <<PYEOF
import json
todas = "$TODAS".split()
out = []
for t in todas:
    v, s, c = t.split(":", 2)
    out.append({"scene_id": s, "video_id": v,
                "program_id": "$PROGRAM_ID", "scene_video_path": c})
print(json.dumps({"items": out}))
PYEOF
)
    POST /caption/batch "$ITENS"
    T=$(J "$R" "d['summary']['total']"); O=$(J "$R" "d['summary']['ok']"); G=$(J "$R" "len(d['groups'])")
    if [ "$HTTP" = "200" ] && [ "$O" = "$T" ]; then
        ok "13. 全 $N_CENAS シーンを 1 バッチで"
        det "total=$T ok=$O グループ数=$G"
    elif [ "$HTTP" = "202" ]; then
        skip "13. 全シーン" "しきい値を超えた → 非同期になった（ケース 14 を参照）"
    else nok "13. 全件バッチ" "HTTP=$HTTP total=$T ok=$O"; fi
fi

# --- 14. しきい値超過時の非同期 ---
if ! pula 14; then
    if [ "$N_CENAS" -le "$LIMIAR_ASSINCRONO" ]; then
        skip "14. 自動非同期" "$N_CENAS シーン ≤ しきい値 $LIMIAR_ASSINCRONO — REFCAP_LIMIAR_ASSINCRONO=2 でサービスを再起動してください"
    else
        POST /caption/batch "$ITENS"
        if [ "$HTTP" = "202" ]; then
            ok "14. ★ しきい値超過 → 202 非同期"
            det "state=$(J "$R" "d['state']")  check_at=$(J "$R" "d['check_at']")"
            sleep 10
        else nok "14. 非同期" "HTTP=$HTTP (期待値: 202)"; fi
    fi
fi

# =============================================================================
t "ブロック 4 — 照会と永続化"

if ! pula 15; then
    GET "/caption/$PROGRAM_ID"
    T=$(J "$R" "d['summary']['total']")
    if [ "$HTTP" = "200" ] && [ -n "$T" ] && [ "$T" -ge 1 ]; then
        ok "15. GET /caption/$PROGRAM_ID — 永続化された内容"
        det "保存済みシーン数: $T"
    else nok "15. GET 全件" "HTTP=$HTTP total=$T"; fi
fi

if ! pula 16; then
    GET "/caption/$PROGRAM_ID?scene_id=$UNICA_SID"
    T=$(J "$R" "d['summary']['total']")
    [ "$T" = "1" ] && ok "16. 1 シーンで絞り込んだ GET" || nok "16. 絞り込み 1" "total=$T"
fi

if ! pula 17; then
    if [ -z "$LOTE_A1_SID" ]; then skip "17. 2 条件で絞り込んだ GET" "2 つ目のシーンなし"
    else
        GET "/caption/$PROGRAM_ID?scene_id=$UNICA_SID&scene_id=$LOTE_A1_SID"
        T=$(J "$R" "d['summary']['total']")
        [ "$T" = "2" ] && ok "17. 2 シーンで絞り込んだ GET" || nok "17. 絞り込み 2" "total=$T"
    fi
fi

if ! pula 18; then
    GET "/caption/programa_que_nunca_existiu"
    T=$(J "$R" "d['summary']['total']")
    { [ "$HTTP" = "200" ] && [ "$T" = "0" ]; } \
        && ok "18. 存在しない番組の GET → 200 + 空" \
        || nok "18. 存在しない番組の GET" "HTTP=$HTTP total=$T"
fi

# =============================================================================
t "ブロック 5 — 番組間の分離"

if ! pula 19; then
    if [ -z "$ISO_SID" ]; then skip "19. ★ 分離" "teste_config.sh に PROGRAM_ID_2 がない"
    else
        POST /caption "$(item "$ISO_SID" "$ISO_VID" "$ISO_PATH" "$PROGRAM_ID_2")"
        S=$(J "$R" "d['items'][0]['status']")
        if [ "$HTTP" = "200" ] && [ "$S" = "success" ]; then
            C2=$(J "$R" "d['items'][0]['scene_caption_en']")
            ok "19. 2 つ目の番組のシーン ($PROGRAM_ID_2)"
            det "キャプション: $C2"
            if [ "$ISO_MESMO_SID" = "1" ]; then
                GET "/caption/$PROGRAM_ID?scene_id=$ISO_SID"
                C1=$(J "$R" "d['items'][0]['scene_caption_en']")
                det "$PROGRAM_ID/$ISO_SID  : ${C1:-—}"
                det "$PROGRAM_ID_2/$ISO_SID: $C2"
                if [ -n "$C1" ] && [ "$C1" = "$C2" ]; then
                    printf "       ${cA}⚠️  キャプションが同一 — 動画が異なるなら、キャッシュが漏洩している${cF}\n"
                elif [ -n "$C1" ]; then
                    det "★ キャプションが異なる — キャッシュは program_id ごとに分離されている"
                fi
            fi
        else nok "19. 分離" "HTTP=$HTTP status=$S"; fi
    fi
fi

if ! pula 20; then
    if [ -z "$PROGRAM_ID_2" ]; then skip "20. 2 つ目の番組の GET" "PROGRAM_ID_2 なし"
    else
        GET "/caption/$PROGRAM_ID_2"
        T=$(J "$R" "d['summary']['total']")
        [ "$HTTP" = "200" ] && [ -n "$T" ] && [ "$T" -ge 1 ] \
            && { ok "20. GET /caption/$PROGRAM_ID_2 — 別々に永続化されている"; det "シーン数: $T"; } \
            || nok "20. 番組 2 の GET" "HTTP=$HTTP total=$T"
    fi
fi

# =============================================================================
t "終了処理 — モデルは常駐したままか？"
GET /health; GPU1=$(J "$R" "d['models']['gpu'].get('allocated_mb','—')")
echo "  allocated_mb（開始時）: $GPU0"
echo "  allocated_mb（終了時）: $GPU1"
if [ "$GPU0" = "$GPU1" ]; then
    printf "  ${cV}✓ 同一 — モデルを再読み込みしたリクエストはない${cF}\n"
else
    printf "  ${cA}⚠️  変化した — 何かが再読み込みしていないか調査してください${cF}\n"
fi

t "結果"
printf "  ${cV}合格 %d${cF}   ${cR}失敗 %d${cF}   ${cA}スキップ %d${cF}\n" "$OK" "$ERRO" "$PULO"
echo
if [ "$ERRO" -eq 0 ]; then
    echo "  ✓ 実行したケースはすべて合格。"
    [ "$PULO" -gt 0 ] && echo "    スキップされたケースには、現在のセットにないシーンが必要 —"
    [ "$PULO" -gt 0 ] && echo "    カバーするには teste_config.sh（VIDEO_IDS, PROGRAM_ID_2）を調整してください。"
else
    echo "  ✗ 上記に失敗がある。"
fi
exit $([ "$ERRO" -eq 0 ] && echo 0 || echo 1)
