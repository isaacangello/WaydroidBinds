"""Leitura de estado atual (sem exigir root quando possível)."""

import os
import subprocess

import binds


def _mount_output() -> str:
    # Dentro de um sandbox Flatpak, o namespace de mounts é o do sandbox.
    # O estado real (binds no host) só é visível via flatpak-spawn --host.
    cmd = ["mount"]
    if os.environ.get("FLATPAK_ID"):
        cmd = ["flatpak-spawn", "--host", "mount"]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, check=False
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
    """Converte a saída KEY=VALUE de `setup-waydroid-firewall.sh status` em dict."""
    data: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if line and "=" in line:
            key, _, value = line.partition("=")
            data[key.strip()] = value.strip()
    return data
