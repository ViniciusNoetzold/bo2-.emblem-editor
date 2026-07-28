"""
BO2 Emblem Studio - GUI Module
==============================
Modern PySide6-based editor for BO2 emblems.
"""

try:
    from .gui.editor import EmblemEditor
    from .gui.widgets import (
        ShapeListWidget, LayerListWidget, PropertyPanel, PreviewWidget
    )
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    EmblemEditor = None

__all__ = ["EmblemEditor", "GUI_AVAILABLE"]