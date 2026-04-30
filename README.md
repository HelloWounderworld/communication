# Checklist de Diagnóstico — Análise de Tempo de Treinamento FSDP

**Objetivo:** Coletar informações precisas sobre hardware, configuração FSDP, configuração de treinamento e métricas empíricas para diagnosticar a causa raiz do tempo de treinamento atual de ~25 minutos por step (Llama-3.3-70B + LoRA + FSDP).

**Tempo estimado:** 30–45 minutos para executar todos os passos.

**Como usar este documento:** Execute cada bloco em ordem. Para cada passo, copie a saída exata (sem editar) em um documento separado. No final, você terá todas as informações necessárias para diagnóstico preciso.

---

## Bloco 1 — Hardware

### Passo 1.1 — Identificar modelo exato da GPU

```bash
nvidia-smi --query-gpu=name --format=csv,noheader
```

**Coletar:** A saída completa. Deve listar 4 linhas (uma por GPU).

**Por que importa:** RTX A6000 (Ampere) e RTX 6000 Ada têm throughput BF16 que difere em ~2.4×. Determinar qual versão muda a estimativa de tempo significativamente.

---

### Passo 1.2 — Versão do driver e CUDA

```bash
nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1
nvcc --version
```

**Coletar:** Versão do driver NVIDIA e versão do CUDA toolkit.

**Por que importa:** Versões antigas de CUDA podem não suportar flash-attention-2 ou ter performance reduzida.

---

### Passo 1.3 — Topologia do interconnect entre GPUs

```bash
nvidia-smi topo -m
```

**Coletar:** A matriz inteira que aparece. Deve ter formato similar a:
```
        GPU0    GPU1    GPU2    GPU3    CPU Affinity
GPU0     X      NV4     PIX     PIX     0-15
GPU1    NV4      X      PIX     PIX     0-15
...
```

**Por que importa:** Determina a velocidade de comunicação entre GPUs:
- `NV1`, `NV2`, `NV4`, `NV6` = NVLink (rápido, 100–600 GB/s)
- `PIX` = PCIe via switch (médio, ~32 GB/s)
- `PHB`, `NODE`, `SYS` = PCIe via host bridge (lento)

FSDP faz comunicação intensa entre GPUs. Se o interconnect for lento, é uma causa importante de gargalo.

---

### Passo 1.4 — Capacidade de cada GPU

```bash
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv
```

**Coletar:** Tabela completa com nome, memória total, em uso e livre de cada GPU.

**Por que importa:** Confirma a configuração de 47.6GB e mostra se há outros processos consumindo VRAM (que poderiam estar competindo por memória durante o treinamento).

---

### Passo 1.5 — Versão do PCIe (se PCIe for usado)

```bash
sudo lspci -vv | grep -A 30 "VGA\|3D" | grep -iE "lnksta|lnkcap"
```

Se não tiver acesso `sudo`, tente:

```bash
nvidia-smi -q | grep -A 5 "PCI"
```

**Coletar:** Linhas com "LnkSta" e "LnkCap" — mostram a velocidade atual e máxima do PCIe.

**Por que importa:** PCIe 4.0 x16 (~32 GB/s) é mais lento que PCIe 5.0 x16 (~64 GB/s). Se os dois primeiros passos não mostrarem NVLink, a velocidade do PCIe vira o gargalo principal.

---

## Bloco 2 — Configuração FSDP do Accelerate

### Passo 2.1 — Localizar arquivo de configuração FSDP

Procure o YAML do accelerate. Os locais mais comuns são:

```bash
# Local padrão
cat ~/.cache/huggingface/accelerate/default_config.yaml

# Se não existir, procure por arquivos YAML no projeto
find . -name "*.yaml" -o -name "*.yml" | xargs grep -l -i "fsdp" 2>/dev/null

# Verifique a variável de ambiente que pode apontar para o config
echo $ACCELERATE_CONFIG_FILE
```

**Coletar:** O conteúdo completo do arquivo YAML que está sendo usado.

**Por que importa:** Esse arquivo determina TODO o comportamento do FSDP. Aqui mora o suspeito principal — `fsdp_offload_params`. Se estiver `true`, é provavelmente a causa do gargalo de 25 min/step.

---

### Passo 2.2 — Verificar comando de lançamento do treinamento

Identifique o comando exato que está sendo usado para lançar o treinamento. Procure no seu script ou histórico:

```bash
history | grep "accelerate launch"
```

Ou abra o script `.sh` ou `.py` que dispara o treinamento.

**Coletar:** O comando completo, incluindo todas as flags (`--config_file`, `--num_processes`, etc.) e variáveis de ambiente (`CUDA_VISIBLE_DEVICES`, etc.).

**Por que importa:** Confirma se o config do passo 2.1 é realmente o que está sendo usado, e se há overrides em linha de comando.

---

## Bloco 3 — Configuração do Script de Treinamento

### Passo 3.1 — Copiar bloco TrainingArguments

Abra o seu `train.py` (ou nome equivalente) e copie **todo** o bloco de criação do `TrainingArguments`. Exemplo do que você deve copiar:

```python
training_args = TrainingArguments(
    output_dir="...",
    num_train_epochs=...,
    per_device_train_batch_size=...,
    gradient_accumulation_steps=...,
    gradient_checkpointing=...,
    bf16=...,
    logging_steps=...,
    save_strategy=...,
    save_steps=...,
    learning_rate=...,
    ...
)
```

**Coletar:** O bloco inteiro, com todos os parâmetros visíveis.

**Por que importa:** Confirma a configuração de batch size, gradient accumulation, gradient checkpointing, bf16, e outras flags que afetam diretamente o tempo de treinamento.

---

### Passo 3.2 — Copiar bloco LoraConfig

No mesmo script, copie o bloco do `LoraConfig`:

```python
lora_config = LoraConfig(
    r=...,
    lora_alpha=...,
    target_modules=[...],
    lora_dropout=...,
    bias=...,
    task_type=...
)
```

**Coletar:** O bloco completo.

**Por que importa:** Determina quantos parâmetros são treináveis. LoRA aplicado a apenas `q_proj, v_proj` vs. todos os 7 módulos lineares (`q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`) muda significativamente o número de parâmetros treináveis e o overhead.

---

### Passo 3.3 — Copiar bloco de carregamento do modelo

Copie a chamada do `AutoModelForCausalLM.from_pretrained(...)`:

```python
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.3-70B-Instruct",
    torch_dtype=...,
    attn_implementation=...,
    use_cache=...,
    ...
)
```

**Coletar:** Bloco inteiro.

**Por que importa:** Confirma `attn_implementation` (sdpa, flash_attention_2, eager), `torch_dtype` (bfloat16, float16, float32) e `use_cache` (deve ser `False` quando gradient_checkpointing está ativo).

---

### Passo 3.4 — Verificar se o snippet do FSDP auto wrap policy está presente

Procure no script se existe este trecho específico (ou similar):

```python
if getattr(trainer.accelerator.state, "fsdp_plugin", None):
    from peft.utils.other import fsdp_auto_wrap_policy
    fsdp_plugin = trainer.accelerator.state.fsdp_plugin
    fsdp_plugin.auto_wrap_policy = fsdp_auto_wrap_policy(trainer.model)
```

**Coletar:** Se está presente ou ausente. Se presente, copie o bloco. Se ausente, anote.

**Por que importa:** Esse snippet é OBRIGATÓRIO para que FSDP + LoRA funcione corretamente. Sem ele, o FSDP trata todos os parâmetros como um bloco monolítico, perdendo a economia de memória do LoRA.

---

## Bloco 4 — Pipeline de Dados

### Passo 4.1 — Estatísticas do dataset tokenizado

Execute o seguinte snippet Python (adapte o caminho do dataset ao seu):

```python
import numpy as np
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.3-70B-Instruct")

# Adapte para o seu caminho de dataset
# Substitua pela forma como você carrega seus dados
import json
with open("seu_dataset.jsonl", "r") as f:
    data = [json.loads(line) for line in f]

# Tokeniza alguns exemplos para estatísticas (use 1000 para amostra rápida)
sample = data[:1000]
lengths = []
for example in sample:
    # Adapte conforme seu formato Ollama
    text = f"{example['instruction']}\n{example['input']}\n{example['output']}"
    tokens = tokenizer(text)["input_ids"]
    lengths.append(len(tokens))

lengths = np.array(lengths)
print(f"Min:    {lengths.min()}")
print(f"Max:    {lengths.max()}")
print(f"Mean:   {lengths.mean():.0f}")
print(f"Median: {np.median(lengths):.0f}")
print(f"P75:    {np.percentile(lengths, 75):.0f}")
print(f"P90:    {np.percentile(lengths, 90):.0f}")
print(f"P95:    {np.percentile(lengths, 95):.0f}")
print(f"P99:    {np.percentile(lengths, 99):.0f}")
print(f"% > 3072: {(lengths > 3072).mean() * 100:.1f}%")
```

**Coletar:** A saída completa.

**Por que importa:** Se a média de tokens for muito menor que 3072 (digamos, 1500), você está desperdiçando ~50% da computação com padding desnecessário. Isso justifica habilitar packing ou dynamic padding.

---

### Passo 4.2 — Verificar configuração do data collator

No script de treinamento, copie como está sendo criado o data collator:

```python
data_collator = DataCollatorForLanguageModeling(...)
# ou
data_collator = DataCollatorForSeq2Seq(...)
```

**Coletar:** O bloco completo, e se há configuração de `pad_to_multiple_of` ou `padding="max_length"` vs. `padding=True`.

**Por que importa:** `padding="max_length"` força tudo até 3072 (ineficiente). `padding=True` faz dynamic padding (cada batch só pad até o maior do batch — muito mais eficiente).

---

## Bloco 5 — Métricas Empíricas Durante Execução

### Passo 5.1 — Tempo por step do log atual

Abra o log do treinamento atual (ou os últimos logs salvos). Copie 10–20 linhas consecutivas de progresso, exemplo:

```
{'loss': 1.234, 'learning_rate': 1e-5, 'epoch': 0.05}
[step 100/2031] - 25:30 elapsed - 25:00/it
```

**Coletar:** Trecho do log mostrando o tempo por iteração (`s/it` ou `it/s`) reportado pelo `Trainer`.

**Por que importa:** Esse é o número empírico mais preciso do tempo por step. Confirma os ~25 min/step calculados.

---

### Passo 5.2 — Snapshot do `nvidia-smi` durante execução

Se ainda houver um treinamento rodando (ou puder fazer um teste curto), execute em outro terminal **enquanto o treinamento está ativo**:

```bash
nvidia-smi
```

**Coletar:** Saída completa, mostrando para cada GPU: memory-usage, GPU-Util, temperatura, power.

**Por que importa:** Mostra se as 4 GPUs estão computando simultaneamente (FSDP funcionando) ou alternando (caiu em algum modo degenerado). GPU-Util baixo (< 50%) indica gargalo de I/O ou comunicação.

---

### Passo 5.3 — Profiling de uma iteração (opcional, se possível)

Se for viável rodar um treinamento de teste curto com profiling, adicione ao script:

```python
from torch.profiler import profile, ProfilerActivity, record_function

with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
             record_shapes=True) as prof:
    # Rodar 5-10 steps de treinamento
    trainer.train()

print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=20))
```

**Coletar:** Tabela com top 20 operações por tempo de CUDA.

**Por que importa:** Identifica exatamente onde o tempo está sendo gasto: comunicação (all-gather), computação (matmul), I/O (data loading). Esse é o "raio-X" do treinamento.

**Nota:** Esse passo é opcional — se for difícil executar, pule. Os passos anteriores já dão informação suficiente.

---

## Bloco 6 — Versões das Bibliotecas

### Passo 6.1 — Versões instaladas

```bash
pip list | grep -iE "torch|transformers|accelerate|peft|trl|datasets|flash"
```

**Coletar:** Saída inteira.

**Por que importa:** Versões antigas podem ter bugs conhecidos com FSDP. Versões muito recentes podem ter incompatibilidades. Confirma se está dentro das faixas recomendadas.

---

### Passo 6.2 — Verificar se flash-attn está instalado

```bash
python -c "import flash_attn; print(flash_attn.__version__)"
```

**Coletar:** Versão se instalado, ou erro se não.

**Por que importa:** Se já estiver instalado, basta mudar uma linha de configuração para ativar. Se não, precisa de instalação (que requer compilação CUDA).

---

## Bloco 7 — Sistema Operacional e Recursos

### Passo 7.1 — Sistema operacional e versão

```bash
uname -a
cat /etc/os-release
```

**Coletar:** Saída completa.

---

### Passo 7.2 — RAM total e em uso

```bash
free -h
```

**Coletar:** Saída completa.

**Por que importa:** Confirma os 880GB de RAM. Se houver outros processos consumindo RAM, pode afetar `fsdp_cpu_ram_efficient_loading`.

---

### Passo 7.3 — Disco onde os checkpoints são salvos

```bash
df -h
# E no diretório de output do treinamento:
ls -lh output_dir/
```

**Coletar:** Espaço disponível, e tipo de disco (HDD vs. SSD vs. NVMe se conhecido).

**Por que importa:** Salvamento de checkpoints em FSDP pode ser lento se for HDD. Para Llama 70B, cada checkpoint sharded ocupa 35GB+, e é salvo a cada `save_steps`.

---

## Resumo dos Itens a Coletar

Para revisão rápida na quinta-feira:

| # | Bloco | Item | Comando-chave |
|---|-------|------|---------------|
| 1.1 | Hardware | Modelo exato da GPU | `nvidia-smi --query-gpu=name --format=csv` |
| 1.2 | Hardware | Driver e CUDA | `nvidia-smi`, `nvcc --version` |
| 1.3 | Hardware | Topologia GPUs | `nvidia-smi topo -m` |
| 1.4 | Hardware | Memória GPU | `nvidia-smi --query-gpu=memory.total,memory.used` |
| 1.5 | Hardware | Versão PCIe | `sudo lspci -vv` ou `nvidia-smi -q` |
| 2.1 | Config FSDP | YAML do accelerate | `cat ~/.cache/huggingface/accelerate/default_config.yaml` |
| 2.2 | Config FSDP | Comando de lançamento | `history`, scripts `.sh` |
| 3.1 | Script | TrainingArguments | Abrir `train.py` |
| 3.2 | Script | LoraConfig | Abrir `train.py` |
| 3.3 | Script | from_pretrained | Abrir `train.py` |
| 3.4 | Script | fsdp_auto_wrap_policy | Abrir `train.py` |
| 4.1 | Dados | Estatísticas tokens | Snippet Python |
| 4.2 | Dados | Data collator | Abrir `train.py` |
| 5.1 | Métricas | Tempo por step | Logs de treinamento |
| 5.2 | Métricas | nvidia-smi durante exec. | `nvidia-smi` durante run |
| 5.3 | Métricas | Profiling (opcional) | `torch.profiler` |
| 6.1 | Versões | pip list bibliotecas | `pip list \| grep ...` |
| 6.2 | Versões | flash-attn instalado? | `python -c "import flash_attn"` |
| 7.1 | Sistema | OS e versão | `uname -a` |
| 7.2 | Sistema | RAM total | `free -h` |
| 7.3 | Sistema | Disco | `df -h` |

---

## Como Compartilhar os Resultados

Sugiro criar um arquivo `diagnostico.md` ou `diagnostico.txt` com a estrutura:

```
# Bloco 1 - Hardware

## 1.1 - Modelo da GPU
[colar saída]

## 1.2 - Driver e CUDA
[colar saída]

(... e assim por diante)
```

Isso facilita revisar tudo de forma estruturada.

---

## Suspeitas Principais Antes da Verificação

Para você já ir com os olhos abertos para os pontos críticos:

**Suspeito #1 (mais provável):** `fsdp_offload_params: true` no YAML do accelerate. Causa de slowdown de ~10–30×.

**Suspeito #2:** `attn_implementation="sdpa"` em vez de `"flash_attention_2"`. Causa ~20–30% de slowdown adicional.

**Suspeito #3:** `padding="max_length"` (padding fixo até 3072) em vez de dynamic padding. Causa ~30–50% de computação desperdiçada.

**Suspeito #4:** `logging_steps=1` causando sincronizações desnecessárias.

**Suspeito #5:** Ausência do snippet `fsdp_auto_wrap_policy` que faz LoRA funcionar corretamente com FSDP.

**Suspeito #6:** Interconnect via PCIe sem NVLink, causando overhead nos all-gathers do FSDP.

A combinação dos suspeitos #1, #3 e #5 sozinha pode explicar os 25 min/step. Após corrigir todos, a expectativa razoável é cair para 30–60 segundos/step, totalizando 17–35 horas em vez dos 35 dias projetados atualmente.

---

## Após Coletar os Dados

Quando voltar com as informações, vou poder:

1. Diagnosticar a causa raiz exata do gargalo de 25 min/step
2. Fornecer estimativa precisa do tempo de treinamento atual e otimizado
3. Listar correções em ordem de impacto, com a configuração exata para cada uma
4. Discutir o trade-off de reduzir epochs (2→1) com base nas estatísticas reais do dataset
5. Avaliar se há configurações alternativas (DeepSpeed ZeRO-3 vs FSDP) que possam ser melhores no seu hardware específico
