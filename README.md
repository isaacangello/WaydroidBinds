# Waydroid Shared Folders

Bind mounts entre o host Linux e o Android (Waydroid) usando o método oficial da documentação, com GUI e firewall auto-config.

## Instalação

Distribuição via empacotamento (gera `.deb`, `.rpm`, `.pkg.tar.zst` e `.flatpak` na CI):

```bash
# Debian/Ubuntu (na pasta do repo)
cp -r packaging/debian debian && dpkg-buildpackage -b -us -uc

# Arch
makepkg -f -p packaging/arch/PKGBUILD

# Roda direto do repositório (sem instalar)
./waydroid-binds-gui
```

Depois de instalar, execute `waydroid-binds-gui` para abrir o painel.

## Mapeamento

| Host | Android |
|---|---|
| `~/Downloads` | `/sdcard/Download` |
| `~/Documentos` | `/sdcard/Documents` |
| `~/Imagens` | `/sdcard/Pictures` |
| `~/videos` | `/sdcard/Movies` |
| `~/Waydroid/WhatsApp` | `/sdcard/Android/media/com.whatsapp/WhatsApp/Media` |

## Requisitos

- [Waydroid](https://waydro.id/) instalado e funcionando
- `pkexec` ou `sudo` (para mounts como root)

## Uso

```bash
# Ativar binds (pede senha via pkexec)
pkexec ./setup-waydroid-binds.sh

# Ativar apenas alguns binds (Downloads, Documentos, Imagens, videos, WhatsApp)
pkexec ./setup-waydroid-binds.sh Downloads Imagens

# Reverter binds
pkexec ./revert-waydroid-binds.sh

# Copiar mídias existentes do WhatsApp para a pasta compartilhada
pkexec ./copy-existing-media.sh

# Detectar e configurar firewall (firewalld/UFW/nftables/iptables) para o Waydroid navegar
pkexec ./setup-waydroid-firewall.sh

# Diagnóstico (não altera nada)
pkexec ./setup-waydroid-firewall.sh check

# Desfazer configuração de firewall
pkexec ./setup-waydroid-firewall.sh revert
```

Os binds e as regras de firewall são automaticamente restaurados toda vez que o container Waydroid inicia, via hook em `/usr/bin/waydroid-startup-scripts`.

## GUI

`waydroid-binds-gui` (PySide6) reúne tudo num painel:

- **Pastas compartilhadas**: aplica/reverte os binds seletivamente (checkbox por pasta)
- **Rede / Firewall**: diagnóstico em tempo real (forwarding, zona do firewalld, conectividade) e botão Aplicar/Reparar
- **Mídia do WhatsApp**: copia mídias que existiam antes do bind

```bash
./waydroid-binds-gui              # abrir a GUI
./waydroid-binds-gui --dry-run    # modo de teste: não executa comandos
```

As ações privilegiadas (mount, firewall) pedem senha via `pkexec`.

## Scripts

| Script | Função |
|---|---|
| `setup-waydroid-binds.sh` | Aplica todos os bind mounts e adiciona persistência |
| `revert-waydroid-binds.sh` | Desmonta todos os binds e remove persistência |
| `copy-existing-media.sh` | Copia mídias já existentes no WhatsApp para a pasta compartilhada |
| `setup-waydroid-firewall.sh` | Detecta e configura firewall para o Waydroid ter internet persistente (IP forwarding, NAT e forwarding rules) |

## Firewall

O `setup-waydroid-firewall.sh` detecta automaticamente o firewall ativo (**firewalld > UFW > nftables > iptables puro**) e aplica a configuração necessária para o Waydroid navegar:

- `net.ipv4.ip_forward=1` persistido em `/etc/sysctl.d/99-waydroid.conf`
- firewalld: interface `waydroid0` movida para a zona `trusted` (permanente)
- UFW: libera DNS (53), DHCP (67) e forwarding em `waydroid0`
- iptables/nftables: `iptables -P FORWARD ACCEPT` + ACCEPT `-i/-o waydroid0` + MASQUERADE
- Restaura a rota default dentro do container a cada boot (via hook)

> **Sintoma comum:** WhatsApp não envia mensagens mas às vezes navega. Causa típica: Docker deixa `FORWARD DROP` e só aceita conexões já estabelecidas — pacotes novos do container são descartados. O script resolve adicionando ACCEPT para `waydroid0`.

```bash
pkexec ./setup-waydroid-firewall.sh         # detecta e configura
pkexec ./setup-waydroid-firewall.sh check   # diagnóstico (não altera nada)
pkexec ./setup-waydroid-firewall.sh revert  # desfaz
```

## Referência

- [Documentação oficial Waydroid - Shared Folder](https://docs.waydro.id/faq/setting-up-a-shared-folder)
- Comando base: `sudo mount --bind <source> ~/.local/share/waydroid/data/media/0/<target>`
