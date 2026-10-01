"""永続化: レスポンスの永続的な履歴と、proposals のマージ。

このモジュールが解決すること
-------------------------
1. 各シーンの結果をディスクに保存する。プロセスより長く残り、後から
   再処理なしで参照できるように。

2. RefCap が `build()` のたびに上書きする `proposals.json` をマージする。

3. 特定のシーンのキャッシュを、他に影響を与えずに削除する（`force`）。

★ マージが必要な理由
    RefCap で確認済み:
        meta/captions/*.jsonl      追記              → 累積 ✓
        meta/framefeatures/*.pt    読む、足す、書く  → 累積 ✓
        meta/scores/*.pt           同上              → 累積 ✓
        results/.../proposals.json save_json で直接  → 上書き ✗
        results/.../tree.json      同上              → 上書き ✗

    `construct_name=""` では、1 つのリクエストのすべてのグループが同じ
    `exp_dir` に書き込む。マージしないと、同じリクエストの中でグループ 2 が
    グループ 1 の proposals を消し — 次のリクエストですべてが消える。

★ レスポンスに 2 つの形式がある理由
    responses.jsonl   追記、累積。書き込みが安く、壊れにくい:
                      1 行が壊れても他の行は無効にならない。
    scenes/{id}.json  シーンごとに 1 ファイル。jsonl を走査せずに直接読め、
                      1 シーンの更新は上書きするだけ。

    jsonl は履歴（すべてのバージョンをタイムスタンプ付きで保持）であり、
    シーンごとのファイルは現在の状態。
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
from datetime import datetime, timezone

log = logging.getLogger(__name__)

#: `res_dir` 内のレスポンス用サブディレクトリ
DIR_RESPONSE = "response"


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# パス
# --------------------------------------------------------------------------- #
def dir_response(res_dir: str, program_id: str) -> pathlib.Path:
    """`{res_dir}/response/{program_id}/`"""
    return pathlib.Path(res_dir) / DIR_RESPONSE / program_id


def caminho_jsonl(res_dir: str, program_id: str) -> pathlib.Path:
    return dir_response(res_dir, program_id) / "responses.jsonl"


def caminho_cena(res_dir: str, program_id: str, scene_id: str) -> pathlib.Path:
    return dir_response(res_dir, program_id) / "scenes" / f"{scene_id}.json"


def caminho_summary(res_dir: str, program_id: str) -> pathlib.Path:
    """アクティブな summaries ファイル。ローテーション済みのものはその隣に置かれる。"""
    return dir_response(res_dir, program_id) / "summary" / "summaries.json"


def caminho_history(res_dir: str, program_id: str) -> pathlib.Path:
    return dir_response(res_dir, program_id) / "history" / "history.jsonl"


#: このサイズを超えると summaries.json はローテーションされる: 日付と時刻を付けて
#: 名前を変え、新しいものを始める。名前に時刻を入れるのは、アクティブな番組は
#: 同じ日に何度も上限を超えうるからだ。
LIMITE_SUMMARY_BYTES = int(os.environ.get("REFCAP_SUMMARY_MAX_BYTES", 5 * 1024 * 1024))


def _data_legivel(dt: datetime) -> str:
    """DD-MM-YYYY HH:MM:SS — 人が読むための形式。

    `timestamp` には ISO 形式も保存する: この形式は辞書順に並ばない
    （'01-12-2026' が '08-09-2026' より前に来てしまう）ので、並べ替えや
    コードでの絞り込みには ISO のフィールドを使う。
    """
    return dt.strftime("%d-%m-%Y %H:%M:%S")


# --------------------------------------------------------------------------- #
# 保存
# --------------------------------------------------------------------------- #
def gravar_respostas(
    res_dir: str,
    program_id: str,
    respostas: list[dict],
    extras_por_cena: dict | None = None,
) -> dict:
    """番組の現在の状態を、3 か所に保存する。

    ★ responses.jsonl の仕組み
        番組全体のエンベロープを持つ 1 行だけ:

            {"program_id": ..., "items": [ ...すべてのシーン... ],
             "updated_at": ...}

        リクエストのたびにファイルを読み、新しいシーンを `scene_id` で
        マージし（新しい方が勝つ）、全体を書き直す。リクエストに含まれない
        シーンはそのまま残る。

    ★ 置き換えられたものは history へ
        マージでシーンが上書きされると、古いバージョンは
        `history/history.jsonl` に記録される — そうしないと失われてしまう。
        `scenes/{id}.json` も上書きされるからだ。

    ⚠️ 並行性: 一度に 1 つのジョブだけが書き込むことを保証するのは `jobs.py` の
    直列化キュー。このモジュールは独自のロックを持たない。
    """
    if not respostas:
        return {"written": 0, "jsonl": None, "scenes_dir": None}

    base = dir_response(res_dir, program_id)
    dir_scenes = base / "scenes"
    dir_scenes.mkdir(parents=True, exist_ok=True)

    extras = extras_por_cena or {}
    agora = datetime.now(timezone.utc)
    momento = agora.isoformat()
    jsonl = caminho_jsonl(res_dir, program_id)

    # --- 1. 以前のエンベロープを読み込む -------------------------------- #
    anteriores: dict[str, dict] = {}
    if jsonl.is_file():
        try:
            with open(jsonl, encoding="utf-8") as f:
                linha = f.readline().strip()
            if linha:
                envelope = json.loads(linha)
                for it in envelope.get("items", []):
                    if it.get("scene_id"):
                        anteriores[it["scene_id"]] = it
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("%s のエンベロープが読み取れない (%s) — 新規に開始する", jsonl, exc)

    # --- 2. マージし、置き換えられるものを保持する ---------------------- #
    substituidas = []
    for r in respostas:
        scene_id = r.get("scene_id")
        if not scene_id:
            continue

        registro = {**r, "timestamp": momento}
        extra = extras.get(scene_id)
        if extra:
            registro["diagnostics"] = extra

        if scene_id in anteriores:
            substituidas.append(anteriores[scene_id])

        anteriores[scene_id] = registro

        # シーンごとのファイル — エンベロープを走査せずに直接アクセスできる
        with open(caminho_cena(res_dir, program_id, scene_id), "w",
                  encoding="utf-8") as fc:
            json.dump({**registro, "program_id": program_id}, fc,
                      ensure_ascii=False, indent=2)

    # --- 3. エンベロープを書き直す -------------------------------------- #
    envelope = {
        "program_id": program_id,
        "items": [anteriores[k] for k in sorted(anteriores)],
        "updated_at": momento,
    }
    with open(jsonl, "w", encoding="utf-8") as f:
        f.write(json.dumps(envelope, ensure_ascii=False) + "\n")

    # --- 4. 置き換えられたものは history へ ------------------------------- #
    if substituidas:
        gravar_history(res_dir, program_id, substituidas, agora,
                       {"written": len(respostas), "jsonl": str(jsonl),
                        "scenes_dir": str(dir_scenes)})

    log.info("[%s] %d シーンを保存; %d 件を置換; 合計 %d 件",
             program_id, len(respostas), len(substituidas), len(anteriores))
    return {
        "written": len(respostas),
        "replaced": len(substituidas),
        "total_in_program": len(anteriores),
        "jsonl": str(jsonl),
        "scenes_dir": str(dir_scenes),
    }


def gravar_history(res_dir: str, program_id: str, substituidas: list[dict],
                   quando: datetime, persisted: dict) -> None:
    """置き換えられたバージョンを記録する — それだけを。

    ★ すべてのシーンのすべてのバージョンを保存すると、このファイルは
    responses.jsonl のコピーになってしまう。ここに残すのは、マージで失われる
    はずのものだけ — それこそ履歴が解決する問題だ。
    """
    caminho = caminho_history(res_dir, program_id)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "a", encoding="utf-8") as f:
        for antiga in substituidas:
            f.write(json.dumps({
                "replaced_at": quando.isoformat(),
                "data": _data_legivel(quando),
                "reason": "overwritten",
                "program_id": program_id,
                "scene": antiga,
                "persisted": persisted,
            }, ensure_ascii=False) + "\n")


def gravar_summary(res_dir: str, program_id: str, entrada: dict) -> dict:
    """summaries.json にエントリを 1 つ追加し、必要ならローテーションする。

    ★ サイズによるローテーション
        LIMITE_SUMMARY_BYTES を超えると、アクティブなファイルは
        `summaries-DD-MM-YYYY_HHMMSS.json` に名前が変わり、新しいものが始まる。
        名前に時刻が入るのは、アクティブな番組は同じ日に何度も上限を超えうるから
        — 日付だけでは衝突する。

        チェックは追加の前に行うので、ファイルはエントリ 1 つ分だけ上限を
        超えることがある。これはローテーションの標準的な挙動であり、
        サイズを測るために 2 回シリアライズせずに済む。
    """
    caminho = caminho_summary(res_dir, program_id)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    rotacionado = None
    if caminho.is_file() and caminho.stat().st_size >= LIMITE_SUMMARY_BYTES:
        agora = datetime.now(timezone.utc)
        destino = caminho.parent / f"summaries-{agora.strftime('%d-%m-%Y_%H%M%S')}.json"
        caminho.rename(destino)
        rotacionado = str(destino)
        log.info("[%s] summaries を %s にローテーションした", program_id, destino.name)

    dados = {"data_summary": []}
    if caminho.is_file():
        try:
            with open(caminho, encoding="utf-8") as f:
                dados = json.load(f)
            dados.setdefault("data_summary", [])
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("summaries が読み取れない (%s) — 新規に開始する", exc)
            dados = {"data_summary": []}

    dados["data_summary"].append(entrada)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    return {"file": str(caminho), "entries": len(dados["data_summary"]),
            "rotated": rotacionado}


# --------------------------------------------------------------------------- #
# 読み込み
# --------------------------------------------------------------------------- #
def ler_respostas(
    res_dir: str,
    program_id: str,
    scene_ids: list[str] | None = None,
) -> list[dict]:
    """各シーンの現在の状態を読む（シーンごとのファイルであり、履歴ではない）。

    `scene_ids` がなければすべてを返す。要求されたシーンが存在しなければ、
    単に省かれる — それをエラーとするかは呼び出し側が決める。
    """
    dir_scenes = dir_response(res_dir, program_id) / "scenes"
    if not dir_scenes.is_dir():
        return []

    if scene_ids:
        arquivos = [dir_scenes / f"{s}.json" for s in scene_ids]
        arquivos = [a for a in arquivos if a.is_file()]
    else:
        arquivos = sorted(dir_scenes.glob("*.json"))

    saida = []
    for a in arquivos:
        try:
            with open(a, encoding="utf-8") as f:
                saida.append(json.load(f))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("%s のレスポンスが読み取れない: %s", a, exc)
    return saida


def historico_da_cena(res_dir: str, program_id: str, scene_id: str) -> list[dict]:
    """あるシーンの、置き換えられたバージョンを時系列順に。

    ★ `responses.jsonl` ではなく `history/history.jsonl` を読む。前者は
    現在の状態だけを保持するようになった。古いバージョンは、マージで
    置き換えられたときに history へ移る。

    現行のバージョンはここにはない — `scenes/{scene_id}.json` にある。
    """
    caminho = caminho_history(res_dir, program_id)
    if not caminho.is_file():
        return []
    versoes = []
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                r = json.loads(linha)
            except json.JSONDecodeError:
                continue
            if r.get("scene", {}).get("scene_id") == scene_id:
                versoes.append(r)
    return versoes


def ler_summaries(res_dir: str, program_id: str, limite: int = 0) -> list[dict]:
    """アクティブな summaries.json のエントリを、新しいものから古いものへ。

    ローテーション済みのファイルは読まない — 手動で参照できるよう、隣に置いてある。
    """
    caminho = caminho_summary(res_dir, program_id)
    if not caminho.is_file():
        return []
    try:
        with open(caminho, encoding="utf-8") as f:
            entradas = json.load(f).get("data_summary", [])
    except (json.JSONDecodeError, OSError):
        return []
    entradas = list(reversed(entradas))
    return entradas[:limite] if limite > 0 else entradas


# --------------------------------------------------------------------------- #
# proposals.json のマージ
# --------------------------------------------------------------------------- #
def fundir_proposals(exp_dir: str, proposals_file: str) -> dict:
    """書き込まれたばかりの `proposals.json` を、番組の累積分とマージする。

    ★ 各 `build()` の直後、グループのループの中で呼ぶこと。

    RefCap がそこに保存するのは現在のグループのシーンだけ。隣に累積ファイル
    （`proposals_acumulado.json`）を保持し、両者を `vid_name` でマージして、
    両方を書き直す — これにより、システムの他の部分が読む `proposals.json` に
    番組全体が入るようになる。

    再処理されたシーンは古いバージョンを上書きする（新しい方が勝つ）。
    """
    if not exp_dir:
        return {"merged": 0, "total": 0}

    atual = pathlib.Path(exp_dir) / proposals_file
    acumulado = pathlib.Path(exp_dir) / "proposals_acumulado.json"

    if not atual.is_file():
        return {"merged": 0, "total": 0}

    with open(atual, encoding="utf-8") as f:
        novas = json.load(f)

    anteriores = {}
    if acumulado.is_file():
        try:
            with open(acumulado, encoding="utf-8") as f:
                anteriores = json.load(f)
        except json.JSONDecodeError:
            log.warning("%s の累積ファイルが読み取れない — 累積を新規に開始する", acumulado)

    # 新しい方が勝つ: `novas` を最後にした dict のアンパック
    fundido = {**anteriores, **novas}

    for destino in (acumulado, atual):
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(fundido, f, ensure_ascii=False, indent=2)

    log.info("proposals をマージした: 新規 %d 件, 合計 %d 件",
             len(novas), len(fundido))
    return {"merged": len(novas), "total": len(fundido)}


# --------------------------------------------------------------------------- #
# キャッシュのピンポイント削除（`force`）
# --------------------------------------------------------------------------- #
def limpar_cache_das_cenas(cfg, collection: str, nomes_base: list[str]) -> dict:
    """3 つのキャッシュから、指定したシーンだけを削除する。

    ⚠️ コスト: キーを 1 つ削除するために、2 つの `.pt` を丸ごとメモリに読み込む。
    数百シーンの番組ではこれが重くなる — ピンポイントの範囲指定の代償だ。
    `force` は手動なので、このコストは明示的に要求したときにしか
    発生しない。

    各アーティファクトから削除したエントリ数を返す。
    """
    if not nomes_base:
        return {}

    alvo = set(nomes_base)
    resultado: dict[str, int] = {}

    # --- 1. キャプション: 対象シーンの行を除いて jsonl を書き直す ------- #
    caminho = os.path.join(
        cfg.meta_dir, cfg.captions_dir,
        f"{collection}_{cfg.caption_generator}.jsonl")
    if os.path.isfile(caminho):
        mantidas, removidas = [], 0
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                linha_limpa = linha.strip()
                if not linha_limpa:
                    continue
                try:
                    if json.loads(linha_limpa).get("vid_name") in alvo:
                        removidas += 1
                        continue
                except json.JSONDecodeError:
                    pass          # 読み取れない行: 残す。扱うのは我々の役目ではない
                mantidas.append(linha_limpa)
        if removidas:
            with open(caminho, "w", encoding="utf-8") as f:
                for linha in mantidas:
                    f.write(linha + "\n")
        resultado["captions"] = removidas

    # --- 2 と 3. 2 つの .pt: 読み込み、キーを削除し、書き直す ----------- #
    #
    # import は遅延かつ寛容: キャプションのキャッシュの削除（上）は torch に
    # 依存せず、BLIP を再実行するかを決めるのはそれだ。torch がなければ、
    # リクエスト全体を落とす代わりに、警告して部分的な削除のまま
    # 先へ進む。
    try:
        import torch  # noqa: PLC0415
    except ImportError:
        log.warning(
            "torch が利用できない: force はキャプションを削除したが、"
            "features/scores の .pt キャッシュは削除していない。これらが再計算されるのは"
            "動画のサイズが変わった場合だけ。"
        )
        resultado["framefeatures"] = "torch なし"
        resultado["scores"] = "torch なし"
        return resultado

    for rotulo, caminho_pt in (
        ("framefeatures",
         os.path.join(cfg.meta_dir, cfg.framefeatures_dir, f"{collection}.pt")),
        ("scores",
         os.path.join(cfg.meta_dir, cfg.raw_capframe_scores_dir,
                      f"{collection}_{cfg.caption_generator}.pt")),
    ):
        if not os.path.isfile(caminho_pt):
            continue
        try:
            dados = torch.load(caminho_pt)
        except Exception as exc:  # noqa: BLE001 — 読み取れないキャッシュで落とさない
            log.warning("キャッシュ %s が読み取れない (%s) — スキップ", caminho_pt, exc)
            continue
        if not isinstance(dados, dict):
            log.warning("キャッシュ %s は dict ではない — スキップ", caminho_pt)
            continue
        removidas = 0
        for nb in list(dados.keys()):
            if nb in alvo:
                del dados[nb]
                removidas += 1
        if removidas:
            torch.save(dados, caminho_pt)
        resultado[rotulo] = removidas

    log.info("[%s] force: 削除件数 %s", collection, resultado)
    return resultado
