Perfeito! Vamos fazer uma **auditoria completa** do seu Ubuntu 22.04 antes de instalar o Pyenv. Isso garante que não haverá conflitos com pacotes existentes, outras linguagens ou a arquitetura do sistema.

---

## **FASE 1: AUDITORIA RIGOROSA DO AMBIENTE**

### **Passo 1: Verificar arquitetura e versão do sistema**
```bash
uname -m                    # Deve retornar x86_64 (64-bit) ou aarch64 (ARM 64-bit)
lsb_release -a              # Confirma Ubuntu 22.04 LTS (Jammy)
```
✅ **Esperado:** `x86_64` ou `aarch64`. Pyenv funciona em ambas.

---

### **Passo 2: Verificar se há conflitos com Python existente**
```bash
which python3               # Onde está o Python do sistema?
python3 --version           # Qual versão?
which python                # Existe link simbólico para python?
ls -la /usr/bin/python*     # Lista todos os Pythons do sistema
```
✅ **Esperado:** Python do sistema em `/usr/bin/python3` (versão 3.10 no Ubuntu 22.04).  
⚠️ **Atenção:** Se houver um `python` (sem o 3) apontando para outra versão, anote. O Pyenv não sobrescreve o Python do sistema, mas é bom saber.

---

### **Passo 3: Verificar se há outras instalações de Python**
```bash
ls -la /usr/local/bin/python* 2>/dev/null   # Python compilado manualmente?
ls -la /opt/python* 2>/dev/null             # Python em /opt?
find / -name "python3*" -type f 2>/dev/null | head -20  # Busca global (pode demorar)
```
✅ **Esperado:** Apenas `/usr/bin/python3*`. Se houver outros, podem conflitar com o Pyenv.

---

### **Passo 4: Verificar variáveis de ambiente críticas**
```bash
echo $PATH | tr ':' '\n'    # Mostra o PATH linha por linha
echo $PYTHONPATH            # Deve estar vazio ou não existir
echo $VIRTUAL_ENV           # Deve estar vazio (fora de um venv)
```
✅ **Esperado:**  
- `PATH` começando com `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`  
- `PYTHONPATH` vazio (ou inexistente)  
- `VIRTUAL_ENV` vazio  

⚠️ **Se `PYTHONPATH` estiver definido:** pode causar conflitos com o Pyenv. Anote o valor para investigar depois.

---

### **Passo 5: Verificar pacotes de desenvolvimento essenciais**
```bash
dpkg -l | grep -E "build-essential|libssl-dev|zlib1g-dev|libbz2-dev|libreadline-dev|libsqlite3-dev|libncursesw5-dev|libffi-dev|liblzma-dev|libxml2-dev|libxmlsec1-dev|tk-dev|xz-utils|llvm|wget|curl"
```
✅ **Esperado:** Todos os pacotes listados com `ii` (instalados).  
❌ **Se faltar algum:** anote quais estão ausentes.

---

### **Passo 6: Verificar conflitos com outras linguagens/ferramentas**
```bash
which rbenv nodenv nvm go rustup 2>/dev/null   # Outros gerenciadores de versão?
ls -la ~/.pyenv 2>/dev/null                      # Pyenv já existe?
ls -la ~/.local/bin 2>/dev/null | head -10       # Binários locais
```
✅ **Esperado:** Nenhum conflito direto, mas é bom saber se há outros gerenciadores.

---

### **Passo 7: Verificar espaço em disco e permissões**
```bash
df -h ~                      # Espaço disponível no home (mínimo 2GB recomendado)
whoami                       # Deve ser seu usuário (não root)
groups                       # Verifica se está no grupo sudo
```
✅ **Esperado:** Pelo menos 2GB livres, usuário comum com permissão `sudo`.

---

### **Passo 8: Verificar shell e arquivos de configuração**
```bash
echo $SHELL                  # Qual shell está usando? (bash ou zsh)
ls -la ~/.bashrc ~/.zshrc 2>/dev/null   # Arquivos de configuração existem?
grep -E "pyenv|PYTHON" ~/.bashrc ~/.zshrc 2>/dev/null   # Já há configuração de Pyenv?
```
✅ **Esperado:** Shell padrão (`/bin/bash`), arquivos de configuração existem, **sem** linhas de Pyenv antigas.

---

## **FASE 2: CORREÇÃO DE PROBLEMAS (SE HOUVER)**

Se alguma verificação acima falhou, corrija **antes** de prosseguir:

| Problema | Solução |
|----------|---------|
| `PYTHONPATH` definido | `unset PYTHONPATH` e remover do `~/.bashrc`/`~/.zshrc` |
| Outros Pythons em `/usr/local` | Renomear ou remover (cuidado!) |
| Pacotes faltando | `sudo apt install -y <pacotes_faltantes>` |
| Pouco espaço | Liberar espaço ou usar outra partição |

---

## **FASE 3: INSTALAÇÃO DO PYENV (APÓS AUDITORIA LIMPA)**

Agora sim, vamos instalar o Pyenv com segurança.

### **Passo 1: Instalar dependências (se faltarem)**
```bash
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

### **Passo 2: Baixar e instalar o Pyenv**
```bash
curl https://pyenv.run | bash
```
Isso instala em `~/.pyenv` (não afeta o sistema).

### **Passo 3: Configurar o shell**
Adicione ao final do `~/.bashrc` (ou `~/.zshrc`):
```bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

### **Passo 4: Recarregar o shell**
```bash
exec "$SHELL"  # Reinicia o shell sem precisar fazer logout
```

### **Passo 5: Verificar instalação**
```bash
pyenv --version              # Deve mostrar a versão instalada
pyenv install --list         # Lista versões disponíveis
```

---

## **FASE 4: CRIAR O AMBIENTE VIRTUAL DO PROJETO**

### **Passo 1: Instalar a versão necessária**
```bash
pyenv install 3.11.8  # Substitua pela versão 'y' do seu projeto
```

### **Passo 2: Criar o venv na pasta do projeto**
```bash
cd /caminho/do/seu/projeto
pyenv local 3.11.8
python -m venv venv
```

### **Passo 3: Ativar e usar**
```bash
source venv/bin/activate
python --version  # Deve mostrar 3.11.8
```

---

## **CHECKLIST FINAL DE SEGURANÇA**
- [ ] Arquitetura é `x86_64` ou `aarch64`
- [ ] Python do sistema intacto em `/usr/bin/python3`
- [ ] `PYTHONPATH` está vazio
- [ ] Não há outros Pythons em `/usr/local` ou `/opt`
- [ ] Todos os pacotes de desenvolvimento instalados
- [ ] Pelo menos 2GB de espaço livre
- [ ] Pyenv instalado em `~/.pyenv` (não no sistema)
- [ ] Shell recarregado e `pyenv --version` funciona

Se **todos** os itens estiverem OK, seu ambiente está 100% seguro para usar o Pyenv sem conflitos!

Quer que eu detalhe algum passo específico da auditoria?
