"""RefCap のモデルの選択的な読み込み。

このファイルが存在する理由
---------------------------
RefCap には読み込み処理が 1 か所しかない — `utils/model_utils.py:load_pretrained_models`
— そしてそれは全か無か: GloVe を含む 4 つのモデルを読み込む。

GloVe の利用者は 1 つだけ: `pipeline/treebuilder/capTree.py:23`。そして `CapTree` が
インスタンス化されるのは `retrieve.py:269` だけ。この API は retrieval を行わないので、
読み込むのは大きなテキストファイルのパースに無駄なコストを払うことになる。

このモジュールは `construct` が必要とする 3 つのモデルを読み込み、
`load_pretrained_models` と同じ形式の辞書を返す — RefCap の
`build(cfg, pretrained_models)` が一切の手直しなしに受け付けられるように。

各モデルの用途（RefCap のコードで確認済み）
--------------------------------------------------------
    cap_gen_model / cap_gen_processor
        BlipCapGener.py:14-15  -> キャプション生成（ステップ 1）

    blip_itrtv_model / blip_itrtv_processor
        constructpipe/base.py:50-51  -> フレーム特徴量とスコア（ステップ 2,3,5）
        denoiser/base.py:26-27       -> ノイズ除去（ステップ 4）
        WholePropGener.py            -> scene_score / self_score（ステップ 6）

    sentence_transformer
        WholePropGener.py  -> コンセンサスのシグナル（ステップ 6）
        QMPropGener.py:22  -> 自己類似度行列

    glove_model = None
        読み込まない。使うのは CapTree だけで、CapTree は retrieve 側のもの。
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class InfoDeCarga:
    """読み込みの診断情報 — /health とログで役立つ。"""
    nome: str
    identificador: str
    segundos: float


class ModelosResidentes:
    """一度だけ読み込んだモデルを、プロセスの生存期間中ずっと保持する。

    使い方:
        residentes = ModelosResidentes()
        residentes.carregar(caption_model=..., blip_itm_model=..., ...)
        ...
        build(cfg, residentes.como_dict())
    """

    def __init__(self) -> None:
        self.cap_gen_model = None
        self.cap_gen_processor = None
        self.blip_itrtv_model = None
        self.blip_itrtv_processor = None
        self.sentence_transformer = None
        self.spacy_nlp = None
        self.device: str | None = None
        self.cargas: list[InfoDeCarga] = []

    # ------------------------------------------------------------------ #
    @property
    def pronto(self) -> bool:
        return all([
            self.cap_gen_model is not None,
            self.cap_gen_processor is not None,
            self.blip_itrtv_model is not None,
            self.blip_itrtv_processor is not None,
            self.sentence_transformer is not None,
            self.spacy_nlp is not None,
        ])

    def carregar(
        self,
        *,
        caption_model: str,
        blip_itm_model: str,
        sentence_transformer: str,
        device: str = "cuda",
        spacy_model: str = "en_core_web_sm",
    ) -> None:
        """3 つのモデルを読み込む。サービスの起動時に 1 回だけ呼ばれる。

        import をファイル先頭ではなくここに置く理由は 2 つ:
        1. torch を読み込まずに、モジュールを調査目的で import できる;
        2. 重いコストがこの呼び出しで発生することを明示できる。
        """
        # 遅延 import: 実際に読み込むときだけ。
        from transformers import (
            BlipForConditionalGeneration,
            BlipForImageTextRetrieval,
            BlipProcessor,
        )
        from sentence_transformers import SentenceTransformer
        import spacy

        self.device = device
        self.cargas = []

        # --- 1. BLIP キャプション生成（ステップ 1） ------------------- #
        # utils/model_utils.py:12-13 と同じ
        t0 = time.perf_counter()
        log.info("cap_gen_model=%s を読み込み中 ...", caption_model)
        self.cap_gen_model = BlipForConditionalGeneration.from_pretrained(
            caption_model
        ).to(device)
        self.cap_gen_processor = BlipProcessor.from_pretrained(caption_model)
        self._registrar("cap_gen", caption_model, t0)

        # --- 2. BLIP-ITM（ステップ 2,3,4,5,6） ------------------------- #
        # utils/model_utils.py:30-31 と同じ
        t0 = time.perf_counter()
        log.info("blip_itrtv_model=%s を読み込み中 ...", blip_itm_model)
        self.blip_itrtv_model = BlipForImageTextRetrieval.from_pretrained(
            blip_itm_model
        ).to(device)
        self.blip_itrtv_processor = BlipProcessor.from_pretrained(blip_itm_model)
        self._registrar("blip_itm", blip_itm_model, t0)

        # --- 3. sentence-transformer（ステップ 6） -------------------- #
        # utils/model_utils.py:35 と同じ
        t0 = time.perf_counter()
        log.info("sentence_transformer=%s を読み込み中 ...", sentence_transformer)
        self.sentence_transformer = SentenceTransformer(sentence_transformer).to(device)
        self._registrar("sentence_transformer", sentence_transformer, t0)

        # --- 4. spaCy（ステップ 6: キーワード抽出） ------------------- #
        # これがないと、propgenerator はリクエストのたびに spacy.load() を実行してしまう:
        # propgen の __init__ は起動時ではなく build() の中で実行される。
        t0 = time.perf_counter()
        log.info("spacy=%s を読み込み中 ...", spacy_model)
        self.spacy_nlp = spacy.load(spacy_model)
        self._registrar("spacy", spacy_model, t0)

        total = sum(c.segundos for c in self.cargas)
        log.info("常駐モデルの準備完了: %.1fs (device=%s)", total, device)

    def _registrar(self, nome: str, identificador: str, t0: float) -> None:
        info = InfoDeCarga(nome, identificador, time.perf_counter() - t0)
        self.cargas.append(info)
        log.info("  %s 読み込み完了: %.1fs", nome, info.segundos)

    # ------------------------------------------------------------------ #
    def como_dict(self) -> dict:
        """RefCap が期待する、まさにその形式の辞書。

        6 つのキーは `load_pretrained_models` と同じ。`glove_model` は意図的に
        None にしている: `construct` のどのコンポーネントも参照しない
        （参照するのは retrieve 側の CapTree だけ）。キーを残しておけば、将来の
        コードが `models.get("glove_model")` を行っても KeyError を防げる。
        """
        if not self.pronto:
            raise RuntimeError(
                "モデルが読み込まれていない — サービスの起動時に carregar() を呼んでください"
            )
        return {
            "cap_gen_model": self.cap_gen_model,
            "cap_gen_processor": self.cap_gen_processor,
            "blip_itrtv_model": self.blip_itrtv_model,
            "blip_itrtv_processor": self.blip_itrtv_processor,
            "sentence_transformer": self.sentence_transformer,
            # ★ 追加のキー（load_pretrained_models には存在しない）。
            # WholePropGenerator は .get() で参照し、QMPropGenerator は無視して
            # 自前のものを読み込む。このキーで壊れるコンポーネントはない。
            "spacy_nlp": self.spacy_nlp,
            "glove_model": None,
        }

    def liberar(self) -> None:
        """参照を手放し、GPU のキャッシュをクリアする。終了時に呼ばれる。"""
        self.cap_gen_model = None
        self.cap_gen_processor = None
        self.blip_itrtv_model = None
        self.blip_itrtv_processor = None
        self.sentence_transformer = None
        self.spacy_nlp = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:  # noqa: BLE001 — 終了時に、これで落とす価値はない
            pass
        log.info("モデルを解放した")

    def diagnostico(self) -> dict:
        """/health エンドポイント用の要約。

        GPU の実際の状態を含む — 「モデルは本当に常駐しているか？」に答えるのは
        これだ。これがなければ、`pronto: true` はオブジェクトが存在することしか示さず、
        GPU メモリを使っていることまでは示さない。
        """
        return {
            "ready": self.pronto,
            "device": self.device,
            "models": [
                {"name": c.nome, "id": c.identificador,
                 "load_seconds": round(c.segundos, 2)}
                for c in self.cargas
            ],
            "glove_loaded": False,
            "gpu": self.estado_da_gpu(),
        }

    @staticmethod
    def estado_da_gpu() -> dict:
        """このプロセスが実際に使っている GPU メモリ。

        `alocado_mb` はこのプロセスのテンソルが使っている量。モデルが GPU に
        常駐していれば、この数値は大きく、リクエスト間で安定している。
        `pronto: true` で 0 なら、モデルは CPU 上にある。
        """
        try:
            import torch
        except ImportError:
            return {"available": False, "reason": "torch not installed"}

        if not torch.cuda.is_available():
            return {
                "available": False,
                "reason": "torch.cuda.is_available() == False",
                "hint": "CPU-only torch build, or empty CUDA_VISIBLE_DEVICES",
            }

        try:
            indice = torch.cuda.current_device()
            return {
                "available": True,
                "device_count": torch.cuda.device_count(),
                "current_index": indice,
                "name": torch.cuda.get_device_name(indice),
                # ★ allocated_mb > 0 かつ呼び出し間で安定 = モデルは
                #   GPU に常駐している。ready:true で 0 なら、CPU 上にある。
                "allocated_mb": round(torch.cuda.memory_allocated(indice) / 1024**2, 1),
                "reserved_mb": round(torch.cuda.memory_reserved(indice) / 1024**2, 1),
                "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            }
        except Exception as exc:  # noqa: BLE001 — 診断が落ちてはならない
            return {"available": True, "error": f"{type(exc).__name__}: {exc}"}
