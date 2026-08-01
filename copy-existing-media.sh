#!/bin/bash
# Copiar mídias existentes do WhatsApp para a pasta compartilhada
# As mídias novas já vão direto para ~/Waydroid/WhatsApp/ via bind mount
# Este script copia as que já estavam no WhatsApp antes do bind
# Uso: pkexec ./copy-existing-media.sh

echo "=== Copiando mídias existentes do WhatsApp ==="

# Detect real user
if [ -n "${PKEXEC_UID:-}" ]; then
    REAL_USER=$(id -nu "$PKEXEC_UID" 2>/dev/null)
elif [ -n "${SUDO_USER:-}" ]; then
    REAL_USER="$SUDO_USER"
else
    REAL_USER=$(logname 2>/dev/null || echo "$USER")
fi
USER_HOME=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f6)
[ -z "$USER_HOME" ] && { echo "ERRO: não foi possível detectar o usuário"; exit 1; }

# Desmonta bind temporariamente pra acessar dados originais
WAYDROID_MEDIA="$USER_HOME/.local/share/waydroid/data/media/0"
TARGET="$WAYDROID_MEDIA/Android/media/com.whatsapp/WhatsApp/Media"
HOST_DIR="$USER_HOME/Waydroid/WhatsApp"

mountpoint -q "$TARGET" && umount "$TARGET" && echo "Bind desmontado para cópia"

echo "Copiando do Android para $HOST_DIR ..."
MEDIA="/sdcard/Android/media/com.whatsapp/WhatsApp/Media"
waydroid shell cp -r "$MEDIA"/* "$MEDIA"/ 2>/dev/null || waydroid shell cp -r "$MEDIA"/. "$MEDIA"/ 2>/dev/null || echo "Nada a copiar"

# Reaplica bind
mount --bind "$HOST_DIR" "$TARGET" && echo "Bind reaplicado"

echo ""
echo "Pronto! Mídias em ~/Waydroid/WhatsApp/"
echo "Subpastas:"
ls -d "$HOST_DIR"/*/ 2>/dev/null
