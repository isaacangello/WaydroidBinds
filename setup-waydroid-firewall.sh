#!/bin/bash
# Waydroid Firewall Auto-Config
# Detecta o firewall ativo e aplica as regras necessárias para o Waydroid
# ter internet persistente (IP forwarding + NAT + regras de forwarding).
#
# Baseado na documentação oficial:
#   https://docs.waydro.id/debugging/networking-issues
#
# Detecta automaticamente: firewalld > UFW > nftables > iptables puro.
#
# Uso:
#   pkexec ./setup-waydroid-firewall.sh            # detecta e configura
#   pkexec ./setup-waydroid-firewall.sh check      # só diagnóstico (não altera nada)
#   pkexec ./setup-waydroid-firewall.sh status     # diagnóstico em formato KEY=VALUE (GUI)
#   pkexec ./setup-waydroid-firewall.sh revert     # desfaz a configuração

set -euo pipefail

WAYDROID_IF="waydroid0"
SYSCONF_FILE="/etc/sysctl.d/99-waydroid.conf"
STARTUP_SCRIPT="/usr/bin/waydroid-startup-scripts"
FBEGIN="# Waydroid Firewall BEGIN"
FEND="# Waydroid Firewall END"
SBEGIN="# Waydroid Shared Folders BEGIN"
SEND="# Waydroid Shared Folders END"

MODE="apply"
case "${1:-}" in
    check|-c)            MODE="check" ;;
    status|-s)           MODE="status" ;;
    revert|--revert|-r)  MODE="revert" ;;
    *)                   MODE="apply" ;;
esac

[ "$(id -u)" = "0" ] || { echo "ERRO: execute com pkexec ou sudo."; exit 1; }

msg()  { echo -e "$*"; }
ok()   { echo "  [OK] $*"; }
warn() { echo "  [AVISO] $*"; }

# Rede interna do Waydroid (padrão 192.168.240.0/24)
waydroid_net() {
    local net
    net=$(ip -4 -o addr show dev "$WAYDROID_IF" 2>/dev/null | awk '{print $4}' | \
        awk -F'[./]' '{print $1"."$2"."$3".0/"$5}')
    echo "${net:-192.168.240.0/24}"
}

default_iface() {
    ip -4 route show default 2>/dev/null | awk '{print $5; exit}'
}

detect_firewall() {
    local fd uf nf
    fd=$(systemctl is-active firewalld 2>/dev/null || echo inactive)
    uf=$(systemctl is-active ufw 2>/dev/null || echo inactive)
    nf=$(systemctl is-active nftables 2>/dev/null || echo inactive)
    if   [ "$fd" = "active" ]; then FIREWALL="firewalld"
    elif [ "$uf" = "active" ]; then FIREWALL="ufw"
    elif [ "$nf" = "active" ]; then FIREWALL="nftables"
    else FIREWALL="iptables"; fi
}

ensure_ip_forward() {
    msg ""
    msg "== IP Forwarding =="
    if [ "$(sysctl -n net.ipv4.ip_forward 2>/dev/null || echo 0)" = "1" ]; then
        ok "net.ipv4.ip_forward já ativo"
    else
        sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1 || true
        ok "net.ipv4.ip_forward ativado"
    fi
    if [ -f "$SYSCONF_FILE" ] && grep -q '^net.ipv4.ip_forward=1$' "$SYSCONF_FILE"; then
        ok "Persistência já existe ($SYSCONF_FILE)"
    else
        printf 'net.ipv4.ip_forward=1\n' >> "$SYSCONF_FILE"
        ok "Persistência criada ($SYSCONF_FILE)"
    fi
}

fix_forward_policy() {
    msg ""
    msg "== Política FORWARD (Docker/nftables costumam deixar DROP) =="
    local policy
    policy=$(iptables -L FORWARD -n 2>/dev/null | sed -n '1s/.*(policy \([A-Z]*\)).*/\1/p' || true)
    if [ "${policy:-DROP}" = "ACCEPT" ]; then
        ok "Política FORWARD já é ACCEPT"
    else
        iptables -P FORWARD ACCEPT 2>/dev/null || true
        ok "Política FORWARD ajustada para ACCEPT (era ${policy:-DROP})"
    fi
}

apply_waydroid_iptables() {
    msg ""
    msg "== Regras iptables para $WAYDROID_IF =="
    iptables -C FORWARD -i "$WAYDROID_IF" -j ACCEPT 2>/dev/null || \
        iptables -I FORWARD -i "$WAYDROID_IF" -j ACCEPT 2>/dev/null || true
    iptables -C FORWARD -o "$WAYDROID_IF" -j ACCEPT 2>/dev/null || \
        iptables -I FORWARD -o "$WAYDROID_IF" -j ACCEPT 2>/dev/null || true
    iptables -t nat -C POSTROUTING -s "$WAYDROID_NET" -j MASQUERADE 2>/dev/null || \
        iptables -t nat -A POSTROUTING -s "$WAYDROID_NET" -j MASQUERADE 2>/dev/null || true
    ok "ACCEPT em FORWARD (i/o) + MASQUERADE para $WAYDROID_NET"
}

setup_firewalld() {
    msg ""
    msg "== firewalld: $WAYDROID_IF para a zona trusted =="
    firewall-cmd --permanent --zone=trusted --add-interface="$WAYDROID_IF" >/dev/null 2>&1 || true
    firewall-cmd --permanent --zone=trusted --add-forward >/dev/null 2>&1 || true
    firewall-cmd --permanent --zone=trusted --add-masquerade >/dev/null 2>&1 || true
    firewall-cmd --reload >/dev/null 2>&1 || true
    local zone
    zone=$(firewall-cmd --get-zone-of-interface="$WAYDROID_IF" 2>/dev/null || true)
    ok "$WAYDROID_IF na zona: ${zone:-trusted} (permanente)"
}

setup_ufw() {
    msg ""
    msg "== UFW =="
    ufw allow 53 >/dev/null 2>&1 || true
    ufw allow 67 >/dev/null 2>&1 || true
    ufw route allow in on "$WAYDROID_IF" >/dev/null 2>&1 || true
    ufw route allow out on "$WAYDROID_IF" >/dev/null 2>&1 || true
    ok "Regras UFW aplicadas (DNS 53, DHCP 67 e forwarding em $WAYDROID_IF)"
}

setup_iptables() {
    msg ""
    msg "== iptables (sem firewall gerenciado) =="
    if command -v iptables-save >/dev/null 2>&1; then
        mkdir -p /etc/iptables
        iptables-save > /etc/iptables/iptables.rules 2>/dev/null || true
        if systemctl list-unit-files 2>/dev/null | grep -q '^iptables.service'; then
            systemctl enable iptables.service >/dev/null 2>&1 || true
            ok "Regras salvas em /etc/iptables/iptables.rules e serviço iptables habilitado"
        else
            ok "Regras salvas em /etc/iptables/iptables.rules (persistência via hook)"
        fi
    fi
}

# Insere um bloco marcado ANTES do primeiro 'exit' do hook.
# (O hook original termina com 'exit'; conteúdo adicionado depois dele é código morto.)
insert_before_exit() {
    local hook="$1" begin="$2" end="$3" block="$4"
    local tmp
    tmp=$(mktemp)
    sed -i "/${begin}/,/${end}/d" "$hook"
    awk -v b="$block" '
        /^exit[[:space:]]*$/ && !done {
            print b
            done=1
        }
        { print }
    ' "$hook" > "$tmp"
    mv "$tmp" "$hook"
    if ! grep -qF "$begin" "$hook"; then
        printf '\n%s\n' "$block" >> "$hook"
    fi
}

# Move um bloco que esteja depois do 'exit' (inativo) para antes do 'exit'.
relocate_block_before_exit() {
    local hook="$1" begin="$2" end="$3"
    local after_exit block
    after_exit=$(sed -n '/^exit[[:space:]]*$/,$p' "$hook" 2>/dev/null || true)
    if echo "$after_exit" | grep -qF "$begin"; then
        block=$(sed -n "/${begin}/,/${end}/p" "$hook")
        insert_before_exit "$hook" "$begin" "$end" "$block"
        return 0
    fi
    return 1
}

install_hook() {
    [ -f "$STARTUP_SCRIPT" ] || return 0
    local block
    block=$(cat <<EOF

$FBEGIN
sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1 || true
iptables -P FORWARD ACCEPT 2>/dev/null || true
iptables -C FORWARD -i $WAYDROID_IF -j ACCEPT 2>/dev/null || iptables -I FORWARD -i $WAYDROID_IF -j ACCEPT 2>/dev/null || true
iptables -C FORWARD -o $WAYDROID_IF -j ACCEPT 2>/dev/null || iptables -I FORWARD -o $WAYDROID_IF -j ACCEPT 2>/dev/null || true
iptables -t nat -C POSTROUTING -s $WAYDROID_NET -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -s $WAYDROID_NET -j MASQUERADE 2>/dev/null || true
waydroid shell -- ip route replace default via 192.168.240.1 dev eth0 2>/dev/null || true
$FEND
EOF
)
    insert_before_exit "$STARTUP_SCRIPT" "$FBEGIN" "$FEND" "$block"
    if relocate_block_before_exit "$STARTUP_SCRIPT" "$SBEGIN" "$SEND"; then
        ok "Bloco de bind mounts (Shared Folders) movido para antes do 'exit' — estava inativo"
    fi
    ok "Persistência instalada em $STARTUP_SCRIPT (blocos executam antes do 'exit')"
}

self_test() {
    msg ""
    msg "== Teste de conectividade =="
    if systemctl is-active waydroid-container >/dev/null 2>&1; then
        if waydroid shell -- ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
            ok "Ping 8.8.8.8 dentro do Waydroid: OK"
        else
            warn "Ping 8.8.8.8 falhou (container ainda iniciando? tente novamente em instantes)"
        fi
    else
        warn "waydroid-container não ativo — teste adiado"
    fi
}

check() {
    msg "== Diagnóstico da rede do Waydroid =="
    msg "  IP forwarding: $(sysctl -n net.ipv4.ip_forward 2>/dev/null)"
    msg "  Firewall ativo: $FIREWALL"
    msg "  Rede do container: $WAYDROID_NET"
    msg "  Interface de internet: ${DEFAULT_IF:-desconhecida}"
    local policy zone
    policy=$(iptables -L FORWARD -n 2>/dev/null | sed -n '1s/.*(policy \([A-Z]*\)).*/\1/p' || true)
    msg "  Política FORWARD: ${policy:-desconhecida}"
    if [ "$FIREWALL" = "firewalld" ]; then
        zone=$(firewall-cmd --get-zone-of-interface="$WAYDROID_IF" 2>/dev/null || true)
        msg "  Zona de $WAYDROID_IF: ${zone:-não atribuída}"
        if [ "${zone:-}" != "trusted" ]; then
            warn "$WAYDROID_IF fora da zona trusted — provável causa do problema"
        else
            ok "$WAYDROID_IF na zona trusted"
        fi
    fi
    if systemctl is-active waydroid-container >/dev/null 2>&1; then
        if waydroid shell -- ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
            ok "Conectividade dentro do Waydroid: OK"
        else
            warn "Conectividade dentro do Waydroid: FALHOU"
        fi
    else
        msg "  waydroid-container não ativo (nada a testar)"
    fi
}

# Saída legível por máquina (KEY=VALUE) para a GUI
status() {
    local policy zone container conn
    policy=$(iptables -L FORWARD -n 2>/dev/null | sed -n '1s/.*(policy \([A-Z]*\)).*/\1/p' || true)
    zone=""
    if [ "$FIREWALL" = "firewalld" ]; then
        zone=$(firewall-cmd --get-zone-of-interface="$WAYDROID_IF" 2>/dev/null || true)
    fi
    if systemctl is-active waydroid-container >/dev/null 2>&1; then
        container="active"
        if waydroid shell -- ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
            conn="OK"
        else
            conn="FAIL"
        fi
    else
        container="inactive"
        conn="NA"
    fi
    cat <<EOF
ip_forward=$(sysctl -n net.ipv4.ip_forward 2>/dev/null || echo 0)
firewall=${FIREWALL:-unknown}
waydroid_net=${WAYDROID_NET:-unknown}
default_iface=${DEFAULT_IF:-unknown}
forward_policy=${policy:-unknown}
zone=${zone:-}
container=${container:-unknown}
connectivity=${conn:-NA}
EOF
}

revert() {
    msg "== Revertendo configurações de firewall do Waydroid =="
    if [ -f "$STARTUP_SCRIPT" ]; then
        sed -i "/${FBEGIN}/,/${FEND}/d" "$STARTUP_SCRIPT"
        ok "Bloco de firewall removido de $STARTUP_SCRIPT"
    fi
    if [ -f "$SYSCONF_FILE" ]; then
        sed -i '/^net.ipv4.ip_forward=1$/d' "$SYSCONF_FILE"
        [ -s "$SYSCONF_FILE" ] || rm -f "$SYSCONF_FILE"
        ok "Persistência de ip_forward removida"
    fi
    if [ "$FIREWALL" = "firewalld" ]; then
        firewall-cmd --permanent --zone=trusted --remove-interface="$WAYDROID_IF" >/dev/null 2>&1 || true
        firewall-cmd --reload >/dev/null 2>&1 || true
        ok "$WAYDROID_IF removida da zona trusted"
    fi
    if [ "$FIREWALL" = "ufw" ]; then
        ufw route delete allow in on "$WAYDROID_IF" >/dev/null 2>&1 || true
        ufw route delete allow out on "$WAYDROID_IF" >/dev/null 2>&1 || true
        ok "Regras de forwarding UFW removidas"
    fi
    iptables -D FORWARD -i "$WAYDROID_IF" -j ACCEPT 2>/dev/null || true
    iptables -D FORWARD -o "$WAYDROID_IF" -j ACCEPT 2>/dev/null || true
    iptables -t nat -D POSTROUTING -s "$WAYDROID_NET" -j MASQUERADE 2>/dev/null || true
    ok "Regras iptables do Waydroid removidas"
    warn "Política FORWARD mantida como está (não revertida para DROP, para não quebrar Docker)"
    msg ""
    msg "Pronto!"
}

# ---------- main ----------
WAYDROID_NET=$(waydroid_net)
DEFAULT_IF=$(default_iface)
detect_firewall

case "$MODE" in
    check)
        check
        ;;
    status)
        status
        ;;
    revert)
        revert
        ;;
    apply)
        msg "Firewall detectado: $FIREWALL"
        msg "Rede do Waydroid: $WAYDROID_NET"
        msg "Interface de internet: ${DEFAULT_IF:-?}"
        msg ""
        ensure_ip_forward
        case "$FIREWALL" in
            firewalld) setup_firewalld ;;
            ufw)       setup_ufw ;;
            *)         setup_iptables ;;
        esac
        fix_forward_policy
        apply_waydroid_iptables
        install_hook
        self_test
        msg ""
        msg "Pronto! Reinicie o container para aplicar: systemctl restart waydroid-container"
        msg "Obs.: se usar Docker, ele pode redefinir FORWARD para DROP ao reiniciar; o hook reaplica na inicialização do container."
        ;;
esac
