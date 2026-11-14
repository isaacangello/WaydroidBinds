#!/bin/bash
# Reverter Waydroid Shared Folders
# Uso: pkexec ./revert-waydroid-binds.sh
#
# Desmonta os binds do usuário atual, remove sua entrada de
# /etc/waydroid-binds.conf e remove o drop-in systemd se a config
# ficar vazia. Também limpa blocos legados de waydroid-startup-scripts.

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
CONF="/etc/waydroid-binds.conf"
DROPIN_DIR="/etc/systemd/system/waydroid-container.service.d"
DROPIN="$DROPIN_DIR/waydroid-binds.conf"

# Targets to unmount (mesma tabela da GUI e do setup)
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

# Remove a entrada do usuário da config (preserva outros usuários)
if [ -f "$CONF" ]; then
    tmpconf=$(mktemp)
    awk -F: -v u="$REAL_USER" '$1 != u' "$CONF" > "$tmpconf" || true
    if [ -s "$tmpconf" ]; then
        install -m 644 "$tmpconf" "$CONF"
        echo "Entrada de $REAL_USER removida de $CONF (outros usuários preservados)"
    else
        rm -f "$CONF" "$DROPIN"
        [ -d "$DROPIN_DIR" ] && rmdir "$DROPIN_DIR" 2>/dev/null || true
        systemctl daemon-reload
        echo "Config vazia — $CONF e drop-in systemd removidos"
    fi
    rm -f "$tmpconf"
fi

# Migração/limpeza: remove blocos legados do hook do Waydroid (se existirem)
if [ -f "$STARTUP_SCRIPT" ] && grep -q "# Waydroid Shared Folders BEGIN" "$STARTUP_SCRIPT"; then
    sed -i '/# Waydroid Shared Folders BEGIN/,/# Waydroid Shared Folders END/d' "$STARTUP_SCRIPT"
    echo "Bloco legado removido de $STARTUP_SCRIPT"
fi

echo "Binds removidos."