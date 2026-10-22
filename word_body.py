import unicodedata
import fugashi

def tratar_e_normalizar_utf8(texto):
    """
    Garante que o texto esteja em string UTF-8 limpa e normaliza 
    Katakanas e símbolos para o padrão Full-Width (NFKC), evitando quebras de bytes.
    """
    if isinstance(texto, bytes):
        texto = texto.decode('utf-8', errors='ignore')
    
    # Converte variações como half-width (ﾏｽｸ) para full-width (マスク)
    # de modo que a verificação de Katakana seja 100% precisa
    return unicodedata.normalize('NFKC', texto)


def eh_katakana(texto):
    """
    Função auxiliar que verifica se todos os caracteres da string 
    pertencem ao bloco Unicode do Katakana (incluindo o traço longo ー).
    """
    for char in texto:
        codigo = ord(char)
        # Range Unicode do Katakana padrão e do traço de prolongamento (ー)
        if not (0x30A0 <= codigo <= 0x30FF or char == 'ー'):
            return False
    return True


def mesclar_nomes_katakana(tokens_fugashi):
    """
    Recebe a lista de nós gerada pelo Fugashi Tagger e reconstrói 
    as quebras causadas pelo caractere '・' quando cercado por Katakanas.
    Runs em O(n) - Linear e direto.
    """
    palavras_processadas = []
    i = 0
    n = len(tokens_fugashi)
    
    while i < n:
        # Verifica se o nó atual é Katakana e se os próximos formam "・" + Katakana
        if (i + 2 < n and 
            eh_katakana(tokens_fugashi[i].surface) and 
            tokens_fugashi[i+1].surface == "・" and 
            eh_katakana(tokens_fugashi[i+2].surface)):
            
            # Inicia a fusão da entidade
            entidade_mesclada = tokens_fugashi[i].surface + tokens_fugashi[i+1].surface + tokens_fugashi[i+2].surface
            pos_final = tokens_fugashi[i].feature.pos1  # Mantém a classe gramatical original (geralmente 名詞)
            
            i += 3  # Avança o ponteiro por ter consumido 3 nós
            
            # Loop Look-ahead extra para capturar nomes compostos triplos ou maiores (ex: A・B・C)
            while i + 1 < n and tokens_fugashi[i].surface == "・" and eh_katakana(tokens_fugashi[i+1].surface):
                entidade_mesclada += tokens_fugashi[i].surface + tokens_fugashi[i+1].surface
                i += 2
                
            palavras_processadas.append({
                "surface": entidade_mesclada,
                "pos": pos_final,
                "foi_mesclado": True
            })
        else:
            # Caso normal: mantém a palavra exatamente como o Fugashi extraiu
            # Tratamento preventivo caso o recurso venha vazio (None)
            pos = tokens_fugashi[i].feature.pos1 if tokens_fugashi[i].feature.pos1 else "未知語"
            
            palavras_processadas.append({
                "surface": tokens_fugashi[i].surface,
                "pos": pos,
                "foi_mesclado": False
            })
            i += 1
            
    return palavras_processadas

# 1. Instancia o seu Tagger padrão do seu projeto
tagger = fugashi.Tagger()

# Matéria de exemplo vindo do seu crawler
materia_jornalistica = "昨夜、イーロン・マスク氏とティム・クック氏が新しいテクノロジーについて会談した。"

# 2. Executa a limpeza UTF-8 antes do Tagger
texto_limpo = tratar_e_normalizar_utf8(materia_jornalistica)

# 3. Executa o parser do Fugashi
nos_originais = list(tagger(texto_limpo))

# 4. Corrige a fragmentação do ponto médio ('・') após o processamento
resultado_final = mesclar_nomes_katakana(nos_originais)

# Resultado limpo e estruturado
for token in resultado_final:
    if token["foi_mesclado"]:
        print(f"🌟 Palavra Corrigida: {token['surface']} | Tipo: {token['pos']}")
    else:
        print(f"Palavra: {token['surface']}")
