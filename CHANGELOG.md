# Waydroid Shared Folders - Changelog

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
