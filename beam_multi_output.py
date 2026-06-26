#!/usr/bin/env python3
"""
Script para gerar múltiplos títulos jornalísticos usando Beam Search
com modelo Llama 3.3 70B quantizado (bitsandbytes) + adaptador LoRA.
"""

import torch
import sys
import argparse
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    GenerationConfig
)
from peft import PeftModel


# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

# Caminhos dos modelos (AJUSTE AQUI!)
CAMINHO_MODELO_BASE = "./Llama-3.3-70B-Instruct"  # ou caminho do HuggingFace
CAMINHO_ADAPTADOR_LORA = "./lora-adapter-titulos"  # pasta com adapter_config.json

# Configuração de quantização 4-bit (NF4)
QUANTIZACAO_CONFIG = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",           # Normal Float 4 - melhor para distribuições normais
    bnb_4bit_use_double_quant=True,     # Quantização aninhada para economia extra de memória
    bnb_4bit_compute_dtype=torch.bfloat16,  # Computação em bfloat16
)

# Parâmetros do Beam Search
CONFIG_BEAM = {
    "num_beams": 10,              # Largura do beam: quantos caminhos explorar em paralelo
    "num_return_sequences": 10,   # Quantos títulos diferentes retornar (deve ser <= num_beams)
    "max_new_tokens": 64,         # Tamanho máximo do título gerado
    "no_repeat_ngram_size": 3,    # Evita repetição de trigramas
    "early_stopping": True,       # Para quando todos os beams gerarem EOS
    "length_penalty": 1.0,        # 1.0 = neutro; >1.0 favorece sequências mais longas
    "output_scores": True,        # Necessário para obter scores das sequências
    "return_dict_in_generate": True,  # Retorna objeto com metadados completos
}

# Parâmetros de diversidade (OPCIONAL - descomente para usar Group Beam Search)
# Isso força os beams a serem mais diversos entre si
# CONFIG_BEAM["num_beam_groups"] = 5      # Divide 10 beams em 5 grupos
# CONFIG_BEAM["diversity_penalty"] = 1.0  # Penaliza beams similares


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def formatar_prompt_alpaca(instrucao: str, entrada: str) -> str:
    """
    Formata o prompt no estilo Alpaca usado no seu fine-tuning.
    Ajuste conforme o template exato que você usou no treinamento.
    """
    # Template padrão Alpaca
    prompt = f"""### Instruction:
{instrucao}

### Input:
{entrada}

### Response:
"""
    return prompt


def carregar_modelo(caminho_base: str, caminho_lora: str):
    """
    Carrega o modelo base quantizado e aplica o adaptador LoRA.
    """
    print("=" * 70)
    print("CARREGANDO MODELO")
    print("=" * 70)
    
    # 1. Carregar tokenizer
    print(f"\n[1/4] Carregando tokenizer de: {caminho_base}")
    tokenizer = AutoTokenizer.from_pretrained(
        caminho_base,
        trust_remote_code=True,
        padding_side="left"  # Importante para geração causal
    )
    
    # Definir token de padding se não existir
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    
    # 2. Carregar modelo base quantizado em 4-bit
    print(f"\n[2/4] Carregando modelo base quantizado (4-bit) de: {caminho_base}")
    print("      Isso pode levar alguns minutos dependendo do hardware...")
    
    modelo = AutoModelForCausalLM.from_pretrained(
        caminho_base,
        quantization_config=QUANTIZACAO_CONFIG,
        device_map="auto",           # Distribui camadas automaticamente na GPU/CPU
        torch_dtype=torch.bfloat16,  # Tipo para camadas não quantizadas
        trust_remote_code=True,
        attn_implementation="flash_attention_2",  # Opcional: mais rápido se disponível
    )
    
    # 3. Aplicar adaptador LoRA
    print(f"\n[3/4] Aplicando adaptador LoRA de: {caminho_lora}")
    modelo = PeftModel.from_pretrained(modelo, caminho_lora)
    
    # 4. Preparar para inferência
    print("\n[4/4] Preparando modelo para inferência...")
    modelo.eval()  # Modo avaliação (desativa dropout, etc.)
    
    # Info de memória
    memoria_gb = modelo.get_memory_footprint() / (1024 ** 3)
    print(f"\n✅ Modelo carregado! Uso de VRAM: ~{memoria_gb:.2f} GB")
    print("=" * 70)
    
    return modelo, tokenizer


def gerar_titulos(modelo, tokenizer, materia: str, config: dict):
    """
    Gera múltiplos títulos usando beam search.
    """
    # Formatar prompt no estilo Alpaca
    instrucao = "Gere um título jornalístico impactante e conciso para a matéria abaixo."
    prompt = formatar_prompt_alpaca(instrucao, materia)
    
    # Tokenizar
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=4096,  # Ajuste conforme necessário
    ).to(modelo.device)
    
    print(f"\n{'='*70}")
    print("GERANDO TÍTULOS")
    print(f"{'='*70}")
    print(f"\nPrompt (primeiros 200 chars):\n{prompt[:200]}...")
    print(f"\nMatéria: {materia[:100]}...")
    print(f"\nParâmetros do Beam Search:")
    print(f"  • num_beams: {config['num_beams']}")
    print(f"  • num_return_sequences: {config['num_return_sequences']}")
    print(f"  • max_new_tokens: {config['max_new_tokens']}")
    print(f"\nGerando... (isso pode levar alguns segundos)\n")
    
    # Gerar com beam search
    with torch.no_grad():
        outputs = modelo.generate(
            **inputs,
            **config,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    # Extrair resultados
    resultados = []
    prompt_length = inputs.input_ids.shape[1]
    
    for i in range(config['num_return_sequences']):
        # Pegar apenas os tokens gerados (excluindo o prompt)
        sequencia_gerada = outputs.sequences[i][prompt_length:]
        
        # Decodificar
        titulo = tokenizer.decode(sequencia_gerada, skip_special_tokens=True).strip()
        
        # Obter score da sequência (log-probabilidade normalizada)
        score = outputs.sequences_scores[i].item() if hasattr(outputs, 'sequences_scores') else None
        
        resultados.append({
            "rank": i + 1,
            "titulo": titulo,
            "score": score,
            "tokens": len(sequencia_gerada)
        })
    
    return resultados


def exibir_resultados(resultados: list, mostrar_scores: bool = True):
    """
    Exibe os títulos gerados de forma organizada no terminal.
    """
    print(f"\n{'='*70}")
    print("TÍTULOS GERADOS (ORDENADOS POR PROBABILIDADE)")
    print(f"{'='*70}\n")
    
    for r in resultados:
        barra = "─" * 70
        print(f"{barra}")
        print(f"  #{r['rank']} | Score: {r['score']:.4f}" if mostrar_scores and r['score'] is not None else f"  #{r['rank']}")
        print(f"  Título: {r['titulo']}")
        print(f"{barra}\n")
    
    print(f"{'='*70}")
    print(f"Total de títulos gerados: {len(resultados)}")
    print(f"{'='*70}")


# =============================================================================
# MODO INTERATIVO (TERMINAL)
# =============================================================================

def modo_interativo(modelo, tokenizer, config: dict):
    """
    Loop interativo para gerar títulos a partir de matérias inseridas no terminal.
    """
    print("\n" + "=" * 70)
    print("MODO INTERATIVO")
    print("=" * 70)
    print("\nDigite o texto da matéria jornalística.")
    print("Comandos especiais:")
    print("  /sair     - Encerra o programa")
    print("  /config   - Mostra configuração atual do beam search")
    print("  /ajuda    - Mostra esta mensagem")
    print("=" * 70 + "\n")
    
    while True:
        try:
            # Ler matéria do usuário
            print("\n📰 Cole a matéria (pressione Enter duas vezes para gerar):")
            linhas = []
            while True:
                try:
                    linha = input()
                    if linha.strip() == "":
                        break
                    linhas.append(linha)
                except EOFError:
                    break
            
            materia = "\n".join(linhas).strip()
            
            # Comandos especiais
            if materia.lower() == "/sair":
                print("\n👋 Encerrando. Até mais!")
                break
            elif materia.lower() == "/config":
                print(f"\nConfiguração atual: {config}")
                continue
            elif materia.lower() == "/ajuda":
                continue  # Reimprime o cabeçalho de ajuda no próximo loop
            elif not materia:
                print("⚠️  Matéria vazia. Tente novamente.")
                continue
            
            # Gerar e exibir títulos
            resultados = gerar_titulos(modelo, tokenizer, materia, config)
            exibir_resultados(resultados)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrompido pelo usuário. Até mais!")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            import traceback
            traceback.print_exc()


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Gera múltiplos títulos jornalísticos usando Beam Search com Llama + LoRA"
    )
    parser.add_argument(
        "--base", 
        default=CAMINHO_MODELO_BASE,
        help="Caminho para o modelo base Llama 3.3 70B"
    )
    parser.add_argument(
        "--lora", 
        default=CAMINHO_ADAPTADOR_LORA,
        help="Caminho para o adaptador LoRA"
    )
    parser.add_argument(
        "--beams", 
        type=int, 
        default=10,
        help="Largura do beam search (default: 10)"
    )
    parser.add_argument(
        "--retornar", 
        type=int, 
        default=10,
        help="Número de títulos a retornar (default: 10, max=beams)"
    )
    parser.add_argument(
        "--max-tokens", 
        type=int, 
        default=64,
        help="Máximo de tokens por título (default: 64)"
    )
    parser.add_argument(
        "--materia", 
        type=str,
        help="Gera títulos para uma única matéria e sai (modo não-interativo)"
    )
    parser.add_argument(
        "--diversidade", 
        action="store_true",
        help="Ativa Group Beam Search para maior diversidade entre títulos"
    )
    
    args = parser.parse_args()
    
    # Atualizar configurações com argumentos
    config = CONFIG_BEAM.copy()
    config["num_beams"] = args.beams
    config["num_return_sequences"] = min(args.retornar, args.beams)
    config["max_new_tokens"] = args.max_tokens
    
    # Ativar diversidade (Group Beam Search) se solicitado
    if args.diversidade:
        config["num_beam_groups"] = max(2, args.beams // 2)
        config["diversity_penalty"] = 1.0
        print(f"\n🌈 Modo de diversidade ativado: {config['num_beam_groups']} grupos de beams")
    
    # Carregar modelo
    modelo, tokenizer = carregar_modelo(args.base, args.lora)
    
    # Modo não-interativo (uma única matéria via CLI)
    if args.materia:
        resultados = gerar_titulos(modelo, tokenizer, args.materia, config)
        exibir_resultados(resultados)
        return
    
    # Modo interativo (terminal)
    modo_interativo(modelo, tokenizer, config)


if __name__ == "__main__":
    main()
