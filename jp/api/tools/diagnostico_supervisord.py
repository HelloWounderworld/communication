#!/usr/bin/env python3
"""
diagnostico_supervisord.py — サービスが常駐し続けない理由を調査する。

`diagnostico_gpu.py` を補完する。あちらが torch と GPU を見るのに対し、
こちらは supervisord を見る: プロセスは本当に生きているのか、それとも
ループで再起動を繰り返しているのか？

使い方
    python diagnostico_supervisord.py --logs /var/log/refcap-api
    python diagnostico_supervisord.py --logs ./logs --programa refcap-api

再起動ループの特徴
--------------------------------
プロセスが読み込みの後に死ぬと、supervisord が再起動する。stdout には
同じ読み込みシーケンスが、異なる PID で繰り返し現れる:

    [PID 493] carregando cap_gen_model ...
    [PID 494] carregando cap_gen_model ...      <- PID が違う！
    [PID 497] carregando cap_gen_model ...

そして `supervisorctl status` には RUNNING ではなく BACKOFF または FATAL と表示される。
このシナリオはこうして再現した: 3 回試行した後に
"gave up: entered FATAL state, too many start retries too quickly"。

確認する項目（順番に）
---------------------
    1. supervisorctl status        -> RUNNING で uptime が増えているか？
    2. プログラムの stderr          -> 終了の本当の原因
    3. supervisord のログ           -> spawned / exited / gave up
    4. stdout 内の PID の数         -> 何回読み込まれたか？
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
from collections import Counter

LARG = 74


def titulo(t: str) -> None:
    print("\n" + "=" * LARG)
    print(f" {t}")
    print("=" * LARG)


# --------------------------------------------------------------------------- #
def bloco_status(programa: str, conf: str | None) -> None:
    titulo("1. supervisorctl status")
    cmd = ["supervisorctl"]
    if conf:
        cmd += ["-c", conf]
    cmd += ["status", programa]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        saida = (r.stdout + r.stderr).strip()
        print(f"  {saida or '（出力なし）'}")
    except FileNotFoundError:
        print("  supervisorctl が PATH に見つからない — 手動で実行してください:")
        print(f"      supervisorctl status {programa}")
        return
    except Exception as exc:  # noqa: BLE001
        print(f"  実行できなかった: {type(exc).__name__}: {exc}")
        return

    print("""
  読み方:
    RUNNING  pid 1234, uptime 0:15:32   -> ✓ 15 分間生存。2 回の確認の間で uptime が
                                            増えていれば安定している
    RUNNING  pid 5678, uptime 0:00:03   -> ⚠️ 起動した直後。30 秒後に再確認する:
                                            PID が変わっていればループ
    BACKOFF  Exited too quickly          -> ✗ 起動直後に終了している
    FATAL    too many start retries      -> ✗ 諦めた。stderr を確認する
    STOPPED                              -> 動いていない
""")


def _pids_no_log(texto: str) -> list[str]:
    """uvicorn/supervisord のログ行から PID を抽出する。"""
    padroes = [
        r"Started server process \[(\d+)\]",       # uvicorn
        r"spawned: '[^']+' with pid (\d+)",        # supervisord
        r"\[PID (\d+)\]",                          # 独自フォーマット
    ]
    achados: list[str] = []
    for p in padroes:
        achados += re.findall(p, texto)
    return achados


def bloco_logs(pasta: pathlib.Path, programa: str) -> None:
    titulo("2. プログラムのログ")
    if not pasta.is_dir():
        print(f"  ✗ フォルダが見つからない: {pasta}")
        return

    arquivos = sorted(p for p in pasta.iterdir() if p.is_file() and p.suffix in (".log", ""))
    if not arquivos:
        print(f"  ✗ {pasta} にログファイルが 1 つもない")
        return

    for arq in arquivos:
        try:
            texto = arq.read_text(errors="replace")
        except Exception as exc:  # noqa: BLE001
            print(f"  {arq.name}: 読み取れなかった ({exc})")
            continue

        linhas = texto.splitlines()
        print(f"\n  --- {arq.name}  ({len(linhas)} 行) ---")

        pids = _pids_no_log(texto)
        if pids:
            contagem = Counter(pids)
            print(f"      検出した PID: {len(contagem)} 種類")
            if len(contagem) > 1:
                print(f"      ⚠️ 複数の PID — 再起動ループの特徴")
                for pid, n in list(contagem.items())[:6]:
                    print(f"          PID {pid}: {n} 回出現")
            else:
                print(f"      ✓ PID は 1 つだけ ({list(contagem)[0]}) — 再起動なし")

        # 繰り返し読み込みの兆候
        marcas = [l for l in linhas if "carregando" in l.lower() or "carregado em" in l.lower()]
        if marcas:
            print(f"      読み込みの行: {len(marcas)}")
            if len(marcas) > 4:
                print("      ⚠️ 何度も読み込まれている — ループの裏付け")

        # エラー
        erros = [l for l in linhas
                 if re.search(r"error|erro|Traceback|Exception|CUDA|out of memory",
                              l, re.IGNORECASE)]
        if erros:
            print(f"      ⚠️ エラーの兆候がある行: {len(erros)} 行。直近のもの:")
            for l in erros[-5:]:
                print(f"          {l.strip()[:110]}")
        elif "err" in arq.name:
            print("      ✓ 記録されたエラーなし")


def bloco_log_supervisord(caminho: pathlib.Path | None) -> None:
    titulo("3. supervisord 自体のログ")
    candidatos = [caminho] if caminho else [
        pathlib.Path("/var/log/supervisor/supervisord.log"),
        pathlib.Path("/tmp/supervisord.log"),
    ]
    for c in candidatos:
        if c and c.is_file():
            texto = c.read_text(errors="replace")
            eventos = [l for l in texto.splitlines()
                       if re.search(r"spawned|exited|gave up|backoff|FATAL", l)]
            print(f"  {c}  (関連イベント {len(eventos)} 件)")
            for l in eventos[-12:]:
                print(f"      {l.strip()[:110]}")
            spawns = len(re.findall(r"spawned:", texto))
            exits = len(re.findall(r"exited:", texto))
            print(f"\n      spawned: {spawns}   exited: {exits}")
            if exits >= 2:
                print("      ⚠️ プロセスが複数回終了している — ループ確定")
            if "gave up" in texto:
                print("      ✗ supervisord が諦めた (FATAL)。上の stderr を確認してください。")
            return
    print("  supervisord のログが見つからなかった。次で探してください:")
    print("      grep -E 'spawned|exited|gave up' /var/log/supervisor/supervisord.log")


def bloco_conclusao() -> None:
    titulo("結果をどう扱うか")
    print("""
  ループがある場合（複数の PID / 複数の "exited"）
      原因はプログラムの STDERR にある。よくあるもの:
        - CUDA out of memory            -> 別のプロセスがすでに GPU を使っている
        - モデルが見つからない          -> モデルの名前/パスが間違っている
        - ModuleNotFoundError           -> venv が違う（`command=` には uvicorn の
                                           絶対パスを使う）
        - Permission denied             -> `user=` に GPU/HF_HOME へのアクセス権がない

  RUNNING で uptime が増えている場合
      サービスは常駐している。それでも nvidia-smi に何も表示されないなら:
        curl -s localhost:8000/health | python -m json.tool
      `modelos.gpu.alocado_mb` を確認する:
        > 0   -> GPU 上にある。nvidia-smi が同じ GPU を見ているか確認する
                 （CUDA_VISIBLE_DEVICES はインデックスを付け替える）
        = 0   -> モデルは CPU に配置された。REFCAP_DEVICE を確認する

  STOPPED の場合
      supervisorctl start refcap-api
      そして追跡する:  supervisorctl tail -f refcap-api stderr
""")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--logs", default="/var/log/refcap-api",
                    help="プログラムの stdout.log と stderr.log があるフォルダ")
    ap.add_argument("--programa", default="refcap-api")
    ap.add_argument("--conf", default=None, help="supervisord.conf のパス")
    ap.add_argument("--log-supervisord", default=None)
    args = ap.parse_args()

    print("=" * LARG)
    print(" 診断 — supervisord: サービスは本当に常駐しているか？")
    print("=" * LARG)

    bloco_status(args.programa, args.conf)
    bloco_logs(pathlib.Path(args.logs), args.programa)
    bloco_log_supervisord(
        pathlib.Path(args.log_supervisord) if args.log_supervisord else None
    )
    bloco_conclusao()
    return 0


if __name__ == "__main__":
    sys.exit(main())
