#!/bin/bash
# Waydroid Binds — persistência de montagens no boot
# Chamado pelo systemd via drop-in (ExecStartPost) de waydroid-container.service:
#   /etc/systemd/system/waydroid-container.service.d/waydroid-binds.conf
#
# Lê /etc/waydroid-binds.conf (uma entrada por usuário):
#   usuario:Downloads,Imagens,WhatsApp     (lista de binds)
#   outrouser:all                          (todos os binds padrão)
#
# Resolve a home de CADA usuário via getent (dinâmico a cada boot — nunca
# caminho literal), garante permissões e monta de forma idempotente.
# Nunca falha o serviço: sempre exit 0 (problemas viram warning no journald).
#
# Para testes sem root: WAYDROID_BINDS_DRY_RUN=1 WAYDROID_BINDS_CONF=/tmp/test.conf ./apply-binds.sh

set -uo pipefail

CONF="${WAYDROID_BINDS_CONF:-/etc/waydroid-binds.conf}"
DRY_RUN="${WAYDROID_BINDS_DRY_RUN:-0}"

# Mesma tabela da GUI (gui/binds.py) e do setup-waydroid-binds.sh
declare -A SRC=(
    [Downloads]="Downloads"
    [Documentos]="Documentos"
    [Imagens]="Imagens"
    [videos]="videos"
    [WhatsApp]="Waydroid/WhatsApp"
)
declare -A TGT=(
    [Downloads]="Download"
    [Documentos]="Documents"
    [Imagens]="Pictures"
    [videos]="Movies"
    [WhatsApp]="Android/media/com.whatsapp/WhatsApp/Media"
)
ALL_NAMES="Downloads Documentos Imagens videos WhatsApp"

log() { echo "[waydroid-binds] $*"; }

run() {
    if [ "$DRY_RUN" = "1" ]; then
        log "DRY-RUN: $*"
    else
        "$@"
    fi
}

[ -r "$CONF" ] || { log "sem config em $CONF — nada a fazer"; exit 0; }

applied=0
while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"
    line="$(echo "$line" | tr -d '[:space:]')"
    [ -z "$line" ] && continue
    case "$line" in *:*) ;; *) log "linha inválida ignorada: $line"; continue ;; esac

    user="${line%%:*}"
    list="${line#*:}"
    case "$user" in
        *[!A-Za-z0-9_.-]*) log "usuário inválido ignorado: $user"; continue ;;
    esac

    home="$(getent passwd "$user" 2>/dev/null | cut -d: -f6)"
    if [ -z "$home" ]; then
        log "usuário '$user' não existe — pulando"
        continue
    fi

    media="$home/.local/share/waydroid/data/media/0"
    if [ ! -d "$media" ]; then
        if [ "$DRY_RUN" = "1" ]; then
            # Em modo teste (usuário comum) o dir pode ser inacessível por
            # permissão LXC — em produção o helper roda como root e o gate vale.
            log "AVISO DRY-RUN: $media inacessível/inexistente — simulando mesmo assim"
        else
            log "waydroid não inicializado para $user ($media) — pulando"
            continue
        fi
    fi

    # 'all' expande para a lista completa
    if [ "$list" = "all" ]; then
        list="$ALL_NAMES"
    fi

    IFS=',' read -ra names <<< "$list"
    for name in "${names[@]}"; do
        [ -z "$name" ] && continue
        if [ -z "${SRC[$name]:-}" ]; then
            log "bind desconhecido '$name' — pulando"
            continue
        fi
        src="$home/${SRC[$name]}"
        tgt="$media/${TGT[$name]}"

        run mkdir -p "$src" "$tgt"
        run chmod 777 "$src"

        if [ "$DRY_RUN" = "1" ]; then
            log "DRY-RUN: mountpoint -q '$tgt' || mount --bind '$src' '$tgt'"
            applied=$((applied + 1))
            continue
        fi

        if mountpoint -q "$tgt" 2>/dev/null; then
            log "já montado: $tgt"
            applied=$((applied + 1))
            continue
        fi

        if mount --bind "$src" "$tgt" 2>/dev/null; then
            log "montado: $src → $tgt"
            applied=$((applied + 1))
        else
            log "FALHA ao montar: $src → $tgt (continuando)"
        fi
    done
done < "$CONF"

log "concluído: $applied bind(s) verificados"
exit 0