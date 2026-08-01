"""Definição dos binds de pastas compartilhadas.

Deve permanecer em sincronia com a tabela BINDS de
setup-waydroid-binds.sh e com os TARGETS de revert-waydroid-binds.sh.
"""

from pathlib import Path

HOME = Path.home()
WAYDROID_MEDIA = HOME / ".local/share/waydroid/data/media/0"

BINDS: dict[str, tuple[Path, str]] = {
    "Downloads": (HOME / "Downloads", "Download"),
    "Documentos": (HOME / "Documentos", "Documents"),
    "Imagens": (HOME / "Imagens", "Pictures"),
    "videos": (HOME / "videos", "Movies"),
    "WhatsApp": (
        HOME / "Waydroid" / "WhatsApp",
        "Android/media/com.whatsapp/WhatsApp/Media",
    ),
}
