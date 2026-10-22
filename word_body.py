import unicodedata
import fugashi

def tratar_e_normalizar_utf8(texto):
    if isinstance(texto, bytes):
        texto = texto.decode('utf-8', errors='ignore')
    return unicodedata.normalize('NFKC', texto)

def eh_katakana(texto):
    if not texto:
        return False
    for char in texto:
        codigo = ord(char)
        if not (0x30A0 <= codigo <= 0x30FF or char == 'ー'):
            return False
    return True

def mesclar_nomes_katakana(tokens_fugashi):
    """
    Mescla sequências de Katakana separadas por '・'.
    Lida com: イー + ロン + ・ + マスク → イーロン・マスク
    """
    palavras_processadas = []
    i = 0
    n = len(tokens_fugashi)
    
    while i < n:
        # Se o token atual é katakana, começa a verificar sequência
        if eh_katakana(tokens_fugashi[i].surface):
            # Acumula katakana até encontrar não-katakana
            j = i
            sequencia = []
            
            # Pega todos os katakana e ・ consecutivos
            while j < n:
                surface = tokens_fugashi[j].surface
                if eh_katakana(surface) or surface == '・':
                    sequencia.append(surface)
                    j += 1
                else:
                    break
            
            # Junta a sequência
            nome_junto = ''.join(sequencia)
            
            # Só marca como mesclado se tiver ・ (nome composto)
            if '・' in nome_junto:
                palavras_processadas.append({
                    "surface": nome_junto,
                    "pos": tokens_fugashi[i].feature.pos1 or "名詞",
                    "foi_mesclado": True
                })
            else:
                # Katakana simples sem ・, adiciona como está
                palavras_processadas.append({
                    "surface": nome_junto,
                    "pos": tokens_fugashi[i].feature.pos1 or "未知語",
                    "foi_mesclado": False
                })
            
            i = j  # Avança o ponteiro para depois da sequência
        else:
            # Não é katakana, adiciona normalmente
            pos = tokens_fugashi[i].feature.pos1 if tokens_fugashi[i].feature.pos1 else "未知語"
            palavras_processadas.append({
                "surface": tokens_fugashi[i].surface,
                "pos": pos,
                "foi_mesclado": False
            })
            i += 1
            
    return palavras_processadas

# ========== TESTE ==========
tagger = fugashi.Tagger()
materia = "昨夜、イーロン・マスク氏とティム・クック氏が新しいテクノロジーについて会談した。"

texto_limpo = tratar_e_normalizar_utf8(materia)
nos = list(tagger(texto_limpo))

print("🔍 Tokens do Fugashi:")
for i, token in enumerate(nos):
    print(f"  [{i}] '{token.surface}'")

resultado = mesclar_nomes_katakana(nos)

print("\n🎯 Resultado final:")
for token in resultado:
    if token["foi_mesclado"]:
        print(f"🌟 {token['surface']} | {token['pos']}")
    else:
        print(f"   {token['surface']}")
