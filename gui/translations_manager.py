"""Gerenciador de traduções para Waydroid Binds."""

from pathlib import Path

from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtWidgets import QApplication


def get_translation_language() -> str:
    """Retorna o código do idioma para traduções.

    Regras:
    - pt_BR, pt_PT, pt → 'pt' (português)
    - Qualquer outro → 'en' (inglês, fallback)
    """
    locale = QLocale.system().name()  # ex: "pt_BR", "en_US", "es_ES"
    if locale.startswith("pt"):
        return "pt"
    return "en"


class TranslationsManager:
    """Gerencia carregamento e instalação de traduções Qt."""

    def __init__(self, app: QApplication) -> None:
        self.translator = QTranslator()
        self.app = app
        self._load_translations()

    def _load_translations(self) -> None:
        lang = get_translation_language()
        # Tenta carregar do resource embutido (:/
        qm_file = f":/translations/waydroid-binds_{lang}.qm"
        if self.translator.load(qm_file):
            self.app.installTranslator(self.translator)
            return

        # Fallback: tenta carregar do sistema de arquivos (desenvolvimento)
        base_dir = Path(__file__).resolve().parent
        fs_qm = base_dir / f"waydroid-binds_{lang}.qm"
        if fs_qm.exists() and self.translator.load(str(fs_qm)):
            self.app.installTranslator(self.translator)
            return

        # Se não achou tradução específica, tenta fallback inglês
        if lang != "en":
            self._load_fallback_english()

    def _load_fallback_english(self) -> None:
        qm_file = ":/translations/waydroid-binds_en.qm"
        if self.translator.load(qm_file):
            self.app.installTranslator(self.translator)
            return

        base_dir = Path(__file__).resolve().parent
        fs_qm = base_dir / "waydroid-binds_en.qm"
        if fs_qm.exists() and self.translator.load(str(fs_qm)):
            self.app.installTranslator(self.translator)
