"""Janela principal do Waydroid Binds."""

from datetime import datetime, timezone

import binds as binds_mod
import paths
import status as status_mod
from backend import TaskRunner
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

GOOD = "#1a7f37"
BAD = "#cf222e"
WARN = "#9a6700"
MUTED = "#57606a"


def colored(text: str, color: str) -> str:
    return f'<span style="color:{color}; font-weight:600;">{text}</span>'


class MainWindow(QMainWindow):
    def __init__(self, runner: TaskRunner) -> None:
        super().__init__()
        self.runner = runner
        self._running_tags: set[str] = set()
        self._checks: dict[str, QCheckBox] = {}
        self._bind_state: dict[str, QLabel] = {}
        self._fw_cards: dict[str, QLabel] = {}
        self._action_buttons: list[QPushButton] = []
        self._button_tags: dict[QPushButton, str] = {}

        self.setWindowTitle("Waydroid Binds")
        self.resize(880, 660)

        self._build_ui()
        self._wire()

        self.refresh_binds()

        self._timer = QTimer(self)
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self.refresh_binds)
        self._timer.start()

        if self.runner.dry_run:
            self.statusBar().showMessage(
                "MODO DRY-RUN — nenhum comando será executado de verdade"
            )

    # ---------- UI ----------

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_binds_tab(), "Pastas compartilhadas")
        self._tabs.addTab(self._build_firewall_tab(), "Rede / Firewall")
        self._tabs.addTab(self._build_media_tab(), "Mídia do WhatsApp")

        log_box = QGroupBox("Log")
        log_lay = QVBoxLayout(log_box)
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        self._log.setFont(font)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        log_lay.addWidget(self._log)
        log_lay.addWidget(self._progress)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self._tabs)
        splitter.addWidget(log_box)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter)
        self.setCentralWidget(central)

    def _build_binds_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)

        box = QGroupBox("Pastas compartilhadas (Host → Android)")
        grid = QGridLayout(box)
        grid.setColumnStretch(1, 1)
        for row, (name, (src, _tgt)) in enumerate(binds_mod.BINDS.items()):
            check = QCheckBox(name)
            path_lbl = QLabel(str(src))
            path_lbl.setToolTip(str(src))
            path_lbl.setStyleSheet(f"color:{MUTED};")
            state_lbl = QLabel("—")
            state_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(check, row, 0)
            grid.addWidget(path_lbl, row, 1)
            grid.addWidget(state_lbl, row, 2)
            self._checks[name] = check
            self._bind_state[name] = state_lbl
        v.addWidget(box)

        self.btn_bind_apply = QPushButton("Aplicar selecionados")
        self.btn_bind_revert = QPushButton("Reverter todos")
        self.btn_bind_refresh = QPushButton("Atualizar")
        self._register_button(self.btn_bind_apply, "bind_apply")
        self._register_button(self.btn_bind_revert, "bind_revert")

        row = QHBoxLayout()
        row.addWidget(self.btn_bind_apply)
        row.addWidget(self.btn_bind_revert)
        row.addStretch(1)
        row.addWidget(self.btn_bind_refresh)
        v.addLayout(row)

        note = QLabel(
            "Aplicar: monta as pastas selecionadas e persiste no boot "
            "(waydroid-startup-scripts). Reverter todos: desmonta tudo e "
            "remove a persistência."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{MUTED};")
        v.addWidget(note)
        v.addStretch(1)
        return tab

    def _build_firewall_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)

        box = QGroupBox("Rede / Firewall do Waydroid")
        grid = QGridLayout(box)
        grid.setColumnStretch(1, 1)
        rows = [
            ("IP forwarding", "ip_forward"),
            ("Firewall ativo", "firewall"),
            ("Rede do container", "waydroid_net"),
            ("Interface de internet", "default_iface"),
            ("Política FORWARD", "forward_policy"),
            ("Zona (firewalld)", "zone"),
            ("Container", "container"),
            ("Conectividade (ping)", "connectivity"),
        ]
        for r, (label, key) in enumerate(rows):
            grid.addWidget(QLabel(label), r, 0)
            val = QLabel("—")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(val, r, 1)
            self._fw_cards[key] = val
        v.addWidget(box)

        self.btn_fw_apply = QPushButton("Aplicar / Reparar")
        self.btn_fw_check = QPushButton("Diagnóstico")
        self.btn_fw_revert = QPushButton("Reverter")
        self.btn_fw_refresh = QPushButton("Atualizar")
        self._register_button(self.btn_fw_apply, "fw_apply")
        self._register_button(self.btn_fw_check, "fw_check")
        self._register_button(self.btn_fw_revert, "fw_revert")

        row = QHBoxLayout()
        row.addWidget(self.btn_fw_apply)
        row.addWidget(self.btn_fw_check)
        row.addWidget(self.btn_fw_revert)
        row.addStretch(1)
        row.addWidget(self.btn_fw_refresh)
        v.addLayout(row)

        note = QLabel(
            "Aplicar/Reparar: corrige forwarding, NAT e zona do firewalld e "
            "instala a persistência. Diagnóstico: executa o check sem alterar nada."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{MUTED};")
        v.addWidget(note)
        v.addStretch(1)
        return tab

    def _build_media_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)

        box = QGroupBox("Mídia do WhatsApp")
        box_v = QVBoxLayout(box)
        info = QLabel(
            "As mídias novas já caem direto em ~/Waydroid/WhatsApp/ via bind. "
            "Este botão copia as mídias que já existiam antes do bind: ele "
            "desmonta o bind, copia do Android e reaplica."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color:{MUTED};")
        box_v.addWidget(info)
        self.btn_media_copy = QPushButton("Copiar mídias existentes")
        self._register_button(self.btn_media_copy, "media_copy")
        box_v.addWidget(self.btn_media_copy, alignment=Qt.AlignLeft)
        v.addWidget(box)
        v.addStretch(1)
        return tab

    def _register_button(self, button: QPushButton, tag: str) -> None:
        self._action_buttons.append(button)
        self._button_tags[button] = tag
        button.setProperty("running", False)

    def _wire(self) -> None:
        self.btn_bind_apply.clicked.connect(self.on_bind_apply)
        self.btn_bind_revert.clicked.connect(self.on_bind_revert)
        self.btn_bind_refresh.clicked.connect(self.refresh_binds)
        self.btn_fw_apply.clicked.connect(self.on_fw_apply)
        self.btn_fw_check.clicked.connect(self.on_fw_check)
        self.btn_fw_revert.clicked.connect(self.on_fw_revert)
        self.btn_fw_refresh.clicked.connect(self.refresh_firewall)
        self.btn_media_copy.clicked.connect(self.on_media_copy)

        self._tabs.currentChanged.connect(self._on_tab_changed)
        self.runner.started.connect(self._on_started)
        self.runner.output.connect(self._on_output)
        self.runner.finished.connect(self._on_finished)

    # ---------- ações ----------

    def on_bind_apply(self) -> None:
        selected = [n for n, cb in self._checks.items() if cb.isChecked()]
        if not selected:
            QMessageBox.information(
                self, "Waydroid Binds", "Selecione ao menos uma pasta para aplicar."
            )
            return
        self.runner.run(
            "bind_apply", [str(paths.BINDS_SCRIPT)] + selected, timeout_ms=120000
        )

    def on_bind_revert(self) -> None:
        answer = QMessageBox.question(
            self,
            "Reverter todos os binds",
            "Isso desmonta todas as pastas compartilhadas e remove a "
            "persistência do boot. Continuar?",
        )
        if answer == QMessageBox.Yes:
            self.runner.run(
                "bind_revert", [str(paths.REVERT_BINDS_SCRIPT)], timeout_ms=60000
            )

    def on_fw_apply(self) -> None:
        self.runner.run("fw_apply", [str(paths.FIREWALL_SCRIPT)], timeout_ms=120000)

    def on_fw_check(self) -> None:
        self.runner.run(
            "fw_check", [str(paths.FIREWALL_SCRIPT), "check"], timeout_ms=60000
        )

    def on_fw_revert(self) -> None:
        self.runner.run(
            "fw_revert", [str(paths.FIREWALL_SCRIPT), "revert"], timeout_ms=60000
        )

    def on_media_copy(self) -> None:
        answer = QMessageBox.question(
            self,
            "Copiar mídias do WhatsApp",
            "O bind do WhatsApp será desmontado temporariamente para copiar "
            "as mídias antigas. Continuar?",
        )
        if answer == QMessageBox.Yes:
            self.runner.run("media_copy", [str(paths.MEDIA_SCRIPT)], timeout_ms=120000)

    # ---------- refresh ----------

    def refresh_binds(self) -> None:
        QTimer.singleShot(0, self._do_refresh_binds)

    def _do_refresh_binds(self) -> None:
        state = status_mod.bind_status()
        for name, label in self._bind_state.items():
            ok = state.get(name, False)
            label.setText(
                colored("MONTADO" if ok else "não montado", GOOD if ok else BAD)
            )

    def refresh_firewall(self) -> None:
        self.runner.run("fw_status", [str(paths.FIREWALL_SCRIPT), "status"])

    def _apply_firewall_status(self, data: dict[str, str]) -> None:
        for key, label in self._fw_cards.items():
            value = data.get(key, "—")
            if key == "ip_forward":
                value = "ON" if value == "1" else "OFF"
                color = GOOD if value == "ON" else BAD
                label.setText(colored(value, color))
            elif key == "connectivity":
                color = GOOD if value == "OK" else BAD if value == "FAIL" else MUTED
                label.setText(colored(value, color))
            elif key == "forward_policy":
                color = GOOD if value == "ACCEPT" else BAD
                label.setText(colored(value, color))
            elif key == "zone":
                color = GOOD if value == "trusted" else WARN if value else BAD
                label.setText(colored(value or "—", color))
            elif key == "container":
                color = GOOD if value == "active" else MUTED
                label.setText(colored(value, color))
            else:
                label.setText(value)

    def _on_tab_changed(self, index: int) -> None:
        if index == 1:
            self.refresh_firewall()

    # ---------- runner ----------

    def _on_started(self, tag: str, display: str) -> None:
        self._running_tags.add(tag)
        self._set_button_running(tag, True)
        self._progress.setVisible(True)
        self.log(f"→ {display}")

    def _on_output(self, tag: str, line: str) -> None:
        self.log(f"    {line}")

    def _on_finished(self, tag: str, stdout: str, stderr: str, code: int) -> None:
        self._running_tags.discard(tag)
        self._set_button_running(tag, False)
        if not self._running_tags:
            self._progress.setVisible(False)
        self._log_result(stdout, stderr, code)

        if tag == "fw_status":
            self._apply_firewall_status(status_mod.parse_firewall_status(stdout))
        elif tag in ("bind_apply", "bind_revert"):
            self.refresh_binds()
        elif tag in ("fw_apply", "fw_check", "fw_revert"):
            self.refresh_firewall()

    def _set_button_running(self, tag: str, running: bool) -> None:
        for button, button_tag in self._button_tags.items():
            if button_tag == tag:
                button.setProperty("running", running)
                button.setEnabled(not running)
                button.style().unpolish(button)
                button.style().polish(button)
                break

    def _log_result(self, stdout: str, stderr: str, code: int) -> None:
        if code == 0:
            self.log("[OK] tarefa concluída")
        else:
            self.log(f"[ERRO] falha (código {code})")

    def log(self, text: str) -> None:
        stamp = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
        self._log.appendPlainText(f"[{stamp}] {text}")
        self._log.moveCursor(QTextCursor.End)
