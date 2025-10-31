from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
from pathlib import Path
import pandas as pd
import json
import random

app = FastAPI(title="Excel Processor API", version="2.0")

# ========================================
# 🔧 Configurações gerais
# ========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_PATH = Path(__file__).parent
EXCEL_PATH = BASE_PATH / "dados.xlsx"
JSON_ORIGINAL_PATH = BASE_PATH / "dados-original.json"
JSON_PARES_PATH = BASE_PATH / "pares-embaralhados.json"

# ========================================
# ⚙️ Funções auxiliares
# ========================================

def embaralhar(lista: list) -> list:
    arr = lista[:]
    random.shuffle(arr)
    return arr


def ler_excel_em_estrutura() -> list[dict]:
    """Lê o Excel e gera a estrutura do dados-original.json"""
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Arquivo Excel não encontrado em: {EXCEL_PATH}")

    df = pd.read_excel(EXCEL_PATH, sheet_name="Sheet1")
    colunas = df.columns.tolist()
    registros = []

    for idx, row in df.iloc[1:].iterrows():  # pula a primeira linha
        texto = row[colunas[0]]
        titulo1, titulo2, titulo3 = row[colunas[1]], row[colunas[2]], row[colunas[3]]

        registro = {
            "texto": texto,
            "par1": {
                "titulo1": titulo1,
                "linha_em_que_titulo1_se_encontra": int(idx + 2),
                "coluna_em_que_esse_titulo1_se_encontra": colunas[1],
            },
            "par2": {
                "titulo2": titulo2,
                "linha_em_que_titulo2_se_encontra": int(idx + 2),
                "coluna_em_que_esse_titulo2_se_encontra": colunas[2],
            },
            "par3": {
                "titulo3": titulo3,
                "linha_em_que_titulo3_se_encontra": int(idx + 2),
                "coluna_em_que_esse_titulo3_se_encontra": colunas[3],
            },
            "posicao_atual_index": len(registros),
        }

        registros.append(registro)

    return registros


def gerar_pares_estrutura(dados_original: list[dict]) -> list[dict]:
    """Gera a estrutura embaralhada para pares-embaralhados.json"""
    pares_total = []

    for linha in dados_original:
        texto = linha["texto"]
        pares = [
            {"texto": texto, "par": linha["par1"], "posicao_atual_index": linha["posicao_atual_index"]},
            {"texto": texto, "par": linha["par2"], "posicao_atual_index": linha["posicao_atual_index"]},
            {"texto": texto, "par": linha["par3"], "posicao_atual_index": linha["posicao_atual_index"]},
        ]
        pares_total.extend(embaralhar(pares))  # embaralha pares dessa linha

    return embaralhar(pares_total)  # embaralhamento global final


def salvar_json(dados: Any, caminho: Path):
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


# ========================================
# 🧠 Processamento automático ao iniciar
# ========================================

@app.on_event("startup")
def inicializar_processamento():
    """
    Executado automaticamente no momento em que o FastAPI é iniciado.
    Cria os arquivos dados-original.json e pares-embaralhados.json
    apenas se eles ainda não existirem.
    """
    try:
        if JSON_ORIGINAL_PATH.exists() and JSON_PARES_PATH.exists():
            print("✅ Arquivos JSON já existentes — pulando processamento inicial.")
            return

        print("🔄 Iniciando processamento automático de dados.xlsx...")

        dados_original = ler_excel_em_estrutura()
        salvar_json(dados_original, JSON_ORIGINAL_PATH)
        print(f"📄 Gerado: {JSON_ORIGINAL_PATH.name} ({len(dados_original)} linhas)")

        pares = gerar_pares_estrutura(dados_original)
        salvar_json(pares, JSON_PARES_PATH)
        print(f"📄 Gerado: {JSON_PARES_PATH.name} ({len(pares)} pares)")

        print("✅ Processamento inicial concluído com sucesso.")

    except Exception as e:
        print(f"❌ Erro ao processar dados.xlsx: {e}")


# ========================================
# 🚀 ENDPOINTS
# ========================================

@app.post("/api/pares")
def obter_pares():
    """Retorna o conteúdo atual de pares-embaralhados.json"""
    try:
        if not JSON_PARES_PATH.exists():
            raise FileNotFoundError("O arquivo pares-embaralhados.json ainda não existe.")
        pares = json.loads(JSON_PARES_PATH.read_text(encoding="utf-8"))
        return {"sucesso": True, "pares": pares}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/score")
def atualizar_score(item: dict):
    """
    Recebe:
    {
      "texto": "...",
      "par": {...},
      "score": 1-4,
      "posicao_atual_index": int
    }
    Atualiza o dados-original.json na posição correspondente.
    """
    try:
        if not JSON_ORIGINAL_PATH.exists():
            raise FileNotFoundError("O arquivo dados-original.json não foi encontrado.")

        dados = json.loads(JSON_ORIGINAL_PATH.read_text(encoding="utf-8"))

        index = item.get("posicao_atual_index")
        if index is None or not (0 <= index < len(dados)):
            raise ValueError("Índice inválido ou fora do intervalo.")

        score = item.get("score")
        if not isinstance(score, (int, float)) or not (1 <= score <= 4):
            raise ValueError("O score deve ser um número entre 1 e 4.")

        # Atualiza o score
        dados[index]["score"] = score
        salvar_json(dados, JSON_ORIGINAL_PATH)

        return {
            "sucesso": True,
            "mensagem": f"Score atualizado na posição {index}",
            "atualizado": dados[index],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
def status():
    """Verifica se os arquivos estão prontos e quantas linhas têm."""
    status = {
        "xlsx_existe": EXCEL_PATH.exists(),
        "original_existe": JSON_ORIGINAL_PATH.exists(),
        "pares_existe": JSON_PARES_PATH.exists(),
    }

    if JSON_ORIGINAL_PATH.exists():
        dados = json.loads(JSON_ORIGINAL_PATH.read_text(encoding="utf-8"))
        status["linhas_original"] = len(dados)

    if JSON_PARES_PATH.exists():
        pares = json.loads(JSON_PARES_PATH.read_text(encoding="utf-8"))
        status["total_pares"] = len(pares)

    return status
