"""
WholePropGener.py — それ自体がすでに目的のシーンである動画のための proposal 生成器。

"whole" として登録される。動画ごとに [0, duration] をカバーするセグメントを 1 つ出力し、
境界検出は行わず、BLIP が生成したキャプションをランキングする。

存在理由（要約。詳細は RefCap_Projeto_WholePropGenerator.md）:
  - QMPropGenerator は境界を検出する。キャプションが N<=5 なら影響はない
    （常に 1 セグメント）が、N>=6 以降はシーンを分割してしまう — 各動画が
    すでに目的のカットである場合には破壊的だ。
  - その選択基準は argmax(capframe_scores) で、これはクロス行列の対角成分。
    キャプション i はフレーム i から生成されたので、この量には
    構造的なバイアスがある。
  - パイプラインは完全なクロス行列を計算して捨てている
    （constructpipe/base.py:110、`sims, _ = ...`）。このコンポーネントはそれを再計算する。

コードを読むうえで重要な設計判断:
  - 引数は 4 つ（QMPropGenerator の実際のもの）で、ABC の 3 つではない。
  - ランキングに `scores`（capframe_scores）は使わない: これは min-max
    正規化されており、N==1 のとき NaN を生み、動画ごとにちょうど 1 つの
    キャプションを 0 にしてしまう。生の行列を使う。`scores` は診断用にのみ入れる。
  - `get_caption_frame_sims` には `assert frame_features.shape == cap_features.shape` が
    あるので、N 個すべてのキャプションで呼ぶ必要がある。重複排除は行列に対して
    その後で行う。
  - 勝者となる基準は選ばない: すべてのシグナルを列として出力する。
"""
import os
import numpy as np
import torch

from sentence_transformers import util as sim_util

from .base import BasePropGen, REGISTER_PROPGEN

import utils.sim_utils as sim_utils
import utils.basic_utils as basic_utils
import utils.tree_utils as tree_utils
import spacy


# ──────────────────────────────────────────────────────────────────────────
# ローカル定数（マジックナンバーにせず、文書化する）
# ──────────────────────────────────────────────────────────────────────────
_RANK_CRITERIA = ("scene_score", "self_score", "consensus", "pipeline_score")
_DEFAULT_RANK_BY = "scene_score"
_LONG_SCENE_WARN_SECONDS = 30.0   # これを超えたら警告する: そのファイルでは
                                  # 「1 動画 = 1 シーン」の前提が成り立たないかもしれない


def _normalizar_texto(cap: str) -> str:
    """重複排除でキャプションを比較するための正規形。

    小文字化、空白の圧縮、末尾の句読点の除去。出力するテキストは
    変えない — グルーピングのキーとしてのみ使う。
    """
    return " ".join(cap.lower().split()).rstrip(".!?,;: ")


def _extrair_legendas_ordenadas(frame_captions: dict) -> list:
    """キャプションを時間順に返す。キーの型に依存しない。

    `frame_captions` のキーは、初回の実行では `int`
    （BlipCapGener.py:34 は enumerate の `id` を使う）、以降の実行では `str`
    （capgenerator/base.py:33-34 が .jsonl から再読み込みし、JSON はキーを
    文字列に変換する）。並べ替える前に int に正規化する。
    """
    pares = []
    for chave, meta in frame_captions.items():
        try:
            idx = int(chave)
        except (TypeError, ValueError):
            # 想定外のキー: フォールバックとして挿入順を保つ
            idx = len(pares)
        pares.append((idx, meta["cap"]))
    pares.sort(key=lambda p: p[0])
    return [cap for _, cap in pares]


@REGISTER_PROPGEN(["whole"])
class WholePropGenerator(BasePropGen):
    def __init__(self, cfg, models) -> None:
        # QMPropGenerator（QMPropGener.py:20-25）のパターンに従う: super() なしの
        # 直接代入。ABC は self.cfg を定義するだけなので、super() は何も
        # 付け加えない。
        self.cfg = cfg
        self.txt_sim_model = models["sentence_transformer"]
        self.it_sim_model = models["blip_itrtv_model"]
        self.it_sim_processor = models["blip_itrtv_processor"]
        # ★ spaCy: 呼び出し側が渡してくれれば、読み込み済みのものを再利用する。
        #
        # QMPropGenerator は __init__ で直接 `spacy.load(...)` を行う — そして
        # propgen の __init__ は build() の呼び出しのたびに実行される。長時間稼働する
        # サービスでは、リクエストのたびに spaCy を再読み込みすることになる。
        #
        # ここでは、モデルの辞書に "spacy_nlp" があればそれを使う。
        # なければ以前と同じように読み込む — だから CLI は何も変えずに
        # 動き続ける。
        self.nlp = models.get("spacy_nlp") or spacy.load("en_core_web_sm")

        # cfg に新しいフィールドを要求しないオプション: BuildArguments に
        # `whole_rank_by` / `whole_dedup` を追加すれば有効になる。
        # 追加しなければ、下のデフォルトが使われる。
        self.rank_by = getattr(cfg, "whole_rank_by", _DEFAULT_RANK_BY)
        if self.rank_by not in _RANK_CRITERIA:
            raise ValueError(
                f"whole_rank_by={self.rank_by!r} は無効。{_RANK_CRITERIA} のいずれかを使ってください"
            )
        self.dedup = bool(getattr(cfg, "whole_dedup", True))

    # ──────────────────────────────────────────────────────────────────
    # ステップ 1 — 重複排除
    # ──────────────────────────────────────────────────────────────────
    def _deduplicar(self, legendas: list) -> list:
        """同一のキャプションを、最初に現れた順序を保ってグループ化する。

        dict のリストを返す:
            {'texto': str, 'frames': [int], 'linha': int}
        ここで `linha` はいずれかの出現のインデックス — クロス行列の参照に
        使う。同一のキャプションは同一の埋め込みを生み、したがって行列でも
        同一の行になる。どの出現でもかまわない。
        """
        if not self.dedup:
            return [{"texto": c, "frames": [i], "linha": i}
                    for i, c in enumerate(legendas)]

        vistos = {}
        ordem = []
        for i, cap in enumerate(legendas):
            chave = _normalizar_texto(cap)
            if chave not in vistos:
                vistos[chave] = {"texto": cap, "frames": [i], "linha": i}
                ordem.append(chave)
            else:
                vistos[chave]["frames"].append(i)
        return [vistos[k] for k in ordem]

    # ──────────────────────────────────────────────────────────────────
    # ステップ 2 — ランキングのシグナル
    # ──────────────────────────────────────────────────────────────────
    def _calcular_sinais(self, distintas, all_sims, txt_sims, pipeline_scores):
        """異なるキャプションそれぞれについて、4 つのシグナルを計算する。

        all_sims  : [N, N] 生の値（キャプション i x フレーム j）、min-max なし
        txt_sims  : [n_distinct, n_distinct] 異なるキャプション間のテキスト類似度
        pipeline_scores : [N] パイプラインの capframe_scores（NaN を含みうる）
        """
        n_dist = len(distintas)
        registros = []

        for d, item in enumerate(distintas):
            linha = item["linha"]
            frames = item["frames"]

            # scene_score: シーン全体への適合度（全フレームの平均）
            scene = float(all_sims[linha].mean().item())

            # self_score: このキャプションを生成したフレームへの適合度。
            # n_occurrences == 1 なら元の対角成分と一致する。
            self_sc = float(all_sims[linha, frames].mean().item())

            # consensus: 異なるキャプション間でのテキスト上の中心性。
            # n_distinct == 1 では「他」がないので未定義（None）になる。
            if n_dist > 1:
                linha_txt = txt_sims[d]
                soma = float(linha_txt.sum().item()) - float(linha_txt[d].item())
                consenso = soma / (n_dist - 1)
            else:
                consenso = None

            # pipeline_score: 元の基準ならどう判断するか（診断用）。
            # N==1 のとき NaN になりうる（min-max が 0/0 になる）— その場合は None を報告する。
            ps = pipeline_scores[frames] if pipeline_scores is not None else None
            if ps is None or len(ps) == 0 or bool(np.isnan(ps).any()):
                pipeline_sc = None
            else:
                pipeline_sc = float(np.mean(ps))

            registros.append({
                "cap": item["texto"],
                "scene_score": scene,
                "self_score": self_sc,
                "consensus": consenso,
                "pipeline_score": pipeline_sc,
                "n_words": len(item["texto"].split()),
                "n_occurrences": len(frames),
                "frames": frames,
            })
        return registros

    def _ordenar(self, registros: list) -> list:
        """`self.rank_by` で降順に並べる。`None` は末尾へ。"""
        def chave(r):
            v = r[self.rank_by]
            return (v is None, -(v if v is not None else 0.0))
        return sorted(registros, key=chave)

    # ──────────────────────────────────────────────────────────────────
    # ステップ 3 — keywords（検索の GloVe 系統への入力）
    # ──────────────────────────────────────────────────────────────────
    def _coletar_keywords(self, legendas: list) -> list:
        """すべてのフレームのすべてのキャプションに含まれる名詞と動詞。

        QMPropGener.py:134-139 と同じ。（選ばれたものだけでなく）すべてから
        集めることで、検索のキーワード系統が利用する豊かさを保つ。
        """
        keys = []
        for cap in legendas:
            nouns, verbs = tree_utils.get_nouns_verbs(self.nlp, cap)
            keys += nouns
            keys += verbs
        return list(set(keys))

    # ──────────────────────────────────────────────────────────────────
    # オーケストレーター
    # ──────────────────────────────────────────────────────────────────
    def __call__(self, vid_list, captions, scores, all_frame_features):
        # 引数は 4 つ: ABC は 3 つを宣言している（propgenerator/base.py:28）が、
        # 実際の実装と呼び出し側は 4 つを使う
        # （QMPropGener.py:44 と constructpipe/base.py:86）。
        proposals = {}
        vid_2_cap = {x["vid_name"]: x for x in captions}

        # ★ 累積する prop_sims
        #
        # 以前の版は実行のたびに `prop_sims = {}` とし、`vid_list` のシーン
        # だけでファイルを書き直していた。API の `annos` にはリクエストの
        # シーンしか含まれないので、1 シーンを処理すると番組の他のすべての
        # シーンの行列が消え — それを取り戻すにはすべてを再処理する必要があった。
        #
        # 現在は既存のものを読み込み、追加していく。`compute_frame_features` と
        # `compute_capframe_scores` がすでに使っているのと同じパターン
        # （constructpipe/base.py:123 と :97）。
        #
        # ⚠️ このファイルが何でないか: 各エントリは、1 つのシーンのキャプション
        # 同士の [N, N] 行列。ここにシーン間の類似度はない
        # — 累積は個々の行列を保存するだけで、新しい関係は作らない。
        # これを利用するのは `retrieve.py`。
        caminho_sims = os.path.join(self.cfg.exp_dir, self.cfg.prop_sim_path)
        prop_sims = {}
        if os.path.exists(caminho_sims):
            try:
                prop_sims = torch.load(caminho_sims)
                if not isinstance(prop_sims, dict):
                    print(f"[WholePropGener] {caminho_sims} は dict ではない — 新規に開始する")
                    prop_sims = {}
            except Exception as exc:  # noqa: BLE001 — 読み取れないキャッシュで落とさない
                print(f"[WholePropGener] prop_sims が読み取れない ({exc}) — 新規に開始する")
                prop_sims = {}

        for vid in vid_list:
            video_name = vid.split(".")[0]

            if video_name not in vid_2_cap:
                # キャプション生成がその動画をスキップしたときに起きる（例: デコードの
                # 失敗、BlipCapGener.py:23）。例外を出す代わりに警告する。
                print(f"[whole] 警告: {video_name} にキャプションがない。無視する。")
                continue

            cap_meta = vid_2_cap[video_name]
            duration = cap_meta["duration"]
            legendas = _extrair_legendas_ordenadas(cap_meta["frame_captions"])
            n_raw = len(legendas)

            # ── 分岐 A: キャプションが 1 つもない ─────────────────────
            # 動画が 1 秒未満（int(duration) == 0）で、パイプラインがここまで
            # 到達した場合にのみ起きる。防御的な処理 — 理想はこうした動画を
            # 入口（make_annos.py）で除外すること。
            if n_raw == 0:
                print(f"[whole] 警告: {video_name} にはキャプションが 1 つもない "
                      f"(duration={duration})。proposal は空。")
                proposals[video_name] = {
                    "proposals": [],
                    "duration": duration,
                    "n_raw": 0,
                    "n_distinct": 0,
                    "warning": "キャプションなし（長さ < 1s？）",
                }
                continue

            distintas = self._deduplicar(legendas)
            n_distinct = len(distintas)
            keys = self._coletar_keywords(legendas)

            aviso = None
            if duration > _LONG_SCENE_WARN_SECONDS:
                aviso = (f"長さ {duration:.1f}s が "
                         f"{_LONG_SCENE_WARN_SECONDS:.0f}s を超えている: この"
                         f"動画が本当に単一のシーンか確認してください")

            # ── 分岐 B: 異なるキャプションが 1 つ → そのまま返す ─────
            # N==1 と「すべてのキャプションが同じ」をカバーする。行列なし、シグナルなし、
            # argmax なし — そして NaN のリスクもない（行うべき正規化がない）。
            if n_distinct == 1:
                unica = distintas[0]
                ranking = [{
                    "cap": unica["texto"],
                    "scene_score": None,
                    "self_score": None,
                    "consensus": None,
                    "pipeline_score": None,
                    "n_words": len(unica["texto"].split()),
                    "n_occurrences": len(unica["frames"]),
                    "frames": unica["frames"],
                }]
                proposals[video_name] = {
                    "proposals": [{
                        "st": 0.0,
                        "ed": duration,
                        "cap": unica["texto"],
                        "keys": keys,
                        "ranking": ranking,
                        "rank_by": self.rank_by,
                        "n_raw": n_raw,
                        "n_distinct": 1,
                    }],
                    "duration": duration,
                    "n_raw": n_raw,
                    "n_distinct": 1,
                    "warning": aviso,
                }
                continue

            # ── 分岐 C: ランキング（n_distinct が 2 でも 300 でも同じ） ──
            frame_features = all_frame_features[video_name].to(self.cfg.device)

            # 生のクロス行列。N 個すべてのキャプションで呼ぶのは、
            # get_caption_frame_sims（sim_utils.py:87）が
            # frame_features.shape == cap_features.shape を要求するから。2 つ目の戻り値は
            # パイプラインが捨てている完全な [N, N] 行列。
            with torch.no_grad():
                _, all_sims = sim_utils.get_caption_frame_sims(
                    self.it_sim_model, self.it_sim_processor,
                    frame_features, legendas, self.cfg
                )

                # consensus のための、異なるキャプション間のテキスト類似度。
                textos_distintos = [d["texto"] for d in distintas]
                emb = self.txt_sim_model.encode(textos_distintos)
                txt_sims = sim_util.cos_sim(emb, emb)

            prop_sims[video_name] = all_sims.cpu()

            ps = scores.get(video_name) if isinstance(scores, dict) else None
            pipeline_scores = ps.cpu().numpy() if ps is not None else None

            registros = self._calcular_sinais(
                distintas, all_sims, txt_sims, pipeline_scores)
            ranking = self._ordenar(registros)

            proposals[video_name] = {
                "proposals": [{
                    "st": 0.0,
                    "ed": duration,
                    "cap": ranking[0]["cap"],   # build_tree_meta:177 の契約
                    "keys": keys,               # 任意の契約、L178-179
                    # 以下は診断用。build_tree_meta は余分なキーを無視するので、
                    # これは tree.json を汚さずに proposals.json に残る。
                    "ranking": ranking,
                    "rank_by": self.rank_by,
                    "n_raw": n_raw,
                    "n_distinct": n_distinct,
                }],
                "duration": duration,
                "n_raw": n_raw,
                "n_distinct": n_distinct,
                "warning": aviso,
            }

        # 永続化。QMPropGener.py:63-64 と同じ。
        #
        # 辞書全体を保存する — ディスクから読んだものに、この実行で追加した
        # ものを加えて。`if prop_sims` のガードは残す: 行列が 1 つもなければ
        # （古いものも新しいものも）、保存するものはない。
        if prop_sims:
            torch.save(prop_sims, caminho_sims)
        basic_utils.save_json(
            proposals,
            os.path.join(self.cfg.exp_dir, self.cfg.proposals_file),
            save_pretty=True,
        )
        return proposals
