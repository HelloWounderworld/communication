#!/usr/bin/env bash
# =============================================================================
# diagnostico_mount.sh — マウントしたディレクトリが「見つからない」理由
#
# ★ 核心となる問い
#   「ディレクトリは存在するか？」ではない — 「誰にとって存在するのか？」だ。
#
#   シェルはあなたとして動く。サービスは supervisord（または systemd）の
#   ユーザーとして動く。あるユーザーが行った CIFS/SMB マウントは、適切な
#   オプションでマウントしない限り、他のユーザーからは見えないことが多い。
#   それが症状の正体: あなたが `ls` するとすべて見えるのに、サービスは 404 を返す。
#
#   このスクリプトは両側をチェックして比較する。
#
# 使い方
#     bash diagnostico_mount.sh                    # teste_config.sh を読む
#     bash diagnostico_mount.sh /マウント済みの/パス
#     API=http://host:8000 bash diagnostico_mount.sh /パス
# =============================================================================

AQUI="$(cd "$(dirname "$0")" && pwd)"
CONFIG="${CONFIG:-$AQUI/teste_config.sh}"

cV='\033[0;32m'; cR='\033[0;31m'; cA='\033[0;33m'; cC='\033[0;36m'; cF='\033[0m'
t() { echo; echo "═══════════════════════════════════════════════════════════════════"; echo " $1"; echo "═══════════════════════════════════════════════════════════════════"; }
ok()  { printf "  ${cV}✓${cF} %s\n" "$1"; }
mal() { printf "  ${cR}✗${cF} %s\n" "$1"; }
av()  { printf "  ${cA}⚠️${cF}  %s\n" "$1"; }
det() { printf "     ${cC}%s${cF}\n" "$1"; }

# --------------------------------------------------------------------------- #
if [ -n "$1" ]; then
    BASE="$1"
elif [ -f "$CONFIG" ]; then
    . "$CONFIG"
    API="${API:-${API_SCHEME:-http}://${API_HOST:-localhost}:${API_PORT:-8000}}"
else
    echo "使い方: bash diagnostico_mount.sh /マウント済みの/パス"; exit 1
fi
API="${API:-http://localhost:8000}"

t "調査対象"
printf "  %-14s %s\n" "BASE"        "$BASE"
printf "  %-14s %s\n" "PROGRAM_ID"  "${PROGRAM_ID:-—}"
printf "  %-14s %s\n" "API"         "$API"
printf "  %-14s %s (uid=%s)\n" "実行ユーザー" "$(id -un)" "$(id -u)"

# =============================================================================
t "0. ★ API はコンテナで動いているか？"

EM_DOCKER=0
if command -v docker >/dev/null 2>&1; then
    CTR=$(docker ps --format '{{.Names}}\t{{.Ports}}' 2>/dev/null | grep -iE 'caption|refcap|api' | head -1)
    if [ -n "$CTR" ]; then
        EM_DOCKER=1
        NOME=$(echo "$CTR" | cut -f1)
        ok "コンテナを検出: $NOME"
        det "ポート: $(echo "$CTR" | cut -f2)"
        echo
        printf "  ${cA}★ これですべてが変わる${cF}\n"
        echo "    コンテナは独自のファイルシステムを持つ。ホストで行った SMB マウントは、"
        echo "    bind-mount しない限りコンテナ内には存在しない。"
        echo
        echo "    そして、値は逆のルールに従う:"
        echo "      API の URL         -> ホストのポート"
        echo "      scene_video_path   -> コンテナ内のパス"
        echo
        echo "  このコンテナの bind-mount:"
        docker inspect "$NOME" --format '{{range .Mounts}}     {{.Source}} -> {{.Destination}} ({{if .RW}}rw{{else}}ro{{end}}){{"\n"}}{{end}}' 2>/dev/null
        echo
        echo "  ★ コンテナから BASE は見えるか？"
        if docker exec "$NOME" test -d "$BASE" 2>/dev/null; then
            ok "はい — $BASE はコンテナ内に存在する"
            det "$(docker exec "$NOME" ls "$BASE" 2>/dev/null | head -5 | tr '\n' ' ')"
        else
            mal "いいえ — $BASE はコンテナ内に存在しない"
            echo
            echo "     ★ これが原因。docker-compose.yml に次を追加してください:"
            echo
            echo "         volumes:"
            echo "           - $BASE:$BASE:ro"
            echo
            echo "     両側で同じパスを使えば、ホストとコンテナ間のパス変換が"
            echo "     不要になる。その後:  docker compose up -d"
        fi
    else
        det "caption/refcap/api という名前の稼働中コンテナはない"
        det "（API がホスト上で直接動いているなら、このブロックは無視してよい）"
    fi
else
    det "docker が見つからない — API はホスト上で動いているとみなす"
fi

t "1. ここから見たパス（あなたのシェル$([ "$EM_DOCKER" = "1" ] && echo "、ホスト上")）"

if [ -d "$BASE" ]; then
    ok "ユーザー $(id -un) にとって、ディレクトリは存在する"
else
    mal "ユーザー $(id -un) にとって、ディレクトリは存在しない"
    det "入力ミスがないか、マウントが生きているかを確認してください"
fi

if [ -r "$BASE" ]; then ok "読み取り権限がある"
else mal "読み取り権限がない"; fi

if [ -x "$BASE" ]; then ok "ディレクトリに入れる（x ビット）"
else mal "実行ビットがない — 中に入れない"; fi

echo
echo "  パーミッションと所有者:"
ls -ld "$BASE" 2>/dev/null | sed 's/^/     /' || det "（読み取れなかった）"

# =============================================================================
t "2. マウントか？ その種類は？"

MONTAGEM=""
if command -v findmnt >/dev/null; then
    MONTAGEM=$(findmnt -T "$BASE" -o TARGET,SOURCE,FSTYPE,OPTIONS 2>/dev/null)
    [ -n "$MONTAGEM" ] && echo "$MONTAGEM" | sed 's/^/     /'
else
    MONTAGEM=$(mount 2>/dev/null | grep -F "$BASE")
    [ -n "$MONTAGEM" ] && echo "$MONTAGEM" | sed 's/^/     /'
fi

FSTYPE=$(findmnt -T "$BASE" -no FSTYPE 2>/dev/null)
OPCOES=$(findmnt -T "$BASE" -no OPTIONS 2>/dev/null)

echo
case "$FSTYPE" in
    cifs|smb3|smbfs)
        ok "CIFS/SMB マウントである"
        echo
        echo "  ★ 誰から見えるかを決めるオプション:"
        for opt in uid gid file_mode dir_mode noperm multiuser; do
            valor=$(echo "$OPCOES" | tr ',' '\n' | grep "^${opt}" | head -1)
            if [ -n "$valor" ]; then printf "     ${cV}✓${cF} %s\n" "$valor"
            else printf "     ${cA}○${cF} %s (なし)\n" "$opt"; fi
        done
        echo
        if ! echo "$OPCOES" | grep -q "uid="; then
            av "マウントに uid= がない"
            det "これがないと、ファイルはマウントしたユーザーの所有になる — パスが"
            det "存在していても、サービスのユーザーは読めないことがある。"
        fi
        ;;
    nfs|nfs4)  ok "NFS — uid/gid についての注意点は同様に当てはまる" ;;
    "")        av "マウントを特定できなかった — ローカルのパスかもしれない" ;;
    *)         ok "ファイルシステム: $FSTYPE" ;;
esac

# =============================================================================
t "3. 想定されるディレクトリ構造"

if [ -d "$BASE" ]; then
    echo "  BASE のサブディレクトリ（program_id に相当）:"
    find "$BASE" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -10 | \
        while read -r d; do printf "     %s\n" "$(basename "$d")"; done
    N=$(find "$BASE" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    [ "$N" -eq 0 ] && av "サブディレクトリがない — BASE の階層は正しいか？"

    if [ -n "$PROGRAM_ID" ]; then
        echo
        D="$BASE/$PROGRAM_ID"
        if [ -d "$D" ]; then
            ok "$PROGRAM_ID は存在する"
            echo "     その中の video_id:"
            find "$D" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -8 | \
                while read -r v; do
                    n=$(find "$v" -maxdepth 1 -iname '*.mp4' 2>/dev/null | wc -l)
                    printf "       %-24s %s .mp4\n" "$(basename "$v")" "$n"
                done
        else
            mal "$PROGRAM_ID は $BASE に存在しない"
            det "★ 大文字・小文字に注意: SMB マウントは Windows 側では大文字小文字を"
            det "  区別しないことがあるが、Linux はバイト単位で比較する。'Prog' ≠ 'prog'。"
        fi
    fi
fi

# =============================================================================
t "4. ★ サービスから見えるもの  (重要なのはこの比較)"

if ! command -v curl >/dev/null; then
    av "curl がない — この部分はスキップする"
elif ! curl -s -m 5 -o /dev/null "$API/health" 2>/dev/null; then
    av "$API の API が応答しない — 比較できない"
    det "サービスを起動して、このスクリプトを再実行してください"
else
    # ここに存在するパスをサービスに問い合わせ、何と答えるかを見る。
    ALVO=$(find "$BASE" -iname '*.mp4' 2>/dev/null | head -1)
    if [ -z "$ALVO" ]; then
        av "ここに .mp4 が見つからない — 比較対象がない"
    else
        echo "  テスト用ファイル（あなたには存在する）:"
        det "$ALVO"
        echo
        RESP=$(curl -s -m 20 --get "$API/diagnostics/caption" \
               --data-urlencode "scene_video_path=$ALVO" 2>/dev/null)
        CODIGO=$(curl -s -m 20 -o /dev/null -w '%{http_code}' --get \
                 "$API/diagnostics/caption" \
                 --data-urlencode "scene_video_path=$ALVO" 2>/dev/null)

        if [ "$CODIGO" = "404" ]; then
            mal "サービスからはこのファイルが見えない (HTTP 404)"
            echo
            echo "$RESP" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin).get('detail', {})
except Exception:
    print('     （レスポンスを解釈できない）'); raise SystemExit
print(f\"     サービスから親ディレクトリは見えるか？ {d.get('existe_o_diretorio')}\")
viz = d.get('primeiros_arquivos_la') or []
print(f\"     サービスがそこで列挙したもの: {viz if viz else '（なし）'}\")
" 2>/dev/null
            echo
            printf "  ${cA}★ これが診断結果:${cF} パスはあなたには存在するが、サービスには\n"
            echo "    存在しない。原因はほぼ必ず次の 3 つのいずれか:"
            echo
            echo "    a) ユーザーが異なる"
            echo "       あなたは $(id -un) として実行している。サービスは supervisord の"
            echo "       'user=' として動く。確認してください:"
            echo "           grep -E '^user=' /etc/supervisor/conf.d/*.conf"
            echo "           sudo -u <サービスのユーザー> ls '$BASE'"
            echo
            echo "    b) マウントが共有されていない"
            echo "       あるユーザーが行ったマウントは、他のユーザーには見えない。"
            echo "       サービスのユーザーの uid/gid で再マウントしてください:"
            echo "           sudo mount -t cifs //servidor/share '$BASE' \\"
            echo "             -o username=USER,uid=\$(id -u SERVICO),gid=\$(id -g SERVICO),\\"
            echo "                file_mode=0644,dir_mode=0755"
            echo
            echo "    c) マウント名前空間が分離されている"
            echo "       supervisord/systemd が独自の名前空間で起動していると、後から"
            echo "       行ったマウントは見えない。サービスを再起動してください:"
            echo "           sudo supervisorctl restart refcap-api"
        elif [ -n "$CODIGO" ]; then
            ok "サービスからもファイルが見える (HTTP $CODIGO)"
            det "マウントの問題ではない — teste_config.sh の BASE/PROGRAM_ID を確認してください"
        fi
    fi
fi

# =============================================================================
t "5. よく引っかかる追加チェック"

# 空白や不可視文字
if [ "$BASE" != "$(echo "$BASE" | tr -d '[:space:]' | sed 's|/*$||')" ]; then
    LIMPO=$(echo "$BASE" | xargs)
    [ "$BASE" != "$LIMPO" ] && av "BASE の先頭または末尾に空白がある — 余計な引用符を取り除いてください"
fi
case "$BASE" in
    */) av "BASE が '/' で終わっている — 動作はするが、パスが '//' にならないよう避けること" ;;
esac
case "$BASE" in
    ~*) mal "BASE に '~' が使われている — 引用符の中では展開されない。絶対パスを使ってください。" ;;
esac

# マウントが切れていないか？
if [ -d "$BASE" ] && [ -z "$(ls -A "$BASE" 2>/dev/null)" ]; then
    av "ディレクトリは存在するが空"
    det "SMB マウントが切れると、マウントポイントが空のまま残ることが多い"
    det "確認:  mount | grep -i cifs   と   dmesg | tail"
fi

t "まとめ"
cat <<'FIM'
  解決の順番:

    1. あなたには `ls -l` が動くか？                (ブロック 1)
    2. CIFS マウントで、uid=/gid= があるか？        (ブロック 2)
    3. program_id/video_id の構造は合っているか？   (ブロック 3)
    4. ★ サービスから同じファイルが見えるか？       (ブロック 4)

  1〜3 が通って 4 が失敗するなら、パスではなく権限か名前空間の問題。

  ★ Docker では、原因はほぼ必ずブロック 0: ホストのマウントがコンテナ内に
    bind-mount されていない。DOCKER.md を参照。
FIM
