"""Janela principal do Waydroid Binds."""

from datetime import UTC, datetime

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
    # Tags de tarefas silenciosas: nada no log, nada na barra de progresso
    # (sys_status roda a cada 30s — poluiria o log).
    _QUIET_TAGS = frozenset({"sys_status"})
    # Tarefas longas que logam mas não mostram barra (Android aberto = horas)
    _NO_PROGRESS_TAGS = frozenset({"open_android"})

    def __init__(self, runner: TaskRunner) -> None:
        super().__init__()
        self.runner = runner
        self._running_tags: set[str] = set()
        self._checks: dict[str, QCheckBox] = {}
        self._bind_state: dict[str, QLabel] = {}
        self._fw_cards: dict[str, QLabel] = {}
        self._st_cards: dict[str, QLabel] = {}
        self._fw_cache: dict[str, str] = {}
        self._action_buttons: list[QPushButton] = []
        self._button_tags: dict[QPushButton, str] = {}

        self.setWindowTitle(self.tr("Waydroid Binds", "window_title"))
        self.resize(880, 660)

        self._build_ui()
        self._wire()

        self.refresh_binds()

        self._timer = QTimer(self)
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self.refresh_binds)
        self._timer.start()

        # Auto-refresh da aba Status (só roda enquanto a aba está aberta)
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(30000)
        self._status_timer.timeout.connect(self.refresh_status)

        if self.runner.dry_run:
            self.statusBar().showMessage(
                self.tr(
                    "MODO DRY-RUN — nenhum comando será executado de verdade",
                    "statusbar",
                )
            )

    # ---------- UI ----------

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        self._tabs = QTabWidget()
        self._tabs.addTab(
            self._build_binds_tab(), self.tr("Pastas compartilhadas", "tab")
        )
        self._tabs.addTab(self._build_firewall_tab(), self.tr("Rede / Firewall", "tab"))
        self._tabs.addTab(self._build_media_tab(), self.tr("Mídia do WhatsApp", "tab"))
        self._tabs.addTab(self._build_status_tab(), self.tr("Status", "tab"))

        log_box = QGroupBox(self.tr("Log", "groupbox"))
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

        box = QGroupBox(self.tr("Pastas compartilhadas (Host → Android)", "groupbox"))
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

        self.btn_bind_apply = QPushButton(self.tr("Aplicar selecionados", "button"))
        self.btn_bind_revert = QPushButton(self.tr("Reverter todos", "button"))
        self.btn_bind_refresh = QPushButton(self.tr("Atualizar", "button"))
        self._register_button(self.btn_bind_apply, "bind_apply")
        self._register_button(self.btn_bind_revert, "bind_revert")

        row = QHBoxLayout()
        row.addWidget(self.btn_bind_apply)
        row.addWidget(self.btn_bind_revert)
        row.addStretch(1)
        row.addWidget(self.btn_bind_refresh)
        v.addLayout(row)

        note = QLabel(
            self.tr(
                "Aplicar: monta as pastas selecionadas e persiste no boot "
                "(waydroid-startup-scripts). Reverter todos: desmonta tudo e "
                "remove a persistência.",
                "note",
            )
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{MUTED};")
        v.addWidget(note)
        v.addStretch(1)
        return tab

    def _build_firewall_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)

        box = QGroupBox(self.tr("Rede / Firewall do Waydroid", "groupbox"))
        grid = QGridLayout(box)
        grid.setColumnStretch(1, 1)
        rows = [
            (self.tr("IP forwarding", "label"), "ip_forward"),
            (self.tr("Firewall ativo", "label"), "firewall"),
            (self.tr("Rede do container", "label"), "waydroid_net"),
            (self.tr("Interface de internet", "label"), "default_iface"),
            (self.tr("Política FORWARD", "label"), "forward_policy"),
            (self.tr("Zona (firewalld)", "label"), "zone"),
            (self.tr("Container", "label"), "container"),
            (self.tr("Conectividade (ping)", "label"), "connectivity"),
        ]
        for r, (label, key) in enumerate(rows):
            grid.addWidget(QLabel(label), r, 0)
            val = QLabel("—")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(val, r, 1)
            self._fw_cards[key] = val
        v.addWidget(box)

        self.btn_fw_apply = QPushButton(self.tr("Aplicar / Reparar", "button"))
        self.btn_fw_check = QPushButton(self.tr("Diagnóstico", "button"))
        self.btn_fw_revert = QPushButton(self.tr("Reverter", "button"))
        self.btn_fw_refresh = QPushButton(self.tr("Atualizar", "button"))
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
            self.tr(
                "Aplicar/Reparar: corrige forwarding, NAT e zona do firewalld e "
                "instala a persistência. Diagnóstico: executa o check sem alterar nada.",
                "note",
            )
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{MUTED};")
        v.addWidget(note)
        v.addStretch(1)
        return tab

    def _build_media_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)

        box = QGroupBox(self.tr("Mídia do WhatsApp", "groupbox"))
        box_v = QVBoxLayout(box)
        info = QLabel(
            self.tr(
                "As mídias novas já caem direto em ~/Waydroid/WhatsApp/ via bind. "
                "Este botão copia as mídias que já existiam antes do bind: ele "
                "desmonta o bind, copia do Android e reaplica.",
                "note",
            )
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color:{MUTED};")
        box_v.addWidget(info)
        self.btn_media_copy = QPushButton(self.tr("Copiar mídias existentes", "button"))
        self._register_button(self.btn_media_copy, "media_copy")
        box_v.addWidget(self.btn_media_copy, alignment=Qt.AlignLeft)
        v.addWidget(box)
        v.addStretch(1)
        return tab

    def _build_status_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)

        box = QGroupBox(self.tr("Estado do Waydroid", "groupbox"))
        grid = QGridLayout(box)
        grid.setColumnStretch(1, 1)
        rows = [
            (self.tr("Serviço (systemd)", "label"), "container"),
            (self.tr("Container Android", "label"), "wcontainer"),
            (self.tr("Serviço no boot", "label"), "enabled"),
            (self.tr("Sessão (GUI)", "label"), "session"),
            (self.tr("Uptime", "label"), "uptime"),
            (self.tr("Versão do Waydroid", "label"), "version"),
            (self.tr("Tipo de imagem", "label"), "vendor"),
            (self.tr("Distribuição Android", "label"), "distro"),
            (self.tr("IP do Android", "label"), "android_ip"),
        ]
        for r, (label, key) in enumerate(rows):
            grid.addWidget(QLabel(label), r, 0)
            val = QLabel("—")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(val, r, 1)
            self._st_cards[key] = val
        v.addWidget(box)

        box = QGroupBox(self.tr("Recursos", "groupbox"))
        grid = QGridLayout(box)
        grid.setColumnStretch(1, 1)
        rows = [
            (self.tr("Kernel binder", "label"), "binder"),
            (self.tr("Disco (partição)", "label"), "disk"),
        ]
        for r, (label, key) in enumerate(rows):
            grid.addWidget(QLabel(label), r, 0)
            val = QLabel("—")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(val, r, 1)
            self._st_cards[key] = val
        v.addWidget(box)

        box = QGroupBox(self.tr("Resumo", "groupbox"))
        grid = QGridLayout(box)
        grid.setColumnStretch(1, 1)
        rows = [
            (self.tr("Pastas montadas", "label"), "binds"),
            (self.tr("Internet", "label"), "internet"),
        ]
        for r, (label, key) in enumerate(rows):
            grid.addWidget(QLabel(label), r, 0)
            val = QLabel("—")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(val, r, 1)
            self._st_cards[key] = val
        v.addWidget(box)

        self.btn_st_open = QPushButton(self.tr("Abrir Android (GUI)", "button"))
        self.btn_st_refresh = QPushButton(self.tr("Atualizar", "button"))
        self._register_button(self.btn_st_refresh, "sys_status")

        row = QHBoxLayout()
        row.addWidget(self.btn_st_open)
        row.addStretch(1)
        row.addWidget(self.btn_st_refresh)
        v.addLayout(row)

        note = QLabel(
            self.tr(
                "Atualiza automaticamente a cada 30 segundos enquanto esta aba "
                "estiver aberta. Nenhum comando desta aba pede senha.",
                "note",
            )
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{MUTED};")
        v.addWidget(note)
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
        self.btn_st_refresh.clicked.connect(self.refresh_status)
        self.btn_st_open.clicked.connect(self.on_open_android)

        self._tabs.currentChanged.connect(self._on_tab_changed)
        self.runner.started.connect(self._on_started)
        self.runner.output.connect(self._on_output)
        self.runner.finished.connect(self._on_finished)

    # ---------- ações ----------

    def on_bind_apply(self) -> None:
        selected = [n for n, cb in self._checks.items() if cb.isChecked()]
        if not selected:
            QMessageBox.information(
                self,
                self.tr("Waydroid Binds", "dialog_title"),
                self.tr("Selecione ao menos uma pasta para aplicar.", "dialog_msg"),
            )
            return
        self.runner.run(
            "bind_apply", [str(paths.BINDS_SCRIPT)] + selected, timeout_ms=120000
        )

    def on_bind_revert(self) -> None:
        answer = QMessageBox.question(
            self,
            self.tr("Reverter todos os binds", "dialog_title"),
            self.tr(
                "Isso desmonta todas as pastas compartilhadas e remove a "
                "persistência do boot. Continuar?",
                "dialog_msg",
            ),
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
            self.tr("Copiar mídias do WhatsApp", "dialog_title"),
            self.tr(
                "O bind do WhatsApp será desmontado temporariamente para copiar "
                "as mídias antigas. Continuar?",
                "dialog_msg",
            ),
        )
        if answer == QMessageBox.Yes:
            self.runner.run("media_copy", [str(paths.MEDIA_SCRIPT)], timeout_ms=120000)

    def on_open_android(self) -> None:
        # Sem pkexec: 'waydroid show-full-ui' roda como usuário.
        # Sem timeout (0): a GUI do Android fica aberta indefinidamente.
        self.runner.run("open_android", ["waydroid", "show-full-ui"], use_pkexec=False)

    # ---------- refresh ----------

    def refresh_binds(self) -> None:
        QTimer.singleShot(0, self._do_refresh_binds)

    def _do_refresh_binds(self) -> None:
        state = status_mod.bind_status()
        for name, label in self._bind_state.items():
            ok = state.get(name, False)
            label.setText(
                colored(
                    self.tr("MONTADO", "status")
                    if ok
                    else self.tr("não montado", "status"),
                    GOOD if ok else BAD,
                )
            )

    def refresh_firewall(self) -> None:
        self.runner.run("fw_status", [str(paths.FIREWALL_SCRIPT), "status"])

    def refresh_status(self) -> None:
        self.runner.run(
            "sys_status",
            ["bash", "-c", status_mod.STATUS_SCRIPT],
            use_pkexec=False,
            timeout_ms=15000,
        )

    def _apply_status(self, data: dict[str, str]) -> None:
        container = data.get("container", "unknown")
        if container == "active":
            text, color = self.tr("rodando", "status"), GOOD
        elif container == "inactive":
            text, color = self.tr("parado", "status"), MUTED
        elif container == "failed":
            text, color = self.tr("falhou", "status"), BAD
        else:
            text, color = container, WARN
        self._st_cards["container"].setText(colored(text, color))

        enabled = data.get("enabled", "unknown")
        if enabled == "enabled":
            text, color = self.tr("habilitado", "status"), GOOD
        elif enabled == "disabled":
            text, color = self.tr("desabilitado", "status"), BAD
        else:
            text, color = enabled, MUTED
        self._st_cards["enabled"].setText(colored(text, color))

        session = data.get("session", "none")
        if session == "RUNNING":
            text, color = self.tr("ativa", "status"), GOOD
        elif session in ("none", "None", "STOPPED"):
            text, color = self.tr("inativa", "status"), MUTED
        elif session == "unknown":
            text, color = "—", MUTED
        else:
            text, color = session, WARN
        self._st_cards["session"].setText(colored(text, color))
        # 'Abrir Android (GUI)' só faz sentido sem sessão ativa
        self.btn_st_open.setEnabled(session != "RUNNING")

        wcontainer = data.get("wcontainer", "none")
        if wcontainer == "RUNNING":
            text, color = self.tr("rodando", "status"), GOOD
        elif wcontainer in ("STOPPED", "none", "None"):
            text, color = self.tr("parado", "status"), MUTED
        else:
            text, color = "—", MUTED
        self._st_cards["wcontainer"].setText(colored(text, color))

        self._st_cards["uptime"].setText(
            status_mod.format_uptime(data.get("uptime", "0"))
            if container == "active"
            else "—"
        )

        version = data.get("version", "")
        self._st_cards["version"].setText(version or "—")

        vendor = data.get("vendor", "")
        self._st_cards["vendor"].setText(vendor or "—")

        product = data.get("distro_product", "")
        android_v = data.get("distro_android", "")
        distro = status_mod.distro_display(product, android_v)
        self._st_cards["distro"].setText(distro or "—")
        if distro:
            tip = f"Android {android_v}" if android_v else distro
            if product:
                tip += f" · {product}"
            self._st_cards["distro"].setToolTip(tip)
        else:
            self._st_cards["distro"].setToolTip("")

        android_ip = data.get("android_ip", "")
        self._st_cards["android_ip"].setText(android_ip or "—")

        binder = data.get("binder", "missing")
        if binder == "ok":
            text, color = self.tr("OK", "status"), GOOD
        else:
            text, color = self.tr("ausente", "status"), BAD
        self._st_cards["binder"].setText(colored(text, color))

        disk = data.get("disk", "")
        self._st_cards["disk"].setText(disk or "—")

        binds = status_mod.bind_status()
        mounted = sum(1 for ok in binds.values() if ok)
        total = len(binds_mod.BINDS)
        if mounted == total:
            color = GOOD
        elif mounted == 0:
            color = BAD
        else:
            color = WARN
        self._st_cards["binds"].setText(colored(f"{mounted}/{total}", color))

        conn = self._fw_cache.get("connectivity", "")
        if conn == "OK":
            text, color = self.tr("OK", "status"), GOOD
        elif conn == "FAIL":
            text, color = self.tr("falhou", "status"), BAD
        else:
            text, color = "—", MUTED
        self._st_cards["internet"].setText(colored(text, color))

    def _apply_firewall_status(self, data: dict[str, str]) -> None:
        self._fw_cache = data  # reutilizado pela aba Status (sem novo pkexec)
        for key, label in self._fw_cards.items():
            value = data.get(key, "—")
            if key == "ip_forward":
                value = (
                    self.tr("ON", "status")
                    if value == "1"
                    else self.tr("OFF", "status")
                )
                color = GOOD if value == self.tr("ON", "status") else BAD
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
        if index == 3:
            self.refresh_status()
            self._status_timer.start()
        else:
            self._status_timer.stop()

    # ---------- runner ----------

    def _on_started(self, tag: str, display: str) -> None:
        self._running_tags.add(tag)
        self._set_button_running(tag, True)
        if tag in self._QUIET_TAGS:
            return
        if tag not in self._NO_PROGRESS_TAGS:
            self._progress.setVisible(True)
        self.log(f"→ {display}")

    def _on_output(self, tag: str, line: str) -> None:
        if tag not in self._QUIET_TAGS:
            self.log(f"    {line}")

    def _on_finished(self, tag: str, stdout: str, stderr: str, code: int) -> None:
        self._running_tags.discard(tag)
        self._set_button_running(tag, False)
        if not self._progress_tasks():
            self._progress.setVisible(False)
        # Tarefas silenciosas só aparecem no log quando FALHAM
        if tag not in self._QUIET_TAGS or code != 0:
            self._log_result(stdout, stderr, code)

        if tag == "fw_status":
            self._apply_firewall_status(status_mod.parse_firewall_status(stdout))
        elif tag == "sys_status":
            self._apply_status(status_mod.parse_firewall_status(stdout))
        elif tag in ("bind_apply", "bind_revert"):
            self.refresh_binds()
        elif tag in ("fw_apply", "fw_check", "fw_revert"):
            self.refresh_firewall()

    def _progress_tasks(self) -> set[str]:
        """Tags rodando que de fato exibem barra de progresso."""
        return self._running_tags - self._NO_PROGRESS_TAGS - self._QUIET_TAGS

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
            self.log(self.tr("[OK] tarefa concluída", "log"))
        else:
            self.log(self.tr("[ERRO] falha (código {code})", "log").format(code=code))

    def log(self, text: str) -> None:
        stamp = datetime.now(UTC).astimezone().strftime("%H:%M:%S")
        self._log.appendPlainText(f"[{stamp}] {text}")
        self._log.moveCursor(QTextCursor.End)
