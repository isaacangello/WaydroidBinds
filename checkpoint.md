# Waydroid Shared Folders - Checkpoint

## Status Atual (2026-08-01)

### ✅ Internet / Firewall (novo)
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
├── README.md
├── CHANGELOG.md
└── checkpoint.md
```

### Método
- Binds: `sudo mount --bind <source> ~/.local/share/waydroid/data/media/0/<target>`
- Firewall: `pkexec ./setup-waydroid-firewall.sh` (apply | check | revert)
