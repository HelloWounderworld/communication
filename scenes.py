import os
import json
import re

def gerar_json_scenes(diretorio_raiz, program_id, caminho_saida="scenes.json"):
    """
    Varre o diretório raiz, encontra subdiretórios e arquivos .mp4 no formato
    {nome_do_sub_diretorio}-scene-{valor_numerico}.mp4 e gera um JSON único.
    
    Args:
        diretorio_raiz (str): Caminho do diretório raiz onde estão os subdiretórios.
        program_id (str): Valor constante para o campo "program_id".
        caminho_saida (str): Nome do arquivo JSON de saída.
    """
    
    lista_scenes = []
    
    # Expressão regular para validar o padrão {nome}-scene-{numero}.mp4
    # Captura o nome do subdiretório e o valor numérico
    padrao_arquivo = re.compile(r'^(?P<video_id>.+)-scene-(?P<numero>\d+)\.mp4$')
    
    # Verifica se o diretório raiz existe
    if not os.path.isdir(diretorio_raiz):
        raise ValueError(f"O diretório '{diretorio_raiz}' não existe.")
    
    # Percorre todos os itens no diretório raiz
    for nome_subdir in sorted(os.listdir(diretorio_raiz)):
        caminho_subdir = os.path.join(diretorio_raiz, nome_subdir)
        
        # Verifica se é um diretório
        if not os.path.isdir(caminho_subdir):
            continue
        
        # Percorre os arquivos dentro do subdiretório
        for nome_arquivo in sorted(os.listdir(caminho_subdir)):
            caminho_arquivo = os.path.join(caminho_subdir, nome_arquivo)
            
            # Verifica se é um arquivo .mp4
            if not nome_arquivo.lower().endswith('.mp4'):
                continue
            
            # Verifica se o nome do arquivo corresponde ao padrão esperado
            match = padrao_arquivo.match(nome_arquivo)
            if not match:
                print(f"Aviso: Arquivo '{nome_arquivo}' não segue o padrão esperado. Ignorado.")
                continue
            
            # Extrai o video_id do nome do arquivo (grupo 'video_id' do regex)
            video_id_do_arquivo = match.group('video_id')
            
            # Opcional: Verifica se o nome do subdiretório corresponde ao prefixo do arquivo
            if video_id_do_arquivo != nome_subdir:
                print(f"Aviso: Arquivo '{nome_arquivo}' não corresponde ao subdiretório '{nome_subdir}'. "
                      f"Usando o nome do subdiretório como video_id.")
            
            # Monta o dicionário no formato solicitado
            elemento = {
                "scene_id": nome_arquivo,
                "video_id": nome_subdir,
                "program_id": program_id,
                "scene_video_path": f"/caminho/onde/mostra/arquivo/{program_id}/scenes/{nome_subdir}/{nome_arquivo}"
            }
            
            lista_scenes.append(elemento)
    
    # Ordena a lista por video_id e depois pelo valor numérico da cena
    lista_scenes.sort(key=lambda x: (x["video_id"], 
                                     int(re.search(r'-scene-(\d+)\.mp4$', x["scene_id"]).group(1))))
    
    # Salva o JSON em um único arquivo
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(lista_scenes, f, ensure_ascii=False, indent=2)
    
    print(f"Sucesso! {len(lista_scenes)} cenas processadas.")
    print(f"Arquivo salvo em: {os.path.abspath(caminho_saida)}")
    
    return lista_scenes

# ==================== EXEMPLO DE USO ====================
if __name__ == "__main__":
    # Configure aqui o caminho do diretório raiz
    DIRETORIO_RAIZ = "/caminho/para/seu/diretorio/raiz"
    
    # Configure aqui o valor constante do program_id
    PROGRAM_ID = "CONSTANTE"
    
    # Nome do arquivo de saída
    ARQUIVO_SAIDA = "scenes.json"
    
    # Executa a função
    try:
        resultado = gerar_json_scenes(DIRETORIO_RAIZ, PROGRAM_ID, ARQUIVO_SAIDA)
        
        # Exibe um exemplo do primeiro elemento (se houver)
        if resultado:
            print("\nExemplo do primeiro elemento:")
            print(json.dumps(resultado[0], indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Erro: {e}")
