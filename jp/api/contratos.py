"""API の契約: Pydantic モデルとエラーコード。

意図的にパイプラインから分離している: API の利用者が理解すべきなのはこの
ファイルだけ。2 つのリクエスト形式（単一シーンとバッチ）は `como_itens()` によって
1 つのリストに正規化されるので、処理側で同期を保つべき経路が 2 つになることは
ない。
"""
from __future__ import annotations

import os

from pydantic import BaseModel, Field

MODEL_NAME_PADRAO = os.environ.get("REFCAP_MODEL_NAME", "refcap")
MODEL_VERSION_PADRAO = os.environ.get("REFCAP_MODEL_VERSION", "v1")


class ErrorCode:
    """契約のエラーコード（シーンごと）。

    それぞれが異なる原因に対応する — 利用者が自由記述のメッセージを読まずに
    どう対処するかを決められるようにするのが狙い。
    """

    #: 不正なペイロード、必須フィールドの欠落、空のリクエスト
    INVALID_REQUEST = "INVALID_REQUEST"
    #: `scene_video_path` がディスク上に存在しない
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    #: パスは存在するが、その `scene_id` の動画がない
    SCENE_NOT_FOUND = "SCENE_NOT_FOUND"
    #: パイプラインは実行されたがキャプションが生成されなかった（動画 < 1s、デコード失敗）
    CAPTION_FAILED = "CAPTION_FAILED"
    #: 任意の箇所での予期しない例外
    INTERNAL_ERROR = "INTERNAL_ERROR"




# --------------------------------------------------------------------------- #
# 契約
# --------------------------------------------------------------------------- #
class SceneItem(BaseModel):
    """キャプションを付けるシーン 1 つ。"""
    scene_id: str
    video_id: str | None = None
    program_id: str | None = None
    scene_video_path: str = Field(
        ...,
        description="シーンのパス。動画ファイル、またはそれを含むディレクトリを受け付ける"
                    "（後者の場合、ファイルはその中で探される）。",
    )


class CaptionRequest(BaseModel):
    """合意した 2 つの形式を、別々のエンドポイントなしで受け付ける。

    単一シーン:
        {"scene_id": "...", "video_id": "...", "program_id": "...",
         "scene_video_path": "/caminho/..."}

    バッチ:
        {"items": [ {...}, {...} ]}
    """
    # --- 「単一シーン」形式（最上位のフィールド） ---
    scene_id: str | None = None
    video_id: str | None = None
    program_id: str | None = None
    scene_video_path: str | None = None

    # --- 「バッチ」形式 ---
    items: list[SceneItem] | None = None

    # --- 任意の制御 ---
    callback_url: str | None = None
    assincrono: bool = Field(
        default=False,
        description="モードの手動上書き。アイテム数がしきい値を超えると API は自動で"
                    "非同期に切り替わる。このフィールドはどちらかを強制する。",
    )
    proposal_generator: str = "whole"
    force: bool = Field(
        default=False,
        description="このリクエストのシーンを、そのキャッシュ（キャプション、特徴量、"
                    "スコア）を消して再処理する。自動では決して行われない — "
                    "明示的に要求された場合のみ。",
    )

    # ⚠️ `collection` は意図的に契約から削除された。
    #
    # 現在は `program_id` から導出される: 1 つの識別子が RefCap の 5 つの
    # パス（annos、meta/ の 3 つのキャッシュ、results/）を決める。
    # ここで上書きを受け付けると番組間の分離が壊れる — 同じ `collection` を
    # 持つ 2 つの番組がキャッシュを共有し、2 つ目は 1 つ目のキャプションを
    # 黙って受け取ることになる。
    #
    # 唯一の例外は診断ルート: 実データを汚さないよう、専用の `collection`
    # ("diagnostics") を使う。

    def como_itens(self) -> list[SceneItem]:
        """2 つの形式を 1 つのリストに正規化する。

        単一シーンは 1 件のバッチになる。以降のコードはすべてリストだけを扱う —
        保守すべき実行経路が 2 つになることはない。
        """
        if self.items:
            return list(self.items)
        if self.scene_id and self.scene_video_path:
            return [SceneItem(
                scene_id=self.scene_id,
                video_id=self.video_id,
                program_id=self.program_id,
                scene_video_path=self.scene_video_path,
            )]
        return []


class Keyword(BaseModel):
    token: str
    weight: float


class SceneResponse(BaseModel):
    """出力の契約（シーンごと）。3 つのルートで同一。"""

    scene_id: str
    scene_caption_en: str | None = None
    keywords_en: list[Keyword] = Field(default_factory=list)
    model_name: str = MODEL_NAME_PADRAO
    model_version: str = MODEL_VERSION_PADRAO
    status: str = "success"

    # `status == "error"` の場合にのみ設定される。
    error_code: str | None = None
    message: str | None = None

    @classmethod
    def falha(cls, scene_id: str, error_code: str, message: str) -> "SceneResponse":
        """フィールドを繰り返さずにエラーレスポンスを組み立てるショートカット。"""
        return cls(scene_id=scene_id, status="error",
                   error_code=error_code, message=message)
