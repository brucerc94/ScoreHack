from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtQuickControls2 import QQuickStyle

from app.core.logging_utils import configure_logging
from app.ui.controller import AppController


def run() -> int:
    configure_logging()
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    app.setApplicationName("ScoreCapture")
    app.setOrganizationName("Bruno Rivas")

    icon = Path(__file__).resolve().parents[2] / "icon.ico"
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))

    controller = AppController()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", controller)

    qml_path = Path(__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))

    if not engine.rootObjects():
        controller.close()
        return 1

    exit_code = app.exec()
    controller.close()
    return exit_code
