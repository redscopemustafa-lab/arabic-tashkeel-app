"""Compatibility layer for Qt bindings.

The project standardises on PySide6. This module exists mostly to provide
concise imports for widgets/core/gui elements and Signal/Slot helpers.
"""

from PySide6 import QtWidgets, QtCore, QtGui

Signal = QtCore.Signal
Slot = QtCore.Slot

__all__ = ["QtWidgets", "QtCore", "QtGui", "Signal", "Slot"]
