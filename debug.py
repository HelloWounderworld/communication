import numpy as np
import traceback
import sys
import time

def faiss_add_transparente(index, vetores, nome_operacao="add"):
    """
    Wrapper cirúrgico para index.add() com transparência total.
    Cole isso EXATAMENTE onde você chama o add().
    
    Uso: faiss_add_transparente(seu_index, seus_vetores)
    """
    # --- CAPTURA DO ESTADO ANTES ---
    estado_antes = {
        "total_antes": index.ntotal,
        "dimensao_indice": index.d,
        "tipo_indice": type(index).__name__,
        "treinado": getattr(index, 'is_trained', 'N/A')
    }
    
    print(f"\n{'='*60}")
    print(f"🔍 FAISS ADD TRANSPARENTE: {nome_operacao}")
    print(f"{'='*60}")
    print(f"📊 Índice: {estado_antes['tipo_indice']} | Dim: {estado_antes['dimensao_indice']} | "
          f"Total antes: {estado_antes['total_antes']}")
    
    # --- ANÁLISE DO INPUT ---
    try:
        arr = np.asarray(vetores)
        print(f"📥 Input recebido: tipo={type(vetores).__name__}, shape={arr.shape}, dtype={arr.dtype}")
        
        # Validações rápidas
        problemas = []
        if arr.dtype != np.float32:
            problemas.append(f"❌ Dtype errado ({arr.dtype} → precisa float32)")
        if arr.ndim == 1:
            problemas.append(f"❌ Array 1D detectado (precisa 2D: n, dim)")
        if arr.ndim == 2 and arr.shape[1] != index.d:
            problemas.append(f"❌ Dimensão errada ({arr.shape[1]} ≠ {index.d})")
        if not arr.flags['C_CONTIGUOUS']:
            problemas.append(f"⚠️  Não C-contíguo")
        if np.isnan(arr).any():
            problemas.append(f"❌ Contém NaN")
            
        if problemas:
            print("⚠️  PROBLEMAS DETECTADOS:")
            for p in problemas:
                print(f"   {p}")
            print("🔧 Tentando auto-correção...")
            
            # Auto-correção
            arr = np.ascontiguousarray(arr, dtype=np.float32)
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)
            print(f"✅ Corrigido: shape={arr.shape}, dtype={arr.dtype}")
        else:
            print("✅ Input válido")
            
    except Exception as e:
        print(f"💥 Erro ao analisar input: {e}")
        arr = vetores  # passa como está pra tentar e ver o erro real
    
    # --- EXECUÇÃO COM CAPTURA TOTAL ---
    inicio = time.time()
    try:
        # AQUI ESTÁ O ADD EM SI
        index.add(arr)
        tempo = time.time() - inicio
        
        # --- SUCESSO ---
        print(f"\n✅ SUCESSO!")
        print(f"   ⏱️  Tempo: {tempo*1000:.2f}ms")
        print(f"   📈 Total depois: {index.ntotal} (+{index.ntotal - estado_antes['total_antes']})")
        print(f"{'='*60}\n")
        return True, index.ntotal
        
    except Exception as e:
        # --- FALHA: CAPTURA TUDO ---
        tempo = time.time() - inicio
        print(f"\n💥 FALHA NO ADD!")
        print(f"   ⏱️  Tempo até erro: {tempo*1000:.2f}ms")
        print(f"   🚨 Tipo: {type(e).__name__}")
        print(f"   📝 Mensagem: {str(e)}")
        print(f"\n📍 TRACEBACK COMPLETO:")
        traceback.print_exc()
        print(f"\n🔬 ESTADO DO ÍNDICE NO MOMENTO DO ERRO:")
        print(f"   Total atual: {index.ntotal}")
        print(f"   Input que causou erro: shape={getattr(arr, 'shape', 'N/A')}, "
              f"dtype={getattr(arr, 'dtype', 'N/A')}")
        print(f"{'='*60}\n")
        return False, None