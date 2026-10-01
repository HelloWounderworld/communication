"""キャプション生成: 解決済みのリクエストから、保存されたレスポンスまで。

★ このファイルの名前が `pipeline.py` ではない理由
    RefCap のルートには `pipeline/` パッケージがある — そして `api/` はその中にある。
    アプリのディレクトリは先に `sys.path` に入るので、`api/pipeline.py` があると
    `sys.modules` の `pipeline` という名前を占有し、construct.py の
    `from pipeline.denoiser import *` が次のように失敗する:

        ModuleNotFoundError: No module named 'pipeline.denoiser';
                             'pipeline' is not a package

    ここで作るモジュールはすべて、RefCap のトップレベルの名前を避ける必要がある:
    annos, config, construct, dataset, meta, pipeline, results, retrieve,
    scripts, standalone_eval, utils。

このモジュールが解決すること
-------------------------
`/teste/construct` と `/teste/construct-lote` のルートで、モデルの再利用が
機能することは証明された。`POST /jobs` に欠けていたのは、キャプション生成の前の
パイプラインの 5 つのステップだった:

    1. 要求された動画で annos を書き出す
    2. ディレクトリを受け付ける
    3. キャッシュを制御しながら読み書き・削除する
    4. collection で分離する
    5. リクエストの video_root を使う

このモジュールはその 5 つを行い、さらに RefCap の出力を合意した
レスポンス形式に変換する。

★ 設計を形作る制約
    `constructpipe/base.py:43` は `os.listdir(cfg.video_root)` を行う — 1 回の実行で
    ディレクトリは 1 つ。シーンは次の場所にあるので

        /caminho/{program_id}/{video_id}/{scene_id}

    `video_id` が異なるバッチは複数のディレクトリに散らばっており、
    1 回の `build()` 呼び出しには収まらない。

    解決策: アイテムをディレクトリ単位でグルーピングし、グループごとに `build()` を
    1 回呼ぶ。同じ動画のシーンはまとめて処理され（効率的）、異なる動画のシーンは
    別々の実行になる。
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
import re
import time
from collections import defaultdict
from datetime import datetime, timezone

import persistencia
from contratos import (MODEL_NAME_PADRAO, MODEL_VERSION_PADRAO, CaptionRequest,
                       ErrorCode, Keyword, SceneItem, SceneResponse)

log = logging.getLogger(__name__)

# シーンのパスを解決するときに受け付ける拡張子。
EXTENSOES_VIDEO = (".mp4", ".mkv", ".avi", ".webm", ".mov", ".m4v")

# ★★★ パスの形式を知っている唯一の箇所 ★★★
#
# 合意した契約は:
#     scene_video_path = <prefixo>/{program_id}/{video_id}/{scene_id}.mp4
#
# RefCap は各動画をファイルのベース名で識別する — 現在それは
# `scene_id`。これが成り立つのは、同じ `program_id` の中では
# `scene_id` が一意だから（チームに確認済みの前提）。
#
# リクエストの形式が変わったら、ここだけを変えること:
#
#   "scene_id"            -> ベース名は scene_id そのもの  (現在のデフォルト)
#   "video_id__scene_id"  -> いつか同じ program_id 内の異なる video_id の間で
#                            scene_id が重複するようになったら使う
#
# この定数を変えても変わるのは、annos とキャッシュへのシーンの登録方法だけ。
# パイプラインの残り — グルーピング、build、レスポンス — は、単一リクエストでも
# バッチでも同じまま。
IDENTIFICADOR = "scene_id"


def montar_identificador(item: "SceneItem", nome_do_arquivo: str) -> str:
    """RefCap がこのシーンを登録するときのベース名を返す。

    `nome_do_arquivo` はディスク上で見つかったファイルの stem — IDENTIFICADOR が
    "scene_id" のときに使う。RefCap が os.listdir で見るのはこれだからだ。
    """
    if IDENTIFICADOR == "video_id__scene_id":
        if not item.video_id:
            raise CenaNaoResolvida(
                ErrorCode.INVALID_REQUEST,
                f"IDENTIFICADOR には `video_id` が必要だが、シーン "
                f"'{item.scene_id}' にはない",
            )
        return f"{item.video_id}__{item.scene_id}"
    return nome_do_arquivo

MODEL_NAME_PADRAO = os.environ.get("REFCAP_MODEL_NAME", "refcap")
MODEL_VERSION_PADRAO = os.environ.get("REFCAP_MODEL_VERSION", "v1")


# --------------------------------------------------------------------------- #
# パスの解決
# --------------------------------------------------------------------------- #
class CenaNaoResolvida(Exception):
    """メッセージと一緒にエラーコードを運ぶ。

    これがないと、捕捉する側はテキストからコードを推測しなければならない — それは
    脆く、メッセージが変わると壊れる。
    """

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


def resolver_cena(item: SceneItem) -> tuple[str, str, str]:
    """シーンのディレクトリとファイルを突き止める。

    合意した `scene_video_path` は `/caminho/{program_id}/{video_id}/{scene_id}`
    — 拡張子が明示されていない。これは曖昧なので、3 つのケースを扱う:

        1. 既存のファイル                 -> そのまま使う
        2. 拡張子のないファイル           -> 既知の拡張子を 1 つずつ試す
        3. ディレクトリ                   -> その中で、ベース名が scene_id である
                                            動画を探す

    (diretorio, nome_do_arquivo, nome_base) を返す。
    見つからなければ、診断用のメッセージ付きで FileNotFoundError を送出する。
    """
    caminho = pathlib.Path(item.scene_video_path)

    # ケース 1: 既存のファイル
    if caminho.is_file():
        return str(caminho.parent), caminho.name, caminho.stem

    # ケース 2: 拡張子がない
    for ext in EXTENSOES_VIDEO:
        candidato = caminho.with_suffix(ext)
        if candidato.is_file():
            return str(candidato.parent), candidato.name, candidato.stem

    # ケース 3: ディレクトリ — その中で scene_id を探す
    if caminho.is_dir():
        for ext in EXTENSOES_VIDEO:
            candidato = caminho / f"{item.scene_id}{ext}"
            if candidato.is_file():
                return str(caminho), candidato.name, candidato.stem
        # ⚠️ ステップ 2 で削除: scene_id に一致するものがないとき、ディレクトリ内の
        # 唯一の動画を使っていたフォールバック。
        #
        # 理由: 誤ったファイルに黙ってキャプションを付け、別のシーンのキャプションで
        # status "success" を返していた。失敗する方がましだ。
        videos = sorted(
            p for p in caminho.iterdir()
            if p.is_file() and p.suffix.lower() in EXTENSOES_VIDEO
        )
        raise CenaNaoResolvida(
            ErrorCode.SCENE_NOT_FOUND,
            f"ディレクトリ {caminho} には動画が {len(videos)} 件あるが、"
            f"'{item.scene_id}' という名前のものはない",
        )

    # 2 つのコードの区別は利用者にとって重要:
    #   FILE_NOT_FOUND  -> パス自体がまったく存在しない
    #   SCENE_NOT_FOUND -> パスは存在するが、その scene_id の動画がない
    if not caminho.exists():
        raise CenaNaoResolvida(
            ErrorCode.FILE_NOT_FOUND,
            f"パスが見つからない: {item.scene_video_path}",
        )
    raise CenaNaoResolvida(
        ErrorCode.SCENE_NOT_FOUND,
        f"シーン '{item.scene_id}' が {item.scene_video_path} に見つからなかった "
        f"（ファイルとして、拡張子 {EXTENSOES_VIDEO} を付けて、ディレクトリとして試した）",
    )


# --------------------------------------------------------------------------- #
# 重み付きキーワード
# --------------------------------------------------------------------------- #
_PALAVRA = re.compile(r"[a-z0-9']+")


def ranquear_keywords(
    keys: list[str],
    caption: str,
    modelo_texto=None,
    maximo: int = 10,
) -> list[Keyword]:
    """キャプションに含まれるキーワードを、重み 1.0 で返す。

    このフィルターが必要な理由
        proposal の `keys` フィールドには、シーンのすべてのフレームのすべての
        キャプションの名詞と動詞が入っている（WholePropGener._coletar_keywords）。
        その多くは、ランキングで選ばれたキャプションと関係がない。ここでは
        実際にそこに現れるものだけを残す。

    ★ 重みは 1.0 に固定 — 意図的に
        以前の重み付け（下記参照）は、重みが retrieval にそもそも必要かどうかが
        決まるまで保留されている。retrieval は GloVe を使う別の API が行う。
        それまでは、出力するキーワードはすべて同じ価値を持つ。

        キャプションに文字どおり現れる語だけが入るので、1.0 は
        筋が通っている: 表現すべき段階がない。

    ─────────────────────────────────────────────────────────────────────────
    保留中の計算。GloVe についての判断が下されたときのために:

        weight = 0.6 × 文字どおりの出現 + 0.4 × 意味的類似度

        (a) 文字どおりの出現 — その語がキャプションに現れるか？ 基本の重みは 1.0。

        (b) 意味的類似度 — sentence-transformer の空間における、語の埋め込みと
            キャプションの埋め込みのコサイン。文字どおりの繰り返しなしでも関係を
            捉えていた（"cooking" × "a woman preparing food"）。

        保留にした理由（必要性への疑問に加えて）:
          - `paraphrase-distilroberta-v2` は文を比較するために学習されており、
            単独の語向けではない — そのように使うのは学習の
            ドメイン外での運用になる;
          - 重み 0.6/0.4 は一度も較正されていない: アノテーション済みデータなしに、
            判断で選ばれた。

        この話題が戻ってきたときに評価すべき代替案:
          1. フレームに対する BLIP-ITM —「この語が見えているものをどれだけ
             よく表すか」。より動画に根ざしている。フレームを後段に渡す必要がある。
          2. 語のベクトルを持つモデル（spaCy _md/_lg、または retrieval が
             すでに使っている GloVe そのもの）。
          3. 文字どおりの出現 + フレームのキャプション間での頻度。

        `modelo_texto` パラメーターは意図的にシグネチャに残してある:
        呼び出し側は sentence-transformer を渡し続けており、計算を再び有効にしても
        呼び出し側を変える必要はない。
    ─────────────────────────────────────────────────────────────────────────
    """
    if not keys or not caption:
        return []

    tokens_legenda = set(_PALAVRA.findall(caption.lower()))

    # dict.fromkeys は最初に現れた順序を保つ
    unicas = list(dict.fromkeys(
        k.strip().lower() for k in keys if k and k.strip()
    ))

    presentes = [k for k in unicas if k in tokens_legenda]
    return [Keyword(token=k, weight=1.0) for k in presentes[:maximo]]


# --------------------------------------------------------------------------- #
# パイプライン
# --------------------------------------------------------------------------- #
def _limpar_caches(cfg, collection: str, nomes_base: list[str]) -> dict:
    """ピンポイントの削除: 指定したシーンだけで、番組全体ではない。

    以前の版は 3 つのファイルを丸ごと削除していた — それでは番組の他のすべての
    シーンのキャッシュが捨てられてしまう。ステップ 2 の
    `collection = program_id` によって、それは破壊的になった。
    """
    return persistencia.limpar_cache_das_cenas(cfg, collection, nomes_base)


def _escrever_annos(cfg, collection: str, nomes_base: list[str]) -> str:
    """このグループの動画でアノテーションファイルを書き出す。

    ★ これがないと何も処理されない。`select_videos`（constructpipe/base.py:186-203）は
    `vid_name` がここにある動画だけを残す — それ以外は黙って捨てられる。
    エラーも警告もない。
    """
    dir_anno = os.path.join(cfg.anno_dir, collection)
    os.makedirs(dir_anno, exist_ok=True)
    caminho = os.path.join(dir_anno, cfg.anno_file)
    with open(caminho, "w", encoding="utf-8") as f:
        for nb in nomes_base:
            f.write(json.dumps({"vid_name": nb}, ensure_ascii=False) + "\n")
    return caminho


def processar_pedido(
    pedido: CaptionRequest,
    job_id: str,
    montar_cfg,
    modelos,
    config_servico,
    mode: str = "sync",
) -> dict:
    """パイプライン全体を実行し、合意した形式でレスポンスを返す。

    `montar_cfg` と `modelos` はサービスから渡される — これらをパラメーターに
    しておけば、FastAPI を起動せずにこの関数をテストできる。
    """
    t0 = time.perf_counter()
    itens = pedido.como_itens()
    if not itens:
        raise CenaNaoResolvida(
            ErrorCode.INVALID_REQUEST,
            "空のリクエスト: `scene_id` + `scene_video_path`、または `items` を指定してください",
        )

    # ★ どの return よりも前に、ここで定義する: 失敗時の summary に必要で、
    # すべてのシーンがパスの解決で失敗したときには早期 return が
    # ある。
    program_id = next((i.program_id for i in itens if i.program_id), None)

    # --- ステップ 1: パスを解決する --------------------------------------- #
    resolvidos: list[dict] = []
    falhas: list[SceneResponse] = []
    for item in itens:
        try:
            diretorio, arquivo, stem = resolver_cena(item)
            resolvidos.append({
                "item": item, "diretorio": diretorio, "arquivo": arquivo,
                # RefCap がシーンを登録するときのベース名 — モジュール先頭の
                # IDENTIFICADOR を参照
                "nome_base": montar_identificador(item, stem),
            })
        except CenaNaoResolvida as exc:
            falhas.append(SceneResponse.falha(
                item.scene_id, exc.error_code, exc.message))

    if not resolvidos:
        # ★ すべてのシーンがパスの解決で失敗した。早期に返すが、
        # summary はそれでも保存する — 完全に失敗したリクエストこそ、
        # 後で調査したいものだからだ。
        #
        # ここではまだ `cfg` が存在しない（グループのループの中で作られる）ので、
        # res_dir を知るためだけに 1 つ組み立てる。
        segundos = round(time.perf_counter() - t0, 2)
        erros_por_codigo: dict[str, int] = {}
        for f in falhas:
            if f.error_code:
                erros_por_codigo[f.error_code] = erros_por_codigo.get(f.error_code, 0) + 1
        if program_id:
            try:
                agora = datetime.now(timezone.utc)
                persistencia.gravar_summary(montar_cfg().res_dir, program_id, {
                    "state": "concluded",
                    "data": persistencia._data_legivel(agora),
                    "timestamp": agora.isoformat(),
                    "total": len(itens), "ok": 0, "errors": len(falhas),
                    "seconds": segundos,
                    "scenes": [i.scene_id for i in itens],
                    "from_cache": 0, "processed": 0,
                    "force": pedido.force,
                    "proposal_generator": pedido.proposal_generator,
                    "mode": mode,
                    "groups": [],
                    "error_codes": erros_por_codigo,
                    "persisted": {},
                })
            except Exception:  # noqa: BLE001 — summary は診断用
                log.exception("%s の summary の保存に失敗", program_id)
        return {
            "items": [f.model_dump(exclude_none=True) for f in falhas],
            "summary": {"total": len(itens), "ok": 0, "errors": len(falhas)},
            "groups": [],
            "persisted": {},
            "seconds": segundos,
        }

    # --- ステップ 2: ディレクトリ単位でグルーピングする ------------------- #
    # ★ `build()` は 1 つのディレクトリを列挙する（constructpipe/base.py:43）。
    # `video_id` が異なるシーンは別のディレクトリにある -> グループごとに build 1 回。
    grupos: dict[str, list[dict]] = defaultdict(list)
    for r in resolvidos:
        grupos[r["diretorio"]].append(r)

    # --- ステップ 3: collection を決める ---------------------------------- #
    # 優先順位: リクエストの指定 > program_id > job_id。
    # program_id を使うと、同じ番組のシーンがキャッシュを共有する — これは
    # 望ましい。たいてい一緒に再処理されるからだ。
    def collection_de(grupo: list[dict]) -> str:
        """`collection` は `program_id` そのもの。1 つの識別子で、5 つのパス:

            annos/{program_id}/vcmr.jsonl
            meta/captions/{program_id}_blip.jsonl
            meta/framefeatures/{program_id}.pt
            meta/scores/{program_id}_blip.pt
            results/construct/{program_id}/

        これが、2 つの番組が決して交わらないことを保証している: キャッシュ、annos、
        結果はすべて同じ識別子の下に置かれる。

        `program_id` がない場合 — 契約が想定していないケース — は job_id に
        フォールバックする。これは誰のキャッシュも再利用せず、完全な分離を与える。
        """
        pid = grupo[0]["item"].program_id
        return pid if pid else f"job_{job_id[:12]}"

    # --- ステップ 4: グループごとに build を 1 回実行する ----------------- #
    from construct_new import build

    por_cena: dict[str, SceneResponse] = {}
    diagnostico_por_cena: dict[str, dict] = {}
    diagnostico_grupos = []
    # `cfg` はループ内でグループごとに作られる。res_dir を保持しておき、
    # すべてのグループの後に行う永続化で使う
    cfg_res_dir: str | None = None

    for diretorio, grupo in grupos.items():
        collection = collection_de(grupo)
        nomes_base = [g["nome_base"] for g in grupo]

        cfg = montar_cfg(
            video_root=diretorio,                       # ← ステップ 5: リクエストから
            collection=collection,                      # ← ステップ 4: 分離
            # ★ construct_name は空: RefCap の exp_dir は
            #     res_dir/construct_dir/{collection}/{construct_name}
            #   "" にすると os.path.join が最後の階層を潰し、次になる
            #     results/construct/{program_id}/
            #   これにより番組のアーティファクトは、ジョブごとのディレクトリではなく、
            #   リクエストをまたいで累積する 1 か所にまとまる。
            construct_name="",
            caption_generator="blip",
            proposal_generator=pedido.proposal_generator,
            device=config_servico.device,
            caption_model=config_servico.caption_model,
            blip_itm_model=config_servico.blip_itm_model,
            sentence_transformer=config_servico.sentence_transformer,
        )

        cfg_res_dir = cfg.res_dir

        # すでにキャッシュにあるもの（実行の前に読む）
        caminho_cache = os.path.join(
            cfg.meta_dir, cfg.captions_dir,
            f"{collection}_{cfg.caption_generator}.jsonl")
        ja_em_cache = set()
        if os.path.isfile(caminho_cache):
            with open(caminho_cache, encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()
                    if linha:
                        try:
                            ja_em_cache.add(json.loads(linha)["vid_name"])
                        except (json.JSONDecodeError, KeyError):
                            pass

        # ★ force: このリクエストのシーンだけを削除する。自動では決して行わない。
        apagados = _limpar_caches(cfg, collection, nomes_base) if pedido.force else {}
        if apagados:
            # 削除したシーンは「キャッシュ済み」として数えない
            ja_em_cache -= set(nomes_base)

        caminho_anno = _escrever_annos(cfg, collection, nomes_base)

        log.info("[job %s] %s で build(): %d シーン, collection=%s",
                 job_id[:8], diretorio, len(nomes_base), collection)
        try:
            tree_meta = build(cfg, modelos.como_dict()) or {}
        except Exception as exc:
            # ★ 完全な失敗: 再送出する前に、state "failed" で summary を
            # 記録する。これがないと、build での例外によってリクエスト全体が
            # 履歴から消えてしまう — それこそ、後で最も調査したい
            # ものなのに。
            if program_id and cfg_res_dir:
                try:
                    agora = datetime.now(timezone.utc)
                    persistencia.gravar_summary(cfg_res_dir, program_id, {
                        "state": "failed",
                        "data": persistencia._data_legivel(agora),
                        "timestamp": agora.isoformat(),
                        "total": len(itens), "ok": 0, "errors": len(itens),
                        "seconds": round(time.perf_counter() - t0, 2),
                        "scenes": [i.scene_id for i in itens],
                        "from_cache": 0, "processed": 0,
                        "force": pedido.force,
                        "proposal_generator": pedido.proposal_generator,
                        "mode": mode,
                        "groups": diagnostico_grupos,
                        "error_codes": {ErrorCode.INTERNAL_ERROR: len(itens)},
                        "error": f"{type(exc).__name__}: {exc}",
                        "failed_at": {"directory": diretorio, "collection": collection},
                    })
                except Exception:  # noqa: BLE001
                    log.exception("エラー時の summary の保存に失敗")
            raise

        # ★ マージ — build の直後、ループの中で。
        #
        # construct_name="" では、すべてのグループが同じ exp_dir に書き込む。
        # マージを最後にだけ行うと、グループ 2 がグループ 1 の proposals.json を
        # すでに上書きしており — 次のリクエストですべてが消えてしまう。
        fusao = persistencia.fundir_proposals(
            getattr(cfg, "exp_dir", ""), cfg.proposals_file)

        # --- ステップ 6: 出力を変換する ----------------------------------- #
        exp_dir = getattr(cfg, "exp_dir", None)
        props = {}
        if exp_dir:
            caminho_props = os.path.join(exp_dir, cfg.proposals_file)
            if os.path.isfile(caminho_props):
                with open(caminho_props, encoding="utf-8") as f:
                    props = json.load(f)

        for g in grupo:
            nb, scene_id = g["nome_base"], g["item"].scene_id
            dados = props.get(nb, {})
            proposta = (dados.get("proposals") or [{}])[0]
            legenda = proposta.get("cap")

            if not legenda:
                por_cena[scene_id] = SceneResponse.falha(
                    scene_id, ErrorCode.CAPTION_FAILED,
                    f"パイプラインは '{nb}' のキャプションを生成しなかった。"
                    f"動画がデコードされたか確認してください"
                    f"（長さ < 1s ではフレームが 0 になる）。")
                continue

            por_cena[scene_id] = SceneResponse(
                scene_id=scene_id,
                scene_caption_en=legenda,
                keywords_en=ranquear_keywords(
                    proposta.get("keys", []), legenda, modelos.sentence_transformer),
                status="success",
            )
            # 永続化する履歴のために、proposal が持つすべての情報:
            # 完全なランキング、件数、警告
            diagnostico_por_cena[scene_id] = {
                "vid_name": nb,
                "collection": collection,
                "video_root": diretorio,
                "ranking": proposta.get("ranking"),
                "rank_by": proposta.get("rank_by"),
                "n_raw": proposta.get("n_raw"),
                "n_distinct": proposta.get("n_distinct"),
                "keys_brutas": proposta.get("keys"),
                "warning": proposta.get("warning"),
                "estava_em_cache": nb in ja_em_cache,
            }

        diagnostico_grupos.append({
            "directory": diretorio,
            "collection": collection,
            "scenes": len(nomes_base),
            "from_cache": len([n for n in nomes_base if n in ja_em_cache]),
            "cache_cleared": bool(apagados),
            "annos": caminho_anno,
            "exp_dir": exp_dir,
            "merge": fusao,
        })

    # --- レスポンス ------------------------------------------------------ #
    resultado = [por_cena[i.scene_id] for i in itens if i.scene_id in por_cena]
    resultado += falhas
    ok = sum(1 for r in resultado if r.status == "success")

    # ★ 永続化 — 番組の現在の状態。
    #
    # 粒度: シーン単位ではなくグループ単位。build() は 7 つのステップを終えてから
    # 返るので、レスポンスが得られる最初の時点がここだ。その前にプロセスが
    # 落ちても、高価な処理は失われない — キャプションはすでに meta/ の
    # キャッシュにあり、再処理すれば完了済みのものはすべてスキップされる。
    persistencia_info = {}
    if program_id and cfg_res_dir:
        try:
            persistencia_info = persistencia.gravar_respostas(
                res_dir=cfg_res_dir,
                program_id=program_id,
                respostas=[r.model_dump(exclude_none=True) for r in resultado],
                extras_por_cena=diagnostico_por_cena,
            )
        except Exception as exc:  # noqa: BLE001
            # 永続化の失敗でレスポンスを落としてはならない: クライアントは
            # すでに結果を手にしている。記録して先へ進む。
            log.exception("%s のレスポンスの永続化に失敗", program_id)
            persistencia_info = {"error": f"{type(exc).__name__}: {exc}"}

    envelope = {
        "items": [r.model_dump(exclude_none=True) for r in resultado],
        "summary": {"total": len(itens), "ok": ok, "errors": len(resultado) - ok},
        "groups": diagnostico_grupos,
        "persisted": persistencia_info,
        "seconds": round(time.perf_counter() - t0, 2),
    }

    # ★ SUMMARY — リクエストごとに 1 エントリ、summary/summaries.json に。
    #
    # 意図的に responses.jsonl とは分けている: あちらは番組の現在の状態
    # （シーン）を、こちらは各実行で何が起きたかを保持する。
    # 両者を混ぜると `summary` と `items` の整合が取れなくなる —
    # 10 シーンのファイルに合計 1 件、というように。
    if program_id and cfg_res_dir:
        try:
            erros_por_codigo: dict[str, int] = {}
            for r in resultado:
                if r.status == "error" and r.error_code:
                    erros_por_codigo[r.error_code] = erros_por_codigo.get(r.error_code, 0) + 1

            do_cache = sum(g.get("from_cache", 0) for g in diagnostico_grupos)
            persistencia.gravar_summary(cfg_res_dir, program_id, {
                "state": "concluded",
                "data": persistencia._data_legivel(datetime.now(timezone.utc)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total": len(itens), "ok": ok, "errors": len(resultado) - ok,
                "seconds": envelope["seconds"],
                "scenes": [i.scene_id for i in itens],
                "from_cache": do_cache,
                "processed": max(0, ok - do_cache),
                "force": pedido.force,
                "proposal_generator": pedido.proposal_generator,
                "mode": mode,
                "groups": diagnostico_grupos,
                "error_codes": erros_por_codigo,
                "persisted": persistencia_info,
            })
        except Exception:  # noqa: BLE001 — summary は診断用
            log.exception("%s の summary の保存に失敗", program_id)

    return envelope
