import json
from pathlib import Path
from collections import defaultdict

# ベースディレクトリ設定
BASE_DIR = Path(__file__).parent
USERS_DIR = BASE_DIR / "usuarios"  # 各ユーザーのフォルダ
SAIDA_GERAL = BASE_DIR / "medias_gerais.json"  # 出力ファイル


def calcular_media_usuario(orig_path: Path) -> dict:
    """1人のユーザーに対して、スコアの平均値を計算する。"""
    if not orig_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {orig_path}")

    dados = json.loads(orig_path.read_text(encoding="utf-8"))
    soma = defaultdict(float)
    cont = defaultdict(int)
    total_por_coluna = defaultdict(int)

    # 各列（p1, p2, p3）を走査
    for item in dados:
        for key in ["p1", "p2", "p3"]:
            par = item.get(key, {})
            col = par.get("c")
            if not col:
                continue
            total_por_coluna[col] += 1
            if "s" in par:
                soma[col] += par["s"]
                cont[col] += 1

    medias = {}
    total_scores = 0
    total_titulos = len(dados) * 3  # 各行に3つのタイトルがある

    # 各列の詳細データを作成
    for col in total_por_coluna.keys():
        media = round(soma[col] / cont[col], 2) if cont[col] > 0 else None
        total_scores += cont[col]
        medias[col] = {
            "平均値": media,
            "スコア付きタイトル数": cont[col],
            f"列_{col}_タイトル総数": total_por_coluna[col],
        }

    return {
        "列ごとの平均": medias,
        "スコア付き合計": total_scores,
        "タイトル総数": total_titulos,
    }


def gerar_medias_gerais():
    """全ユーザーの平均を計算し、JSONファイルとして出力する。"""
    if not USERS_DIR.exists():
        raise FileNotFoundError(f"ユーザーフォルダが見つかりません: {USERS_DIR}")

    resultado = []
    soma_global = defaultdict(float)
    cont_global = defaultdict(int)
    total_titulos_global = 0
    total_scores_global = 0

    # 各ユーザーの orig.json を処理
    for user_dir in USERS_DIR.iterdir():
        if not user_dir.is_dir():
            continue

        orig_path = user_dir / "orig.json"
        if not orig_path.exists():
            print(
                f"⚠️ ユーザー {user_dir.name} は orig.json が存在しません — スキップします。"
            )
            continue

        try:
            medias = calcular_media_usuario(orig_path)
            resultado.append({"ユーザー": user_dir.name, **medias})
            print(f"✅ {user_dir.name} の平均を計算しました。")

            # グローバル集計用
            for col, info in medias["列ごとの平均"].items():
                if info["平均値"] is not None:
                    soma_global[col] += info["平均値"]
                    cont_global[col] += 1
            total_titulos_global += medias["タイトル総数"]
            total_scores_global += medias["スコア付き合計"]

        except Exception as e:
            print(f"❌ {user_dir.name} の処理中にエラーが発生しました: {e}")

    # 全ユーザーの列ごとの平均を算出
    medias_globais = {
        col: round(soma_global[col] / cont_global[col], 2)
        for col in soma_global
        if cont_global[col] > 0
    }

    # 全体サマリーを作成（全体平均値は削除）
    resumo_global = {
        "ユーザー": "🌏 全体統計（全ユーザー）",
        "列ごとの平均": {
            col: {
                "全体列平均": media,
                "スコア付きユーザー数": cont_global[col],
            }
            for col, media in medias_globais.items()
        },
        "全スコア件数": total_scores_global,
        "全タイトル件数": total_titulos_global,
    }

    resultado.append(resumo_global)

    # JSON出力
    SAIDA_GERAL.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n💾 結果を保存しました: {SAIDA_GERAL.resolve()}")

    return resultado


if __name__ == "__main__":
    print("📊 全ユーザーのスコア平均を計算しています...\n")
    dados = gerar_medias_gerais()

    print("\n📈 各ユーザーの詳細結果:")
    for d in dados:
        print("\n" + "=" * 60)
        print(f"👤 ユーザー: {d['ユーザー']}")
        if d["ユーザー"].startswith("🌏"):
            # 全体統計
            print("\n🌍 全体の列別平均:")
            for col, info in d["列ごとの平均"].items():
                print(
                    f"  - 列 {col}: 平均 {info['全体列平均']}（スコア付きユーザー数 {info['スコア付きユーザー数']}）"
                )
            print(f"\n🧮 全スコア件数: {d['全スコア件数']}")
            print(f"📊 全タイトル件数: {d['全タイトル件数']}")
        else:
            print("\n📋 列ごとの詳細:")
            for col, info in d["列ごとの平均"].items():
                avg = info["平均値"] if info["平均値"] is not None else "―"
                print(
                    f"  - 列 {col}: 平均 {avg}｜スコア付き {info['スコア付きタイトル数']} / 総数 {info[f'列_{col}_タイトル総数']}"
                )
            print(f"\n🧮 スコア付き合計: {d['スコア付き合計']}")
            print(f"📊 タイトル総数: {d['タイトル総数']}")
