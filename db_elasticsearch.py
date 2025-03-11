from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

class ElasticSimpleQuery:
    def __init__(self, 
               hosts=["http://localhost:9200"],
               index_padrao="seu_indice",
               campo_data="data_cadastro",
               campo_genero="genero"):
        
        self.es = Elasticsearch(hosts)
        self.index = index_padrao
        self.campo_data = campo_data
        self.campo_genero = campo_genero

    def buscar_por_data_genero(self, inicio, fim, genero, index=None):
        """Busca documentos entre duas datas com filtro de gênero"""
        query = {
            "query": {
                "bool": {
                    "must": [{
                        "range": {
                            self.campo_data: {
                                "gte": inicio.isoformat(),
                                "lte": fim.isoformat()
                            }
                        }
                    }, {
                        "match": {
                            self.campo_genero: genero.lower()
                        }
                    }]
                }
            }
        }
        
        try:
            resposta = self.es.search(
                index=index or self.index,
                body=query
            )
            return [hit["_source"] for hit in resposta["hits"]["hits"]]
        except:
            return None
        
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
