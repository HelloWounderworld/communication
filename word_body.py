import re
import unicodedata
import fugashi

def tratar_e_normalizar_utf8(texto):
    if isinstance(texto, bytes):
        texto = texto.decode('utf-8', errors='ignore')
    return unicodedata.normalize('NFKC', texto)

def proteger_nomes_katakana(texto):
    """
    Substitui temporariamente '・' por um placeholder em nomes Katakana
    para evitar que o Fugashi quebre indevidamente.
    """
    # Regex: Katakana+ (・Katakana+)+
    # Captura sequências como イーロン・マスク, A・B・C
    pattern = re.compile(r'[ァ-ヶー]+(?:・[ァ-ヶー]+)+')
    
    def substituir(match):
        # Substitui ・ por um caractere raro que não conflita
        return match.group(0).replace('・', '\u0001')  # \u0001 = SOH (Start of Heading)
    
    return pattern.sub(substituir, texto)

def restaurar_nomes_katakana(texto):
    """Restaura o '・' original"""
    return texto.replace('\u0001', '・')

def mesclar_nomes_katakana(tokens_fugashi):
    """
    Agora simplificada: só precisa juntar tokens que foram separados
    mas ainda contêm o placeholder (caso o Fugashi ainda quebre).
    """
    palavras_processadas = []
    buffer = ""
    
    for token in tokens_fugashi:
        surface = token.surface
        
        # Se contém o placeholder, ainda precisa de tratamento especial
        if '\u0001' in surface or buffer:
            buffer += surface
            # Se o próximo não continua o padrão, fecha o buffer
            if not surface.endswith('\u0001') and '\u0001' not in surface:
                palavras_processadas.append({
                    "surface": restaurar_nomes_katakana(buffer),
                    "pos": token.feature.pos1 or "未知語",
                    "foi_mesclado": True
                })
                buffer = ""
            continue
        
        # Caso normal
        pos = token.feature.pos1 if token.feature.pos1 else "未知語"
        palavras_processadas.append({
            "surface": surface,
            "pos": pos,
            "foi_mesclado": False
        })
    
    # Caso sobre algo no buffer no final
    if buffer:
        palavras_processadas.append({
            "surface": restaurar_nomes_katakana(buffer),
            "pos": "未知語",
            "foi_mesclado": True
        })
    
    return palavras_processadas

# ========== USO ==========
tagger = fugashi.Tagger()

materia = "昨夜、イーロン・マスク氏とティム・クック氏が新しいテクノロジーについて会談した。"

# 1. Normaliza
texto_limpo = tratar_e_normalizar_utf8(materia)

# 2. Protege os nomes compostos (NOVO PASSO)
texto_protegido = proteger_nomes_katakana(texto_limpo)

# 3. Fugashi processa
nos = list(tagger(texto_protegido))

# 4. Restaura e mescla se necessário
resultado = mesclar_nomes_katakana(nos)

for token in resultado:
    if token["foi_mesclado"]:
        print(f"🌟 {token['surface']} | {token['pos']}")
    else:
        print(f"   {token['surface']}")
