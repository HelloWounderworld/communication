from datetime import datetime
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
