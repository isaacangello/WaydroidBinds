# Waydroid Shared Folders - Changelog

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
