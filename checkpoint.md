# Waydroid Shared Folders - Checkpoint

## Status Atual (2026-08-01)

### ✅ v1.3.0 — GUI + Empacotamento (novo)
- **GUI PySide6** (`gui/`, launcher `waydroid-binds-gui`):
  - Abas: Pastas compartilhadas (binds seletivos), Rede/Firewall (diagnóstico tempo real) e Mídia do WhatsApp
  - Smoke test offscreen OK; `--dry-run` para testes
- **Empacotamento**: `packaging/{debian,rpm,arch,flatpak}` (versão 1.3.0)
- **GitHub Actions**: `ci.yml` (shellcheck/ruff/py_compile/smoke) + `release.yml` (deb/rpm/pacman/flatpak + GitHub Release)
- Verificado: `shellcheck` limpo nos 4 scripts + launcher, `ruff check/format` limpo no `gui/`, `python3 -m py_compile gui/*.py` OK
- Scripts:
  - `setup-waydroid-binds.sh [nome...]` agora aceita seleção seletiva de binds
  - `setup-waydroid-firewall.sh status` → saída KEY=VALUE para a GUI
  - `copy-existing-media.sh` detecta o usuário real (PKEXEC_UID/SUDO_USER)

### 🚀 Flathub — preparado (pendente: submeter)
- App ID: **`io.github.isaacangello.waydroidbinds`** (runtime 6.11 + `io.qt.PySide.BaseApp`)
- Arquivos prontos: `metainfo.xml`, `LICENSE` (GPL-3.0), screenshots em `docs/screenshots/`, `.desktop`/`.svg` renomeados
- Manifest de dev (fonte local) e de submissão (`*.flathub.yml`, tarball v1.3.0 + `x-checker-data`)
- Flatpak `bind_status` lê mounts do host via `flatpak-spawn --host mount`
- **Falta (manual, você)**: criar release/tag `v1.3.0`, preencher `sha256: REPLACE_ME`, e abrir o PR no `flathub/flathub` (a política proíbe PR por IA) — instruções em `packaging/flatpak/README.md`

### ✅ Internet / Firewall (v1.2.0)
- Firewall detectado: **firewalld** (backend nf_tables)
- `waydroid0` na zona **trusted** (permanente)
- `iptables -P FORWARD ACCEPT` + ACCEPT `-i/-o waydroid0` + MASQUERADE aplicados
- `net.ipv4.ip_forward=1` persistido em `/etc/sysctl.d/99-waydroid.conf`
- **Causa raiz do WhatsApp não enviar**: Docker deixa `FORWARD DROP` e o `DOCKER-CT` só aceita conexões já estabelecidas — pacotes novos do container eram descartados
- Verificado: ping 8.8.8.8 OK, DNS OK, conexões novas TCP para Google e WhatsApp/Facebook estabelecendo normalmente

### ✅ Binds Ativos

| Host | Android | Status |
|---|---|---|
| `~/Downloads` | `/sdcard/Download` | ✅ |
| `~/Documentos` | `/sdcard/Documents` | ✅ |
| `~/Imagens` | `/sdcard/Pictures` | ✅ |
| `~/videos` | `/sdcard/Movies` | ✅ |
| `~/Waydroid/WhatsApp` | `/sdcard/Android/media/com.whatsapp/WhatsApp/Media` | ✅ |

### ✅ Persistência
- `/usr/bin/waydroid-startup-scripts` com blocos **antes do `exit`** (Firewall + Shared Folders)
- 🔧 Corrigido: os blocos adicionados depois do `exit` eram código morto — binds nunca eram restaurados no boot
- Binds e regras de firewall restaurados automaticamente no startup do container

### ✅ Verificação
- Conteúdo visível dentro do Android via `waydroid shell ls`
- Mídias existentes do WhatsApp copiadas (15.570+ imagens)
- 14 subdiretórios de mídia do WhatsApp funcionando

### ⚠️ Corrigido (v1.1.0)
- Diretórios `~/Imagens` e `~/Documentos` tinham permissão 755
- Android Apps não conseguiam escrever (erro ao salvar foto)
- Agora o script aplica `chmod 777` antes de cada bind

### 📁 Estrutura
```
~/WaydroidBinds/
├── setup-waydroid-binds.sh
├── revert-waydroid-binds.sh
├── copy-existing-media.sh
├── setup-waydroid-firewall.sh
├── waydroid-binds-gui
├── gui/                  # GUI PySide6 (+ metainfo/desktop/svg com App ID)
├── docs/screenshots/     # screenshots p/ Flathub
├── packaging/            # debian/ rmp/ arch/ flatpak (+ manifest submissão)
├── LICENSE               # GPL-3.0
├── .github/workflows/    # CI + Release
├── README.md
├── CHANGELOG.md
└── checkpoint.md
```

### Método
- Binds: `sudo mount --bind <source> ~/.local/share/waydroid/data/media/0/<target>`
- Firewall: `pkexec ./setup-waydroid-firewall.sh` (apply | check | revert)
