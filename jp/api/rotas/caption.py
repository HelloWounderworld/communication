"""POST /caption、POST /caption/batch、GET /caption/{program_id}。

2 つの POST ルートは本体（`_executar`）を共有する: 契約上の意図を明示するために
分けてあるが、`como_itens()` が単一シーンとバッチをすでに 1 つのリストに
正規化している — 保守すべき経路が 2 つあるわけではない。
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse

import persistencia
import captioning
from contratos import CaptionRequest, ErrorCode
from estado import LIMIAR_ASSINCRONO, ConfigServico, modelos, registro
from jobs import EstadoJob, Job
from ponte_refcap import montar_cfg

log = logging.getLogger("refcap.api.caption")

router = APIRouter(tags=["caption"])


def processar_job(job: Job) -> dict:
    """ジョブを 1 つ実行する: キャプション生成 + キャプション生成 + レスポンス。

    キャプション生成（annos、ディレクトリ単位のグルーピング、collection、キャッシュ）と
    出力の変換は `captioning.py` にある — ここではサービスの部品を
    つなぐだけ。

    モデルはすでに読み込み済み: `modelos.como_dict()` は RefCap の `build()` が
    期待する形式の辞書を返し、何も再読み込みしない。
    """
    pedido = CaptionRequest(**job.entrada)
    return captioning.processar_pedido(
        pedido=pedido,
        job_id=job.id,
        montar_cfg=montar_cfg,
        modelos=modelos,
        config_servico=ConfigServico,
    )


def _programa_do_pedido(pedido: CaptionRequest) -> str | None:
    """リクエストの `program_id` — collection、キャッシュ、レスポンスを決める。"""
    for item in pedido.como_itens():
        if item.program_id:
            return item.program_id
    return None


async def _executar(pedido: CaptionRequest, tarefas: BackgroundTasks):
    """POST /caption と POST /caption/batch の共通本体。

    2 つのルートは契約上の意図を明示するために存在するが、
    処理は同じ: `como_itens()` が単一シーンとバッチを 1 つのリストに正規化し、
    それ以降に経路は 2 つない。
    """
    if not modelos.pronto:
        raise HTTPException(503, {
            "error_code": ErrorCode.INTERNAL_ERROR,
            "message": "models not loaded",
            "hint": ("start the service without REFCAP_CARREGAR_MODELOS=0 "
                     "so the models load at startup"),
        })

    itens = pedido.como_itens()
    if not itens:
        raise HTTPException(400, {
            "error_code": ErrorCode.INVALID_REQUEST,
            "message": ("empty request: provide `scene_id` + `scene_video_path`, "
                        "or `items`"),
        })

    program_id = _programa_do_pedido(pedido)
    job = registro.criar(entrada=pedido.model_dump(), callback_url=pedido.callback_url)

    # --- 非同期: しきい値を超えたら自動、または強制 --------------------- #
    if len(itens) > LIMIAR_ASSINCRONO or pedido.assincrono:
        tarefas.add_task(registro.executar, job, processar_job)
        return JSONResponse(status_code=202, content={
            "state": "accepted",
            "program_id": program_id,
            "scenes": [i.scene_id for i in itens],
            "total": len(itens),
            "check_at": f"/caption/{program_id}" if program_id else None,
            "reason": ("above the synchronous threshold"
                       if len(itens) > LIMIAR_ASSINCRONO else "requested"),
        })

    # --- 同期: 完了を待って結果を返す ----------------------------------- #
    # `executar` はキューのロックの下、asyncio.to_thread でタスクを実行する —
    # ここで待ってもイベントループはブロックしない: 処理中も /health と
    # GET /caption は応答し続ける。
    await registro.executar(job, processar_job)

    resultado = job.resultado or {}
    corpo = {
        "state": job.estado.value,
        "program_id": program_id,
        **(resultado if isinstance(resultado, dict) else {"result": resultado}),
    }
    if job.erro:
        corpo["error_code"] = ErrorCode.INTERNAL_ERROR
        corpo["message"] = job.erro
    return JSONResponse(
        status_code=200 if job.estado == EstadoJob.CONCLUIDO else 500,
        content=corpo,
    )


@router.post("/caption", summary="Caption a single scene")
async def caption(pedido: CaptionRequest, tarefas: BackgroundTasks):
    """1 つのシーンにキャプションを付け、結果を返す。

        {"scene_id": "...", "video_id": "...", "program_id": "...",
         "scene_video_path": "/path/{program_id}/{video_id}/{scene_id}.mp4"}

    `scene_caption_en`、`keywords_en`、`status` を含む契約を返す。
    結果は永続化もされる — GET /caption/{program_id} で参照できる。
    """
    return await _executar(pedido, tarefas)


@router.post("/caption/batch", summary="Caption a batch of scenes")
async def caption_batch(pedido: CaptionRequest, tarefas: BackgroundTasks):
    """複数のシーンにキャプションを付ける。

        {"items": [ {scene_id, video_id, program_id, scene_video_path}, ... ]}

    `video_id` が異なるシーンは別々のディレクトリにある — API は
    ディレクトリ単位でグルーピングし、グループごとに `build()` を 1 回実行する。

    ★ シーン数が LIMIAR_ASSINCRONO を超えると 202 を返し、バックグラウンドで
      処理する。何も失われず、結果は永続化される。
    """
    return await _executar(pedido, tarefas)


@router.get("/caption/{program_id}", summary="Read persisted captions of a program")
async def caption_do_programa(
    program_id: str,
    scene_id: list[str] | None = Query(
        default=None,
        description="1 つまたは複数のシーンで絞り込む。省略するとすべてを返す。",
    ),
) -> dict:
    """永続化された内容を、何も再処理せずに読む。

        GET /caption/prog1                              すべて
        GET /caption/prog1?scene_id=a                   1 件
        GET /caption/prog1?scene_id=a&scene_id=b        複数

    一度も処理されていない番組は、404 ではなく 200 と空のリストを返す。こうすれば
    クライアントは「存在しない」と「空」を区別せず、1 つのケースだけを扱えばよい。
    """
    cfg = montar_cfg()
    itens = persistencia.ler_respostas(cfg.res_dir, program_id, scene_id)
    ok = sum(1 for i in itens if i.get("status") == "success")
    return {
        "program_id": program_id,
        "items": itens,
        "summary": {"total": len(itens), "ok": ok, "errors": len(itens) - ok},
    }
