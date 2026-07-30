"""
BO2 Emblem Studio - GUI Entry Point
===================================
This allows running the GUI with: python -m bo2_emblem.gui
"""

import sys
import os

# Add src to path for absolute imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from bo2_emblem.gui.editor import main

if __name__ == "__main__":
    main()