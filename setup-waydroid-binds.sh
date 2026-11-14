#!/bin/bash
# Waydroid Shared Folders
# Método oficial: https://docs.waydro.id/faq/setting-up-a-shared-folder
# Uso: pkexec ./setup-waydroid-binds.sh [bind...]
#   Sem argumentos: aplica TODOS os binds.
#   Com argumentos: aplica apenas os binds listados pelo nome
#   (ex.: Downloads Imagens). Nomes válidos: Downloads, Documentos,
#   Imagens, videos, WhatsApp.
#
# Persistência: em vez de injetar blocos no hook do Waydroid (que o
# update do pacote pode sobrescrever), este script:
#   1. monta os binds na hora (visíveis no container em execução);
#   2. grava a seleção em /etc/waydroid-binds.conf (um usuário por linha);
#   3. instala um drop-in systemd (ExecStartPost) que reaplica os binds
#      a CADA início do container via apply-binds.sh;
#   4. migra: remove blocos legados de waydroid-startup-scripts, se houver.

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
CONF="/etc/waydroid-binds.conf"
DROPIN_DIR="/etc/systemd/system/waydroid-container.service.d"
DROPIN="$DROPIN_DIR/waydroid-binds.conf"
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
SHARE_DIR="/usr/share/waydroid-binds"

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

# Apply binds (montagem imediata — visível no container em execução)
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

# ---------- Persistência via config + systemd drop-in ----------

# 1. Copia o helper de boot para o local de sistema (o drop-in aponta pra lá)
install -d -m 755 "$SHARE_DIR"
if [ -f "$SCRIPT_DIR/apply-binds.sh" ]; then
    install -m 755 "$SCRIPT_DIR/apply-binds.sh" "$SHARE_DIR/apply-binds.sh"
fi

# 2. Grava a seleção do usuário na config (preservando outros usuários)
SELECTED_CSV="$(IFS=,; echo "${SELECTED[*]}")"
tmpconf=$(mktemp)
awk -F: -v u="$REAL_USER" '$1 != u' "$CONF" 2>/dev/null > "$tmpconf" || true
echo "${REAL_USER}:${SELECTED_CSV}" >> "$tmpconf"
install -m 644 "$tmpconf" "$CONF"
rm -f "$tmpconf"
echo ""
echo "Persistência registrada em $CONF ($REAL_USER: ${SELECTED_CSV})"

# 3. Instala o drop-in systemd (reaplica a cada início do container)
mkdir -p "$DROPIN_DIR"
cat > "$DROPIN" <<'EOF'
# Gerado por waydroid-binds — reaplica os binds a cada início do container.
# Não edite: este arquivo é reescrito por setup-waydroid-binds.sh.
[Service]
ExecStartPost=/usr/share/waydroid-binds/apply-binds.sh
EOF
systemctl daemon-reload
echo "Drop-in systemd instalado: $DROPIN"

# 4. Migração: remove blocos legados do hook do Waydroid (se existirem)
if [ -f "$STARTUP_SCRIPT" ] && grep -q "# Waydroid Shared Folders BEGIN" "$STARTUP_SCRIPT"; then
    sed -i '/# Waydroid Shared Folders BEGIN/,/# Waydroid Shared Folders END/d' "$STARTUP_SCRIPT"
    echo ""
    echo "Migração: bloco legado removido de $STARTUP_SCRIPT (agora gerenciado pelo systemd)"
fi

echo ""
echo "Pronto!"
for name in "${SELECTED[@]}"; do
    source="${BINDS[$name]%%:*}"
    target="${BINDS[$name]#*:}"
    printf '  %-26s → /sdcard/%s\n' "$source" "$target"
done
echo ""
echo "Os binds serão reaplicados automaticamente a cada início do container."