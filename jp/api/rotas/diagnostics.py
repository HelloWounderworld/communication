"""GET /diagnostics/* — 本番と同じキャプション生成に、診断情報を添えたもの。

★ 何が変わったか（修正）
    以前の版は独自の契約を持っていた — `video` を、cfg.py の `video_root` 内の
    ファイル名として受け取っていた。これは `scene_video_path` 契約より前の古い
    設計に由来し、動画がその設定ディレクトリにない場合は常に 404 になっていた。

    現在これらのルートは本番と同じ種類のパスを受け取り、残りの構造を
    そこから導出する:

        scene_video_path = <prefixo>/{program_id}/{video_id}/{scene_id}.mp4
                                      └─  導出  ─┘ └  導出  ┘ └  導出  ┘

★ そして重複の排除
    これらは `CaptionRequest` を組み立てて `captioning.processar_pedido` を呼ぶ —
    本番と同じ関数だ。違うのは返す内容だけ:

        本番        -> 契約
        診断        -> 契約 + 前後の GPU、ステップ、exp_dir

    以前の版はキャプション生成のロジックを約 500 行重複させていた。どんな修正も
    2 か所で行う必要があり — まさにそのせいで、診断側が取り残された。

★ 専用の `collection`
    デフォルトでは、導出した program_id ではなく `COLLECTION_DIAGNOSTICO`
    ("diagnostics") を使う。これにより、実データのキャッシュ、annos、結果を
    汚さずにテストできる。実データに対して診断するには、
    `usar_program_id=true` を渡す。
"""
from __future__ import annotations

import logging
import os
import pathlib

from fastapi import APIRouter, HTTPException

from carregador import ModelosResidentes
from contratos import CaptionRequest, ErrorCode, SceneItem
from estado import COLLECTION_DIAGNOSTICO, ConfigServico, modelos
from ponte_refcap import montar_cfg
import captioning

log = logging.getLogger("refcap.api.diagnostics")

router = APIRouter(tags=["diagnostics"])

EXTENSOES = (".mp4", ".mkv", ".avi", ".webm", ".mov", ".m4v")


# --------------------------------------------------------------------------- #
def derivar_do_caminho(caminho: str) -> dict:
    """シーンのパスから program_id、video_id、scene_id を取り出す。

        /qualquer/prefixo/{program_id}/{video_id}/{scene_id}.mp4
                            └─ [-3] ─┘  └─ [-2] ─┘  └─ stem ─┘

    階層が足りなければ、欠けたものは None で返る — どうするかは呼び出し側が決める。
    """
    p = pathlib.Path(caminho)
    partes = p.parts
    return {
        "scene_id": p.stem,
        "video_id": partes[-2] if len(partes) >= 2 else None,
        "program_id": partes[-3] if len(partes) >= 3 else None,
    }


def _cenas_do_diretorio(diretorio: str, extensoes: str, limite: int) -> list[dict]:
    """ディレクトリ内のシーンを列挙し、各パスから ID を導出する。"""
    sufixos = tuple(e.strip().lower() for e in extensoes.split(",") if e.strip())
    d = pathlib.Path(diretorio)
    arquivos = sorted(
        f for f in d.iterdir()
        if f.is_file() and f.suffix.lower() in sufixos
    )
    if limite > 0:
        arquivos = arquivos[:limite]
    return [{**derivar_do_caminho(str(f)), "scene_video_path": str(f)}
            for f in arquivos]


def _executar_com_diagnostico(itens: list[dict], collection: str | None,
                              proposal_generator: str, force: bool) -> dict:
    """中核: リクエストを組み立て、キャプション生成を呼び、診断情報をまとめる。

    重複の排除が起きるのはここ — `captioning.processar_pedido` は POST /caption が
    使うのと同じ関数だ。
    """
    if not modelos.pronto:
        raise HTTPException(503, {
            "error_code": ErrorCode.INTERNAL_ERROR,
            "message": "models not loaded",
            "hint": "start the service without REFCAP_CARREGAR_MODELOS=0",
        })

    # 専用の collection を指定した場合は、導出した program_id を上書きする:
    # キャプション生成で collection になるのはこれだ。
    if collection:
        itens = [{**i, "program_id": collection} for i in itens]

    pedido = CaptionRequest(
        items=[SceneItem(**i) for i in itens],
        proposal_generator=proposal_generator,
        force=force,
    )

    gpu_antes = ModelosResidentes.estado_da_gpu()
    resultado = captioning.processar_pedido(
        pedido=pedido,
        job_id="diagnostics",
        montar_cfg=montar_cfg,
        modelos=modelos,
        config_servico=ConfigServico,
    )
    gpu_depois = ModelosResidentes.estado_da_gpu()

    return {
        **resultado,
        "diagnostics": {
            "collection_usado": collection or "（導出した program_id）",
            "cenas_enviadas": [
                {"scene_id": i["scene_id"], "video_id": i.get("video_id"),
                 "program_id": i.get("program_id"),
                 "path": i["scene_video_path"]}
                for i in itens
            ],
            "modelos_reaproveitados": {
                "gpu_allocated_mb_antes": gpu_antes.get("allocated_mb"),
                "gpu_allocated_mb_depois": gpu_depois.get("allocated_mb"),
                "nota": ("値が近く、かつ > 0 = モデルは常駐し続けている。"
                         "build は何も再読み込みしていない"),
            },
        },
    }


# --------------------------------------------------------------------------- #
@router.get("/diagnostics/caption",
            summary="[DIAGNOSTICS] captioning on ONE scene, by path")
def diagnostics_caption(
    scene_video_path: str,
    usar_program_id: bool = False,
    proposal_generator: str = "whole",
    force: bool = False,
) -> dict:
    """1 つのシーンでキャプション生成を完全に実行し、契約 + 診断情報を返す。

    パラメーター
        scene_video_path  ★ .mp4 の完全なパス — POST /caption に送るのと
                          同じもの。`program_id`、`video_id`、`scene_id` は
                          ここから導出される。
        usar_program_id   デフォルトでは分離された collection "diagnostics" を使う。
                          `true` にすると導出した program_id を使う — つまり、
                          実データに手を加える。
        proposal_generator  "whole"（あなたのもの）または "qm"（オリジナル）
        force             そのシーンのキャッシュを消して再処理する

    例
        GET /diagnostics/caption?scene_video_path=/dados/prog1/vidA/cena_01.mp4

    ⚠️ 意図的に同期: ブラウザで結果を直接確認できる。
    """
    if not os.path.isfile(scene_video_path):
        # ★ ここではファイルを確認する。パラメーターがシーンのパスだからだ。
        # 以前の版は設定済みの video_root 内のファイルを確認しており
        # — そこ以外にあるシーンはすべて 404 になっていた。
        pai = os.path.dirname(scene_video_path)
        vizinhos = sorted(os.listdir(pai))[:20] if os.path.isdir(pai) else []
        raise HTTPException(404, {
            "error_code": ErrorCode.FILE_NOT_FOUND,
            "message": f"ファイルが見つからない: {scene_video_path}",
            "diretorio_pai": pai,
            "existe_o_diretorio": os.path.isdir(pai),
            "primeiros_arquivos_la": vizinhos,
        })

    item = {**derivar_do_caminho(scene_video_path),
            "scene_video_path": scene_video_path}
    collection = None if usar_program_id else COLLECTION_DIAGNOSTICO
    return _executar_com_diagnostico([item], collection, proposal_generator, force)


@router.get("/diagnostics/caption-batch",
            summary="[DIAGNOSTICS] captioning on a DIRECTORY of scenes")
def diagnostics_caption_batch(
    diretorio: str,
    usar_program_id: bool = False,
    proposal_generator: str = "whole",
    force: bool = False,
    limite: int = 0,
    extensoes: str = ".mp4",
) -> dict:
    """ディレクトリ内のすべてのシーンでキャプション生成を実行する。

    パラメーター
        diretorio        ★ .mp4 があるフォルダのパス
        usar_program_id  上記を参照
        limite           最大 N シーンまで処理する（0 = すべて）
        extensoes        フィルター。カンマ区切り

    ⚠️ 同期。大きなディレクトリは HTTP のタイムアウトを超える — 事前のテストには
       `limite` を、本番には POST /caption/batch を使うこと。
    """
    if not os.path.isdir(diretorio):
        # ★ ここではディレクトリを確認する。パラメーターがフォルダだからだ。
        raise HTTPException(404, {
            "error_code": ErrorCode.FILE_NOT_FOUND,
            "message": f"ディレクトリが見つからない: {diretorio}",
        })

    itens = _cenas_do_diretorio(diretorio, extensoes, limite)
    if not itens:
        raise HTTPException(404, {
            "error_code": ErrorCode.SCENE_NOT_FOUND,
            "message": f"{extensoes} ファイルが {diretorio} に 1 つもない",
            "primeiros_arquivos_la": sorted(os.listdir(diretorio))[:20],
        })

    collection = None if usar_program_id else COLLECTION_DIAGNOSTICO
    return _executar_com_diagnostico(itens, collection, proposal_generator, force)
