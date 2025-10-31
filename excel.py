# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any, Union
import pandas as pd
import json
import random
from pathlib import Path

app = FastAPI(title="Excel Processor API")

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # URLs do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caminhos
FRONTEND_PUBLIC_PATH = Path(__file__).parent.parent / "frontend" / "public"
EXCEL_PATH = FRONTEND_PUBLIC_PATH / "dados.xlsx"
JSON_ORIGINAL_PATH = FRONTEND_PUBLIC_PATH / "dados-original.json"
JSON_PARES_PATH = FRONTEND_PUBLIC_PATH / "pares-embaralhados.json"

# Servir arquivos estáticos da pasta public do frontend
app.mount("/static", StaticFiles(directory=str(FRONTEND_PUBLIC_PATH)), name="static")


# Tipos
LinhaExcel = Dict[str, Union[str, int, float]]

class Par:
    def __init__(self, base: Union[str, int, float], combinado: Union[str, int, float]):
        self.base = base
        self.combinado = combinado
    
    def to_dict(self):
        return {"base": self.base, "combinado": self.combinado}


class DadosProcessados:
    def __init__(self, original: List[LinhaExcel], pares: List[Par]):
        self.original = original
        self.pares = pares
    
    def to_dict(self):
        return {
            "original": self.original,
            "pares": [p.to_dict() for p in self.pares]
        }


def embaralhar(array: List[Any]) -> List[Any]:
    """Embaralha um array (Fisher-Yates)"""
    arr = array.copy()
    for i in range(len(arr) - 1, 0, -1):
        j = random.randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def ler_excel(caminho_arquivo: Path) -> List[LinhaExcel]:
    """Lê o arquivo Excel e retorna como lista de dicionários"""
    try:
        print(f"📂 Lendo arquivo Excel: {caminho_arquivo}")
        
        if not caminho_arquivo.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
        # Lê o Excel (primeira aba)
        df = pd.read_excel(caminho_arquivo, sheet_name="Sheet1")
        
        # Converte para lista de dicionários
        dados = df.to_dict(orient="records")
        
        print(f"✅ {len(dados)} linhas lidas do Excel")
        return dados
        
    except Exception as erro:
        print(f"❌ Erro ao ler Excel: {erro}")
        raise


def gerar_pares(dados: List[LinhaExcel]) -> List[Par]:
    """Gera pares embaralhados a partir das linhas do Excel"""
    todos_pares = []
    
    # Pula a primeira linha (cabeçalho já foi processado pelo pandas)
    for linha in dados:
        valores = list(linha.values())
        base = valores[0]
        outros = valores[1:]
        
        # Cria pares
        pares = [Par(base, v) for v in outros if pd.notna(v)]  # Ignora valores NaN
        todos_pares.extend(embaralhar(pares))
    
    print(f"✅ {len(todos_pares)} pares gerados")
    return embaralhar(todos_pares)


def salvar_json(dados: Any, caminho: Path) -> None:
    """Salva dados em arquivo JSON"""
    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print(f"💾 Salvo: {caminho}")
    except Exception as erro:
        print(f"❌ Erro ao salvar JSON: {erro}")
        raise


def processar_excel_e_salvar() -> DadosProcessados:
    """Processa o Excel e salva os JSONs na pasta public"""
    try:
        print("🚀 Iniciando processamento do Excel...")
        
        # Lê o Excel
        dados = ler_excel(EXCEL_PATH)
        
        # Gera pares embaralhados
        print("🔀 Gerando pares embaralhados...")
        pares = gerar_pares(dados)
        
        # Salva JSON original
        salvar_json(dados, JSON_ORIGINAL_PATH)
        
        # Salva pares embaralhados
        pares_dict = [p.to_dict() for p in pares]
        salvar_json(pares_dict, JSON_PARES_PATH)
        
        print("✅ Processamento concluído!")
        
        return DadosProcessados(dados, pares)
        
    except Exception as erro:
        print(f"❌ Erro no processamento: {erro}")
        raise


# Variável global para armazenar dados processados
dados_processados: DadosProcessados | None = None
erro_processamento: str | None = None


# Processa automaticamente quando o servidor inicia
@app.on_event("startup")
async def startup_event():
    """Processa o Excel quando o servidor inicia"""
    global dados_processados, erro_processamento
    try:
        print("🚀 Servidor iniciando - processando Excel automaticamente...")
        dados_processados = processar_excel_e_salvar()
        print("✅ Processamento inicial concluído!")
    except Exception as erro:
        erro_processamento = str(erro)
        print(f"❌ Falha no processamento inicial: {erro_processamento}")


# ENDPOINTS

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "mensagem": "API Excel Processor",
        "status": "online",
        "endpoints": {
            "status": "/api/status",
            "dados": "/api/dados",
            "reprocessar": "/api/reprocessar"
        }
    }


@app.get("/api/status")
async def verificar_status():
    """Verifica o status do processamento"""
    if erro_processamento:
        raise HTTPException(status_code=500, detail={
            "sucesso": False,
            "erro": erro_processamento
        })
    
    if not dados_processados:
        raise HTTPException(status_code=500, detail={
            "sucesso": False,
            "erro": "Dados não foram processados"
        })
    
    return {
        "sucesso": True,
        "totalLinhas": len(dados_processados.original),
        "totalPares": len(dados_processados.pares),
        "arquivosGerados": [
            "/static/dados-original.json",
            "/static/pares-embaralhados.json"
        ]
    }


@app.get("/api/dados")
async def obter_dados():
    """Retorna os dados processados"""
    if not dados_processados:
        raise HTTPException(status_code=500, detail={
            "erro": "Dados não foram processados"
        })
    
    return dados_processados.to_dict()


@app.post("/api/reprocessar")
async def reprocessar():
    """Reprocessa o Excel e gera novos JSONs"""
    global dados_processados, erro_processamento
    
    try:
        print("🔄 Reprocessando...")
        dados_processados = processar_excel_e_salvar()
        erro_processamento = None
        
        return {
            "sucesso": True,
            "mensagem": "Reprocessado com sucesso",
            "totalLinhas": len(dados_processados.original),
            "totalPares": len(dados_processados.pares)
        }
    except Exception as erro:
        erro_processamento = str(erro)
        raise HTTPException(status_code=500, detail={
            "sucesso": False,
            "erro": erro_processamento
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)