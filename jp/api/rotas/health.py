"""GET /health — サービスと常駐モデルの状態。"""
from __future__ import annotations

from fastapi import APIRouter

from estado import modelos, registro
from ponte_refcap import RAIZ_REFCAP

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service and model status")
async def health() -> dict:
    """サービスと常駐モデルの状態。

    ★「モデルは本当に GPU 上にあるか？」に答えるフィールドは
      `models.gpu.allocated_mb`。`models.ready` はオブジェクトが存在することしか示さない。
      `ready: true` で `allocated_mb` が 0 なら、モデルは CPU 上にある。
    """
    return {
        "status": "ok",
        "service": "caption-api",
        "refcap_root": str(RAIZ_REFCAP),
        "models": modelos.diagnostico(),
        "queued_jobs": registro.quantos_na_fila(),
    }
