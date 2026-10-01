#!/usr/bin/env python3
"""
diagnostico_gpu.py — モデルが GPU に常駐しなかった理由を突き止める。

使い方（サービスの環境で、.venv を有効にした状態で）:

    # 1. 何も読み込まずに環境をチェックする
    python diagnostico_gpu.py

    # 2. 実際にモデルを 1 つ読み込み、前後の GPU を計測する
    python diagnostico_gpu.py --carregar

    # 3. 読み込んだまま生存させ、nvidia-smi をゆっくり確認できるようにする
    python diagnostico_gpu.py --carregar --manter

調査する項目（順番に）
-----------------------------
    A. torch から GPU が見えているか？
    B. 環境変数は想定どおりか？
    C. モデルを読み込むと、実際に GPU メモリが使われるか？
    D. プロセスが生きている間、メモリは確保されたままか？

「読み込んだのに常駐しない」よくある 3 つの原因
------------------------------------------------------
    1. プロセスが終了した。
       `with TestClient(app):` を使うスクリプトは、ブロックに入るときに読み込み、
       出るときに解放する。__main__ ブロックのない `python app.py` はサーバーすら起動しない。
       nvidia-smi に表示されるのは、生きているプロセスのメモリだけ。

    2. モデルが CPU に載った。
       `device="cpu"`（または REFCAP_DEVICE=cpu）でもすべて動く — ただし GPU は使われない。

    3. 見ている GPU が違う。
       CUDA_VISIBLE_DEVICES=1 のとき、プロセスの「device 0」は物理 GPU 1 になる。
       nvidia-smi は物理 GPU の番号で表示する。
"""
from __future__ import annotations

import argparse
import os
import sys
import time

LARG = 74


def titulo(txt: str) -> None:
    print("\n" + "=" * LARG)
    print(f" {txt}")
    print("=" * LARG)


def item(rotulo: str, valor, nota: str = "") -> None:
    print(f"  {rotulo:<34} {valor}" + (f"   {nota}" if nota else ""))


# --------------------------------------------------------------------------- #
def bloco_a_torch() -> dict:
    titulo("A. torch から GPU が見えているか？")
    try:
        import torch
    except ImportError:
        item("torch", "未インストール", "<- サービスの .venv にインストールしてください")
        return {"ok": False}

    item("torch", torch.__version__)
    item("CUDA 対応ビルド", torch.version.cuda or "いいえ（CPU 専用ビルド）")
    disponivel = torch.cuda.is_available()
    item("torch.cuda.is_available()", disponivel,
         "" if disponivel else "<- ★ ここが問題")

    if not disponivel:
        print("""
  考えられる原因:
    - インストールされた torch が CPU 専用ビルド  (CUDA インデックスなしの pip install torch)
    - CUDA_VISIBLE_DEVICES=""  (空文字列はすべての GPU を隠す)
    - NVIDIA ドライバーがない、または torch の CUDA バージョンと互換性がない
""")
        return {"ok": False}

    n = torch.cuda.device_count()
    item("見えているデバイス数", n)
    for i in range(n):
        props = torch.cuda.get_device_properties(i)
        item(f"  device {i}", f"{props.name}  ({props.total_memory/1024**3:.1f} GB)")
    return {"ok": True, "torch": torch}


def bloco_b_ambiente() -> None:
    titulo("B. 環境変数")
    esperadas = [
        ("CUDA_VISIBLE_DEVICES", "プロセスから見える GPU"),
        ("REFCAP_DEVICE", "モデルの配置先 (cuda/cpu)"),
        ("REFCAP_CARREGAR_MODELOS", "1 なら起動時に読み込む。0 ならモデルなしで起動"),
        ("REFCAP_ROOT", "RefCap のルート（任意）"),
        ("REFCAP_CAPTION_MODEL", ""),
        ("REFCAP_BLIP_ITM_MODEL", ""),
        ("REFCAP_SENTENCE_TRANSFORMER", ""),
    ]
    for nome, desc in esperadas:
        valor = os.environ.get(nome)
        if valor is None:
            item(nome, "（未定義）", f"<- {desc}" if desc else "")
        else:
            item(nome, repr(valor))

    print()
    cvd = os.environ.get("CUDA_VISIBLE_DEVICES")
    if cvd == "":
        print("  ⚠️ CUDA_VISIBLE_DEVICES が空 — これはすべての GPU を隠す。")
    elif cvd and cvd != "0":
        print(f"  ⚠️ CUDA_VISIBLE_DEVICES={cvd!r}: このプロセスの「device 0」は")
        print(f"     物理 GPU {cvd.split(',')[0]}。nvidia-smi ではその行を確認してください。")

    if os.environ.get("REFCAP_CARREGAR_MODELOS") == "0":
        print("  ⚠️ REFCAP_CARREGAR_MODELOS=0 — サービスはモデルを読み込まずに起動する。")
    if os.environ.get("REFCAP_DEVICE") == "cpu":
        print("  ⚠️ REFCAP_DEVICE=cpu — モデルは GPU ではなく CPU に配置される。")


def mb(torch, i: int = 0) -> tuple[float, float]:
    return (
        torch.cuda.memory_allocated(i) / 1024**2,
        torch.cuda.memory_reserved(i) / 1024**2,
    )


def bloco_c_carregar(torch, modelo: str, device: str) -> bool:
    titulo("C. モデルを読み込むと、実際に GPU が使われるか？")
    if device != "cuda":
        item("指定されたデバイス", device, "<- cuda ではない。GPU で計測するものはない")
        return False

    aloc0, res0 = mb(torch)
    item("読み込み前 — 割り当て / 予約", f"{aloc0:.1f} MB / {res0:.1f} MB")

    print(f"\n  {modelo} を読み込み中 ...")
    t0 = time.perf_counter()
    try:
        from transformers import BlipForConditionalGeneration

        m = BlipForConditionalGeneration.from_pretrained(modelo).to(device)
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ 失敗: {type(exc).__name__}: {exc}")
        return False
    dt = time.perf_counter() - t0

    aloc1, res1 = mb(torch)
    item("読み込み後 — 割り当て / 予約", f"{aloc1:.1f} MB / {res1:.1f} MB")
    item("読み込み時間", f"{dt:.1f}s")
    item("割り当ての増分", f"+{aloc1 - aloc0:.1f} MB")

    if aloc1 - aloc0 < 1:
        print("""
  ✗ メモリが増えていない。モデルは GPU に載っていない。
    device と CUDA_VISIBLE_DEVICES を確認してください（ブロック B）。
""")
        return False

    print(f"""
  ✓ モデルは GPU を使用している: +{aloc1 - aloc0:.0f} MB 割り当て済み。
    今すぐ別のターミナルで `nvidia-smi` を実行すると、一覧に
    このプロセス (PID {os.getpid()}) が表示されるはず。
""")
    globals()["_modelo_vivo"] = m          # 参照を保持して生存させる
    return True


def bloco_d_manter(torch) -> None:
    titulo("D. プロセスを生存させたまま保持")
    print(f"""
  このプロセスの PID: {os.getpid()}

  別のターミナルで、次を実行してください:
      nvidia-smi
      nvidia-smi --query-compute-apps=pid,used_memory --format=csv

  PID {os.getpid()} がメモリを使用しているのが見えるはず。このプロセスが
  生きている間、メモリは確保されたまま。Ctrl+C で終了するとメモリは解放される —
  これがまさに「常駐」の挙動。
""")
    try:
        i = 0
        while True:
            time.sleep(5)
            i += 1
            aloc, res = mb(torch)
            print(f"  [{i*5:>4}s] 割り当て={aloc:8.1f} MB   予約={res:8.1f} MB")
    except KeyboardInterrupt:
        print("\n  ユーザーにより終了 — メモリはこれから解放される。")


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carregar", action="store_true",
                    help="実際にモデルを読み込み、GPU を計測する")
    ap.add_argument("--manter", action="store_true",
                    help="読み込み後も生存し、nvidia-smi を確認できるようにする")
    ap.add_argument("--modelo",
                    default=os.environ.get("REFCAP_CAPTION_MODEL",
                                           "Salesforce/blip-image-captioning-large"))
    ap.add_argument("--device", default=os.environ.get("REFCAP_DEVICE", "cuda"))
    args = ap.parse_args()

    print("=" * LARG)
    print(" 診断 — モデルが GPU に常駐しなかった理由")
    print("=" * LARG)
    item("python", sys.version.split()[0])
    item("実行ファイル", sys.executable)
    item("PID", os.getpid())

    resultado = bloco_a_torch()
    bloco_b_ambiente()

    if not resultado["ok"]:
        titulo("結論")
        print("  torch から GPU が見えていない。先にブロック A を解決してください。")
        return 1

    if not args.carregar:
        titulo("次のステップ")
        print("""
  環境は問題なさそう。読み込みで GPU が使われることを確認するには:

      python diagnostico_gpu.py --carregar --manter

  そして、サービスを起動した状態で次と比較する:

      curl -s localhost:8000/health | python -m json.tool

  /health では `modelos.gpu.alocado_mb` を確認する:
      > 0 かつリクエスト間で安定      -> 常駐している ✓
      = 0 かつ `pronto: true`         -> モデルは CPU 上にある
""")
        return 0

    ok = bloco_c_carregar(resultado["torch"], args.modelo, args.device)
    if ok and args.manter:
        bloco_d_manter(resultado["torch"])
    elif ok:
        titulo("注意")
        print("""
  モデルは読み込まれ GPU を使用した — しかし、このプロセスはこれから終了し、
  メモリは解放される。サーバーではなく単発のスクリプトを実行したときに
  起きるのは、まさにこれ。

  メモリが確保されたままになるのを確認するには、--manter を使ってください。
""")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
