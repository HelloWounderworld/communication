"""サービスの共有状態と設定。

このモジュールが存在する理由
--------------------------
ルートを `rotas/` に分けたため、ルートは常駐モデル、ジョブの登録簿、設定に
アクセスする必要がある — しかし `app.py` を import することはできない。ルートを
import しているのが `app.py` だからだ。それは循環 import になる。

解決策: 状態はここに置く。`app.py` もルートもここから import し、
`app.py` を import するものは何もない。

    app.py ──┐
             ├──► estado.py   (両方がここから import する。
    rotas/ ──┘                 estado.py は何も import しない)
"""
from __future__ import annotations

import os

from carregador import ModelosResidentes
from jobs import RegistroDeJobs


class ConfigServico:
    """環境変数による設定 — supervisord が `environment=` ブロックで定義する。

    ⚠️ REFCAP_*_MODEL はローカルモデルへの絶対パスでなければならない。
    下のデフォルトは Hub の repo-id で、ネットワークがある場合にしか使えない。
    オフラインのサーバーでデフォルトのままにすると、from_pretrained() がダウンロードを試みて
    失敗し、プロセスが死ぬ — supervisord ではそれが再起動ループになる。

    起動前にパスを検証すること:
        python validar_modelos_locais.py --caption <dir> --itm <dir> --st <dir>
    """

    device = os.environ.get("REFCAP_DEVICE", "cuda")
    caption_model = os.environ.get(
        "REFCAP_CAPTION_MODEL", "Salesforce/blip-image-captioning-large")
    blip_itm_model = os.environ.get(
        "REFCAP_BLIP_ITM_MODEL", "Salesforce/blip-itm-base-coco")
    sentence_transformer = os.environ.get(
        "REFCAP_SENTENCE_TRANSFORMER", "paraphrase-distilroberta-v2")
    carregar_no_startup = os.environ.get("REFCAP_CARREGAR_MODELOS", "1") == "1"


#: シーン数がこれを超えると、API は自動で非同期に切り替わる。
#:
#: ボトルネックは処理ではなく HTTP 接続。1〜5 秒のシーンは約 1〜3 秒かかるので、
#: 30 シーンでもうプロキシの一般的なタイムアウト（60 秒）に近づく。
LIMIAR_ASSINCRONO = int(os.environ.get("REFCAP_LIMIAR_ASSINCRONO", "30"))

#: 診断ルートは専用の `collection` を使う — program_id は決して使わない。
#: これにより、実データのキャッシュ、annos、結果を汚さずにテストできる。
COLLECTION_DIAGNOSTICO = "diagnostics"


# --------------------------------------------------------------------------- #
# プロセスが生きている間ずっと存在する状態
# --------------------------------------------------------------------------- #
#: 4 つのモデル。起動時に 1 回だけ読み込まれる（`app.ciclo_de_vida` を参照）。
modelos = ModelosResidentes()

#: 直列化されたキュー: GPU を奪い合わないよう、ジョブは 1 つずつ。
registro = RegistroDeJobs()
