from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

class ElasticSimpleQuery:
    def __init__(self):
        self.es = Elasticsearch(["http://localhost:9200"])
        self.indice = "meu_indice"
        self.campo_data = "data"
        self.campo_genero = "genero"

    def buscar(self, inicio_str: str, fim_str: str, genero: str) -> list:
        """Busca por datas no formato yyyy/MM/dd e gênero"""
        
        # Validação rigorosa do formato
        try:
            inicio = datetime.strptime(inicio_str, "%Y/%m/%d")
            fim = datetime.strptime(fim_str, "%Y/%m/%d")
        except ValueError:
            raise ValueError("Formato inválido. Use yyyy/MM/dd (ex: 2025/03/11)")

        # Query otimizada para o novo formato
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {
                            self.campo_data: {
                                "gte": inicio.strftime("%Y/%m/%d"),
                                "lte": fim.strftime("%Y/%m/%d"),
                                "format": "yyyy/MM/dd"
                            }
                        }},
                        {"term": {f"{self.campo_genero}.keyword": genero.lower()}}
                    ]
                }
            }
        }

        return [
            hit["_source"] 
            for hit in self.es.search(
                index=self.indice, 
                body=query
            )["hits"]["hits"]
        ]
        
def gerar_datas(inicio: str, fim: str) -> list:
    """Gera datas entre início e fim (formato YYYY-MM-DD)"""
    data_inicio = datetime.strptime(inicio, "%Y-%m-%d")
    data_fim = datetime.strptime(fim, "%Y-%m-%d")
    
    return [
        (data_inicio + timedelta(days=d)).strftime("%Y-%m-%d")
        for d in range((data_fim - data_inicio).days + 1)
    ]

def gerador_datas(inicio: str, fim: str):
    data_atual = datetime.strptime(inicio, "%Y-%m-%d")
    data_final = datetime.strptime(fim, "%Y-%m-%d")
    
    while data_atual <= data_final:
        yield data_atual.strftime("%Y-%m-%d")
        data_atual += timedelta(days=1)
