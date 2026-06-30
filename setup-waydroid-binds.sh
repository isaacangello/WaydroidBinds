#!/bin/bash
# Waydroid Shared Folders
# Método oficial: https://docs.waydro.id/faq/setting-up-a-shared-folder
# Uso: pkexec ./setup-waydroid-binds.sh

set -euo pipefail

# Detect real user
if [ -n "${PKEXEC_UID:-}" ]; then
    REAL_USER=$(id -nu "$PKEXEC_UID" 2>/dev/null)
elif [ -n "${SUDO_USER:-}" ]; then
    REAL_USER="$SUDO_USER"
else
    REAL_USER=$(logname 2>/dev/null || who am i | awk '{print $1}' || echo "$USER")
fi
USER_HOME=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f6)
[ -z "$USER_HOME" ] && { echo "ERRO: não foi possível detectar o usuário"; exit 1; }

WAYDROID_MEDIA="$USER_HOME/.local/share/waydroid/data/media/0"
STARTUP_SCRIPT="/usr/bin/waydroid-startup-scripts"

echo "Usuário: $REAL_USER"
echo ""

# Binds: Host → Android
BINDS=(
    "$USER_HOME/Downloads:Download"
    "$USER_HOME/Documentos:Documents"
    "$USER_HOME/Imagens:Pictures"
    "$USER_HOME/videos:Movies"
    "$USER_HOME/Waydroid/WhatsApp:Android/media/com.whatsapp/WhatsApp/Media"
)

# Create target dirs inside Android
for entry in "${BINDS[@]}"; do
    target="${entry#*:}"
    mkdir -p "$WAYDROID_MEDIA/$target"
done

# Apply binds
for entry in "${BINDS[@]}"; do
    source="${entry%%:*}"
    target="$WAYDROID_MEDIA/${entry#*:}"

    mountpoint -q "$target" && umount "$target" 2>/dev/null || true
    mount --bind "$source" "$target"
    echo "  bind: $source → $target"
done

echo ""
echo "=== Binds ativos ==="
mount | grep "$WAYDROID_MEDIA" | grep -v waydroid | sed "s|.*on ||" | sed "s| type.*||"

# Persistência via waydroid-startup-scripts
if [ -f "$STARTUP_SCRIPT" ]; then
    sed -i '/# Waydroid Shared Folders BEGIN/,/# Waydroid Shared Folders END/d' "$STARTUP_SCRIPT"
    cat >> "$STARTUP_SCRIPT" << EOF

# Waydroid Shared Folders BEGIN
mount --bind $USER_HOME/Downloads $WAYDROID_MEDIA/Download
mount --bind $USER_HOME/Documentos $WAYDROID_MEDIA/Documents
mount --bind $USER_HOME/Imagens $WAYDROID_MEDIA/Pictures
mount --bind $USER_HOME/videos $WAYDROID_MEDIA/Movies
mount --bind $USER_HOME/Waydroid/WhatsApp $WAYDROID_MEDIA/Android/media/com.whatsapp/WhatsApp/Media
# Waydroid Shared Folders END
EOF
    echo ""
    echo "Persistência adicionada ao $STARTUP_SCRIPT"
fi

echo ""
echo "Pronto!"
echo "  ~/Downloads     → /sdcard/Download"
echo "  ~/Documentos    → /sdcard/Documents"
echo "  ~/Imagens       → /sdcard/Pictures"
echo "  ~/videos        → /sdcard/Movies"
echo "  ~/Waydroid/WhatsApp → /sdcard/Android/media/com.whatsapp/WhatsApp/Media"
