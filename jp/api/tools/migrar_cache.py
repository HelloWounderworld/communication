#!/usr/bin/env python3
"""
migrar_cache.py — 旧 `collection` のアーティファクトを新しいものへ移動する。

このスクリプトが存在する理由
--------------------------
ステップ 2 で、RefCap の `collection` は `program_id` に変更された。それ以前に
保存されたアーティファクトは旧名（テストで使ったもの）の下にあり、サービスは
今後 `program_id` の下を探す — そして何も見つからない。

移行しないと、各番組の最初の処理で BLIP がゼロから実行され、
すでに済んだ処理が捨てられる。

4 つのアーティファクト
    annos/{de}/                     →  annos/{para}/
    meta/captions/{de}_blip.jsonl   →  meta/captions/{para}_blip.jsonl
    meta/framefeatures/{de}.pt      →  meta/framefeatures/{para}.pt
    meta/scores/{de}_blip.pt        →  meta/scores/{para}_blip.pt

⚠️ `results/construct/{de}/` は意図的に移行しない: これは直前の実行の
   作業領域であり、`construct_name` の形式も変わった。保存しておくべきなのは
   キャッシュ — BLIP の再実行を防ぐのはこれだ。

使い方
    # 1. 必ず先にシミュレーションする
    python migrar_cache.py --de teste_api --para meu_programa --simular

    # 2. その後で移行する
    python migrar_cache.py --de teste_api --para meu_programa

    # 現在あるものを調べる
    python migrar_cache.py --listar
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys

LARG = 76


def titulo(t: str) -> None:
    print("\n" + "=" * LARG)
    print(f" {t}")
    print("=" * LARG)


# --------------------------------------------------------------------------- #
def raiz_refcap() -> pathlib.Path:
    """サービスと同じルールで RefCap のルートを特定する。"""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from ponte_refcap import RAIZ_REFCAP  # noqa: PLC0415

    return RAIZ_REFCAP


def caminhos_do(raiz: pathlib.Path, cfg, colecao: str) -> list[dict]:
    """ある `collection` の 4 つのアーティファクトと、それぞれの状態。"""
    itens = [
        {
            "nome": "annos",
            "caminho": raiz / cfg.anno_dir / colecao,
            "tipo": "dir",
        },
        {
            "nome": "キャプションキャッシュ",
            "caminho": raiz / cfg.meta_dir / cfg.captions_dir
            / f"{colecao}_{cfg.caption_generator}.jsonl",
            "tipo": "jsonl",
        },
        {
            "nome": "フレーム特徴量",
            "caminho": raiz / cfg.meta_dir / cfg.framefeatures_dir / f"{colecao}.pt",
            "tipo": "pt",
        },
        {
            "nome": "scores",
            "caminho": raiz / cfg.meta_dir / cfg.raw_capframe_scores_dir
            / f"{colecao}_{cfg.caption_generator}.pt",
            "tipo": "pt",
        },
    ]
    for i in itens:
        c = i["caminho"]
        i["existe"] = c.exists()
        i["cenas"] = _contar_cenas(c, i["tipo"]) if i["existe"] else None
    return itens


def _contar_cenas(caminho: pathlib.Path, tipo: str) -> int | str:
    """アーティファクト内のシーン数 — --simular で得られるものを示すため。"""
    try:
        if tipo == "jsonl":
            with open(caminho, encoding="utf-8") as f:
                return sum(1 for linha in f if linha.strip())
        if tipo == "dir":
            # annos はアノテーションファイルに動画ごとに 1 行を保存している
            arquivos = list(caminho.glob("*.jsonl"))
            if not arquivos:
                return 0
            with open(arquivos[0], encoding="utf-8") as f:
                return sum(1 for linha in f if linha.strip())
        if tipo == "pt":
            # .pt を読むには torch が必要。ここではその依存を避ける
            return "?"
    except Exception:  # noqa: BLE001 — 数えるのは診断用であり、失敗してはならない
        return "?"
    return "?"


# ⚠️ RefCap の cfg.py における `caption_generator` のデフォルトは "minigpt" だが、
# API は常に "blip" を使う — キャッシュファイルの名前を決めるのはこれだ。デフォルトを
# 使うと、スクリプトは `{collection}_minigpt.jsonl` を探して何も見つけられない。
CAPTION_GENERATOR = os.environ.get("REFCAP_CAPTION_GENERATOR", "blip")


def _carregar_cfg(raiz: pathlib.Path):
    sys.path.insert(0, str(raiz))
    from config import BuildArguments  # noqa: PLC0415

    cfg = BuildArguments()
    cfg.caption_generator = CAPTION_GENERATOR
    return cfg


# --------------------------------------------------------------------------- #
def listar(raiz: pathlib.Path, cfg) -> int:
    """現在どの `collection` があるかを表示する — 移行のペアを選ぶため。"""
    titulo("見つかった COLLECTION")

    encontrados: dict[str, list[str]] = {}

    dir_annos = raiz / cfg.anno_dir
    if dir_annos.is_dir():
        for d in sorted(p for p in dir_annos.iterdir() if p.is_dir()):
            encontrados.setdefault(d.name, []).append("annos")

    dir_caps = raiz / cfg.meta_dir / cfg.captions_dir
    if dir_caps.is_dir():
        sufixo = f"_{cfg.caption_generator}.jsonl"
        for f in sorted(dir_caps.glob(f"*{sufixo}")):
            encontrados.setdefault(f.name[: -len(sufixo)], []).append("キャプション")

    dir_feat = raiz / cfg.meta_dir / cfg.framefeatures_dir
    if dir_feat.is_dir():
        for f in sorted(dir_feat.glob("*.pt")):
            encontrados.setdefault(f.stem, []).append("特徴量")

    if not encontrados:
        print(f"  {raiz} の下にアーティファクトが 1 つもない")
        return 1

    print(f"  {'collection':<34} 存在するアーティファクト")
    print("  " + "-" * (LARG - 4))
    for nome, arts in sorted(encontrados.items()):
        print(f"  {nome:<34} {', '.join(arts)}")

    print(f"""
  いずれかを移行するには:
      python migrar_cache.py --de <collection> --para <program_id> --simular
""")
    return 0


# --------------------------------------------------------------------------- #
def migrar(raiz: pathlib.Path, cfg, de: str, para: str, simular: bool) -> int:
    titulo(f"{'シミュレーション' if simular else '移行'}:  {de}  →  {para}")

    if de == para:
        print("  ✗ 移行元と移行先が同じ — 何もすることがない")
        return 1

    origem = caminhos_do(raiz, cfg, de)
    destino = caminhos_do(raiz, cfg, para)

    # --- 1. 移行元に何かあるか？ --------------------------------------- #
    presentes = [i for i in origem if i["existe"]]
    if not presentes:
        print(f"  ✗ collection '{de}' のアーティファクトが 1 つもない")
        print(f"\n  何があるかは --listar で確認してください。")
        return 1

    # --- 2. 移行先は空いているか？ ------------------------------------ #
    # ⚠️ 上書きせず、使用中の移行先は拒否する: 2 つのキャッシュを統合するかは
    # オペレーターが決めることで、スクリプトが決めることではない。誤った統合は
    # 異なる番組のシーンを混ぜてしまう — まさにステップ 2 が防ぐサイレントエラーだ。
    ocupados = [i for i in destino if i["existe"]]
    if ocupados and not simular:
        print(f"  ✗ 移行先 '{para}' にはすでにアーティファクトがある:")
        for i in ocupados:
            print(f"      {i['nome']:<20} {i['caminho']}")
        print(f"""
  2 つのセットを混ぜないよう、移行を拒否する。

  本当に両者を統合したいなら、手作業で慎重に行う — あるいは、
  まだ使われていない移行先の `program_id` を選んでください。
""")
        return 1

    # --- 3. 計画 --------------------------------------------------- #
    print(f"\n  {'アーティファクト':<20} {'移行元':<10} {'シーン数':<7} 移行先")
    print("  " + "-" * (LARG - 4))
    for o, d in zip(origem, destino):
        status = "あり" if o["existe"] else "なし"
        cenas = str(o["cenas"]) if o["cenas"] is not None else "-"
        marca = "⚠️ 使用中" if d["existe"] else "空き"
        print(f"  {o['nome']:<20} {status:<10} {cenas:<7} {marca}")

    print(f"\n  移行元  : {raiz}")
    for o in presentes:
        print(f"      {o['caminho'].relative_to(raiz)}")

    if simular:
        print(f"""
  ── シミュレーション — 何も変更していない ──

  4 件中 {len(presentes)} 件のアーティファクトが移動される。
  {'⚠️ 移行先にアーティファクトがある: 実際の移行は拒否される。' if ocupados else '✓ 移行先は空いている。'}

  実際に実行するには:
      python migrar_cache.py --de {de} --para {para}
""")
        return 0

    # --- 4. 移動 ----------------------------------------------------- #
    print()
    movidos = 0
    for o, d in zip(origem, destino):
        if not o["existe"]:
            print(f"  · {o['nome']:<20} 移行元になし — スキップ")
            continue
        d["caminho"].parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(o["caminho"]), str(d["caminho"]))
        print(f"  ✓ {o['nome']:<20} → {d['caminho'].relative_to(raiz)}")
        movidos += 1

    print(f"""
  {movidos} 件のアーティファクトを移動した。

  ★ 既知のシーンを処理して、移行を確認してください:
    そのシーンはキャッシュによりスキップされ、再処理されないはず。BLIP が再び
    実行されたら、新しいパスでキャッシュが見つかっていない。
""")
    return 0


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--de", help="現在の collection（例: teste_api）")
    ap.add_argument("--para", help="移行先の program_id")
    ap.add_argument("--simular", action="store_true",
                    help="何も変更せず、行う内容を表示する")
    ap.add_argument("--listar", action="store_true",
                    help="既存の collection を一覧表示する")
    args = ap.parse_args()

    raiz = raiz_refcap()
    cfg = _carregar_cfg(raiz)

    print("=" * LARG)
    print(" キャッシュ移行 — 旧 collection → program_id")
    print("=" * LARG)
    print(f"  RefCap の場所: {raiz}")

    if args.listar:
        return listar(raiz, cfg)

    if not args.de or not args.para:
        print("\n  --de と --para を指定するか、--listar を使ってください。")
        ap.print_help()
        return 1

    return migrar(raiz, cfg, args.de, args.para, args.simular)


if __name__ == "__main__":
    sys.exit(main())
