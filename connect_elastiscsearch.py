from elasticsearch import Elasticsearch
from pprint import pprint  # Para formatação bonita

def conectar_elastic():
    """Estabelece conexão com o Elasticsearch"""
    return Elasticsearch(
        hosts=["http://localhost:9200"],
        basic_auth=('usuario', 'senha')  # Remover se não usar autenticação
    )

def listar_indices(es):
    """Lista todos os índices com detalhes importantes"""
    indices = es.cat.indices(h='health,status,index,docs.count,store.size', format='json')
    print("\nÍndices existentes:")
    for idx in indices:
        print(f"{idx['index']} ({idx['health']}) - Docs: {idx['docs.count']} | Tamanho: {idx['store.size']}")

def obter_mapeamento(es, indice):
    """Obtém o mapeamento completo de um índice"""
    mapeamento = es.indices.get_mapping(index=indice)
    print(f"\nMapeamento de {indice}:")
    pprint(mapeamento[indice]['mappings']['properties'])

def analisar_campos(es, indice):
    """Analisa tipos e capacidades dos campos"""
    campos = es.field_caps(index=indice, fields='*')
    print(f"\nCapacidades dos campos em {indice}:")
    for campo, info in campos['fields'].items():
        tipos = list(info.keys())
        print(f"{campo}: {tipos} - Pesquisável: {'searchable' in info[tipos[0]]}")

def documento_exemplo(es, indice):
    """Busca um documento de exemplo"""
    resposta = es.search(
        index=indice,
        body={"size": 1, "_source": {"includes": ["*"]}}
    )
    print(f"\nDocumento exemplo de {indice}:")
    pprint(resposta['hits']['hits'][0]['_source'])

def validar_consulta(es, indice):
    """Executa uma consulta de validação básica"""
    consulta = {
        "query": {
            "term": {"categoria.keyword": "eletronicos"}
        },
        "aggs": {
            "preco_medio": {"avg": {"field": "preco"}}
        }
    }
    
    resultado = es.search(index=indice, body=consulta)
    print("\nResultado da consulta de validação:")
    print(f"Total de documentos: {resultado['hits']['total']['value']}")
    print(f"Preço médio: {resultado['aggregations']['preco_medio']['value']:.2f}")

if __name__ == "__main__":
    try:
        es = conectar_elastic()
        
        # Executar todas as análises
        listar_indices(es)
        indice_alvo = "produtos"  # Alterar para seu índice
        obter_mapeamento(es, indice_alvo)
        analisar_campos(es, indice_alvo)
        documento_exemplo(es, indice_alvo)
        validar_consulta(es, indice_alvo)
        
    except Exception as e:
        print(f"Erro na conexão: {str(e)}")