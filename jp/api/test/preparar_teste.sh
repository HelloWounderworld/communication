#!/usr/bin/env bash
# =============================================================================
# preparar_teste.sh — シーンを見つけ出し、テストのロールに振り分ける
#
# ★ 何も作成しない。既存のものを読んで対応表を組み立てるだけ。
#   （ディレクトリが空で ffmpeg があれば、シーンの生成を提案する。）
#
# 使い方
#     bash preparar_teste.sh              # teste_config.sh を読む
#     bash preparar_teste.sh --gerar      # 空ならば合成シーンを生成する
#
# 生成物
#     teste_papeis.sh — 対応表。teste_manual.sh が読み込む
# =============================================================================

AQUI="$(cd "$(dirname "$0")" && pwd)"
CONFIG="${CONFIG:-$AQUI/teste_config.sh}"
PAPEIS="${PAPEIS:-$AQUI/teste_papeis.sh}"

V='\033[0;32m'; A='\033[0;33m'; R='\033[0;31m'; C='\033[0;36m'; F='\033[0m'
t() { echo; echo "═══════════════════════════════════════════════════════════════════"; echo " $1"; echo "═══════════════════════════════════════════════════════════════════"; }

[ -f "$CONFIG" ] || { printf "${R}✗ %s が見つからない${F}\n" "$CONFIG"; exit 1; }
# shellcheck disable=SC1090
. "$CONFIG"

API="${API_SCHEME}://${API_HOST}:${API_PORT}"

# ★ 2 つのパス
#   BASE_HOST  このスクリプトが .mp4 を探す場所
#   BASE_API   リクエストの scene_video_path に入るプレフィックス
#
# Docker 導入前の config 向けに、旧来の `BASE` も受け付ける。
EXT="${EXT:-.mp4}"
BASE_HOST="${BASE_HOST:-$BASE}"
BASE_API="${BASE_API:-$BASE_HOST}"
CONTAINER="${CONTAINER:-}"
COMPOSE_FILE="${COMPOSE_FILE:-}"

# traduz_para_api <ホスト上のパス>
# ホストのプレフィックスをコンテナのものに置き換える。変換が設定されて
# いなければ、パスをそのまま返す。
traduz_para_api() {
    case "$1" in
        "$BASE_HOST"*) echo "$BASE_API${1#$BASE_HOST}" ;;
        *)             echo "$1" ;;
    esac
}

# ═══════════════════════════════════════════════════════════════════════════
# モード A — 宣言
#
# ★ CENAS_A が記入されていれば、宣言された内容から直接パスを組み立てる。
#   ファイルシステムには一切アクセスしない — ホストにもコンテナにも。
#
#   常に動作するモード: curl を手で組み立てるのと同じ。探索（モード B）は
#   シーンが分からない場合のためだけにあり、ディレクトリを読めることに
#   依存する — Docker + SMB の環境では、これがよく
#   失敗する。
# ═══════════════════════════════════════════════════════════════════════════
if [ -n "$CENAS_A" ]; then
    t "宣言モード — 指定されたシーンを使用"
    printf "  %-14s %s\n" "API"        "$API"
    printf "  %-14s %s\n" "BASE_API"   "$BASE_API"
    printf "  %-14s %s\n" "PROGRAM_ID" "$PROGRAM_ID"
    echo
    EXT="${EXT:-.mp4}"

    cam() { echo "$BASE_API/$PROGRAM_ID/$1/$2$EXT"; }

    # --- ディレクトリ A ---
    set -- $CENAS_A
    A1="$1"; A2="${2:-}"; A3="${3:-}"
    printf "  %-10s %-12s %s\n" "$VIDEO_A" "$A1" "$(cam "$VIDEO_A" "$A1")"
    [ -n "$A2" ] && printf "  %-10s %-12s %s\n" "" "$A2" "$(cam "$VIDEO_A" "$A2")"
    [ -n "$A3" ] && printf "  %-10s %-12s %s\n" "" "$A3" "$(cam "$VIDEO_A" "$A3")"

    # --- ディレクトリ B（任意） ---
    B1=""
    if [ -n "$VIDEO_B" ] && [ -n "$CENAS_B" ]; then
        set -- $CENAS_B; B1="$1"
        echo
        printf "  %-10s %-12s %s\n" "$VIDEO_B" "$B1" "$(cam "$VIDEO_B" "$B1")"
    fi

    # --- ロールを組み立てる ---
    UNICA_SID="$A1";  UNICA_VID="$VIDEO_A";  UNICA_PATH="$(cam "$VIDEO_A" "$A1")"
    LOTE_A1_SID="${A2:-$A1}"; LOTE_A1_VID="$VIDEO_A"; LOTE_A1_PATH="$(cam "$VIDEO_A" "${A2:-$A1}")"
    LOTE_A2_SID="${A3:-${A2:-$A1}}"; LOTE_A2_VID="$VIDEO_A"; LOTE_A2_PATH="$(cam "$VIDEO_A" "${A3:-${A2:-$A1}}")"
    if [ -n "$B1" ]; then
        LOTE_B1_SID="$B1"; LOTE_B1_VID="$VIDEO_B"; LOTE_B1_PATH="$(cam "$VIDEO_B" "$B1")"
    else
        LOTE_B1_SID=""; LOTE_B1_VID=""; LOTE_B1_PATH=""
    fi
    if [ -n "$CENA_CURTA" ]; then
        CURTA_SID="$CENA_CURTA"; CURTA_VID="${CENA_CURTA_VIDEO:-$VIDEO_A}"
        CURTA_PATH="$(cam "${CENA_CURTA_VIDEO:-$VIDEO_A}" "$CENA_CURTA")"; CURTA_DUR="<1"
    else
        CURTA_SID=""; CURTA_VID=""; CURTA_PATH=""; CURTA_DUR=""
    fi

    # 全シーン（全件バッチ用）
    TODAS=""
    for c in $CENAS_A; do TODAS="$TODAS $VIDEO_A:$c:$(cam "$VIDEO_A" "$c")"; done
    for c in $CENAS_B; do TODAS="$TODAS $VIDEO_B:$c:$(cam "$VIDEO_B" "$c")"; done
    TODAS="${TODAS# }"
    N_CENAS=$(echo "$TODAS" | wc -w)
    N_DIRS=$([ -n "$B1" ] && echo 2 || echo 1)

    # 2 つ目の番組（分離テスト用）
    ISO_SID=""; ISO_VID=""; ISO_PATH=""; MESMO=0
    if [ -n "$PROGRAM_ID_2" ]; then
        ISO_VID="${VIDEO_ID_2:-$VIDEO_A}"
        ISO_SID="${CENA_ISO:-$A1}"
        ISO_PATH="$BASE_API/$PROGRAM_ID_2/$ISO_VID/$ISO_SID$EXT"
        [ "$ISO_SID" = "$A1" ] && MESMO=1
    fi

    t "ロール"
    pp() { if [ -n "$2" ]; then printf "  ${cV}✓${cF} %-11s %-16s %s\n" "$1" "$2" "$3"
           else printf "  ${cA}○${cF} %-11s %-16s %s\n" "$1" "(なし)" "$3"; fi; }
    pp "UNICA"   "$UNICA_SID"   "POST /caption + キャッシュ"
    pp "LOTE_A1" "$LOTE_A1_SID" "バッチ — 同一ディレクトリ"
    pp "LOTE_A2" "$LOTE_A2_SID" "バッチ — 同一ディレクトリ"
    pp "LOTE_B1" "$LOTE_B1_SID" "★ 別ディレクトリ — グルーピング"
    pp "CURTA"   "$CURTA_SID"   "★ 1 秒未満 — viddataset のパッチ"
    pp "ISOLAM." "$ISO_SID"     "★ 別の program_id"

    DIR_VAZIO="/tmp/refcap_teste_dir_vazio"; mkdir -p "$DIR_VAZIO" 2>/dev/null
    DIR_COM_VIDEO="$BASE_API/$PROGRAM_ID/$VIDEO_A"
    DECLARADO=1
fi

if [ -z "$DECLARADO" ]; then

t "読み込んだ設定"
printf "  %-14s %s\n" "API"        "$API"
printf "  %-14s %s\n" "BASE_HOST"  "$BASE_HOST"
printf "  %-14s %s%s\n" "BASE_API"   "$BASE_API" \
    "$([ "$BASE_API" != "$BASE_HOST" ] && echo '   ← リクエストに入るパス')"
[ -n "$CONTAINER" ] && printf "  %-14s %s\n" "CONTAINER" "$CONTAINER   ← docker exec で列挙"
printf "  %-14s %s\n" "PROGRAM_ID" "$PROGRAM_ID"
printf "  %-14s %s\n" "VIDEO_IDS"  "${VIDEO_IDS:-(自動探索)}"
printf "  %-14s %s\n" "PROGRAM_ID_2" "${PROGRAM_ID_2:-(分離テストなし)}"
printf "  %-14s %s\n" "MAX_CENAS"  "$MAX_CENAS"

# --------------------------------------------------------------------------- #
DIR_PROG="$BASE_HOST/$PROGRAM_ID"

# ★ コンテナ内での実行方法を判別する。
#
# `docker exec` はコンテナ名（例: projeto-caption-api-1）を受け取る。
# `docker compose exec` はサービス名（例: caption-api）を受け取る。
#
# どちらが指定されたかは推測できないので、両方を試して動いた方を
# 使う。正しいコマンドを $DEXEC に設定する。
descobrir_exec() {
    # 1) コンテナ名で docker exec
    #    ★ どのディレクトリからでも動く方法: docker-compose.yml を読まず、
    #      Docker デーモンとだけ通信する。
    if docker exec "$CONTAINER" true 2>/dev/null; then
        DEXEC="docker exec $CONTAINER"
        det "使用: docker exec $CONTAINER   (コンテナ名)"
        return 0
    fi

    # 2) 指定されたファイルで docker compose exec
    if [ -n "$COMPOSE_FILE" ] && [ -f "$COMPOSE_FILE" ]; then
        if docker compose -f "$COMPOSE_FILE" exec -T "$CONTAINER" true 2>/dev/null; then
            DEXEC="docker compose -f $COMPOSE_FILE exec -T $CONTAINER"
            det "使用: docker compose -f $COMPOSE_FILE exec -T $CONTAINER"
            return 0
        fi
    fi

    # 3) カレントディレクトリのファイルで docker compose exec
    if docker compose exec -T "$CONTAINER" true 2>/dev/null; then
        DEXEC="docker compose exec -T $CONTAINER"
        det "使用: docker compose exec -T $CONTAINER   (カレントディレクトリの compose)"
        return 0
    fi

    # 4) CONTAINER はサービス名か？ コンテナへの解決を試みる
    if [ -n "$COMPOSE_FILE" ] && [ -f "$COMPOSE_FILE" ]; then
        RESOLVIDO=$(docker compose -f "$COMPOSE_FILE" ps -q "$CONTAINER" 2>/dev/null | head -1)
        if [ -n "$RESOLVIDO" ] && docker exec "$RESOLVIDO" true 2>/dev/null; then
            DEXEC="docker exec $RESOLVIDO"
            det "サービス '$CONTAINER' をコンテナ ${RESOLVIDO:0:12} に解決"
            return 0
        fi
    fi
    return 1
}

# ★ コンテナモード: ホストからファイルが見えない（マウントがコンテナ内に
#   しか存在しない）場合、`docker exec` で列挙する。このとき BASE_HOST は
#   無関係 — すべて BASE_API 上で解決される。
if [ -n "$CONTAINER" ]; then
    if ! command -v docker >/dev/null; then
        printf "\n${cR}✗ CONTAINER が設定されているが、docker が PATH にない${cF}\n"; exit 1
    fi
    if ! descobrir_exec; then
        printf "\n${cR}✗ '%s' 内で実行できなかった${cF}\n" "$CONTAINER"
        echo
        echo "  4 通り試したが、すべて失敗した:"
        echo "      1. docker exec $CONTAINER"
        echo "      2. docker compose -f \"$COMPOSE_FILE\" exec -T $CONTAINER"
        echo "      3. docker compose exec -T $CONTAINER   (カレントの compose)"
        echo "      4. '$CONTAINER' をサービスとして解決し、その ID を使う"
        echo
        printf "  ${cA}★ いちばん簡単な解決策${cF}\n"
        echo '    コンテナ名を使う — docker exec は docker-compose.yml が'
        echo "    なくても、どのディレクトリからでも動く:"
        echo
        echo "        docker ps --format '{{.Names}}'"
        echo
        echo "    表示された名前をコピーし、config の CONTAINER に設定してください。"
        echo
        echo "  サービス名を使いたい場合は、compose ファイルの"
        echo "  場所を指定してください:"
        echo "        COMPOSE_FILE=\"../../.docker/docker-compose.yml\""
        echo
        printf "  ${cA}★ あるいは、これらはすべて無視して${cF}\n"
        echo "    teste_config.sh の CENAS_A を記入し、宣言モードを"
        echo "    使ってください — コンテナ内では何も実行しません。"
        exit 1
    fi
    # ★ <BASE_API>/<PROGRAM_ID> と <BASE_API> のどちらも受け付ける — どちらを使うかは探索側が決める
    DIR_PROG_API="$BASE_API/$PROGRAM_ID"
    if ! $DEXEC test -d "$DIR_PROG_API" 2>/dev/null && ! $DEXEC test -d "$BASE_API" 2>/dev/null; then
        printf "\n${cR}✗ コンテナ内に、次のいずれも存在しない:${cF}\n"
        printf "     %s\n     %s\n" "$DIR_PROG_API" "$BASE_API"
        echo "  $BASE_API の中身:"
        docker exec "$CONTAINER" ls "$BASE_API" 2>/dev/null | head -10 | sed 's/^/     /'
        echo
        echo "  teste_config.sh の BASE_API と PROGRAM_ID を確認してください。"
        exit 1
    fi
elif [ ! -d "$DIR_PROG" ] && [ ! -d "$BASE_HOST" ]; then
    if [ "$1" = "--gerar" ] && command -v ffmpeg >/dev/null; then
        t "合成シーンを生成中"
        mkdir -p "$DIR_PROG/vidA" "$DIR_PROG/vidB"
        g() { ffmpeg -f lavfi -i "testsrc=duration=$2:size=320x240:rate=25" \
                     -y "$1" -loglevel error 2>/dev/null; echo "  ${1#$BASE_HOST/}  ${2}s"; }
        g "$DIR_PROG/vidA/cena_01.mp4" 3
        g "$DIR_PROG/vidA/cena_02.mp4" 2
        g "$DIR_PROG/vidA/cena_03.mp4" 0.5
        g "$DIR_PROG/vidB/cena_04.mp4" 3
        g "$DIR_PROG/vidB/cena_05.mp4" 2
        if [ -n "$PROGRAM_ID_2" ]; then
            mkdir -p "$BASE_HOST/$PROGRAM_ID_2/${VIDEO_ID_2:-vidX}"
            g "$BASE_HOST/$PROGRAM_ID_2/${VIDEO_ID_2:-vidX}/cena_01.mp4" 2
        fi
    else
        printf "\n${cR}✗ ホスト上に、次のいずれも存在しない:${cF}\n"
        printf "     %s\n     %s\n" "$DIR_PROG" "$BASE_HOST"
        echo
        echo "  解決策は 3 つ:"
        echo "    1. teste_config.sh の BASE_HOST と PROGRAM_ID を修正する"
        echo "    2. ファイルがコンテナ内にしか存在しないなら、config に"
        echo "       CONTAINER=\"コンテナ名\" と BASE_API を指定する"
        echo "    3. テスト用シーンを生成する:  bash preparar_teste.sh --gerar"
        exit 1
    fi
fi

# --------------------------------------------------------------------------- #
t "見つかったシーン"

# 列挙: ホスト上、またはコンテナ内で行う。
# ★ MAPA の 3 番目のフィールドは常にリクエストに入るパス（変換がある場合は
#   コンテナ側のパス）— ホストのパスになることは決してない。
# 探索スクリプト。どちらのモードでも同じものを使う。
BUSCA_PY=$(cat <<'PYBUSCA'
import pathlib, subprocess, sys

# ★ 階層の深さに依存しない探索
#
# 以前の版は <raiz>/{video_id}/*.mp4 という構造を厳密に要求し、構造が
# 異なると説明なしに空を返していた。現在は:
#
#   1. <BASE_API>/<PROGRAM_ID> を試し、存在しなければ <BASE_API> を使う
#   2. .mp4 を再帰的に探す
#   3. video_id はルートから見た親ディレクトリ。ファイルがルート直下に
#      あれば、video_id は空になる
BASE_API, PROGRAM_ID, EXT = sys.argv[1], sys.argv[2], sys.argv[3]

candidatos = [pathlib.Path(BASE_API) / PROGRAM_ID, pathlib.Path(BASE_API)]
raiz = next((c for c in candidatos if c.is_dir()), None)
if raiz is None:
    print("__SEM_RAIZ__", "|".join(str(c) for c in candidatos), sep="\t")
    raise SystemExit

arquivos = sorted(raiz.rglob("*" + EXT))
if not arquivos:
    # 診断: そこに実際に何があるかを表示する
    itens = sorted(p.name + ("/" if p.is_dir() else "") for p in raiz.iterdir())[:15]
    print("__VAZIO__", str(raiz), "|".join(itens), sep="\t")
    raise SystemExit

def dur(p):
    try:
        r = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
                            "-show_entries","stream=duration","-of","csv=p=0",str(p)],
                           capture_output=True, text=True, timeout=20)
        return float(r.stdout.strip())
    except Exception:
        return -1.0

for f in arquivos:
    rel = f.relative_to(raiz)
    # video_id はルート直下の 1 階層目。ファイルがルート直下にあれば空
    vid = rel.parts[-2] if len(rel.parts) >= 2 else ""
    print("%s|%s|%s|%.3f" % (vid, f.stem, f, dur(f)))
PYBUSCA
)

if [ -n "$CONTAINER" ]; then
    # ★ stderr は捨てない: コンテナ内で失敗したら、その内容を見たい。
    ERRO_CTR=$(mktemp)
    BRUTO=$($DEXEC python3 -c "$BUSCA_PY" "$BASE_API" "$PROGRAM_ID" "$EXT" 2>"$ERRO_CTR")
else
    ERRO_CTR=$(mktemp)
    BRUTO=$(python3 -c "$BUSCA_PY" "$BASE_HOST" "$PROGRAM_ID" "$EXT" 2>"$ERRO_CTR")
fi

# --- 探索スクリプトは 2 つの失敗ケースを明示的に報告する ---
case "$BRUTO" in
    __SEM_RAIZ__*)
        printf "\n${cR}✗ 次のパスはいずれも存在しない:${cF}\n"
        echo "$BRUTO" | cut -f2 | tr '|' '\n' | sed 's/^/     /'
        echo
        echo "  teste_config.sh の BASE_API と PROGRAM_ID を確認してください。"
        rm -f "$ERRO_CTR"; exit 1 ;;
    __VAZIO__*)
        RAIZ_USADA=$(echo "$BRUTO" | cut -f2)
        CONTEUDO=$(echo "$BRUTO" | cut -f3)
        printf "\n${cR}✗ %s ファイルが %s に 1 つもない${cF}\n" "$EXT" "$RAIZ_USADA"
        echo
        echo "  そこに実際にあるもの（再帰的に探索済み）:"
        echo "$CONTEUDO" | tr '|' '\n' | sed 's/^/     /'
        echo
        echo "  動画の拡張子が異なる場合は、teste_config.sh の EXT を修正してください。"
        rm -f "$ERRO_CTR"; exit 1 ;;
esac

if [ -z "$BRUTO" ]; then
    printf "\n${cR}✗ 探索が何も返さなかった${cF}\n"
    if [ -s "$ERRO_CTR" ]; then
        echo; echo "  エラー:"; sed 's/^/     /' "$ERRO_CTR" | head -12
    fi
    echo
    printf "  ${cA}★ 宣言モードを使ってください${cF} — config の CENAS_A を記入する。\n"
    echo "    コンテナ内で何も実行せず、ディスクも読みません。"
    rm -f "$ERRO_CTR"; exit 1
fi
rm -f "$ERRO_CTR"

# VIDEO_IDS で絞り込み、MAX_CENAS を適用し、パスを変換する
MAPA=$(printf '%s' "$BRUTO" | python3 -c "
import sys
filtro = [v for v in '''$VIDEO_IDS'''.split() if v]
limite = int('''$MAX_CENAS''' or 0)
b_host, b_api = '''$BASE_HOST''', '''$BASE_API'''

linhas = []
for l in sys.stdin.read().strip().splitlines():
    if not l.strip(): continue
    v, s, c, d = l.split('|')
    if filtro and v not in filtro: continue
    # ★ 変換: ホストのプレフィックスをコンテナのものに置き換える。
    #
    # ⚠️ 'b_host' は空であってはならない。空文字列だと
    # c.startswith('') は常に True になり、c[0:] はパス全体を返す —
    # 結果は b_api + 絶対パスとなり、プレフィックスが重複していた:
    #     '/dados/cenas' + '/dados/cenas/prog/x.mp4'
    #       = '/dados/cenas/dados/cenas/prog/x.mp4'
    #
    # コンテナモードでは b_host は空（探索はすでにコンテナ内で実行され、
    # 正しいパスを返す）なので、変換するものは何もない。
    if b_host and b_api and b_api != b_host and c.startswith(b_host):
        c = b_api + c[len(b_host):]
    try: d = float(d)
    except ValueError: d = -1.0
    linhas.append((v, s, c, d))

if limite > 0:
    # ★ 上限を最初のディレクトリで打ち切るのではなく、ディレクトリ間で配分する。
    # そのまま打ち切ると 2 つ目のディレクトリが外れてしまい、それがなければ
    # グルーピングをテストできない。
    por_dir = {}
    for t in linhas: por_dir.setdefault(t[0], []).append(t)
    saida, i = [], 0
    while len(saida) < limite:
        avancou = False
        for v in por_dir:
            if i < len(por_dir[v]) and len(saida) < limite:
                saida.append(por_dir[v][i]); avancou = True
        if not avancou: break
        i += 1
    linhas = saida

for v, s, c, d in linhas:
    print('%s|%s|%s|%.3f' % (v, s, c, d))
")

[ -z "$MAPA" ] && { printf "${R}✗ %s に .mp4 が 1 つもない${F}\n" "$DIR_PROG"; exit 1; }

printf "  %-14s %-22s %9s %7s\n" "video_id" "scene_id" "長さ" "フレーム数"
echo "  ─────────────────────────────────────────────────────────"
echo "$MAPA" | while IFS='|' read -r v s c d; do
    fr=$(python3 -c "print(max(1,int($d)) if $d>0 else '?')" 2>/dev/null)
    av=$(python3 -c "print(' <-- 1秒未満' if 0<$d<1 else '')" 2>/dev/null)
    printf "  %-14s %-22s %8.3fs %6s%s\n" "$v" "$s" "$d" "$fr" "$av"
done

N_TOTAL=$(echo "$MAPA" | wc -l)
N_DIRS=$(echo "$MAPA" | cut -d'|' -f1 | sort -u | wc -l)

# --------------------------------------------------------------------------- #
t "ロール — シーンの振り分け"

eval "$(python3 - <<PYEOF
linhas = [l.split("|") for l in """$MAPA""".strip().splitlines() if l.strip()]
por_dir = {}
for v, s, c, d in linhas:
    por_dir.setdefault(v, []).append((s, c, float(d)))

dirs = sorted(por_dir)
dA = dirs[0]
dB = dirs[1] if len(dirs) > 1 else ""

A = por_dir[dA]
B = por_dir[dB] if dB else []

def emit(nome, t, vid):
    if t:
        s, c, d = t
        print(f'{nome}_SID="{s}"; {nome}_VID="{vid}"; {nome}_PATH="{c}"; {nome}_DUR="{d:.3f}"')
    else:
        print(f'{nome}_SID=""; {nome}_VID=""; {nome}_PATH=""; {nome}_DUR=""')

# UNICA: POST /caption とキャッシュテストで使うシーン
emit("UNICA",  A[0] if len(A) > 0 else None, dA)
# LOTE_A1/A2: 同一ディレクトリの 2 シーン
emit("LOTE_A1", A[1] if len(A) > 1 else (A[0] if A else None), dA)
emit("LOTE_A2", A[2] if len(A) > 2 else (A[1] if len(A) > 1 else None), dA)
# LOTE_B1: 別ディレクトリ -> グルーピング
emit("LOTE_B1", B[0] if B else None, dB)

# 短いシーン（あれば）
curtas = [(s, c, d, v) for v in por_dir for s, c, d in por_dir[v] if 0 < d < 1.0]
if curtas:
    s, c, d, v = min(curtas, key=lambda x: x[2])
    print(f'CURTA_SID="{s}"; CURTA_VID="{v}"; CURTA_PATH="{c}"; CURTA_DUR="{d:.3f}"')
else:
    print('CURTA_SID=""; CURTA_VID=""; CURTA_PATH=""; CURTA_DUR=""')

# TODAS: 大きなバッチと非同期テスト用
todas = [f"{v}:{s}:{c}" for v in dirs for s, c, _ in por_dir[v]]
print(f'TODAS="{chr(32).join(todas)}"')
print(f'N_CENAS={len(todas)}; N_DIRS={len(dirs)}; DIR_A="{dA}"; DIR_B="{dB}"')
PYEOF
)"

p() {  # p <ロール> <値> <説明>
    if [ -n "$2" ]; then printf "  ${V}✓${F} %-11s %-24s %s\n" "$1" "$2" "$3"
    else printf "  ${A}○${F} %-11s %-24s %s\n" "$1" "(なし)" "$3"; fi
}
p "UNICA"   "$UNICA_SID"   "POST /caption + キャッシュテスト"
p "LOTE_A1" "$LOTE_A1_SID" "バッチ — 同一ディレクトリ"
p "LOTE_A2" "$LOTE_A2_SID" "バッチ — 同一ディレクトリ"
p "LOTE_B1" "$LOTE_B1_SID" "★ 別ディレクトリ — グルーピング"
p "CURTA"   "$CURTA_SID"   "★ 1 秒未満 — viddataset のパッチ"
echo
printf "  %-13s %s シーン / %s ディレクトリ\n" "合計:" "$N_CENAS" "$N_DIRS"

# --------------------------------------------------------------------------- #
# 2 つ目の番組（分離テスト用）
ISO_SID=""; ISO_VID=""; ISO_PATH=""
if [ -n "$PROGRAM_ID_2" ]; then
    D2="$BASE_HOST/$PROGRAM_ID_2/${VIDEO_ID_2}"
    [ -z "$VIDEO_ID_2" ] && D2=$(find "$BASE_HOST/$PROGRAM_ID_2" -mindepth 1 -maxdepth 1 -type d | head -1)
    if [ -d "$D2" ]; then
        # できれば UNICA と同じ scene_id のシーンを選ぶ — キャッシュの漏洩が
        # あれば、それを証明できるケース
        CAND="$D2/$UNICA_SID.mp4"
        [ -f "$CAND" ] || CAND=$(find "$D2" -maxdepth 1 -name '*.mp4' | head -1)
        if [ -f "$CAND" ]; then
            ISO_PATH="$CAND"; ISO_SID=$(basename "$CAND" .mp4); ISO_VID=$(basename "$D2")
        fi
    fi
fi
if [ -n "$ISO_SID" ]; then
    MESMO=$([ "$ISO_SID" = "$UNICA_SID" ] && echo "1" || echo "0")
    printf "  ${V}✓${F} %-11s %-24s %s\n" "ISOLAMENTO" "$PROGRAM_ID_2/$ISO_SID" \
        "$([ "$MESMO" = "1" ] && echo '★ 同一の scene_id — 完全なテスト' || echo '異なる scene_id')"
else
    MESMO=0
    printf "  ${A}○${F} %-11s %-24s %s\n" "ISOLAMENTO" "(なし)" "PROGRAM_ID_2 なし"
fi

# 空ディレクトリ。/tmp に作る — シーンのディレクトリ内には決して作らない
DIR_VAZIO="/tmp/refcap_teste_dir_vazio"; mkdir -p "$DIR_VAZIO"

fi   # 探索ブロック（モード B）の終わり

# --------------------------------------------------------------------------- #
cat > "$PAPEIS" <<CFG
#!/usr/bin/env bash
# $(date '+%Y-%m-%d %H:%M') に preparar_teste.sh が生成 — 手で編集しないこと。
# シーンを変更するには、teste_config.sh を修正して preparar_teste.sh を再実行する。

API="$API"
TIMEOUT="$TIMEOUT"
LIMIAR_ASSINCRONO="$LIMIAR_ASSINCRONO"
PROGRAM_ID="$PROGRAM_ID"
PROGRAM_ID_2="$PROGRAM_ID_2"

# POST /caption とキャッシュテストで使うシーン
UNICA_SID="$UNICA_SID"; UNICA_VID="$UNICA_VID"; UNICA_PATH="$UNICA_PATH"

# 同一ディレクトリの 2 シーン
LOTE_A1_SID="$LOTE_A1_SID"; LOTE_A1_VID="$LOTE_A1_VID"; LOTE_A1_PATH="$LOTE_A1_PATH"
LOTE_A2_SID="$LOTE_A2_SID"; LOTE_A2_VID="$LOTE_A2_VID"; LOTE_A2_PATH="$LOTE_A2_PATH"

# 別ディレクトリ — グルーピング
LOTE_B1_SID="$LOTE_B1_SID"; LOTE_B1_VID="$LOTE_B1_VID"; LOTE_B1_PATH="$LOTE_B1_PATH"

# 1 秒未満 — viddataset のパッチ
CURTA_SID="$CURTA_SID"; CURTA_VID="$CURTA_VID"; CURTA_PATH="$CURTA_PATH"; CURTA_DUR="$CURTA_DUR"

# 別の番組 — キャッシュの分離
ISO_SID="$ISO_SID"; ISO_VID="$ISO_VID"; ISO_PATH="$ISO_PATH"; ISO_MESMO_SID="$MESMO"

# 全シーン。形式は video:scene:path
TODAS="$TODAS"
N_CENAS=$N_CENAS
N_DIRS=$N_DIRS

DIR_VAZIO="$DIR_VAZIO"
DIR_COM_VIDEO="\$(dirname "$UNICA_PATH")"
CFG

t "完了"
echo "  対応表の保存先: $PAPEIS"
echo
[ "$N_DIRS" -lt 2 ] && printf "  ${A}⚠️  ディレクトリが 1 つだけ — グルーピングのテストはスキップされる。${F}\n     検証するには teste_config.sh に VIDEO_IDS を 2 つ指定してください。\n\n"
[ -z "$CURTA_SID" ] && printf "  ${A}⚠️  1 秒未満のシーンがない — このテストはスキップされる。${F}\n\n"
echo "  次は:  bash teste_manual.sh"
