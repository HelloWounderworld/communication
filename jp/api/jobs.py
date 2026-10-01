"""非同期ジョブの登録簿: 直列化されたキュー、照会可能な状態、webhook。

なぜ直列化キューなのか（複数ワーカーではなく）
------------------------------------------------
ワーカーを追加するたびに、そのワーカー専用のモデル一式が GPU に読み込まれる — BLIP-large を
使う 2 つのワーカーは、常駐する 2 つの BLIP-large になる。そして同じモデルでの
同時推論は実質的な利得をもたらさない。GPU が内部ですでに直列化しているからだ。

したがって: 1 プロセス、1 組のモデル、リクエストは 1 つずつ
実行する。スループットが必要なら、進むべき道はバッチ（複数のリクエストの
フレームを 1 回の呼び出しにまとめる）であり、プロセスを増やすことではない。

JOB_ID + GET と WEBHOOK — 両方とも
--------------------------------
    job_id + GET : シンプルで、どんなクライアントでも動き、結果の再照会や
                   失敗したジョブの診断ができる。
    webhook      : クライアントが別システムの場合にポーリングを避けられる。

一方が他方を置き換えるわけではない: webhook があっても、再照会のため、そして
callback の配信が失敗したときのために、GET は依然として欠かせない。
"""
from __future__ import annotations

import asyncio
import logging
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

log = logging.getLogger(__name__)


class EstadoJob(str, Enum):
    NA_FILA = "na_fila"
    EXECUTANDO = "executando"
    CONCLUIDO = "concluido"
    FALHOU = "falhou"


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Job:
    id: str
    estado: EstadoJob = EstadoJob.NA_FILA
    criado_em: str = field(default_factory=_agora)
    iniciado_em: str | None = None
    terminado_em: str | None = None
    resultado: Any = None
    erro: str | None = None
    callback_url: str | None = None
    callback_entregue: bool | None = None
    entrada: dict = field(default_factory=dict)

    def como_dict(self, incluir_resultado: bool = True) -> dict:
        d = {
            "job_id": self.id,
            "estado": self.estado.value,
            "criado_em": self.criado_em,
            "iniciado_em": self.iniciado_em,
            "terminado_em": self.terminado_em,
            "erro": self.erro,
            "callback_url": self.callback_url,
            "callback_entregue": self.callback_entregue,
            "entrada": self.entrada,
        }
        if incluir_resultado:
            d["resultado"] = self.resultado
        return d


class RegistroDeJobs:
    """ジョブを保持し、1 つずつ実行する。

    ⚠️ 保存先はメモリ上: プロセスを再起動すると履歴は失われる。
    永続化するには `self._jobs` を SQLite/Redis に置き換える — このオブジェクトの
    公開インターフェースは変わらない。
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        # 実行を直列化する: モデルを使えるのは一度に 1 ジョブだけ。
        self._trava = asyncio.Lock()

    # ------------------------------------------------------------------ #
    def criar(self, entrada: dict, callback_url: str | None = None) -> Job:
        job = Job(id=uuid.uuid4().hex, entrada=entrada, callback_url=callback_url)
        self._jobs[job.id] = job
        log.info("job %s を作成", job.id)
        return job

    def obter(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def listar(self, limite: int = 50) -> list[dict]:
        jobs = sorted(self._jobs.values(), key=lambda j: j.criado_em, reverse=True)
        return [j.como_dict(incluir_resultado=False) for j in jobs[:limite]]

    def quantos_na_fila(self) -> int:
        return sum(1 for j in self._jobs.values() if j.estado == EstadoJob.NA_FILA)

    # ------------------------------------------------------------------ #
    async def executar(self, job: Job, tarefa: Callable[[Job], Any]) -> None:
        """ロックの下、スレッドで `tarefa(job)` を実行する。

        `tarefa` は同期的で重い（動画のデコード + 推論）。イベントループを止めないよう
        `asyncio.to_thread` で実行する — これにより、処理中もサーバーは
        /health と GET /jobs に応答し続ける。
        """
        async with self._trava:                      # <- 一度に 1 ジョブ
            job.estado = EstadoJob.EXECUTANDO
            job.iniciado_em = _agora()
            log.info("job %s を開始", job.id)
            try:
                job.resultado = await asyncio.to_thread(tarefa, job)
                job.estado = EstadoJob.CONCLUIDO
                log.info("job %s が完了", job.id)
            except Exception as exc:  # noqa: BLE001 — 失敗はジョブに記録する
                job.estado = EstadoJob.FALHOU
                job.erro = f"{type(exc).__name__}: {exc}"
                log.exception("job %s が失敗", job.id)
                job.resultado = {"traceback": traceback.format_exc()}
            finally:
                job.terminado_em = _agora()

        # ロックの外: callback の配信でキューをブロックしてはならない。
        if job.callback_url:
            await self._entregar_callback(job)

    async def _entregar_callback(self, job: Job) -> None:
        """ジョブの最終状態を callback_url に POST する。

        配信の失敗でジョブは落ちない — `callback_entregue=False` として
        記録され、クライアントは引き続き GET で照会できる。
        """
        import httpx  # noqa: PLC0415 — 遅延 import。callback があるときだけ

        try:
            async with httpx.AsyncClient(timeout=10.0) as cliente:
                r = await cliente.post(job.callback_url, json=job.como_dict())
                r.raise_for_status()
            job.callback_entregue = True
            log.info("job %s の callback を %s に配信した", job.id, job.callback_url)
        except Exception as exc:  # noqa: BLE001
            job.callback_entregue = False
            log.warning(
                "job %s の callback が失敗 (%s): %s — GET /jobs/%s で照会してください",
                job.id, job.callback_url, exc, job.id,
            )
