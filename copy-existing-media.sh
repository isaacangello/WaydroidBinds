#!/bin/bash
# Copiar mídias existentes do WhatsApp para a pasta compartilhada
# As mídias novas já vão direto para ~/Waydroid/WhatsApp/ via bind mount
# Este script copia as que já estavam no WhatsApp antes do bind
# Uso: pkexec ./copy-existing-media.sh

echo "=== Copiando mídias existentes do WhatsApp ==="

SRC="/sdcard/Android/media/com.whatsapp/WhatsApp/Media"
DST="/sdcard/Android/media/com.whatsapp/WhatsApp/Media"  # mesmo caminho (bind mount)

# Desmonta bind temporariamente pra acessar dados originais
WAYDROID_MEDIA="/home/isaacca/.local/share/waydroid/data/media/0"
TARGET="$WAYDROID_MEDIA/Android/media/com.whatsapp/WhatsApp/Media"
HOST_DIR="/home/isaacca/Waydroid/WhatsApp"

mountpoint -q "$TARGET" && umount "$TARGET" && echo "Bind desmontado para cópia"

echo "Copiando do Android para $HOST_DIR ..."
waydroid shell cp -r "$SRC"/* "$DST"/ 2>/dev/null || waydroid shell cp -r "$SRC"/. "$DST"/ 2>/dev/null || echo "Nada a copiar"

# Reaplica bind
mount --bind "$HOST_DIR" "$TARGET" && echo "Bind reaplicado"

echo ""
echo "Pronto! Mídias em ~/Waydroid/WhatsApp/"
echo "Subpastas:"
ls -d "$HOST_DIR"/*/ 2>/dev/null
