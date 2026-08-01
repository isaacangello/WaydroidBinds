"""Resolução dos caminhos dos scripts de apoio (repo ou instalação)."""

import os
from pathlib import Path

_SCRIPT_DIR = None


def script_dir() -> Path:
    """Diretório onde os scripts .sh vivem.

    Prioridade:
    1. Env WAYDROID_BINDS_DIR (testes / empacotamento).
    2. Layout de repo: <repo>/*.sh e <repo>/gui/.
    3. Layout instalado: /usr/share/waydroid-binds/.
    """
    global _SCRIPT_DIR
    if _SCRIPT_DIR is not None:
        return _SCRIPT_DIR
    env = os.getenv("WAYDROID_BINDS_DIR")
    if env:
        _SCRIPT_DIR = Path(env)
        return _SCRIPT_DIR
    here = Path(__file__).resolve().parent
    repo = here.parent
    for candidate in (
        repo,
        here,
        Path("/usr/share/waydroid-binds"),
        Path("/app/share/waydroid-binds"),
    ):
        if (candidate / "setup-waydroid-binds.sh").exists():
            _SCRIPT_DIR = candidate
            return _SCRIPT_DIR
    _SCRIPT_DIR = here
    return _SCRIPT_DIR


BINDS_SCRIPT = script_dir() / "setup-waydroid-binds.sh"
REVERT_BINDS_SCRIPT = script_dir() / "revert-waydroid-binds.sh"
FIREWALL_SCRIPT = script_dir() / "setup-waydroid-firewall.sh"
REVERT_FIREWALL_SCRIPT = script_dir() / "setup-waydroid-firewall.sh"
MEDIA_SCRIPT = script_dir() / "copy-existing-media.sh"
