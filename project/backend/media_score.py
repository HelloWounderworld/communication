import json
from pathlib import Path
from collections import defaultdict

# Caminho do arquivo JSON de entrada
ARQUIVO = Path("orig.json")

# Caminho de saída
SAIDA = Path("media_por_coluna.json")


def calcular_medias_por_coluna(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    # Lê o JSON
    dados = json.loads(path.read_text(encoding="utf-8"))

    # Estruturas dinâmicas para soma e contagem por coluna (ex: "B", "C", "D")
    soma = defaultdict(float)
    cont = defaultdict(int)

    # Percorre cada linha e cada par p1, p2, p3
    for item in dados:
        for key in ["p1", "p2", "p3"]:
            par = item.get(key, {})
            col = par.get("c")  # nome da coluna
            if col and "s" in par:
                soma[col] += par["s"]
                cont[col] += 1

    # Calcula média de cada coluna
    medias = {}
    for col in soma:
        medias[col] = round(soma[col] / cont[col], 2) if cont[col] > 0 else None

    # Calcula média geral das colunas com valores válidos
    if medias:
        valores = [v for v in medias.values() if v is not None]
        media_geral = round(sum(valores) / len(valores), 2) if valores else None
    else:
        media_geral = None

    # Resultado completo
    resultado = {
        "medias_por_coluna": medias,
        "media_geral": media_geral,
        "total_colunas_com_score": len(medias),
    }

    # Salva o resultado no arquivo JSON
    SAIDA.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"💾 Resultado salvo em: {SAIDA.resolve()}")

    return resultado


if __name__ == "__main__":
    print("📊 Calculando médias dos scores...")
    resultado = calcular_medias_por_coluna(ARQUIVO)

    print("\n📈 Médias por coluna:")
    for col, media in resultado["medias_por_coluna"].items():
        print(f"  Coluna {col}: {media}")

    print(f"\n📏 Média geral: {resultado['media_geral']}")
    print(f"🧮 Colunas com score: {resultado['total_colunas_com_score']}")
