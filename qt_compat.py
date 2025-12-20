"""Compatibility layer for Qt bindings.

Tries to import PySide6 first and falls back to PyQt5 if necessary.
Exposes QtWidgets, QtCore, QtGui, and Signal/Slot helpers for convenience.
"""

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    Signal = QtCore.Signal
    Slot = QtCore.Slot
except ImportError:  # pragma: no cover - fallback when PySide6 unavailable
    from PyQt5 import QtWidgets, QtCore, QtGui
    Signal = QtCore.pyqtSignal
    Slot = QtCore.pyqtSlot

__all__ = ["QtWidgets", "QtCore", "QtGui", "Signal", "Slot"]
