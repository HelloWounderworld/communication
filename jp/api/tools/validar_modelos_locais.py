#!/usr/bin/env python3
"""
validar_modelos_locais.py — モデルのローカルディレクトリが、`from_pretrained()` が
受け付ける形式になっているかを確認する。

なぜこれが重要か
--------------------
HuggingFace のキャッシュからローカルディレクトリにモデルを移すと、
2 通りの構造があり得る — そのまま動くのは片方だけ:

  ✓ フラットなレイアウト (snapshot)    ✗ キャッシュのレイアウト (~/.cache のもの)
    /modelos/blip-caption/             /modelos/models--Salesforce--blip.../
    ├── config.json                    ├── blobs/
    ├── model.safetensors              ├── refs/
    ├── preprocessor_config.json       └── snapshots/
    ├── tokenizer_config.json              └── a1b2c3.../      <- ファイル本体
    └── vocab.txt                              ├── config.json  (blobs へのリンク)
                                               └── ...
    from_pretrained("/modelos/         from_pretrained("/modelos/models--...")
       blip-caption")  -> OK              -> 失敗

  キャッシュのレイアウトでは、`snapshots/<hash>/` を指すか、
  `hub/` フォルダを含むディレクトリを HF_HOME に設定する必要がある。

★ これが supervisord でループを引き起こす理由
  パスが間違っていると、`from_pretrained()` はそれを Hub の repo-id と解釈し、
  ダウンロードを試みる。ネットワークがなければ失敗し、プロセスが死に、supervisord が再起動する。
  結果: ログには読み込みが異なる PID で何度も現れる。

  推奨: HF_HUB_OFFLINE=1 を設定する。これがあれば、パスの誤りは
  ネットワーク待ちの後のわかりにくいエラーではなく、即座に明示的なエラーになる。

使い方
    python validar_modelos_locais.py /モデルの/パス
    python validar_modelos_locais.py --caption /m/blip-cap --itm /m/blip-itm --st /m/sbert
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

LARG = 76

# モデルの種類ごとに、ディレクトリに必要なファイル。
PESOS = ("model.safetensors", "pytorch_model.bin", "model.ckpt.index", "flax_model.msgpack")

EXIGENCIAS = {
    "blip": {
        "obrigatorios": ["config.json"],
        "pesos": True,
        "processador": ["preprocessor_config.json"],
        "tokenizador": ["tokenizer_config.json", "vocab.txt"],
        "descricao": "BlipForConditionalGeneration / BlipForImageTextRetrieval + BlipProcessor",
    },
    "sentence_transformer": {
        "obrigatorios": ["modules.json", "config.json"],
        "pesos": True,
        "processador": [],
        "tokenizador": ["tokenizer_config.json"],
        "descricao": "SentenceTransformer",
        "extra_dirs": ["1_Pooling"],
    },
}


def titulo(t: str) -> None:
    print("\n" + "=" * LARG)
    print(f" {t}")
    print("=" * LARG)


def detectar_layout(caminho: pathlib.Path) -> tuple[str, pathlib.Path | None]:
    """フラットなレイアウトか、キャッシュのレイアウトか、不明かを判別する。

    (layout, 使用すべき正しいパス) を返す。
    """
    if not caminho.exists():
        return "inexistente", None

    if (caminho / "config.json").is_file():
        return "plano", caminho

    # キャッシュのレイアウト: snapshots/<hash>/ がある
    snapshots = caminho / "snapshots"
    if snapshots.is_dir():
        hashes = [d for d in snapshots.iterdir() if d.is_dir()]
        if hashes:
            mais_recente = max(hashes, key=lambda d: d.stat().st_mtime)
            return "cache", mais_recente
        return "cache_vazio", None

    # 複数の models--* を含む親ディレクトリかもしれない
    filhos_cache = [d for d in caminho.iterdir() if d.is_dir() and d.name.startswith("models--")]
    if filhos_cache:
        return "pai_de_cache", None

    return "desconhecido", None


def validar(nome: str, caminho_str: str, tipo: str) -> bool:
    print(f"\n  ── {nome}")
    print(f"     指定されたパス: {caminho_str}")

    caminho = pathlib.Path(caminho_str).expanduser()

    # パスではなく Hub の repo-id か？
    if not caminho.is_absolute() and not caminho.exists() and "/" in caminho_str:
        print(f"     ⚠️ ローカルパスではなく、Hub の repo-id のように見える ('{caminho_str}')。")
        print(f"        ネットワークがなければ、from_pretrained() はここで失敗する。")
        return False

    layout, usar = detectar_layout(caminho)

    if layout == "inexistente":
        print(f"     ✗ ディレクトリが存在しない")
        return False

    if layout == "cache":
        print(f"     ⚠️ キャッシュのレイアウトを検出")
        print(f"        from_pretrained() はこのディレクトリを直接は受け付けない。")
        print(f"        次のパスを使ってください:")
        print(f"            {usar}")
        caminho = usar
    elif layout == "pai_de_cache":
        print(f"     ⚠️ これは HuggingFace キャッシュの親ディレクトリのように見える")
        print(f"        ('models--*' フォルダを含む)。各モデルの snapshot を指すか、")
        print(f"        'hub/' の親ディレクトリを HF_HOME に設定してください。")
        return False
    elif layout == "cache_vazio":
        print(f"     ✗ 'snapshots/' はあるが空")
        return False
    elif layout == "desconhecido":
        print(f"     ✗ config.json もキャッシュ構造も見つからなかった")
        listagem = sorted(p.name for p in caminho.iterdir())[:8]
        print(f"        中身: {listagem}")
        return False
    else:
        print(f"     ✓ フラットなレイアウト")

    # --- ファイルを確認する ---
    exig = EXIGENCIAS[tipo]
    faltando: list[str] = []

    for arq in exig["obrigatorios"]:
        if not (caminho / arq).is_file():
            faltando.append(arq)

    if exig["pesos"]:
        tem_peso = any((caminho / p).is_file() for p in PESOS)
        # safetensors は分割されている場合がある
        if not tem_peso:
            tem_peso = any(caminho.glob("*.safetensors")) or any(caminho.glob("*.bin"))
        if not tem_peso:
            faltando.append(f"重み ({' または '.join(PESOS[:2])})")

    for arq in exig["processador"] + exig["tokenizador"]:
        if not (caminho / arq).is_file():
            faltando.append(arq)

    for d in exig.get("extra_dirs", []):
        if not (caminho / d).is_dir():
            faltando.append(f"{d}/ (ディレクトリ)")

    if faltando:
        print(f"     ✗ 不足: {', '.join(faltando)}")
        print(f"        必要とする対象: {exig['descricao']}")
        return False

    tamanho = sum(f.stat().st_size for f in caminho.rglob("*") if f.is_file())
    print(f"     ✓ 完全 — {tamanho / 1024**3:.2f} GB")
    print(f"     ✓ このパスをそのまま使ってください: {caminho}")
    return True


def bloco_offline() -> None:
    titulo("オフラインモード — モデルがローカルにある場合は推奨")
    hho = os.environ.get("HF_HUB_OFFLINE")
    tro = os.environ.get("TRANSFORMERS_OFFLINE")
    hf_home = os.environ.get("HF_HOME")
    print(f"  HF_HUB_OFFLINE       = {hho or '（未定義）'}")
    print(f"  TRANSFORMERS_OFFLINE = {tro or '（未定義）'}")
    print(f"  HF_HOME              = {hf_home or '（未定義）'}")
    if hho != "1":
        print("""
  ⚠️ HF_HUB_OFFLINE=1 がないと、パスが間違っているときに from_pretrained() は
     ネットワークにアクセスしようとする。外部接続のないサーバーでは、待たされた末に
     わかりにくいエラーになる — そして supervisord では、診断しにくい再起動ループになる。

     supervisord.conf に次を設定してください:
         HF_HUB_OFFLINE="1",
         TRANSFORMERS_OFFLINE="1"

     これがあれば、パスの誤り = 即座に明示的なエラー。
""")
    else:
        print("  ✓ オフラインモード有効 — パスの誤りは即座に、明確なエラーになる")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base", nargs="?", help="3 つのモデルを含むディレクトリ")
    ap.add_argument("--caption", help="キャプション生成用 BLIP のパス")
    ap.add_argument("--itm", help="BLIP-ITM のパス")
    ap.add_argument("--st", help="sentence-transformer のパス")
    args = ap.parse_args()

    print("=" * LARG)
    print(" ローカルモデルの検証")
    print("=" * LARG)

    alvos: list[tuple[str, str, str]] = []

    if args.caption or args.itm or args.st:
        if args.caption:
            alvos.append(("caption_model (BLIP captioning)", args.caption, "blip"))
        if args.itm:
            alvos.append(("blip_itm_model (BLIP-ITM)", args.itm, "blip"))
        if args.st:
            alvos.append(("sentence_transformer", args.st, "sentence_transformer"))
    elif args.base:
        base = pathlib.Path(args.base).expanduser()
        titulo(f"{base} を探索中")
        if not base.is_dir():
            print(f"  ✗ ディレクトリではない")
            return 1
        subdirs = sorted(d for d in base.iterdir() if d.is_dir())
        print(f"  サブディレクトリ {len(subdirs)} 件:")
        for d in subdirs:
            layout, _ = detectar_layout(d)
            print(f"    {d.name:<50} [{layout}]")
        print("""
  各モデルを明示的に指定して、もう一度実行してください:
      python validar_modelos_locais.py --caption <dir> --itm <dir> --st <dir>
""")
        bloco_offline()
        return 0
    else:
        # サービスの環境変数から試みる
        mapa = [
            ("caption_model (BLIP captioning)", "REFCAP_CAPTION_MODEL", "blip"),
            ("blip_itm_model (BLIP-ITM)", "REFCAP_BLIP_ITM_MODEL", "blip"),
            ("sentence_transformer", "REFCAP_SENTENCE_TRANSFORMER", "sentence_transformer"),
        ]
        for nome, var, tipo in mapa:
            valor = os.environ.get(var)
            if valor:
                alvos.append((f"{nome}  [{var}]", valor, tipo))
        if not alvos:
            print("\n  パスが指定されておらず、REFCAP_*_MODEL も定義されていない。")
            print("  使い方:  python validar_modelos_locais.py /モデルの/パス")
            return 1

    titulo("各モデルを検証中")
    resultados = [validar(n, c, t) for n, c, t in alvos]

    bloco_offline()

    titulo("結果")
    ok = sum(resultados)
    print(f"  {ok} / {len(resultados)} 件のモデルがローカルで使用可能")
    if ok < len(resultados):
        print("""
  どれか 1 つでも誤っている間は、サービスは起動時に失敗する — そして
  supervisord がループで再起動し続ける。起動する前に、supervisord.conf
  （environment= ブロック）のパスを修正してください。
""")
        return 1
    print("\n  ✓ これらのパスを supervisord.conf の REFCAP_*_MODEL 変数に設定してください")
    return 0


if __name__ == "__main__":
    sys.exit(main())
