# Waydroid Shared Folders - Changelog

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
