#!/bin/bash
# Reverter Waydroid Shared Folders
# Uso: pkexec ./revert-waydroid-binds.sh

set -euo pipefail

if [ -n "${PKEXEC_UID:-}" ]; then
    REAL_USER=$(id -nu "$PKEXEC_UID" 2>/dev/null)
elif [ -n "${SUDO_USER:-}" ]; then
    REAL_USER="$SUDO_USER"
else
    REAL_USER=$(logname 2>/dev/null || echo "$USER")
fi
USER_HOME=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f6)
[ -z "$USER_HOME" ] && { echo "ERRO: não foi possível detectar o usuário"; exit 1; }

WAYDROID_MEDIA="$USER_HOME/.local/share/waydroid/data/media/0"
STARTUP_SCRIPT="/usr/bin/waydroid-startup-scripts"

# Targets to unmount
TARGETS=(
    "Download"
    "Documents"
    "Pictures"
    "Movies"
    "Android/media/com.whatsapp/WhatsApp/Media"
)

for target in "${TARGETS[@]}"; do
    mountpoint -q "$WAYDROID_MEDIA/$target" 2>/dev/null && \
        umount "$WAYDROID_MEDIA/$target" && \
        echo "Desmontado: $WAYDROID_MEDIA/$target" || true
done

# Remove persistência
if [ -f "$STARTUP_SCRIPT" ]; then
    sed -i '/# Waydroid Shared Folders BEGIN/,/# Waydroid Shared Folders END/d' "$STARTUP_SCRIPT"
    echo "Persistência removida de $STARTUP_SCRIPT"
fi

echo "Binds removidos."
