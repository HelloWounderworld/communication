---
title: "Protocolo de Checagem de Vulnerabilidades Sistêmicas — Estações Locais (Ubuntu, Windows 10, Windows 11)"
caso_gatilho: "PHP2Shell — CVE-2026-109618 / CVE-2026-109619 (outubro de 2026)"
status: vivo
versao: "1.0"
data: 2026-10-23
complementa: ["Protocolo_Seguranca_v2.md", "Protocolo_Auditoria_OS_Ubuntu_Windows.md"]
scripts: ["inventario_php.sh", "Inventario-PHP.ps1"]
---

# Protocolo de Vulnerabilidades Sistêmicas — Estações Locais

> **O que é uma vulnerabilidade sistêmica.** Uma falha num componente tão difundido que ele está embutido em lugares que você não lembra de ter instalado: PHP, OpenSSL, log4j, xz, glibc. O dano não vem da gravidade da falha isolada, e sim de três fatores juntos: **onipresença** (milhões de hosts), **invisibilidade** (o componente vem dentro de outro software) e **velocidade de exploração** (bots varrendo a internet horas depois da divulgação). O PHP2Shell é um caso exemplar dos três.
>
> **A pergunta que este protocolo responde não é "estou vulnerável ao PHP2Shell?"**, e sim: *"quando a próxima falha desse tipo aparecer, eu consigo responder em horas, e não em semanas?"*. Isso exige três capacidades: **saber o que tenho** (inventário), **saber o que está exposto** (superfície) e **conseguir atualizar rápido** (latência de patch). O PHP2Shell é o exercício que testa as três agora.

---

# PARTE A — O caso PHP2Shell: fatos e leitura crítica

## A.1 O que se sabe (situação em 23/10/2026)

| Item | Fato |
|---|---|
| CVEs | **CVE-2026-109618** (corrupção quando a memória acaba no meio da preparação de uma requisição) e **CVE-2026-109619** (use-after-free: estado de uma requisição sobrevive e é usado pela seguinte no mesmo worker) |
| Impacto | Execução remota de código **sem autenticação**; o segundo CVE também permite vazamento de memória |
| Gravidade | CVSS v4.0 **9.2** nos dois. A nota 10.0 que circulou antes da divulgação estava errada |
| Quem é afetado | Toda instalação que **serve requisições web** com PHP: PHP-FPM, Apache `mod_php`, `php-cgi`, FrankenPHP, LiteSpeed. `mod_php` é o pior caso: a exploração acontece antes de qualquer código da aplicação rodar |
| Versões corrigidas | **8.5.12, 8.4.27, 8.3.36, 8.2.35** |
| Sem correção oficial | 7.4 a 8.1 (só backports de código-fonte ou pacote de distribuição/LTS); 7.3 e anteriores, inclusive PHP 5: **sem correção**, a única saída é migrar |
| Linha do tempo | 17/10: primeira tentativa de exploração vista num honeypot da Amazon, **quatro dias antes da divulgação**. 20/10: detalhes vazaram. 21/10 às 14:00 UTC: correções publicadas, e exploração ativa observada por vários grupos |
| KEV | Até 22/10, **não** estava no catálogo CISA KEV |
| Mitigação | Atualizar é a **única correção completa**. Ajustes de configuração apenas reduzem o risco |

## A.2 Leitura crítica (o que a cobertura da imprensa distorce)

1. **"Ataque cibernético de escala global" precisa ser decomposto.** O que está confirmado é **tentativa de exploração em massa**, observada em honeypots por vários grupos. A taxa de sucesso contra sistemas reais **não está confirmada**, e exploits públicos que circulam não foram validados. Isso não reduz a urgência: em falha pré-autenticação com PoC vazado, tentativa vira sucesso rápido. Mas a decisão certa é "patch agora", não "presuma que todo servidor PHP do mundo caiu".

2. **Por que não estar no KEV não é motivo para esperar.** O KEV exige evidência de exploração bem-sucedida e leva dias para incluir uma CVE. Na Parte 0.3 do protocolo de OS, KEV é o segundo critério de prioridade; aqui, **exposição + pré-autenticação + exploração em curso** já bastam para tratar como P1.

3. **A janela de investigação começa em 17/10, não em 21/10.** Quem tinha PHP exposto entre 17 e a aplicação do patch deve procurar sinais de comprometimento nesse intervalo (Parte D).

4. **A lição estrutural: a janela entre divulgação e exploração está encolhendo.** A cobertura associa a descoberta a ferramentas de IA, e a exploração começou antes da divulgação. Se o seu processo de atualização depende de você lembrar de rodar `apt upgrade` no fim de semana, ele é lento demais para essa classe de ameaça. **Atualização automática deixou de ser conveniência e virou requisito.**

## A.3 Respostas comuns, porém erradas

| Resposta | Por que está errada | O correto |
|---|---|---|
| "`php -v` mostra 8.3.6, então estou vulnerável" (no Ubuntu) | O Ubuntu faz **backport** das correções sem mudar o número da versão upstream. Um `8.3.6` do Ubuntu pode estar corrigido | Verificar a **versão do pacote** contra o aviso de segurança da Canonical (C.1) |
| "`php -v` mostra 8.3.36, então estou corrigido" | O PHP de linha de comando pode não ser o que o servidor web usa. XAMPP, Docker e apps empacotados trazem **cópias próprias** | Inventariar **todas** as instalações e saber qual delas serve requisições (Parte C) |
| "Atualizei o pacote, estou seguro" | Workers do PHP-FPM e o Apache continuam rodando o código antigo **na memória** até reiniciar | Reiniciar `php*-fpm` e `apache2` e confirmar com `needrestart` |
| "Minha máquina é desktop, não é alvo" | Bots não escolhem alvos; varrem endereços. Um XAMPP escutando em `0.0.0.0:80` numa rede de café, ou um IPv6 global sem filtro no roteador, é um alvo | Verificar exposição real (Parte B) |
| "O WAF da Cloudflare resolve" | Só protege tráfego que passa pela Cloudflare, e os próprios mantenedores do WAF o tratam como paliativo | Patch; WAF é camada adicional |
| "Coloquei limite de memória no container, mitiguei o primeiro CVE" | Limite de cgroup é fronteira de disponibilidade, não mitigação | Patch |

---

# PARTE B — Você está exposto? (árvore de decisão)

Responda em ordem. Cada "não" encerra a cadeia para o PHP2Shell, mas **não** encerra o protocolo: a Parte E vale para todas as máquinas.

```
1. Existe PHP instalado nesta máquina (sistema, XAMPP/WAMP/Laragon, Docker, app empacotado)?
   └─ não → PHP2Shell não se aplica. Vá para a Parte E.
2. Alguma dessas instalações SERVE requisições web (Apache, Nginx+FPM, php-cgi, FrankenPHP, container com porta publicada)?
   └─ não → PHP só de linha de comando (composer, scripts): risco do PHP2Shell muito baixo. Atualize mesmo assim.
3. Esse serviço escuta em algo além de 127.0.0.1 / ::1?
   └─ não → alcançável só por processos locais. Risco baixo; atualize.
4. Alguém fora da sua máquina alcança essa porta? (LAN, Wi-Fi público, port forwarding, UPnP, IPv6 global, túnel)
   └─ sim → P1: corrija hoje e faça a checagem de comprometimento (Parte D) desde 17/10.
```

**Por que a pergunta 4 é a mais difícil:** um serviço em `0.0.0.0` numa rede doméstica atrás de NAT costuma ser alcançável só pela LAN. Mas há quatro caminhos que furam essa suposição sem você perceber:
- **Wi-Fi público ou de hotel** (a "LAN" passa a ser desconhecidos);
- **UPnP** no roteador (um programa pode abrir uma porta no roteador sozinho);
- **IPv6**: o computador tem um endereço global; a proteção depende do firewall IPv6 do roteador estar bloqueando entrada;
- **túneis** (ngrok, cloudflared, Tailscale Funnel, `share=True` do Gradio).

---

# PARTE C — Checagem do PHP (por sistema)

Os scripts `inventario_php.sh` e `Inventario-PHP.ps1` automatizam esta parte e são **somente leitura**.

## C.1 Ubuntu

```bash
# Todas as cópias de PHP no disco (não só a do PATH)
sudo find / -xdev -type f \( -name 'php' -o -name 'php[0-9]*' -o -name 'php-fpm*' -o -name 'php-cgi*' -o -name 'libphp*.so' -o -name 'frankenphp' \) -perm -u+x 2>/dev/null

# Pacotes de PHP instalados pelo apt (a versão DO PACOTE é o que importa)
dpkg -l | awk '/^ii/ && $2 ~ /^(php|libapache2-mod-php|libphp)/ {print $2, $3}'

# Snaps que podem embutir PHP (ex.: nextcloud)
snap list 2>/dev/null

# Situação oficial da Canonical para esta CVE nesta máquina (somente leitura com --dry-run)
pro fix CVE-2026-109618 --dry-run
pro fix CVE-2026-109619 --dry-run

# Quem está servindo
systemctl list-units --type=service --state=running | grep -Ei 'php|apache2|nginx|lsws|frankenphp'
apache2ctl -M 2>/dev/null | grep -i php       # mod_php carregado? (pior caso)
sudo ss -tlnp | grep -Ei 'apache2|nginx|php|httpd|frankenphp|lsws'

# Workers ainda rodando código antigo depois de atualizar
sudo needrestart -b -r l
```

**Como ler a versão no Ubuntu:** a referência é a página da CVE na Canonical (`ubuntu.com/security/CVE-2026-109618`), que lista, para cada release, a versão do pacote que contém a correção. Compare com a coluna de versão do `dpkg -l`. O `pro fix ... --dry-run` faz essa comparação por você.

**Evidência direta, offline:** o changelog do pacote instalado registra cada correção de segurança.
```bash
zgrep -n 'CVE-2026-10961[89]' /usr/share/doc/php*-common/changelog.Debian.gz
```
Caso real verificado ao preparar este protocolo, num Ubuntu 24.04 atualizado: `php -v` mostra **8.3.6** (abaixo do 8.3.36 corrigido upstream), mas o pacote `8.3.6-0ubuntu0.24.04.13` traz o patch `CVE-2026-109618_109619.patch` no changelog. Ou seja: **corrigido**, apesar do número. Julgar pelo `php -v` daria um falso alarme aqui, e um falso "ok" no caso inverso (Parte A.3).

**Correção:** `sudo apt update && sudo apt full-upgrade`, depois `sudo systemctl restart php*-fpm apache2 nginx` (os que existirem). Se a sua versão do Ubuntu estiver fora do suporte padrão, o pacote corrigido pode existir só via Ubuntu Pro (ESM).

## C.2 Windows 10 e 11

No Windows não há PHP nativo; ele chega por pacotes de terceiros, e é aí que a atualização falha:

| Origem | Onde costuma ficar | Problema típico |
|---|---|---|
| XAMPP | `C:\xampp\php` | Atualização exige reinstalar o pacote; muita gente fica anos na mesma versão. O Apache do XAMPP usa **`mod_php`** (o pior caso) e, na primeira execução, o Windows pede permissão de firewall: um clique em "Permitir" em rede pública expõe a porta 80 |
| WampServer | `C:\wamp64\bin\php\php*` | Várias versões lado a lado; a ativa nem sempre é a mais nova |
| Laragon | `C:\laragon\bin\php\php*` | Idem |
| Scoop / Chocolatey / winget | `~\scoop\apps\php`, `C:\tools\php*`, `C:\ProgramData\chocolatey` | Atualiza só quando você roda o gerenciador |
| Docker Desktop / WSL2 | Dentro de imagens e distros WSL | Invisível para o Windows: a distro WSL é um Ubuntu, aplique C.1 dentro dela |

```powershell
# Versão do arquivo, SEM executar o binário encontrado
Get-ChildItem 'C:\xampp','C:\wamp64','C:\laragon','C:\tools',"$env:USERPROFILE\scoop\apps",'C:\ProgramData\chocolatey\lib',$env:ProgramFiles -Recurse -Filter php.exe -ErrorAction SilentlyContinue |
  ForEach-Object { [pscustomobject]@{ Caminho=$_.FullName; Versao=$_.VersionInfo.ProductVersion } }

# mod_php do Apache (o pior caso)
Get-ChildItem 'C:\xampp','C:\wamp64','C:\laragon' -Recurse -Filter 'php*apache*.dll' -ErrorAction SilentlyContinue | Select-Object FullName

# Quem está escutando, e em qual endereço
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 80,443,8000,8080,8443,9000 } |
  Select-Object LocalAddress, LocalPort, @{n='Proc';e={(Get-Process -Id $_.OwningProcess).Path}}

# Regras de firewall criadas para Apache/PHP (o clique em "Permitir")
Get-NetFirewallApplicationFilter | Where-Object Program -match 'httpd|php|nginx' |
  ForEach-Object { $r = $_ | Get-NetFirewallRule; [pscustomobject]@{ Programa=$_.Program; Regra=$r.DisplayName; Perfil=$r.Profile; Acao=$r.Action; Ativa=$r.Enabled } }

# Distros WSL (cada uma é um Linux a auditar com C.1)
wsl -l -v
```

**Correção:** atualizar o pacote (XAMPP/WAMP/Laragon) para uma versão que traga PHP ≥ 8.2.35 / 8.3.36 / 8.4.27 / 8.5.12, ou trocar só a pasta do PHP pelo build oficial correspondente. Enquanto não atualiza: **pare o Apache** se não estiver usando, e configure-o para escutar só em `127.0.0.1` (`Listen 127.0.0.1:80` no `httpd.conf`). Ambiente de desenvolvimento não tem motivo para escutar na rede.

## C.3 Docker (Ubuntu ou Windows)

```bash
# Imagens com PHP: as imagens oficiais "php" declaram a versão na variável PHP_VERSION
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | while read -r ref id; do
  v=$(docker image inspect "$id" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep '^PHP_VERSION=')
  [ -n "$v" ] && echo "$ref  $v"
done
# Containers em execução que publicam porta
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Ports}}'
```
Imagem antiga **não se atualiza sozinha**: é preciso `docker pull` da tag corrigida, rebuild das imagens derivadas e recriação dos containers. Imagens que não usam a base oficial (ex.: baseadas em Debian/Ubuntu com `apt install php`) não têm `PHP_VERSION`; verifique com `docker run --rm <imagem> php -v` (isso executa a imagem; faça só com imagens suas).

## C.4 Mitigação temporária (só se o patch for impossível hoje)

Os mantenedores afirmam que **nenhuma configuração mitiga por completo**. Se não puder atualizar imediatamente:
1. **Corte a exposição** (é a única medida forte): parar o serviço, ou escutar só em `127.0.0.1`, ou bloquear a porta no firewall.
2. Ajustes publicados para reduzir o risco, cada um com custo: `session.upload_progress.enabled=0` (e, no 8.5, `fatal_error_backtraces=0`) para o segundo CVE; `memory_limit=-1`, de forma que a aplicação não consiga sobrescrever, para o primeiro. **Atenção:** `memory_limit=-1` remove o teto de memória por requisição e troca um risco de execução remota por um risco de esgotamento de memória. Só faz sentido como ponte de horas, não de semanas.
3. Reinicie todos os workers depois de qualquer mudança.

---

# PARTE D — Se havia PHP exposto desde 17/10: checar comprometimento

Sem IoCs oficiais publicados até agora, a checagem é comportamental: o que um invasor faz depois de executar código num servidor PHP.

**Ubuntu:**
```bash
# Arquivos .php criados ou alterados desde 17/10 nas raízes web (web shells)
sudo find /var/www /srv /home -type f \( -name '*.php' -o -name '*.phtml' -o -name '*.phar' \) -newermt '2026-10-17' 2>/dev/null
# Qualquer arquivo gravado pelo usuário do servidor web desde 17/10
sudo find / -xdev -user www-data -newermt '2026-10-17' -type f 2>/dev/null | grep -v '/var/lib/php/sessions'
# Processos filhos do usuário do servidor web que não deveriam existir (shells, curl, wget, mineradores)
ps -u www-data -o pid,ppid,etime,args 2>/dev/null
# Conexões de saída do usuário do servidor web
sudo ss -tupn state established | grep -E 'apache2|php|nginx'
# Logs de acesso: picos de POST, requisições com corpo grande, respostas 500 em sequência
sudo awk '$6 ~ /POST/' /var/log/apache2/access.log* 2>/dev/null | awk '{print $1}' | sort | uniq -c | sort -rn | head
sudo grep -ciE 'segfault|zend_mm_heap corrupted|allowed memory size' /var/log/apache2/error.log /var/log/php*-fpm.log 2>/dev/null
```

**Windows (XAMPP e similares):**
```powershell
$desde = Get-Date '2026-10-17'
Get-ChildItem 'C:\xampp\htdocs','C:\wamp64\www','C:\laragon\www' -Recurse -Include *.php,*.phtml,*.phar -ErrorAction SilentlyContinue |
  Where-Object { $_.LastWriteTime -ge $desde -or $_.CreationTime -ge $desde } | Select-Object FullName, CreationTime, LastWriteTime
# Processos filhos do Apache (httpd.exe gerando cmd/powershell é sinal forte)
Get-CimInstance Win32_Process | Where-Object { (Get-Process -Id $_.ParentProcessId -ErrorAction SilentlyContinue).ProcessName -eq 'httpd' } |
  Select-Object ProcessId, Name, CommandLine
Select-String -Path 'C:\xampp\apache\logs\error.log' -Pattern 'segfault|heap corrupted|exit signal' -ErrorAction SilentlyContinue | Select-Object -Last 20
```

**Como interpretar:**
- Erros de memória e crashes de worker em sequência a partir de 17/10 são consistentes com **tentativas** (esperado em qualquer host exposto).
- Arquivo `.php` novo que você não criou, processo `sh`/`cmd`/`powershell` filho do servidor web, ou conexão de saída do usuário `www-data`/`httpd` são **P0**: siga a Parte 5 do protocolo de OS (isolar, preservar, rotacionar credenciais a partir de outra máquina, reconstruir).
- Ausência de achados **não prova** ausência de invasão (limite 0.1 do protocolo de OS), mas, numa estação de desenvolvimento sem exposição externa real, é a conclusão razoável.

---

# PARTE E — O protocolo geral para estações locais (vale para a próxima falha sistêmica)

## E.1 As três capacidades, verificáveis

| Capacidade | Pergunta de teste | Como verificar |
|---|---|---|
| **Inventário** | "Quantas cópias de PHP / OpenSSL / Python / Node existem nesta máquina, e em que versão?" | Se você não consegue responder em 10 minutos, o inventário falhou. Scripts desta pasta + gerenciadores de pacotes (E.2) |
| **Superfície** | "O que nesta máquina aceita conexão de fora dela, e de onde?" | `ss -tlnp` / `Get-NetTCPConnection` + firewall + roteador (E.3) |
| **Latência de patch** | "Quantas horas entre a correção sair e ela estar ativa aqui?" | Atualização automática ligada + reboot recente (E.4) |

## E.2 Inventário de software (onde os componentes se escondem)

**Ubuntu:**
```bash
apt list --installed 2>/dev/null | wc -l
snap list; flatpak list 2>/dev/null
pipx list 2>/dev/null; npm ls -g --depth=0 2>/dev/null
docker images 2>/dev/null
ls /opt                                  # software instalado fora do gerenciador (não recebe atualização automática)
```

**Windows:**
```powershell
winget list --upgrade-available          # o que tem atualização pendente (somente leitura)
winget list                              # inventário (inclui muito do que não veio do winget)
Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue |
  Where-Object DisplayName | Select-Object DisplayName, DisplayVersion, Publisher | Sort-Object DisplayName
wsl -l -v
```

**Princípio:** tudo instalado **fora** de um gerenciador que atualiza sozinho (`/opt`, ZIPs extraídos, XAMPP, binários baixados) é dívida de patch. Na próxima falha sistêmica, é ali que a cópia vulnerável vai estar. Reduza essa lista ou anote cada item para atualização manual.

**Opcional (T1+):** gerar uma SBOM do disco com Syft e cruzar com Grype permite perguntar "tenho a biblioteca X em versão Y em algum lugar?" em segundos quando a próxima CVE sair. Fixe as versões das ferramentas por hash, pela lição do incidente do Trivy (Protocolo v2).

## E.3 Superfície de uma estação local

1. **Escuta local:** nada de desenvolvimento escutando em `0.0.0.0`. Servidores de desenvolvimento (Apache, Jupyter, Ollama, `npm run dev --host`, `python -m http.server`) em `127.0.0.1`.
2. **Firewall do host:**
   - Ubuntu: `sudo ufw status verbose` → ative com `deny incoming` (o Ubuntu desktop vem com o UFW **desligado**).
   - Windows: perfil da rede de casa como *Private*, Wi-Fi público como *Public*; revise regras "Permitir" criadas por cliques antigos (`Get-NetFirewallRule -Direction Inbound -Action Allow -Enabled True`).
3. **Roteador** (o perímetro real da estação doméstica):
   - **UPnP desligado**, a menos que um jogo ou app específico precise. No Ubuntu, `upnpc -l` (pacote `miniupnpc`) lista os mapeamentos que programas já abriram no roteador.
   - **Port forwarding**: nenhum apontando para a estação.
   - **IPv6**: em conexões IPv6 nativas (comuns no Japão, via IPoE), cada computador tem endereço global. Confirme que o firewall IPv6 do roteador **bloqueia conexões de entrada** (padrão na maioria dos roteadores, mas verifique).
   - Firmware do roteador atualizado: roteadores são alvo frequente de exploração em massa e raramente são lembrados.
4. **Teste externo:** de outra rede (hotspot do celular), `nmap -Pn <seu IP público>` e, para IPv6, `nmap -6 -Pn <IPv6 global da estação>`. O resultado esperado numa estação doméstica é **nenhuma porta aberta**.

## E.4 Latência de patch, por sistema

### Ubuntu
```bash
systemctl is-active unattended-upgrades; cat /etc/apt/apt.conf.d/20auto-upgrades
[ -f /var/run/reboot-required ] && echo "REBOOT PENDENTE"
pro security-status                       # cobertura de patches (main vs universe) e ESM
snap refresh --list                       # snaps atualizam sozinhos, mas confira se não estão travados
```
Pacotes de PHP no Ubuntu ficam no repositório **main** (cobertos pela Canonical); muitos outros vêm de **universe**, que só recebe correções com Ubuntu Pro. O Ubuntu Pro é gratuito para uso pessoal em poucas máquinas e vale ativar.

### Windows 11
- Windows Update automático; confirme que a última atualização cumulativa tem menos de 45 dias (`Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 3`).
- **Integridade de memória (HVCI)** ligada: Segurança do Windows → Segurança do dispositivo → Isolamento de núcleo. Verificação: `(Get-CimInstance -Namespace root\Microsoft\Windows\DeviceGuard -ClassName Win32_DeviceGuard).SecurityServicesRunning` contém `2`.
- Defender com proteção em tempo real e **Tamper Protection** ligados; exclusões revisadas (Parte 2.6 do protocolo de OS).
- Conta de uso diário **sem** privilégio de administrador. A maior parte do malware de estação depende de o usuário já ser admin.

### Windows 10 (o ponto mais crítico das suas máquinas)
- O suporte normal acabou em outubro de 2025. Atualizações de segurança só chegam pelo programa **ESU para consumidores**, cujo prazo foi estendido até **12 de outubro de 2027**.
- O ESU **não é automático**: exige Windows 10 22H2, conta Microsoft de administrador e inscrição (gratuita via Windows Backup, via pontos Microsoft Rewards, ou paga).
- **Verificação:** Configurações → Windows Update deve indicar que o PC está inscrito em Atualizações de Segurança Estendidas, e `Get-HotFix` deve mostrar atualizações cumulativas recentes. Se a última atualização for de 2025, **a máquina está há um ano sem patches**: isso é P1, e é um risco sistêmico maior para você do que o PHP2Shell.
- `winver` deve mostrar versão **22H2**; versões anteriores não são elegíveis.
- Plano de saída: o ESU tem prazo final. Se o hardware suportar o Windows 11, migre; se não, avalie Ubuntu nessa máquina ou isolamento de rede.

## E.5 Os outros vetores sistêmicos de uma estação (onde o próximo caso vai cair)

| Vetor | Por que é sistêmico | Controle |
|---|---|---|
| Navegador | Maior superfície de ataque de qualquer desktop; exploração de dia zero é recorrente | Atualização automática, reiniciar o navegador quando ele pedir, poucas extensões |
| Runtimes embutidos (Electron, Node, Python, Java em apps) | Cada app traz sua cópia; o sistema não as atualiza | Apps atualizados pelo próprio mecanismo deles; inventário E.2 |
| Cadeia de suprimentos de desenvolvimento (pip, npm, VS Code extensions, imagens Docker) | Um pacote comprometido roda com o seu usuário | Protocolo v2, B.5 |
| Firmware (BIOS/UEFI, roteador) | Atualiza raramente e fica abaixo do sistema operacional | Ubuntu: `fwupdmgr get-updates`; Windows: ferramenta do fabricante; roteador: painel |

---

# PARTE F — Cadência e gatilhos

| Quando | O quê |
|---|---|
| **Gatilho: nova falha sistêmica divulgada** | 1) O componente existe aqui? (inventário) 2) Serve rede? 3) Está exposto? 4) Patch + reinício + verificação. 5) Se esteve exposto: checagem de comprometimento a partir da **primeira data de exploração conhecida**, não da data de divulgação |
| Semanal | Reboot pendente; última atualização cumulativa (Windows); `winget list --upgrade-available`; `apt list --upgradable` |
| Mensal | Scripts de inventário (diff contra o anterior); portas em escuta; regras de firewall; UPnP/port forwarding no roteador |
| Trimestral | Teste externo de portas; revisão do que está fora de gerenciador de pacotes; prazo do ESU no Windows 10 |

---

## Fontes do caso PHP2Shell

- Tenable — FAQ PHP2Shell: https://www.tenable.com/blog/php2shell-cve-2026-109618-cve-2026-109619-frequently-asked-questions-about-critical-php-remote
- watchTowr — FAQ PHP2Shell: https://watchtowr.com/intelligence/php-cve-2026-109618-faq/
- Patchstack — alerta: https://patchstack.com/articles/php-major-vulnerability-alert-10-2026/
- Canonical — página da CVE (versões corrigidas por release): https://ubuntu.com/security/CVE-2026-109618
- Help Net Security — extensão do ESU do Windows 10: https://www.helpnetsecurity.com/2026/06/26/microsoft-windows-10-free-security-updates-esu-program/
