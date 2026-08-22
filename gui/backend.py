"""Execução assíncrona de comandos (com pkexec) via QProcess."""

import os

from PySide6.QtCore import QObject, QProcess, QTimer, Signal


class TaskRunner(QObject):
    """Roda tarefas em background sem travar a UI.

    Sinais:
        started(tag, display): a tarefa começou (display = linha de comando).
        output(tag, line): uma linha de stdout/stderr em tempo real.
        finished(tag, stdout, stderr, exit_code): a tarefa terminou.
    """

    started = Signal(str, str)
    output = Signal(str, str)
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

    def run(
        self,
        tag: str,
        command: list[str],
        use_pkexec: bool = True,
        timeout_ms: int = 0,
    ) -> None:
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
            command = ["pkexec"] + command
        proc = QProcess(self)
        proc.setProgram(command[0])
        proc.setArguments(command[1:])
        task = {
            "tag": tag,
            "proc": proc,
            "out": bytearray(),
            "err": bytearray(),
            "timeout_timer": None,
        }
        if timeout_ms > 0:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._kill_task(task))
            timer.start(timeout_ms)
            task["timeout_timer"] = timer
        self._tasks.append(task)
        proc.readyReadStandardOutput.connect(lambda: self._read_stdout(task))
        proc.readyReadStandardError.connect(lambda: self._read_stderr(task))
        proc.finished.connect(lambda code, _status: self._finish(task, code))
        self.started.emit(tag, " ".join(command))
        proc.start()

    def _read_stdout(self, task: dict) -> None:
        data = bytes(task["proc"].readAllStandardOutput())
        task["out"] += data
        text = data.decode("utf-8", "replace")
        for line in text.rstrip().splitlines():
            self.output.emit(task["tag"], line)

    def _read_stderr(self, task: dict) -> None:
        data = bytes(task["proc"].readAllStandardError())
        task["err"] += data
        text = data.decode("utf-8", "replace")
        for line in text.rstrip().splitlines():
            self.output.emit(task["tag"], "ERR " + line)

    def _finish(self, task: dict, code: int) -> None:
        if task["timeout_timer"]:
            task["timeout_timer"].stop()
        if task in self._tasks:
            self._tasks.remove(task)
        stdout = task["out"].decode("utf-8", "replace")
        stderr = task["err"].decode("utf-8", "replace")
        self.finished.emit(task["tag"], stdout, stderr, code)

    def _kill_task(self, task: dict) -> None:
        proc = task["proc"]
        if proc.state() != QProcess.NotRunning:
            proc.kill()
            proc.waitForFinished(1000)

    def cancel(self, tag: str) -> bool:
        for task in self._tasks:
            if task["tag"] == tag:
                self._kill_task(task)
                return True
        return False

    def cancel_all(self) -> None:
        for task in self._tasks[:]:
            self._kill_task(task)
