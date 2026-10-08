try:
    # código
    with open("arquivo_inexistente.txt") as f:
        conteudo = f.read()
        
except Exception as e:
    import sys
    exc_type, exc_obj, exc_tb = sys.exc_info()
    nome_arquivo = exc_tb.tb_frame.f_code.co_filename
    numero_linha = exc_tb.tb_lineno
    nome_erro = type(e).__name__
    
    print(f"🚨 ERRO: {nome_erro}")
    print(f"📍 Local: {nome_arquivo}, linha {numero_linha}")
    print(f"📝 Detalhe: {str(e)}")