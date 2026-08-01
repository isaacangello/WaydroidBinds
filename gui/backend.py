"""Execução assíncrona de comandos (com ou sem pkexec) via QProcess."""

import os

from PySide6.QtCore import QObject, QProcess, QTimer, Signal


def _hostify(path: str) -> str:
    """Dentro de um sandbox Flatpak, /app/* existe apenas no sandbox; o host
    precisa do pacote nativo em /usr/*."""
    if path.startswith("/app/"):
        return path.replace("/app/", "/usr/", 1)
    return path


class TaskRunner(QObject):
    """Roda tarefas em background sem travar a UI.

    Sinais:
        started(tag, display): a tarefa começou (display = linha de comando).
        finished(tag, stdout, stderr, exit_code): a tarefa terminou.
    """

    started = Signal(str, str)
    finished = Signal(str, str, str, int)

    def __init__(self, parent=None, dry_run: bool = False) -> None:
        super().__init__(parent)
        self._dry_run = dry_run
        self._tasks = []

    @property
    def dry_run(self) -> bool:
        return self._dry_run

    def busy(self) -> bool:
        return bool(self._tasks)

    def run(self, tag: str, command: list[str], use_pkexec: bool = True) -> None:
        if isinstance(command, str):
            command = command.split()
        command = list(command)
        if not command or not os.path.exists(command[0]):
            self.finished.emit(
                tag,
                "",
                f"ERRO: comando não encontrado: {command[0] if command else '?'}",
                127,
            )
            return
        if self._dry_run:
            line = ("pkexec " + " ".join(command)) if use_pkexec else " ".join(command)
            self.started.emit(tag, "[DRY-RUN] " + line)
            QTimer.singleShot(300, lambda: self.finished.emit(tag, "", "", 0))
            return
        if use_pkexec:
            if os.environ.get("FLATPAK_ID"):
                command = ["flatpak-spawn", "--host", "pkexec"] + [
                    _hostify(c) for c in command
                ]
            else:
                command = ["pkexec"] + command
        proc = QProcess(self)
        proc.setProgram(command[0])
        proc.setArguments(command[1:])
        task = {"tag": tag, "proc": proc, "out": bytearray(), "err": bytearray()}
        self._tasks.append(task)
        proc.readyReadStandardOutput.connect(lambda: self._read_stdout(task))
        proc.readyReadStandardError.connect(lambda: self._read_stderr(task))
        proc.finished.connect(lambda code, _status: self._finish(task, code))
        self.started.emit(tag, " ".join(command))
        proc.start()

    def _read_stdout(self, task: dict) -> None:
        task["out"] += bytes(task["proc"].readAllStandardOutput())

    def _read_stderr(self, task: dict) -> None:
        task["err"] += bytes(task["proc"].readAllStandardError())

    def _finish(self, task: dict, code: int) -> None:
        if task in self._tasks:
            self._tasks.remove(task)
        stdout = task["out"].decode("utf-8", "replace")
        stderr = task["err"].decode("utf-8", "replace")
        self.finished.emit(task["tag"], stdout, stderr, code)
