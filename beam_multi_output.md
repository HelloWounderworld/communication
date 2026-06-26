Sim, é totalmente possível! Vou adaptar o script para suportar múltiplas precisões (FP4, 8-bit, BF16, FP16) e execução em **multi-GPU** via `accelerate` e `device_map`. Vou buscar as práticas mais recentes para garantir compatibilidade.
Sim, é totalmente possível! Vou criar um script completo e flexível que suporta **todas as precisões** (FP4, 8-bit, BF16, FP16) e **multi-GPU** via `accelerate`/`device_map`. O `device_map="auto"` do Hugging Face já gerencia automaticamente a distribuição do modelo entre múltiplas GPUs , e para inferência em multi-GPU com paralelismo de tensores, o **vLLM** é a opção mais robusta .

Vou criar o script adaptado:

```python
#!/usr/bin/env python3
"""
================================================================================
GERADOR DE TÍTULOS JORNALÍSTICOS COM BEAM SEARCH
================================================================================
Suporta: FP4, 8-bit, BF16, FP16 | Multi-GPU via device_map | LoRA adapters
Modelo: Llama 3.3 70B + Adaptador LoRA (formato Alpaca)
================================================================================
"""

import torch
import sys
import argparse
import os
from typing import Optional, List, Dict
from dataclasses import dataclass

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    GenerationConfig,
)
from peft import PeftModel


# =============================================================================
# CONFIGURAÇÕES DE PRECISÃO
# =============================================================================

@dataclass
class ConfigPrecisao:
    """Configuração de precisão para carregamento do modelo."""
    nome: str
    descricao: str
    quantization_config: Optional[BitsAndBytesConfig]
    torch_dtype: torch.dtype
    device_map: str
    requer_accelerate: bool
    memoria_estimada_gb: float  # Estimativa para Llama 70B


# Registro de configurações de precisão suportadas
PRECOES_SUPORTADAS = {
    "fp4": ConfigPrecisao(
        nome="FP4 (4-bit Normalized Float)",
        descricao="Quantização 4-bit com NF4 + computação bfloat16. Menor uso de VRAM.",
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
        torch_dtype=torch.bfloat16,
        device_map="auto",
        requer_accelerate=True,
        memoria_estimada_gb=42.0,
    ),
    "fp4-fp16": ConfigPrecisao(
        nome="FP4 com compute FP16",
        descricao="Quantização 4-bit com computação em float16 (compatibilidade maior).",
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        ),
        torch_dtype=torch.float16,
        device_map="auto",
        requer_accelerate=True,
        memoria_estimada_gb=42.0,
    ),
    "int8": ConfigPrecisao(
        nome="INT8 (8-bit)",
        descricao="Quantização 8-bit via LLM.int8(). Balance entre qualidade e memória.",
        quantization_config=BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0,
        ),
        torch_dtype=torch.float16,  # bitsandbytes sobrescreve para mixed int8
        device_map="auto",
        requer_accelerate=True,
        memoria_estimada_gb=75.0,
    ),
    "bf16": ConfigPrecisao(
        nome="BF16 (BFloat16)",
        descricao="Precisão reduzida nativa. Requer ~140GB VRAM total (multi-GPU).",
        quantization_config=None,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        requer_accelerate=True,
        memoria_estimada_gb=140.0,
    ),
    "fp16": ConfigPrecisao(
        nome="FP16 (Float16)",
        descricao="Precisão reduzida float16. Requer ~140GB VRAM total (multi-GPU).",
        quantization_config=None,
        torch_dtype=torch.float16,
        device_map="auto",
        requer_accelerate=True,
        memoria_estimada_gb=140.0,
    ),
}


# =============================================================================
# CONFIGURAÇÕES DO BEAM SEARCH
# =============================================================================

CONFIG_BEAM_PADRAO = {
    "num_beams": 10,
    "num_return_sequences": 10,
    "max_new_tokens": 64,
    "no_repeat_ngram_size": 3,
    "early_stopping": True,
    "length_penalty": 1.0,
    "output_scores": True,
    "return_dict_in_generate": True,
}


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def detectar_gpus() -> Dict:
    """Detecta GPUs disponíveis e retorna informações."""
    if not torch.cuda.is_available():
        return {"disponivel": False, "count": 0, "nomes": [], "vram_total_gb": 0}
    
    gpus = []
    vram_total = 0
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        vram_gb = props.total_memory / (1024**3)
        gpus.append({
            "id": i,
            "nome": props.name,
            "vram_gb": vram_gb,
            "capacidade": props.major,
        })
        vram_total += vram_gb
    
    return {
        "disponivel": True,
        "count": len(gpus),
        "nomes": [g["nome"] for g in gpus],
        "vram_total_gb": vram_total,
        "gpus": gpus,
    }


def verificar_compatibilidade(precisao: str, gpus: Dict) -> bool:
    """Verifica se o hardware suporta a precisão escolhida."""
    config = PRECOES_SUPORTADAS[precisao]
    
    if not gpus["disponivel"]:
        print("❌ ERRO: Nenhuma GPU detectada!")
        return False
    
    print(f"\n{'='*70}")
    print("DIAGNÓSTICO DE HARDWARE")
    print(f"{'='*70}")
    print(f"GPUs detectadas: {gpus['count']}")
    for g in gpus["gpus"]:
        print(f"  • GPU {g['id']}: {g['nome']} | {g['vram_gb']:.1f} GB")
    print(f"VRAM total disponível: {gpus['vram_total_gb']:.1f} GB")
    print(f"VRAM estimada necessária ({config.nome}): {config.memoria_estimada_gb:.1f} GB")
    
    if gpus["vram_total_gb"] < config.memoria_estimada_gb * 0.9:
        print(f"\n⚠️  AVISO: VRAM total ({gpus['vram_total_gb']:.1f}GB) pode ser insuficiente")
        print(f"   para {config.nome} ({config.memoria_estimada_gb:.1f}GB estimados).")
        print(f"   O modelo será distribuído entre GPU+CPU (mais lento).")
        return True  # Continua mesmo assim, accelerate gerencia
    
    print(f"\n✅ Hardware compatível!")
    return True


def formatar_prompt_alpaca(instrucao: str, entrada: str, sistema: str = "") -> str:
    """
    Formata o prompt no estilo Alpaca usado no fine-tuning.
    Ajuste conforme o template EXATO do seu treinamento.
    """
    # Template padrão Alpaca (ajuste se usou variação)
    if sistema:
        prompt = f"""{sistema}

### Instruction:
{instrucao}

### Input:
{entrada}

### Response:
"""
    else:
        prompt = f"""### Instruction:
{instrucao}

### Input:
{entrada}

### Response:
"""
    return prompt


def carregar_modelo(caminho_base: str, caminho_lora: str, precisao: str):
    """
    Carrega o modelo com a precisão especificada e aplica o adaptador LoRA.
    Suporta multi-GPU via device_map='auto' do Accelerate.
    """
    config = PRECOES_SUPORTADAS[precisao]
    
    print(f"\n{'='*70}")
    print("CARREGAMENTO DO MODELO")
    print(f"{'='*70}")
    print(f"Precisão: {config.nome}")
    print(f"Descrição: {config.descricao}")
    print(f"torch_dtype: {config.torch_dtype}")
    print(f"device_map: {config.device_map}")
    print(f"Quantização: {'Sim' if config.quantization_config else 'Não'}")
    
    # 1. Tokenizer
    print(f"\n[1/4] Carregando tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        caminho_base,
        trust_remote_code=True,
        padding_side="left",
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    
    # 2. Modelo base
    print(f"\n[2/4] Carregando modelo base (isso pode levar alguns minutos)...")
    
    kwargs = {
        "pretrained_model_name_or_path": caminho_base,
        "torch_dtype": config.torch_dtype,
        "device_map": config.device_map,
        "trust_remote_code": True,
    }
    
    # Adicionar config de quantização se existir
    if config.quantization_config is not None:
        kwargs["quantization_config"] = config.quantization_config
        # NUNCA passar load_in_4bit/load_in_8bit junto com quantization_config
        # 
    
    # Para BF16/FP16 sem quantização, usar attn_implementation mais eficiente
    if config.quantization_config is None:
        kwargs["attn_implementation"] = "flash_attention_2"
    
    modelo = AutoModelForCausalLM.from_pretrained(**kwargs)
    
    # Info de distribuição multi-GPU
    if hasattr(modelo, "hf_device_map"):
        print(f"\n   📊 Distribuição do modelo entre dispositivos:")
        for layer, device in modelo.hf_device_map.items():
            print(f"      {layer}: {device}")
    
    # 3. Aplicar LoRA
    print(f"\n[3/4] Aplicando adaptador LoRA: {caminho_lora}")
    modelo = PeftModel.from_pretrained(modelo, caminho_lora)
    
    # 4. Preparar para inferência
    print("\n[4/4] Preparando para inferência...")
    modelo.eval()
    
    # Memória
    if hasattr(modelo, "get_memory_footprint"):
        memoria_gb = modelo.get_memory_footprint() / (1024**3)
        print(f"\n✅ Modelo carregado! Uso estimado de memória: ~{memoria_gb:.2f} GB")
    
    print(f"{'='*70}")
    
    return modelo, tokenizer


def gerar_titulos_beam_search(modelo, tokenizer, materia: str, config_beam: dict,
                              instrucao: str = None, sistema: str = ""):
    """
    Gera múltiplos títulos usando beam search com retorno de scores.
    """
    if instrucao is None:
        instrucao = "Gere um título jornalístico impactante, conciso e atrativo para a matéria abaixo."
    
    prompt = formatar_prompt_alpaca(instrucao, materia, sistema)
    
    # Tokenizar
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=4096,
    )
    
    # Mover para o dispositivo correto (device_map='auto' já distribuiu o modelo)
    # Não precisamos .to(modelo.device) quando usar device_map='auto'
    # 
    
    print(f"\n{'='*70}")
    print("GERAÇÃO COM BEAM SEARCH")
    print(f"{'='*70}")
    print(f"Matéria: {materia[:120]}...")
    print(f"\nParâmetros:")
    print(f"  • Beams: {config_beam['num_beams']}")
    print(f"  • Retornar: {config_beam['num_return_sequences']}")
    print(f"  • Max tokens: {config_beam['max_new_tokens']}")
    print(f"  • No-repeat n-gram: {config_beam['no_repeat_ngram_size']}")
    print(f"  • Length penalty: {config_beam['length_penalty']}")
    
    if "num_beam_groups" in config_beam:
        print(f"  • Grupos (diversidade): {config_beam['num_beam_groups']}")
        print(f"  • Diversity penalty: {config_beam['diversity_penalty']}")
    
    print(f"\n⏳ Gerando títulos... (aguarde)")
    
    # Gerar
    with torch.no_grad():
        outputs = modelo.generate(
            **inputs,
            **config_beam,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    # Extrair resultados
    resultados = []
    prompt_length = inputs.input_ids.shape[1]
    
    for i in range(config_beam['num_return_sequences']):
        sequencia = outputs.sequences[i][prompt_length:]
        titulo = tokenizer.decode(sequencia, skip_special_tokens=True).strip()
        
        # Score: log-probabilidade normalizada pelo comprimento
        score = None
        if hasattr(outputs, 'sequences_scores') and outputs.sequences_scores is not None:
            score = outputs.sequences_scores[i].item()
        
        resultados.append({
            "rank": i + 1,
            "titulo": titulo,
            "score": score,
            "tokens": len(sequencia),
        })
    
    return resultados


def exibir_resultados(resultados: List[Dict], mostrar_scores: bool = True):
    """Exibe os títulos gerados de forma organizada."""
    print(f"\n{'='*70}")
    print("RESULTADOS - TÍTULOS GERADOS")
    print(f"{'='*70}\n")
    
    for r in resultados:
        barra = "─" * 68
        score_str = f" | Score: {r['score']:.4f}" if mostrar_scores and r['score'] is not None else ""
        print(f"┌{barra}┐")
        print(f"│ #{r['rank']:2d}{score_str:<58} │")
        print(f"├{barra}┤")
        # Quebra linha se título for muito longo
        titulo = r['titulo']
        max_len = 66
        if len(titulo) > max_len:
            linhas = [titulo[i:i+max_len] for i in range(0, len(titulo), max_len)]
            for linha in linhas:
                print(f"│ {linha:<66} │")
        else:
            print(f"│ {titulo:<66} │")
        print(f"└{barra}┘\n")
    
    print(f"Total: {len(resultados)} títulos distintos gerados.")
    print(f"{'='*70}")


# =============================================================================
# MODO INTERATIVO
# =============================================================================

def modo_interativo(modelo, tokenizer, config_beam: dict, precisao: str):
    """Loop interativo para geração de títulos no terminal."""
    print("\n" + "=" * 70)
    print("MODO INTERATIVO - GERADOR DE TÍTULOS JORNALÍSTICOS")
    print(f"Precisão atual: {PRECOES_SUPORTADAS[precisao].nome}")
    print("=" * 70)
    print("\nComandos:")
    print("  /sair              - Encerra")
    print("  /config            - Mostra configuração do beam search")
    print("  /precisao          - Mostra precisão atual")
    print("  /diversidade ON|OFF- Ativa/desativa Group Beam Search")
    print("  /beams N           - Altera largura do beam (ex: /beams 15)")
    print("  /retornar N        - Altera quantos retornar (ex: /retornar 8)")
    print("  /tokens N          - Altera max_new_tokens (ex: /tokens 80)")
    print("  /ajuda             - Mostra comandos")
    print("=" * 70)
    print("\n📰 Cole o texto da matéria (Enter duplo para gerar):")
    
    while True:
        try:
            # Ler matéria
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
            
            # Comandos
            cmd = materia.lower().split()
            if not materia:
                continue
            
            if materia.lower() == "/sair":
                print("\n👋 Até mais!")
                break
            elif materia.lower() == "/config":
                print(f"\nConfiguração atual: {config_beam}")
                continue
            elif materia.lower() == "/precisao":
                print(f"\nPrecisão: {PRECOES_SUPORTADAS[precisao].nome}")
                continue
            elif materia.lower() == "/ajuda":
                continue
            elif materia.lower().startswith("/diversidade"):
                if "on" in materia.lower():
                    config_beam["num_beam_groups"] = max(2, config_beam["num_beams"] // 2)
                    config_beam["diversity_penalty"] = 1.0
                    print("🌈 Diversidade ATIVADA")
                else:
                    config_beam.pop("num_beam_groups", None)
                    config_beam.pop("diversity_penalty", None)
                    print("🌈 Diversidade DESATIVADA")
                continue
            elif materia.lower().startswith("/beams"):
                try:
                    n = int(cmd[1])
                    config_beam["num_beams"] = n
                    config_beam["num_return_sequences"] = min(config_beam["num_return_sequences"], n)
                    print(f"✅ Beams alterado para: {n}")
                except:
                    print("❌ Uso: /beams 15")
                continue
            elif materia.lower().startswith("/retornar"):
                try:
                    n = int(cmd[1])
                    config_beam["num_return_sequences"] = min(n, config_beam["num_beams"])
                    print(f"✅ Retornar alterado para: {config_beam['num_return_sequences']}")
                except:
                    print("❌ Uso: /retornar 8")
                continue
            elif materia.lower().startswith("/tokens"):
                try:
                    n = int(cmd[1])
                    config_beam["max_new_tokens"] = n
                    print(f"✅ Max tokens alterado para: {n}")
                except:
                    print("❌ Uso: /tokens 80")
                continue
            
            # Gerar títulos
            resultados = gerar_titulos_beam_search(modelo, tokenizer, materia, config_beam)
            exibir_resultados(resultados)
            print("\n📰 Próxima matéria (Enter duplo para gerar):")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrompido. Até mais!")
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
        description="Gerador de Títulos Jornalísticos com Beam Search - Multi-GPU & Multi-Precisão",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # FP4 (menor VRAM, recomendado para multi-GPU)
  python %(prog)s --base ./Llama-3.3-70B --lora ./adapter --precisao fp4
  
  # INT8 (balanceado)
  python %(prog)s --base ./Llama-3.3-70B --lora ./adapter --precisao int8
  
  # BF16 (qualidade máxima, requer ~140GB VRAM total)
  python %(prog)s --base ./Llama-3.3-70B --lora ./adapter --precisao bf16
  
  # Modo não-interativo com uma matéria
  python %(prog)s --base ./modelo --lora ./adapter --precisao fp4 \\
      --materia "O governo anunciou hoje novas medidas..."
  
  # Mais diversidade entre títulos
  python %(prog)s --base ./modelo --lora ./adapter --precisao fp4 --diversidade
        """
    )
    
    parser.add_argument("--base", required=True, help="Caminho do modelo base Llama 3.3 70B")
    parser.add_argument("--lora", required=True, help="Caminho do adaptador LoRA")
    parser.add_argument("--precisao", choices=list(PRECOES_SUPORTADAS.keys()),
                        default="fp4", help="Precisão de carregamento (default: fp4)")
    parser.add_argument("--beams", type=int, default=10, help="Largura do beam")
    parser.add_argument("--retornar", type=int, default=10, help="Títulos a retornar")
    parser.add_argument("--max-tokens", type=int, default=64, help="Máximo de tokens")
    parser.add_argument("--diversidade", action="store_true", help="Ativa Group Beam Search")
    parser.add_argument("--materia", type=str, help="Matéria para modo não-interativo")
    parser.add_argument("--instrucao", type=str, 
                        default="Gere um título jornalístico impactante e conciso para a matéria abaixo.",
                        help="Instrução personalizada para o prompt")
    parser.add_argument("--sistema", type=str, default="", help="Texto de sistema/contexto opcional")
    parser.add_argument("--no-verificar", action="store_true", 
                        help="Pula verificação de hardware")
    
    args = parser.parse_args()
    
    # Verificar hardware
    gpus = detectar_gpus()
    if not args.no_verificar:
        if not verificar_compatibilidade(args.precisao, gpus):
            sys.exit(1)
    
    # Configurar beam search
    config_beam = CONFIG_BEAM_PADRAO.copy()
    config_beam["num_beams"] = args.beams
    config_beam["num_return_sequences"] = min(args.retornar, args.beams)
    config_beam["max_new_tokens"] = args.max_tokens
    
    if args.diversidade:
        config_beam["num_beam_groups"] = max(2, args.beams // 2)
        config_beam["diversity_penalty"] = 1.0
    
    # Carregar modelo
    modelo, tokenizer = carregar_modelo(args.base, args.lora, args.precisao)
    
    # Modo não-interativo
    if args.materia:
        resultados = gerar_titulos_beam_search(
            modelo, tokenizer, args.materia, config_beam,
            instrucao=args.instrucao, sistema=args.sistema
        )
        exibir_resultados(resultados)
        return
    
    # Modo interativo
    modo_interativo(modelo, tokenizer, config_beam, args.precisao)


if __name__ == "__main__":
    main()
```

---

## Instalação e Dependências

```bash
# Dependências principais
pip install transformers accelerate bitsandbytes peft torch

# Opcional: Flash Attention 2 (aceleração para BF16/FP16 em GPUs recentes)
pip install flash-attn --no-build-isolation

# Para multi-GPU com DeepSpeed (alternativa avançada)
pip install deepspeed
```

---

## Como Usar

### 1. **FP4 (Recomendado para multi-GPU com VRAM limitada)**

```bash
python gerador_titulos.py \
    --base ./Llama-3.3-70B-Instruct \
    --lora ./lora-titulos-jornalismo \
    --precisao fp4 \
    --beams 15 \
    --retornar 10 \
    --diversidade
```

**VRAM estimada:** ~42 GB total (distribuído automaticamente entre GPUs via `device_map="auto"`)

### 2. **INT8 (Balanceado)**

```bash
python gerador_titulos.py \
    --base ./Llama-3.3-70B-Instruct \
    --lora ./lora-titulos-jornalismo \
    --precisao int8 \
    --beams 12 \
    --retornar 8
```

**VRAM estimada:** ~75 GB total

### 3. **BF16 (Qualidade máxima, requer multi-GPU potente)**

```bash
python gerador_titulos.py \
    --base ./Llama-3.3-70B-Instruct \
    --lora ./lora-titulos-jornalismo \
    --precisao bf16 \
    --beams 10 \
    --retornar 5
```

**VRAM estimada:** ~140 GB total (ex: 2x A100 80GB ou 4x RTX 4090 24GB)

### 4. **Modo não-interativo (script/batch)**

```bash
python gerador_titulos.py \
    --base ./Llama-3.3-70B-Instruct \
    --lora ./lora-titulos-jornalismo \
    --precisao fp4 \
    --materia "O governo federal anunciou nesta terça-feira um pacote de medidas econômicas destinadas a estimular o crescimento do PIB..."
```

---

## Comandos no Modo Interativo

| Comando | Ação |
|---|---|
| `/sair` | Encerra o programa |
| `/config` | Mostra configuração atual do beam search |
| `/precisao` | Mostra precisão atual carregada |
| `/diversidade ON` | Ativa Group Beam Search (títulos mais diversos) |
| `/diversidade OFF` | Desativa diversidade |
| `/beams 15` | Altera largura do beam para 15 |
| `/retornar 8` | Altera para retornar 8 títulos |
| `/tokens 80` | Altera máximo de tokens para 80 |

---

## Pontos Críticos para Multi-GPU

1. **`device_map="auto"`** — O Hugging Face Accelerate distribui automaticamente as camadas do modelo entre todas as GPUs disponíveis. Não precisa configurar manualmente .

2. **Nunca misture `load_in_4bit`/`load_in_8bit` com `quantization_config`** — Isso gera `ValueError`. Use apenas `quantization_config` .

3. **Para BF16/FP16 sem quantização** — O modelo é carregado em precisão nativa e o `device_map` distribui camadas entre GPUs. Flash Attention 2 acelera significativamente.

4. **Se VRAM total for insuficiente** — O Accelerate automaticamente faz offload para CPU. Fica mais lento, mas funciona.

5. **Para inferência em produção com multi-GPU** — Considere **vLLM** com `tensor_parallel_size` para throughput máximo .

Se precisar de uma versão otimizada com **vLLM** para throughput em produção, me avise! 🚀
