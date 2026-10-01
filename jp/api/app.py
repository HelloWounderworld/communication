"""RefCap の FastAPI サービス — ライフサイクルとルートの登録。

    supervisord -> uvicorn -> FastAPI
                              |
                              +-- startup: 4 つのモデルを 1 回だけ読み込む
                              |            (GPU 上に常駐する状態)
                              |
                              +-- POST /caption              1 シーン
                              +-- POST /caption/batch        バッチ
                              +-- GET  /caption/{program_id} 永続化された内容を読む
                              +-- GET  /health               ステータス
                              +-- GET  /diagnostics/*        パイプライン + 診断
                              |
                              +-- shutdown: モデルを解放する

構成
    app.py          このファイル: ライフサイクルと登録
    estado.py       モデル、キュー、設定 — ルート間で共有するもの
    contratos.py    Pydantic モデルとエラーコード
    pipeline.py     リクエストからレスポンスまでの処理
    persistencia.py 永続的な履歴と proposals のマージ
    rotas/          領域ごとに 1 つの router

    ルートは `estado.py` から import し、このファイルからは決して import しない —
    それが循環 import を防いでいる。

開発環境での実行
    uvicorn app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from estado import ConfigServico, modelos
from ponte_refcap import RAIZ_REFCAP, preparar_sys_path
from rotas import caption, diagnostics, health

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
)
log = logging.getLogger("refcap.api")


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """起動と終了。

    ★ 読み込みが行われるのはここ — supervisord がプロセスを起動したときに
    1 回だけ。それ以降モデルは常駐し、各リクエストは再読み込みせずに
    それを使う。
    """
    log.info("サービス起動中 — RefCap の場所: %s", RAIZ_REFCAP)
    preparar_sys_path()

    if ConfigServico.carregar_no_startup:
        modelos.carregar(
            caption_model=ConfigServico.caption_model,
            blip_itm_model=ConfigServico.blip_itm_model,
            sentence_transformer=ConfigServico.sentence_transformer,
            device=ConfigServico.device,
        )
    else:
        # 開発モード: ルートをテストするため、GPU/モデルなしで起動する。
        log.warning("REFCAP_CARREGAR_MODELOS=0 — モデルなしで起動")

    yield

    log.info("サービス終了中")
    modelos.liberar()


app = FastAPI(
    title="RefCap Caption API",
    description=(
        "RefCap のモデルをメモリに常駐させた、シーンのキャプション生成。"
    ),
    version="1.0.0",
    lifespan=ciclo_de_vida,
)

app.include_router(health.router)
app.include_router(caption.router)
app.include_router(diagnostics.router)


if __name__ == "__main__":
    # ⚠️ このブロックがないと、`python app.py` はサーバーを何も起動しない: モジュールが
    # import され、`app` オブジェクトが作られ、プロセスは終了する。lifespan は
    # 一度も実行されず — したがってモデルは一度も読み込まれない。
    #
    # 本番では、起動するのは uvicorn を直接呼ぶ supervisord:
    #     uvicorn app:app --host 0.0.0.0 --port 8000
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        # reload=False は意図的: reload を有効にすると、uvicorn はファイルが変わる
        # たびにプロセスを作り直す — モデルも一緒に再読み込みされ、
        # 常駐状態が無意味になる。
        reload=False,
        log_level=os.environ.get("LOG_LEVEL", "info").lower(),
    )
