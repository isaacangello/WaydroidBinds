# Waydroid Shared Folders - Changelog

## v1.6.0 (2026-11-16)

### Adicionado
- **Persistência consolidada via systemd drop-in** (substitui a injeção de blocos em `/usr/bin/waydroid-startup-scripts`):
  - `/etc/waydroid-binds.conf`: seleção de binds **por usuário** (`usuario:Downloads,Imagens,...` ou `all`)
  - Home resolvida por `getent` **a cada boot** — migração de home não quebra nada
  - Multi-usuário real: cada usuário tem sua linha na config; "Reverter" preserva os outros
  - Drop-ins em `/etc/systemd/system/waydroid-container.service.d/` (`ExecStartPost`) — imunes a updates do pacote Waydroid
  - Dispara em **qualquer** início do container (boot, restart ou manual), não só no boot da máquina
- `apply-binds.sh`: helper de boot (idempotente, log no journald, sempre `exit 0`, `WAYDROID_BINDS_DRY_RUN=1` para testes)
- Firewall: novo modo `boot` (regras host + rota default do container com timeout) aplicado via drop-in próprio

### Alterado
- `setup`/`revert` de binds não escrevem mais no hook do Waydroid; aplicam/revertem a config + drop-in
- Firewall `apply` instala o próprio drop-in; `revert` remove; nenhum dos dois toca mais em `waydroid-startup-scripts`
- Migração automática: blocos legados `BEGIN/END` são removidos do hook na primeira aplicação/reversão

### Corrigido
- Risco de perda silenciosa de persistência em updates do pacote Waydroid (o hook era arquivo vendor)

## v1.5.0 (2026-10-13)

### Adicionado
- **Nova aba "Status"** (4ª aba, 100% sem senha, auto-refresh 30s enquanto aberta):
  - Estado do Waydroid: serviço systemd, container Android real, sessão (GUI), uptime, versão do Waydroid, tipo de imagem, distribuição (ex.: LineageOS 20), IP do Android
  - Recursos: kernel binder, disco (`df -h`)
  - Resumo: pastas montadas (X/5) e internet (cache do firewall)
  - Botão "Abrir Android (GUI)" (habilita só sem sessão ativa) e "Atualizar"
  - Distribuição lida do `build.prop` do rootfs sem root (mapeamento Android→LineageOS)
- **Internacionalização (i18n)**: português nativo; qualquer outro idioma cai para inglês
  - `Qt Linguist` (`tr()` com contextos), `.ts`/`.qm` em pt_BR e en, `TranslationsManager`
  - `pkgdesc` do AUR em inglês; `.desktop` com `Comment` padrão em inglês
- `TaskRunner`: resolve comandos pelo `PATH` (`shutil.which`); scripts `.sh` via `pkexec bash`

### Corrigido
- **GUI**: refresh assíncrono (UI não trava), loading por botão (outros continuam clicáveis), aba firewall sempre atualiza ao abrir, log silencioso para refreshes automáticos
- **noexec**: launcher e ações com `pkexec` funcionam em partições montadas com `noexec`
- **CI/AUR**: job publica via `git clone` do repo AUR (SSH antes do clone) — push incremental em vez de histórico novo a cada release
- Saída de erro do Waydroid não vaza mais para os cartões de status (validação de valores)

## v1.3.0 (2026-08-01)

### Adicionado
- **Preparo para o Flathub**: App ID `io.github.isaacangello.waydroidbinds`
  - Metainfo AppStream (`io.github.isaacangello.waydroidbinds.metainfo.xml`), LICENSE (GPL-3.0) e screenshots em `docs/screenshots/`
  - Manifest Flatpak agora usa a BaseApp oficial `io.qt.PySide.BaseApp` (sem `pip` no build, requisito do Flathub)
  - Manifest de submissão (`*.flathub.yml`) com fonte do tarball do release + `x-checker-data`
  - `.desktop`/`.svg` renomeados com o App ID; status dos binds lido do host no sandbox
- **GUI** (`waydroid-binds-gui`): painel PySide6 com abas para Pastas compartilhadas, Rede/Firewall e Mídia do WhatsApp
  - Aplica/reverte binds seletivamente (checkbox por pasta) com persistência no boot
  - Diagnóstico de firewall em tempo real (via `status` KEY=VALUE) e botão Aplicar/Reparar
  - Cópia de mídias existentes do WhatsApp
  - Modo `--dry-run` para testes sem executar comandos
- **Empacotamento**: `.deb` (debian), `.rpm` (rpmbuild), Arch (`PKGBUILD`) e `Flatpak`
- **GitHub Actions**: CI (shellcheck, ruff, `py_compile`, smoke test offscreen da GUI) e Release (gera `.deb`/`.rpm`/`.pkg.tar.zst`/`.flatpak` e publica no GitHub Releases em tags `v*`)
- `setup-waydroid-binds.sh`: aceita seleção seletiva de binds por nome (ex.: `pkexec ./setup-waydroid-binds.sh Downloads Imagens`)
- `setup-waydroid-firewall.sh`: novo modo `status` com saída KEY=VALUE consumível por máquina
- `copy-existing-media.sh`: detecção automática do usuário real (`PKEXEC_UID`/`SUDO_USER`) em vez de caminhos hardcoded

## v1.2.0 (2026-08-01)

### Adicionado
- `setup-waydroid-firewall.sh`: script de auto-ajuste de firewall para o Waydroid ter internet persistente
  - Detecta automaticamente firewalld > UFW > nftables > iptables puro
  - Modos: `apply` (configura), `check` (só diagnóstico), `revert` (desfaz)
  - Persiste `net.ipv4.ip_forward=1` em `/etc/sysctl.d/99-waydroid.conf`
  - Move `waydroid0` para a zona `trusted` do firewalld (permanente)
  - Aplica `iptables -P FORWARD ACCEPT` + ACCEPT `-i/-o waydroid0` + MASQUERADE
  - Restaura a rota default dentro do container a cada boot

### Corrigido
- Internet/WhatsApp no Waydroid: Docker deixa `FORWARD DROP` e o `DOCKER-CT` só aceita tráfego já estabelecido — pacotes **novos** do container eram descartados (mensagem não enviava). Regras de ACCEPT para `waydroid0` resolvem.
- **Bug de persistência**: `/usr/bin/waydroid-startup-scripts` termina com `exit`; qualquer bloco adicionado depois (binds inclusos) era **código morto** e não rodava no boot. Blocos agora são inseridos **antes** do `exit`.
- `setup-waydroid-binds.sh`: persistência passou a inserir antes do `exit` (antes reapendava depois → código morto); corrigido `grep -v waydroid` que zerava a listagem de binds e abortava o script no `set -e`.

## v1.1.0 (2026-06-30)

### Corrigido
- Salvamento de fotos falhava em `~/Imagens` e `~/Documentos` — Android Apps não tinham permissão de escrita nos binds (permissão 755, precisava 777)
- Adicionado `chmod 777` nos diretórios fonte antes de cada bind mount
- Mesma correção adicionada ao hook de persistência (`/usr/bin/waydroid-startup-scripts`)

## v1.0.0 (2026-06-30)

### Adicionado
- Bind mount `~/Downloads` → `/sdcard/Download`
- Bind mount `~/Documentos` → `/sdcard/Documents`
- Bind mount `~/Imagens` → `/sdcard/Pictures`
- Bind mount `~/videos` → `/sdcard/Movies`
- Bind mount `~/Waydroid/WhatsApp` → `/sdcard/Android/media/com.whatsapp/WhatsApp/Media`
- Persistência automática via `/usr/bin/waydroid-startup-scripts`
- Scripts de setup, revert e copy-media
- Suporte a scoped storage do WhatsApp (Android 10+)

### Alterado
- Substituído bind via LXC `config_session` por `mount --bind` direto (método oficial)
- Download movido de `~/Waydroid/Download` para `~/Downloads`
