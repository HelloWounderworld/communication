---
title: "Protocolo de Auditoria e Hardening — v2 (revisão crítica + reescrita)"
escopo: "Host Linux local ou on-prem acessado por SSH/túnel; venv Python; Docker; VMs; serviços de ML"
status: vivo
versao: "2.0"
data: 2026-10-23
---

# Protocolo de Auditoria e Hardening — v2

> **Veredito sobre a v1, em uma frase.** A v1 é um bom checklist de *higiene de container*, mas não é um protocolo contra o ataque que você declarou querer mitigar. Você quer barrar **invasores entrando na máquina via SSH ou via um túnel/funil**; a v1 não menciona SSH, firewall, portas expostas, túneis, patching do host, usuários, persistência, logs nem recuperação. Ela protege o segundo andar e deixa a porta da frente sem tranca.

**Como ler.** Parte A audita a v1 (o que está errado, o que está fraco, o que falta). Parte B é o protocolo reescrito, organizado pela ordem em que um invasor encontra a sua máquina. Parte C é o script de auditoria somente-leitura. Parte D lista o que preciso saber de você para calibrar.

**Regra de uso (Mandamento 0 da sua Carta, aplicado a segurança):** a dose é proporcional à exposição. Um laptop sem portas de entrada não precisa de Falco; um servidor com SSH aberto à internet precisa de quase tudo abaixo. A Parte B.0 define os tiers.

**Ressalva de contexto profissional.** Se a máquina for do laboratório ou da empresa, a política de TI corporativa prevalece sobre este protocolo. Não rode varreduras (nmap, scanners) contra redes ou hosts que não são seus, ou sem autorização por escrito. Em rede corporativa isso pode disparar o SOC e configurar violação de política.

---

# PARTE A — Auditoria crítica da v1

## A.1 Defeitos fatais (invalidam a v1 como protocolo para o seu objetivo)

**F1. Não há modelo de ameaça.** Um protocolo começa por *quem ataca, por onde entra, o que quer*. Sem isso, não há como decidir o que priorizar, e a v1 acaba priorizando o que é fácil de checar (CVE em pacote) em vez do que é provável de ser explorado (SSH com senha, porta esquecida em `0.0.0.0`, Jupyter exposto, túnel sem autenticação).

**F2. A superfície de entrada declarada (SSH + funil) está ausente.** Nenhum item sobre `sshd_config`, chaves, força bruta, `authorized_keys` como vetor de persistência, firewall, portas em escuta, ou túneis (ngrok, cloudflared, `ssh -R`). Esse é o perímetro real do seu cenário.

**F3. Um erro operacional que anula o firewall: Docker publica portas por cima do UFW.** Ao rodar `-p 8080:80`, o Docker escreve regras próprias no iptables/nftables e a porta fica acessível em **todas** as interfaces, ignorando o que o `ufw status` diz. É uma das causas mais comuns de "eu tinha firewall e mesmo assim estava exposto". A v1 não menciona nada disso. Correção: publicar em `127.0.0.1:8080:80`, ou definir `"ip": "127.0.0.1"` no `daemon.json`, ou filtrar na chain `DOCKER-USER`. E **verificar de fora** com um scan a partir de outra máquina.

**F4. "Grupo docker = root" não aparece.** Qualquer usuário no grupo `docker` consegue rodar `docker run -v /:/host ...` e virar root no host. A v1 alerta sobre montar `docker.sock` dentro de container (correto), mas não sobre o equivalente no host. Também falta checar se o daemon está ouvindo em TCP (`2375` sem TLS = RCE remoto não autenticado, explorado em massa por mineradores).

**F5. Não há recuperação.** Nenhum item sobre backup, restauração testada ou o que fazer quando a detecção dispara. Um protocolo que só previne assume prevenção perfeita, e prevenção perfeita não existe.

**F6. A conclusão afirma uma garantia que não existe.** "A aplicação rigorosa deste protocolo **garante** que..." é falso. Container compartilha o kernel do host; uma CVE de kernel não corrigida permite escape mesmo com todo o hardening de container. Defesa em profundidade *reduz probabilidade e raio de impacto*; não garante. Para código realmente não confiável, a fronteira certa é VM ou sandbox de kernel (gVisor, Kata), não container.

## A.2 Erros técnicos pontuais

| Item da v1 | Problema | Correção |
|---|---|---|
| Fase 1 trata o `venv` como objeto de segurança | `venv` **não é fronteira de segurança**: todo pacote roda com os privilégios do seu usuário. O risco real é a **cadeia de suprimentos** (pacote malicioso, typosquatting, dependency confusion, código executado na instalação de sdist, arquivos `.pth` executados em todo startup do Python) | Fase de Python reescrita em torno de supply chain: lock com hashes, índice fixado, varredura de `.pth`, `pip-audit` |
| "`pyvenv.cfg` adulterado para redirecionar site-packages" | A chave relevante é `include-system-site-packages`, e `home` aponta para o interpretador base. O `python` do venv é normalmente um **symlink** para o interpretador do sistema, então "integridade do binário" é a integridade do Python do sistema (responsabilidade do gerenciador de pacotes do OS) | Checar `include-system-site-packages = false` e para onde `home` aponta |
| `.env` "dentro do diretório virtual" | `.env` vive na raiz do projeto, não no venv. O vazamento real é outro: `.env` entrando no **git** ou na **imagem Docker** via `COPY . .` sem `.dockerignore` | `.gitignore` + `.dockerignore` + permissão `600` + `gitleaks` no histórico |
| `detect-secrets` para "histórico de comandos" | `detect-secrets` varre arquivos, não o histórico do shell. E não varre o **histórico do git**, onde segredos removidos continuam vivos | `gitleaks` (varre histórico git); para o shell, `grep` em `~/.bash_history`/`~/.zsh_history` |
| `docker exec -it <c> whoami` | Falha em imagens distroless/scratch (não existe `whoami`); `-it` quebra em script sem TTY. E o teste está incompleto: usuário não-root no container **sem userns-remap** é o mesmo UID no host | `docker inspect --format '{{.Config.User}}'` e `docker top <c> -eo uid,user,pid,args` (visão do host) |
| `docker inspect ... \| grep -i mounts -C 5` | Frágil (depende do layout do JSON) | `docker inspect --format '{{range .Mounts}}{{.Source}}->{{.Destination}} rw={{.RW}} {{end}}'` |
| Limites de `--memory` e `--cpus` contra DoS | Não impedem **fork bomb** nem esgotamento de disco por log | Adicionar `--pids-limit` e rotação de log (`log-opts max-size/max-file`) |
| Remover `CAP_SYS_ADMIN` | Ela **não está** no conjunto padrão; só aparece com `--privileged` ou `--cap-add`. O que precisa ser auditado é justamente `--privileged`, `--cap-add`, `--pid=host`, `--network=host` | Auditoria explícita dessas flags |
| Trivy como ferramenta recomendada sem ressalva | Em março de 2026 o ecossistema Trivy (binários, imagens no Docker Hub, GitHub Actions) foi comprometido por roubo de credenciais (CVE-2026-33634). Ferramenta de segurança também é dependência | Fixar versão por **digest/SHA**, nunca por tag; verificar assinatura/proveniência; ter Grype como segunda opinião |
| `Safety` em pé de igualdade com `pip-audit` | O Safety CLI atual exige conta e tem licenciamento comercial; confirme os termos antes de adotar | `pip-audit` (PyPA, base OSV) cobre o caso |
| "falha no PHP" na conclusão | Resíduo de outro contexto; o protocolo não trata PHP | Remover |

## A.3 O que a v1 acerta (e fica na v2)

Usuário não-root no container; não montar `docker.sock` nem `/`; `--cap-drop=ALL`; limites de recursos; Hadolint/Checkov para Dockerfile; scanner de imagem; Falco como detecção em tempo de execução (no tier certo).

---

# PARTE B — O protocolo v2

## B.0 Modelo de ameaça e tiers de calibração

**Adversários realistas, por probabilidade:**

1. **Bots oportunistas** varrendo a internet inteira: força bruta em SSH, Docker API em `2375`, Jupyter/Ollama/Ray/MLflow sem autenticação, Redis/Postgres expostos. É de longe a ameaça mais frequente, e é totalmente automatizada.
2. **Cadeia de suprimentos**: pacote PyPI/npm malicioso, imagem Docker adulterada, ferramenta de CI comprometida, modelo `.pt`/pickle com código embutido, `trust_remote_code=True`.
3. **Credencial vazada**: chave SSH sem passphrase copiada de um laptop, token em repositório, `.env` dentro de imagem.
4. **Atacante direcionado**: improvável para uso pessoal; relevante se o servidor guarda dados de terceiros ou acesso corporativo.

**Tiers (escolha o seu antes de aplicar):**

| Tier | Situação | Aplica |
|---|---|---|
| **T0** | Máquina pessoal sem nenhuma porta de entrada exposta | B.1 (parcial), B.3, B.4 essencial, B.7, B.9 |
| **T1** | Servidor on-prem com SSH acessível só pela LAN ou por VPN | T0 + B.2 completo + B.5 + B.8 + logs |
| **T2** | Qualquer serviço alcançável pela internet (porta aberta, port-forward no roteador, túnel) **ou** servidor multiusuário | Tudo, incluindo detecção em tempo de execução (Falco/auditd) e logs fora do host |

**Princípio que organiza tudo:** *o que não está exposto não precisa ser defendido na borda.* A melhor ação de segurança é quase sempre reduzir a superfície (fechar porta, bind em localhost, VPN no lugar de SSH aberto), não endurecer o que está exposto.

**Disciplina de verificação (a sua previsão-antes-de-rodar):** antes de cada checagem, escreva o resultado que você espera ("só a porta 22 deve responder de fora"). Depois rode. A divergência é o achado. O scan **externo** é o oráculo: o que o host acredita sobre si mesmo não é evidência.

---

## B.1 Inventário e superfície (sempre primeiro)

**Objetivo:** saber o que está escutando, para quem, e quem pode logar.

```bash
# Portas em escuta e processo dono. 0.0.0.0 / [::] = exposto em todas as interfaces.
sudo ss -tulpn

# Contas com UID 0 (deve haver só root)
awk -F: '$3 == 0 {print $1}' /etc/passwd

# Quem tem sudo e quem está no grupo docker (ambos = root efetivo)
getent group sudo wheel docker

# Contas com shell de login
grep -Ev '(nologin|false)$' /etc/passwd
```

**Critério de aprovação:** cada porta em escuta tem dono conhecido e justificativa; nada em `0.0.0.0` que deveria estar em `127.0.0.1`; o grupo `docker` contém só quem você aceitaria dar root.

---

## B.2 SSH (a porta da frente)

**Primeiro, a decisão estrutural:** o SSH precisa estar alcançável pela internet? Na maioria dos casos, não. Coloque-o atrás de **WireGuard ou Tailscale** e feche a porta 22 para o mundo. Isso elimina a ameaça 1 inteira para o SSH, e vale mais que todos os ajustes abaixo somados.

**Configuração efetiva** (use `sshd -T`, que resolve os `Include` de `/etc/ssh/sshd_config.d/`; em Ubuntu com cloud-init, um drop-in como `50-cloud-init.conf` pode reativar `PasswordAuthentication yes` sem você ver no arquivo principal):

```bash
sudo sshd -T | grep -Ei '^(permitrootlogin|passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication|permitemptypasswords|maxauthtries|x11forwarding|allowtcpforwarding|gatewayports|allowagentforwarding|allowusers|allowgroups)'
```

| Diretiva | Valor alvo | Por quê |
|---|---|---|
| `PermitRootLogin` | `no` | Força login nomeado + sudo (rastreável) |
| `PasswordAuthentication` | `no` | Elimina força bruta como classe de ataque |
| `KbdInteractiveAuthentication` | `no` | Fecha o caminho alternativo de senha via PAM |
| `PubkeyAuthentication` | `yes` | |
| `MaxAuthTries` | `3` | |
| `AllowUsers` | só os usuários necessários | Lista branca |
| `X11Forwarding` | `no` | |
| `AllowTcpForwarding` | `no` (ou `local` se você usa `ssh -L` para Jupyter) | Impede o servidor de virar pivô |
| `GatewayPorts` | `no` | Impede que um `ssh -R` publique portas para a rede |
| `AllowAgentForwarding` | `no` | Ver lado cliente abaixo |

Depois de editar: `sudo sshd -t` (valida a sintaxe) **antes** de recarregar, e mantenha uma sessão aberta enquanto testa a nova, para não se trancar fora.

**Chaves:**
- `ed25519` com passphrase, ou `ed25519-sk` (chave física FIDO2) se você tiver uma YubiKey. A chave física tira a chave privada de dentro do disco.
- **Auditar `authorized_keys` de todos os usuários.** Uma linha a mais ali é o mecanismo de persistência número 1 depois de uma invasão:
  ```bash
  sudo find / -xdev -name authorized_keys -exec ls -l {} \; -exec cat {} \; 2>/dev/null
  ```
- Permissões: `~/.ssh` em `700`, `authorized_keys` em `600`.

**Lado cliente (o seu laptop também é superfície):**
- `ForwardAgent no` por padrão no `~/.ssh/config`. Com agent forwarding, root no servidor consegue usar suas chaves para pular para outros hosts. Para saltar entre máquinas, use `ProxyJump`.
- Verifique a fingerprint do host na primeira conexão (o modelo é "confiar no primeiro uso").

**Força bruta e logs:**
```bash
# Ubuntu/Debian: unit "ssh"; RHEL/Fedora: "sshd"
sudo journalctl -u ssh --since "7 days ago" | grep -E 'Failed|Invalid user|Accepted' | tail -50
last -a | head -20      # logins bem-sucedidos
sudo lastb | head -20   # tentativas falhas
```
Com senha desativada, `fail2ban`/`sshguard` vira redução de ruído, não proteção essencial. No T2 instale mesmo assim.

---

## B.3 Rede, firewall e túneis ("o funil")

**Firewall com política padrão de negação de entrada:**
```bash
sudo ufw status verbose        # ou: sudo nft list ruleset
```
Alvo: `Default: deny (incoming)`; liberar só o necessário, e de preferência só a partir da sub-rede da VPN/LAN.

**A armadilha do Docker (F3):**
```bash
docker ps --format '{{.Names}}\t{{.Ports}}'
# Qualquer "0.0.0.0:XXXX->" está exposto, independentemente do que o ufw diz.
```
Correções, em ordem de preferência:
1. Publicar só em loopback: `-p 127.0.0.1:8080:80`.
2. Padrão global em `/etc/docker/daemon.json`: `{ "ip": "127.0.0.1" }`.
3. Regras na chain `DOCKER-USER` (para quem precisa expor de forma controlada).

**Verificação externa (obrigatória no T1/T2), a partir de outra máquina sua:**
```bash
nmap -Pn -p- <ip-do-servidor>          # pela LAN
# e, se houver exposição à internet, a partir de uma rede externa (ex.: hotspot do celular)
```

**Túneis.** Todo túnel é uma porta pública que o firewall não vê.
```bash
ps aux | grep -Ei 'ngrok|cloudflared|frpc|tailscale|ssh .*-R' | grep -v grep
systemctl list-units --type=service | grep -Ei 'ngrok|cloudflared|frp'
```
Regras:
- Inventarie cada túnel: o que expõe, para quem, com qual autenticação.
- Túnel **sem camada de autenticação na borda** (Cloudflare Access, OAuth no proxy, autenticação mútua) só serve para serviço que já tem autenticação própria forte.
- Prefira acesso por VPN (WireGuard/Tailscale) a túnel público.
- `ssh -R` só funciona como porta pública se `GatewayPorts` permitir (B.2).

---

## B.4 Host: patching, persistência e integridade

**Atualizações:**
```bash
# Debian/Ubuntu
sudo apt update && apt list --upgradable
ls /var/run/reboot-required 2>/dev/null && echo "REBOOT PENDENTE"
```
- Ative `unattended-upgrades` para atualizações de segurança.
- **Kernel atualizado mas não reiniciado continua vulnerável.** Isso importa duplamente com Docker, porque o kernel é a fronteira dos containers.

**Pontos de persistência (onde um invasor se instala para sobreviver a reboot):**
```bash
sudo ls -la /etc/cron.* /var/spool/cron/crontabs 2>/dev/null
crontab -l 2>/dev/null; sudo crontab -l 2>/dev/null
systemctl list-timers --all
systemctl list-unit-files --state=enabled
ls -la /etc/systemd/system/ ~/.config/systemd/user/ 2>/dev/null
# arquivos de inicialização do shell modificados recentemente
ls -la --time-style=long-iso ~/.bashrc ~/.profile ~/.zshrc 2>/dev/null
# binários SUID: salve como baseline e compare depois
sudo find / -xdev -perm -4000 -type f 2>/dev/null | sort > suid_$(date +%F).txt
```
O valor dessas checagens vem do **diff contra uma baseline** registrada com a máquina limpa. Sem baseline, você não distingue o legítimo do implantado.

**Auditoria geral:** `sudo lynis audit system` dá uma varredura ampla com pontuação e sugestões. Use como lista de pendências, não como nota a maximizar.

**Integridade de arquivos (T2):** AIDE para detectar alteração em binários e configs do sistema.

---

## B.5 Python e cadeia de suprimentos

**Premissa:** o `venv` isola versões, não privilégios. Instalar um pacote é executar código de terceiros com o seu usuário, e às vezes já no momento da instalação.

**1. Lock com hashes (o controle de maior alavancagem):**
```bash
# com uv
uv pip compile requirements.in --generate-hashes -o requirements.txt
# com pip-tools
pip-compile --generate-hashes requirements.in
# instalação recusa qualquer artefato cujo hash não bata
pip install --require-hashes -r requirements.txt
```
Hash pinning impede que uma versão republicada ou adulterada entre em silêncio. Não impede uma versão maliciosa que você mesmo fixou, e é por isso que a varredura (item 4) e a cautela com atualizações continuam necessárias.

**2. Índice de pacotes:**
- Nunca use `--extra-index-url` misturando índice privado e PyPI: o pip escolhe a maior versão entre os índices, e isso é exatamente o mecanismo da **dependency confusion**. Se precisar de índice privado, use um proxy único que resolva os dois.
- `--only-binary :all:` quando possível, para evitar executar `setup.py` de sdist.
- Confira o nome antes de instalar (typosquatting: `reqeusts`, `python-dateutils`...).

**3. Arquivos `.pth` (vetor pouco conhecido).** Linhas que começam com `import` dentro de um `.pth` em `site-packages` são executadas **em todo startup do Python**:
```bash
SP=$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
grep -l '^import' "$SP"/*.pth 2>/dev/null
```
Existem `.pth` legítimos (instalações editáveis, `distutils-precedence.pth` do setuptools). Registre a baseline e investigue o que surgir de novo.

**4. Vulnerabilidades conhecidas:**
```bash
pip-audit -r requirements.txt     # ou, dentro do venv ativo: pip-audit
```

**5. Configuração do venv:**
```bash
cat .venv/pyvenv.cfg                         # include-system-site-packages = false
find .venv -perm -o+w -print | head          # nada world-writable
```

**6. Segredos:**
- `.env` com permissão `600`, listado no `.gitignore` **e** no `.dockerignore`.
- Varredura do histórico git: `gitleaks git .` (v8.19+; versões anteriores usam `gitleaks detect`). Segredo que já foi commitado está comprometido: **rotacione**, reescrever o histórico não basta.
- Histórico do shell: `grep -Ei 'token|secret|password|api[_-]?key' ~/.bash_history ~/.zsh_history 2>/dev/null`. Use `HISTCONTROL=ignorespace` e prefixe com espaço comandos que levam segredo.

**7. Artefatos de ML (risco específico do seu domínio):**
- Checkpoints em pickle (`.pt`, `.pkl`, `.joblib`) **executam código ao carregar**. Use `torch.load(..., weights_only=True)` (padrão a partir do PyTorch 2.6) e prefira `safetensors`.
- `trust_remote_code=True` no Hugging Face executa o Python do repositório do modelo. Só use com repositório que você auditou, e fixe o `revision` em um commit específico.

---

## B.6 Docker

### B.6.1 Daemon (nível host)

```bash
# Daemon ouvindo em TCP? 2375 sem TLS = RCE remoto não autenticado.
sudo ss -tlnp | grep -E ':(2375|2376)\b'
cat /etc/docker/daemon.json 2>/dev/null
systemctl cat docker | grep -E 'ExecStart|-H '

# Mecanismos de segurança ativos (seccomp, apparmor, rootless, userns)
docker info --format '{{.SecurityOptions}}'

# Quem é root efetivo via docker
getent group docker
```

Endurecimento do daemon, em ordem de alavancagem:
1. **Docker rootless**, ou `userns-remap` no `daemon.json`. Com isso, root dentro do container deixa de ser root no host. É o controle que transforma o "nunca rode como root" de regra frágil em fronteira real.
2. `daemon.json` mínimo:
   ```json
   {
     "ip": "127.0.0.1",
     "no-new-privileges": true,
     "live-restore": true,
     "log-driver": "json-file",
     "log-opts": { "max-size": "10m", "max-file": "3" }
   }
   ```
   (`userns-remap` exige migrar volumes existentes; ative com planejamento.)
3. Grupo `docker` restrito ao mínimo de usuários.
4. Benchmark CIS automatizado: `docker-bench-security`.

### B.6.2 Containers em execução (auditoria em lote)

```bash
docker ps -q | xargs -r docker inspect --format \
'{{.Name}} user="{{.Config.User}}" privileged={{.HostConfig.Privileged}} net={{.HostConfig.NetworkMode}} pid={{.HostConfig.PidMode}} capadd={{.HostConfig.CapAdd}} capdrop={{.HostConfig.CapDrop}} ro={{.HostConfig.ReadonlyRootfs}} secopt={{.HostConfig.SecurityOpt}} mem={{.HostConfig.Memory}} pids={{.HostConfig.PidsLimit}}'

# Montagens
docker ps -q | xargs -r docker inspect --format \
'{{.Name}}{{range .Mounts}} {{.Source}}->{{.Destination}}(rw={{.RW}}){{end}}'

# Segredos em variáveis de ambiente (visíveis para qualquer um com acesso ao docker)
docker ps -q | xargs -r docker inspect --format '{{.Name}} {{.Config.Env}}'

# UID real dos processos, vistos do host
docker top <container> -eo uid,user,pid,args
```

**Critérios de reprovação imediata:** `privileged=true`; `net=host` ou `pid=host` sem justificativa escrita; montagem de `/`, `/etc`, `/root`, `/var/run/docker.sock` ou do `$HOME`; `user=""` (root); porta publicada em `0.0.0.0`; segredo em `Env`.

### B.6.3 Modelo de execução endurecido

```bash
docker run -d --name app \
  --user 10001:10001 \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop=ALL \
  --security-opt no-new-privileges:true \
  --pids-limit 256 --memory 512m --cpus 1.0 \
  -p 127.0.0.1:8080:8080 \
  minha-imagem@sha256:<digest>
```
- UID alto (`10001`) que **não existe no host**: sem userns-remap, um UID de container colide com o do usuário de mesmo número no host, e o `1000` costuma ser você.
- `--read-only` + `tmpfs` impede que um invasor grave ferramentas no sistema de arquivos do container.
- Só adicione capabilities de volta (`--cap-add NET_BIND_SERVICE`, por exemplo) quando a aplicação falhar sem ela, e documente o motivo.
- Containers com GPU (`--gpus all`) funcionam com usuário não-root; o runtime da NVIDIA amplia a superfície do host, então mantenha o driver e o NVIDIA Container Toolkit atualizados.
- Segredos: montar como arquivo (Docker secrets, ou bind somente-leitura de um arquivo `600`), nunca via `-e`.

### B.6.4 Imagens e build

- **Base mínima** (`python:3.x-slim`, distroless): menos pacotes, menos CVEs, menos ferramentas para o invasor.
- **Fixar a base por digest** (`FROM python:3.12-slim@sha256:...`), não por tag mutável.
- Multi-stage build: compilador e ferramentas de build não vão para a imagem final.
- `.dockerignore` com `.env`, `.git`, `*.pem`, `id_*`, checkpoints grandes.
- Lint do Dockerfile: `hadolint Dockerfile`.
- Scan de vulnerabilidades: Trivy **ou** Grype. Depois do comprometimento de março de 2026, trate o próprio scanner como dependência: versão fixada por digest/SHA, nunca por tag, e checagem de assinatura quando disponível.
- Lembrete: scan encontra CVE conhecida; não encontra imagem maliciosa nova. A proveniência (de onde veio, quem assinou) é um controle separado.

### B.6.5 Limite da fronteira

Container não é sandbox para código não confiável. Para rodar código de terceiros que você não auditou (modelo com `trust_remote_code`, script baixado, agente executando código), use **gVisor** (`--runtime=runsc`), **Kata Containers** ou uma **VM descartável**.

---

## B.7 Serviços de ML expostos (o risco nº 1 do seu perfil)

Ferramentas de ML costumam vir **sem autenticação** por padrão, e bots varrem especificamente por elas.

| Serviço | Porta comum | Risco se exposto |
|---|---|---|
| Jupyter / JupyterLab | 8888 | Execução de código arbitrário (é um shell no navegador) |
| Ray Dashboard | 8265 | Submissão de jobs sem autenticação = RCE (campanha "ShadowRay") |
| Ollama | 11434 | API sem autenticação; abuso de GPU, troca de modelos |
| MLflow | 5000 | Sem autenticação por padrão; leitura e escrita de artefatos |
| TensorBoard | 6006 | Sem autenticação; vazamento de dados de experimentos |
| vLLM / servidores compatíveis com a API da OpenAI | 8000 | Sem `--api-key`, aberto a qualquer um |
| Gradio com `share=True` | link público | Expõe a aplicação na internet por um túnel |

**Padrão único de mitigação:** bind em `127.0.0.1` e acesso por túnel SSH local:
```bash
# no servidor
jupyter lab --ip 127.0.0.1 --port 8888
# no seu laptop
ssh -L 8888:127.0.0.1:8888 usuario@servidor
# e abra http://127.0.0.1:8888 localmente
```
Isso funciona com `AllowTcpForwarding local` e mantém a porta invisível para a rede.

---

## B.8 Máquinas virtuais

- A VM guest é um host completo: aplique B.1 a B.5 dentro dela.
- **Rede:** NAT isola a VM da LAN; *bridged* a coloca na LAN como mais uma máquina a defender. Escolha de propósito.
- Para análise de algo suspeito: pastas compartilhadas, clipboard compartilhado e arrastar-e-soltar **desligados**. São canais diretos para o host.
- Hypervisor e guest additions atualizados (escape de VM é raro, mas acontece, e quase sempre via drivers de dispositivos virtuais).
- **Snapshot não é backup**: fica no mesmo disco e no mesmo domínio de falha.

---

## B.9 Detecção, logs e resposta a incidente

**Logs:**
- `journald` persistente (`Storage=persistent` em `/etc/systemd/journald.conf`).
- No T2, envie logs para **fora do host**. A primeira ação de um invasor competente é apagar logs locais.
- T2: `auditd` para execução de comandos e alterações em arquivos sensíveis; Falco para comportamento anômalo em containers (shell interativo dentro de container, escrita em `/bin`, conexão de saída inesperada). Falco exige driver de kernel ou eBPF e afinamento de regras; num laptop T0 é custo sem retorno proporcional.

**Backups (o controle que salva você quando todos os outros falham):**
- Regra 3-2-1: três cópias, dois meios, **uma offline ou imutável** (ransomware cifra o que está montado).
- **Teste de restauração** periódico. Backup nunca restaurado é hipótese, não backup.

**Roteiro mínimo de resposta (escreva antes de precisar):**
1. **Isolar** da rede (cabo, Wi-Fi, regras de firewall). Não desligar ainda: a memória contém evidência.
2. **Preservar**: `ss -tupan`, `ps auxf`, `last`, cópia dos logs para mídia externa.
3. **Rotacionar credenciais a partir de uma máquina limpa**: chaves SSH, tokens, senhas, tudo que esteve na máquina.
4. **Reconstruir, não limpar.** Reinstalar a partir de mídia confiável e restaurar dados (não binários) do backup. Uma máquina comprometida com root não é confiável depois de "limpa".
5. Descobrir o vetor de entrada antes de religar à rede, ou ele será usado de novo.

---

## B.10 Cadência

| Frequência | O quê |
|---|---|
| A cada mudança (build/CI) | `hadolint`, `pip-audit`, scan de imagem, `gitleaks` |
| Semanal | Logs de SSH, `ss -tulpn` contra a baseline, atualizações pendentes, reboot pendente |
| Mensal | Script da Parte C completo, `lynis`, `docker-bench-security`, `nmap` externo, revisão de `authorized_keys` e do grupo `docker`, inventário de túneis |
| Trimestral | Teste de restauração de backup, rotação de chaves e tokens, revisão deste protocolo |

---

# PARTE C — Script de auditoria (somente leitura)

Não altera nada; só reporta. Rode com `sudo bash audit_host.sh | tee audit_$(date +%F).txt` e compare com a execução anterior (`diff`).

```bash
#!/usr/bin/env bash
# audit_host.sh — auditoria somente-leitura. Não modifica o sistema.
set -u
sec() { printf '\n===== %s =====\n' "$1"; }

sec "Sistema"
uname -a
[ -f /var/run/reboot-required ] && echo "!! REBOOT PENDENTE"

sec "Portas em escuta (0.0.0.0/[::] = exposto)"
ss -tulpn

sec "Contas UID 0"
awk -F: '$3==0{print $1}' /etc/passwd

sec "Grupos privilegiados"
getent group sudo wheel docker 2>/dev/null

sec "SSH: configuração efetiva"
sshd -T 2>/dev/null | grep -Ei '^(permitrootlogin|passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication|permitemptypasswords|maxauthtries|x11forwarding|allowtcpforwarding|gatewayports|allowagentforwarding|allowusers|allowgroups) '

sec "authorized_keys"
find / -xdev -name authorized_keys 2>/dev/null | while read -r f; do
  echo "--- $f ($(stat -c '%U %a' "$f"))"; cat "$f"
done

sec "Firewall"
(ufw status verbose 2>/dev/null) || (nft list ruleset 2>/dev/null | head -60)

sec "Túneis e processos de exposição"
ps aux | grep -Ei 'ngrok|cloudflared|frpc|tailscale|ssh .*-R' | grep -v grep

sec "Persistência: cron e timers"
ls -la /etc/cron.d /var/spool/cron/crontabs 2>/dev/null
systemctl list-timers --all --no-pager 2>/dev/null | head -30

sec "SUID (compare com a baseline)"
find / -xdev -perm -4000 -type f 2>/dev/null | sort

sec "Últimos logins / falhas"
last -a 2>/dev/null | head -15
lastb 2>/dev/null | head -15

if command -v docker >/dev/null 2>&1; then
  sec "Docker: daemon"
  ss -tlnp | grep -E ':(2375|2376)\b' && echo "!! DOCKER API EM TCP"
  docker info --format 'SecurityOptions={{.SecurityOptions}}' 2>/dev/null
  sec "Docker: portas publicadas"
  docker ps --format '{{.Names}}\t{{.Ports}}'
  sec "Docker: flags de risco"
  docker ps -q | xargs -r docker inspect --format \
  '{{.Name}} user="{{.Config.User}}" privileged={{.HostConfig.Privileged}} net={{.HostConfig.NetworkMode}} pid={{.HostConfig.PidMode}} capadd={{.HostConfig.CapAdd}} ro={{.HostConfig.ReadonlyRootfs}} pids={{.HostConfig.PidsLimit}} mem={{.HostConfig.Memory}}'
  sec "Docker: montagens"
  docker ps -q | xargs -r docker inspect --format \
  '{{.Name}}{{range .Mounts}} {{.Source}}->{{.Destination}}(rw={{.RW}}){{end}}'
fi

sec "Serviços de ML em portas típicas"
ss -tlnp | grep -E ':(8888|8265|11434|5000|6006|8000|7860)\b'
```

**Previsão antes de rodar:** anote, antes da primeira execução, quais portas você espera ver, quem deve estar no grupo `docker` e quantas linhas cada `authorized_keys` deve ter. A divergência entre a previsão e a saída é o seu primeiro achado.

---

# PARTE D — O que preciso saber para calibrar a próxima versão

1. **Quais máquinas**, e de quem: laptop pessoal, servidor pessoal em casa, servidor do laboratório? (Isso define o tier e se há política corporativa por cima.)
2. **Como o acesso remoto acontece hoje:** SSH com porta aberta no roteador? VPN? Qual "funil" exatamente: ngrok, cloudflared, Tailscale, port-forward, `ssh -R`?
3. **Distribuição e versão** (Ubuntu 24.04? Debian? Fedora?) e se o Docker é o Docker Engine nativo, Docker Desktop ou Podman.
4. **Quais serviços** rodam nessas máquinas (Jupyter, Ollama, MLflow, bancos de dados, apps web).
5. **Hypervisor** das VMs (VirtualBox, KVM/libvirt, VMware, WSL2) e para que as VMs servem.
6. Se existe hoje **algum backup**, e quando foi a última restauração testada.

Com isso, o próximo passo é transformar este documento em perfis por máquina (T0/T1/T2) e num script de *hardening* (que altera o sistema), separado deste de *auditoria*, com reversão documentada para cada mudança.
