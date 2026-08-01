#!/bin/bash
# Waydroid Shared Folders
# Método oficial: https://docs.waydro.id/faq/setting-up-a-shared-folder
# Uso: pkexec ./setup-waydroid-binds.sh [bind...]
#   Sem argumentos: aplica TODOS os binds.
#   Com argumentos: aplica apenas os binds listados pelo nome
#   (ex.: Downloads Imagens). Nomes válidos: Downloads, Documentos,
#   Imagens, videos, WhatsApp.

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

# Binds: nome → "Host:Android"
BIND_NAMES=(Downloads Documentos Imagens videos WhatsApp)
declare -A BINDS=(
    [Downloads]="$USER_HOME/Downloads:Download"
    [Documentos]="$USER_HOME/Documentos:Documents"
    [Imagens]="$USER_HOME/Imagens:Pictures"
    [videos]="$USER_HOME/videos:Movies"
    [WhatsApp]="$USER_HOME/Waydroid/WhatsApp:Android/media/com.whatsapp/WhatsApp/Media"
)

# Seleção de binds
SELECTED=()
if [ "$#" -eq 0 ]; then
    SELECTED=("${BIND_NAMES[@]}")
else
    for name in "$@"; do
        if [ -n "${BINDS[$name]:-}" ]; then
            SELECTED+=("$name")
        else
            echo "ERRO: bind desconhecido: $name" >&2
            echo "Válidos: ${BIND_NAMES[*]}" >&2
            exit 1
        fi
    done
fi

echo "Binds selecionados: ${SELECTED[*]}"
echo ""

# Create source dirs (if needed) and ensure world-writable so Android apps can write
for name in "${SELECTED[@]}"; do
    source="${BINDS[$name]%%:*}"
    mkdir -p "$source"
    chmod 777 "$source"
done

# Create target dirs inside Android
for name in "${SELECTED[@]}"; do
    target="${BINDS[$name]#*:}"
    mkdir -p "$WAYDROID_MEDIA/$target"
done

# Apply binds
for name in "${SELECTED[@]}"; do
    source="${BINDS[$name]%%:*}"
    target="$WAYDROID_MEDIA/${BINDS[$name]#*:}"

    mountpoint -q "$target" && umount "$target" 2>/dev/null || true
    mount --bind "$source" "$target"
    echo "  bind: $source → $target"
done

echo ""
echo "=== Binds ativos ==="
mount | grep "$WAYDROID_MEDIA" | sed "s|.*on ||" | sed "s| type.*||" || true

# Persistência via waydroid-startup-scripts
# Insere o bloco ANTES do 'exit' do hook (o hook original termina com 'exit';
# conteúdo adicionado depois dele é código morto e não roda no boot).
# O bloco contém apenas os binds selecionados.
if [ -f "$STARTUP_SCRIPT" ]; then
    CHMOD_SOURCES=()
    MOUNT_LINES=()
    for name in "${SELECTED[@]}"; do
        source="${BINDS[$name]%%:*}"
        target="$WAYDROID_MEDIA/${BINDS[$name]#*:}"
        CHMOD_SOURCES+=("$source")
        MOUNT_LINES+=("mount --bind $source $target")
    done

    BLOCK=$(cat << EOF

# Waydroid Shared Folders BEGIN
chmod 777 ${CHMOD_SOURCES[*]} 2>/dev/null || true
$(printf '%s\n' "${MOUNT_LINES[@]}")
# Waydroid Shared Folders END
EOF
)
    sed -i '/# Waydroid Shared Folders BEGIN/,/# Waydroid Shared Folders END/d' "$STARTUP_SCRIPT"
    if grep -q '^exit' "$STARTUP_SCRIPT"; then
        TMP=$(mktemp)
        awk -v b="$BLOCK" '
            /^exit[[:space:]]*$/ && !done {
                print b
                done=1
            }
            { print }
        ' "$STARTUP_SCRIPT" > "$TMP"
        mv "$TMP" "$STARTUP_SCRIPT"
    else
        printf '\n%s\n' "$BLOCK" >> "$STARTUP_SCRIPT"
    fi
    echo ""
    echo "Persistência adicionada ao $STARTUP_SCRIPT (binds: ${SELECTED[*]})"
fi

echo ""
echo "Pronto!"
for name in "${SELECTED[@]}"; do
    source="${BINDS[$name]%%:*}"
    target="${BINDS[$name]#*:}"
    printf '  %-26s → /sdcard/%s\n' "$source" "$target"
done
