"""
BO2 Emblem Studio - GUI Module
==============================
Modern PySide6-based editor for BO2 emblems.
"""

try:
    from .editor import EmblemEditor, main
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    EmblemEditor = None
    main = None

__all__ = ["EmblemEditor", "GUI_AVAILABLE", "main"]