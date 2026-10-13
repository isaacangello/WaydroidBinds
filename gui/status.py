"""Leitura de estado atual (sem exigir root quando possível)."""

import re
import subprocess

import binds

# Script de diagnóstico do Waydroid (roda SEM pkexec — tudo read-only e rápido).
# Saída em KEY=VALUE, consumida pela aba Status via TaskRunner.
STATUS_SCRIPT = r"""
out=$(systemctl is-active waydroid-container 2>/dev/null || true)
echo "container=${out:-unknown}"
out=$(systemctl is-enabled waydroid-container 2>/dev/null || true)
echo "enabled=${out:-unknown}"
since=$(systemctl show waydroid-container -p ActiveEnterTimestamp --value 2>/dev/null)
uptime=0
if [ -n "$since" ]; then
    start=$(date -d "$since" +%s 2>/dev/null)
    if [ -n "$start" ]; then
        uptime=$(( $(date +%s) - start ))
    fi
fi
echo "uptime=$uptime"
version=$(waydroid --version 2>/dev/null | head -1)
[ -n "$version" ] || version=$(waydroid version 2>/dev/null | head -1)
case "$version" in
    ''|*[!0-9A-Za-z.-]*) version="" ;;
esac
echo "version=$version"
# 'waydroid status' não precisa de root: estado do container, IP, vendor.
wstatus=$(timeout 3 waydroid status 2>/dev/null)
session=$(echo "$wstatus" | grep '^Session:' | cut -d: -f2- | tr -d '[:space:]')
case "$session" in
    RUNNING|STOPPED|None|"") : ;;
    *) session="unknown" ;;
esac
echo "session=${session:-none}"
wcontainer=$(echo "$wstatus" | grep '^Container:' | cut -d: -f2- | tr -d '[:space:]')
case "$wcontainer" in
    RUNNING|STOPPED|None|"") : ;;
    *) wcontainer="unknown" ;;
esac
echo "wcontainer=${wcontainer:-none}"
echo "vendor=$(echo "$wstatus" | grep '^Vendor type:' | cut -d: -f2- | tr -d '[:space:]')"
echo "android_ip=$(echo "$wstatus" | grep '^IP address:' | cut -d: -f2- | tr -d '[:space:]')"
# Distribuição do Android: build.prop do rootfs extraído é legível sem root.
# (o build.prop principal é root-only; as partições dlkm/ext trazem o mesmo nome/versão)
bp=""
for f in /var/lib/waydroid/rootfs/system/system_ext/etc/build.prop \
         /var/lib/waydroid/rootfs/system/system_dlkm/etc/build.prop \
         /var/lib/waydroid/rootfs/system/product/etc/build.prop \
         /var/lib/waydroid/rootfs/vendor/odm_dlkm/etc/build.prop \
         /var/lib/waydroid/rootfs/vendor/vendor_dlkm/etc/build.prop; do
    [ -r "$f" ] && { bp="$f"; break; }
done
if [ -n "$bp" ]; then
    echo "distro_product=$(grep -m1 '^ro\.product\..*name=' "$bp" | cut -d= -f2)"
    echo "distro_android=$(grep -m1 'build\.version\.release=' "$bp" | cut -d= -f2)"
fi
if [ -d /dev/binderfs ] || [ -e /dev/binder ] || lsmod 2>/dev/null | grep -q binder_linux; then
    echo "binder=ok"
else
    echo "binder=missing"
fi
dir="$HOME/.local/share/waydroid"
[ -d "$dir" ] || dir="$HOME"
echo "disk=$(df -h "$dir" 2>/dev/null | awk 'NR==2{print $3" / "$4" livres ("$5")"}')"
"""


def _mount_output() -> str:
    try:
        proc = subprocess.run(
            ["mount"], capture_output=True, text=True, timeout=10, check=False
        )
        return proc.stdout or ""
    except (subprocess.SubprocessError, OSError):
        return ""


def bind_status() -> dict[str, bool]:
    """Nome do bind -> True se o mount alvo aparece em `mount`."""
    out = _mount_output()
    media = str(binds.WAYDROID_MEDIA)
    result: dict[str, bool] = {}
    for name, (_src, tgt) in binds.BINDS.items():
        result[name] = f"{media}/{tgt}" in out
    return result


def bind_source(name: str) -> str:
    src, _tgt = binds.BINDS[name]
    return str(src)


def parse_firewall_status(text: str) -> dict[str, str]:
    """Converte a saída KEY=VALUE (firewall ou status) em dict."""
    data: dict[str, str] = {}
    for match in re.finditer(r"^([^=]+)=(.*)$", text, re.MULTILINE):
        data[match.group(1).strip()] = match.group(2).strip()
    return data


def format_uptime(seconds: str | int) -> str:
    """Formata segundos em '2h15m' / '12m30s' / '45s'."""
    try:
        total = int(seconds)
    except (TypeError, ValueError):
        return "—"
    if total <= 0:
        return "—"
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


# Mapeamento fixo histórico: versão do Android → versão major do LineageOS
_LINEAGE_BY_ANDROID = {
    "9": "16",
    "10": "17.1",
    "11": "18.1",
    "12": "19",
    "13": "20",
    "14": "21",
    "15": "22",
}


def distro_display(product: str, android: str) -> str:
    """Compõe 'LineageOS 20' a partir do nome do produto e versão Android.

    O build.prop legível traz o nome do produto (ex.: lineage_waydroid_x86_64)
    e a versão do Android (ex.: 13); a major do LineageOS deriva da versão.
    """
    if "lineage" in product.lower():
        major = _LINEAGE_BY_ANDROID.get(android)
        if major:
            return f"LineageOS {major}"
        if android:
            return f"LineageOS ({android})"
        return "LineageOS"
    if android:
        return f"Android {android}"
    if product:
        return product
    return ""
