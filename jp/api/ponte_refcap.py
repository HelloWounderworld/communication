"""API と RefCap の橋渡し: sys.path と絶対パス。

このモジュールが解決する 2 つの落とし穴
---------------------------------------

0) このディレクトリを置ける場所
   次の 2 つの配置はどちらも、コードを変えずに動く:

       (A) RefCap の隣                (B) RefCap の中
           projeto/                       projeto/
           |- src/   <- RefCap            `- src/   <- RefCap
           `- api/                           `- api/

   ルートは固定パスではなくマーカー（pipeline/propgenerator/base.py）で特定する。
   REFCAP_ROOT が定義されていれば、探索より優先される。

1) RefCap の import 方法
   RefCap はトップレベルの絶対 import を使う（`from pipeline.denoiser import *`、
   `import utils.basic_utils`）。したがって `sys.path` に入れるべきは RefCap の
   ルートであり — その親ディレクトリではない。

   ✓ 動く     : sys.path += [".../src"]  ->  from pipeline... import
   ✗ 壊れる   : sys.path += ["..."]      ->  from src.pipeline... import
                (確認済み: ModuleNotFoundError: No module named 'utils')

2) cfg のパスは相対パス
   `config/cfg.py` には `meta_dir="meta"`、`res_dir="results"`、
   `anno_dir="annos"` といったデフォルトがある。サービスを CWD=api/ で実行すると、
   これらのパスは RefCap の中ではなく `api/meta`、`api/results` に解決されてしまう。

   ここで採用した解決策は、os.chdir() を行う代わりに、cfg を絶対パスで
   埋めること。こうすればプロセスの CWD は、ログ、一時アップロード、
   自前のコードのあらゆるパスのために自由に使える。
"""
from __future__ import annotations

import os
import pathlib
import sys

# --------------------------------------------------------------------------- #
# RefCap の所在特定 — 考えられる 2 つの配置のどちらでも動く
# --------------------------------------------------------------------------- #
# ルートは固定パスではなく、マーカー（`pipeline/propgenerator/base.py`）で
# 特定する。これによりサービスはレイアウトに依存しない:
#
#   (A) api/ が RefCap の隣             (B) api/ が RefCap の中
#       projeto/                            projeto/
#       ├── src/    <- RefCap               └── src/    <- RefCap
#       └── api/                                └── api/
#
# 環境変数 REFCAP_ROOT が定義されていれば、それがすべてに優先する。
_AQUI = pathlib.Path(__file__).resolve().parent

_MARCADOR = pathlib.Path("pipeline") / "propgenerator" / "base.py"

# RefCap のフォルダが api/ の兄弟である場合の、よくある名前。
_NOMES_IRMAOS = ("src", "RefCap", "refcap")


def _e_raiz(caminho: pathlib.Path) -> bool:
    return (caminho / _MARCADOR).is_file()


def _descobrir_raiz() -> pathlib.Path:
    """2 つの配置をカバーして、RefCap のルートを探し出す。

    試行の順番:
      1. REFCAP_ROOT（定義されていれば） — 絶対的に優先
      2. ここから上へたどる          — 配置 (B)、api/ が中にある場合
      3. よくある名前の兄弟          — 配置 (A)、api/ が隣にある場合
    """
    definida = os.environ.get("REFCAP_ROOT")
    if definida:
        raiz = pathlib.Path(definida).resolve()
        if not _e_raiz(raiz):
            raise RuntimeError(
                f"REFCAP_ROOT は {raiz} を指しているが、そこに '{_MARCADOR}' が存在しない。"
            )
        return raiz

    # (B) api/ が RefCap の中: 上へたどればルートが見つかる
    for candidato in [_AQUI, *_AQUI.parents]:
        if _e_raiz(candidato):
            return candidato

    # (A) api/ が RefCap の隣: 兄弟の中から探す
    for nome in _NOMES_IRMAOS:
        candidato = (_AQUI.parent / nome).resolve()
        if _e_raiz(candidato):
            return candidato

    raise RuntimeError(
        f"{_AQUI} から RefCap が見つからない。\n"
        f"'{_MARCADOR}' を次の場所で探した:\n"
        f"  - ディレクトリツリーを上へ（api/ が RefCap の中にある場合）\n"
        f"  - 兄弟ディレクトリ {_NOMES_IRMAOS}（api/ が RefCap の隣にある場合）\n"
        f"RefCap のルートを指す REFCAP_ROOT を定義してください。"
    )


RAIZ_REFCAP = _descobrir_raiz()


def nomes_de_topo_do_refcap() -> set[str]:
    """RefCap がトップレベルで使っている名前 — パッケージとモジュール。"""
    nomes = set()
    for p in RAIZ_REFCAP.iterdir():
        if p.name.startswith((".", "__")):
            continue
        if p.is_dir():
            nomes.add(p.name)
        elif p.suffix == ".py":
            nomes.add(p.stem)
    return nomes


def checar_colisoes(dir_api: pathlib.Path | None = None) -> list[str]:
    """RefCap のトップレベルの名前を覆い隠す API のモジュールを検出する。

    ★ これが存在する理由
        `api/` は RefCap のルートの中にあり、アプリのディレクトリはルートより先に
        `sys.path` に入る。そのため `api/pipeline.py` があると `sys.modules` の
        `pipeline` という名前を占有し、construct.py の
        `from pipeline.denoiser import *` が、原因を示さないメッセージで失敗する:

            ModuleNotFoundError: No module named 'pipeline.denoiser';
                                 'pipeline' is not a package

        実際に起きたことだ。このチェックは、最初のリクエストでのわかりにくいエラーの
        代わりに、それを起動時の明確な警告に変える。
    """
    dir_api = dir_api or _AQUI
    do_refcap = nomes_de_topo_do_refcap()
    colisoes = []
    for p in dir_api.iterdir():
        if p.name.startswith((".", "__")):
            continue
        nome = p.stem if p.suffix == ".py" else (p.name if p.is_dir() else None)
        if nome and nome in do_refcap:
            colisoes.append(nome)
    return sorted(colisoes)


def preparar_sys_path(avisar_colisoes: bool = True) -> None:
    """RefCap のルートを sys.path に入れる。冪等。"""
    caminho = str(RAIZ_REFCAP)
    if caminho not in sys.path:
        sys.path.insert(0, caminho)

    if avisar_colisoes:
        colisoes = checar_colisoes()
        if colisoes:
            raise RuntimeError(
                f"API と RefCap の間で名前が衝突している: {colisoes}\n"
                f"\n"
                f"上記のモジュールは両方に存在し、api/ のものが優先される — その結果\n"
                f"RefCap 内部の import が、次のようなメッセージで壊れる\n"
                f"  \"No module named 'X.y'; 'X' is not a package\"。\n"
                f"\n"
                f"{dir(_AQUI) and _AQUI} にあるファイルの名前を変更してください。\n"
                f"RefCap が使用している名前: {sorted(nomes_de_topo_do_refcap())}"
            )


# --------------------------------------------------------------------------- #
# 絶対パスによる cfg の構築
# --------------------------------------------------------------------------- #
# `config/cfg.py` のフィールドのうち、デフォルトが相対パスで、どの CWD からでも
# サービスが動くよう絶対パスにする必要があるもの。
_CAMPOS_DE_CAMINHO = (
    "anno_dir",      # cfg.py:5   -> "annos"
    "meta_dir",      # cfg.py:9   -> "meta"
    "res_dir",       # cfg.py:14  -> "results"
    "video_root",    # cfg.py:35
)
# 注: captions_dir、framefeatures_dir、raw_capframe_scores_dir、construct_dir も
# 相対パスだが、RefCap は常に os.path.join(meta_dir, X) または
# os.path.join(res_dir, X) で使う。基点が絶対パスになるので、これらも追従する。


def montar_cfg(**sobrescritas):
    """コマンドラインを経由せずに `BuildArguments` を組み立てる。

    オリジナルの `construct.py` は `HfArgumentParser(...).parse_args_into_dataclasses()` を行い、
    これは `sys.argv` を読む — サービスでは使えない。ここでは直接インスタンス化する。

    パスのフィールドはすべて、RAIZ_REFCAP を基点とした絶対パスになる。

    ⚠️ `cfg.exp_dir` はここでは設定しない: RefCap の `build()`（construct.py）が
    res_dir/construct_dir/collection/construct_name から注入する。
    事前に設定しようとしないこと — 上書きされる。
    """
    preparar_sys_path()
    from config import BuildArguments  # noqa: PLC0415 — sys.path の設定後にのみ

    cfg = BuildArguments()

    # 1) パスを絶対パスにする
    for campo in _CAMPOS_DE_CAMINHO:
        valor = getattr(cfg, campo, None)
        if isinstance(valor, str) and valor and not os.path.isabs(valor):
            setattr(cfg, campo, str(RAIZ_REFCAP / valor))

    # 2) 呼び出し側の指定を適用する（パスであれば、すでに絶対パス）
    for chave, valor in sobrescritas.items():
        if not hasattr(cfg, chave):
            raise AttributeError(
                f"BuildArguments にはフィールド {chave!r} がない。"
                f"新しいフィールドなら、config/cfg.py で宣言してください。"
            )
        setattr(cfg, chave, valor)

    return cfg


def caminho_no_refcap(*partes) -> str:
    """RefCap 内の絶対パスを組み立てる。例: caminho_no_refcap('meta')。"""
    return str(RAIZ_REFCAP.joinpath(*partes))
