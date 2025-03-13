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

def teste_intervalo_datas(es, indice, data_inicio, data_fim, campo_data='timestamp'):
    """
    Busca documentos dentro de um intervalo de datas
    :param es: Conexão do Elasticsearch
    :param indice: Nome do índice
    :param data_inicio: Data inicial (formato ISO: '2025-03-01')
    :param data_fim: Data final (formato ISO: '2025-03-13')
    :param campo_data: Nome do campo de data no documento
    """
    
    consulta = {
        "query": {
            "range": {
                campo_data: {
                    "gte": data_inicio,
                    "lte": data_fim,
                    "format": "yyyy-MM-dd",  # Formato das datas de entrada
                    "time_zone": "-03:00"    # Fuso horário Brasil (BRT)
                }
            }
        },
        "sort": [{campo_data: {"order": "asc"}}],
        "_source": [campo_data, "mensagem"],  # Campos retornados
    }

    try:
        resposta = es.search(index=indice, body=consulta)
        total = resposta['hits']['total']['value']
        print(f"\n🔍 {total} documentos encontrados entre {data_inicio} e {data_fim}")
        
        for hit in resposta['hits']['hits']:
            data_doc = hit['_source'].get(campo_data)
            print(f"📅 {data_doc} | {hit['_source'].get('mensagem','')[:50]}...")
            
    except Exception as e:
        print(f"Erro na consulta: {str(e)}")

if __name__ == "__main__":
    try:
        es = conectar_elastic()
        
        # Executar todas as análises
        listar_indices(es)
        indice_alvo = "produtos"  # Alterar para seu índice
        obter_mapeamento(es, indice_alvo)
        analisar_campos(es, indice_alvo)
        documento_exemplo(es, indice_alvo)
        teste_intervalo_datas(
            es=es,
            indice="logs-2024.07*",  # Padrão de índices diários
            data_inicio="2024-07-01",
            data_fim="2024-07-27"
        )
        validar_consulta(es, indice_alvo)
        
    except Exception as e:
        print(f"Erro na conexão: {str(e)}")