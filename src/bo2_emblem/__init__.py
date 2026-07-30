"""
BO2 Emblem Studio - Complete Python Package
============================================
A comprehensive toolkit for working with Call of Duty: Black Ops II
/ Plutonium T6 emblem files (.emblem / .bin).

Features:
- Full parser/serializer for 1408-byte emblem format (32 layers × 44 bytes)
- Pixel-perfect renderer using reference shape glyphs
- Image-to-emblem converter (PNG, JPEG, WebP, BMP, SVG)
- Layer optimizer (reduces to 32 layers with 95%+ fidelity)
- AI text-to-emblem generator
- Hermes AI integration for advanced emblem generation
- Plutonium T6 exporter (auto-copies to game directory)
- Shape database with 260+ confirmed shape IDs
- Modern GUI editor (PySide6)

Installation:
    pip install -r requirements.txt

Quick Start:
    from bo2_emblem import load_emblem, save_emblem, render_emblem
    
    # Load existing emblem
    layers = load_emblem("1#emblem.emblem")
    
    # Render to PNG
    render_emblem(layers, size=512, output_path="preview.png")
    
    # Create new emblem
    from bo2_emblem import EmblemLayer
    layers = [
        EmblemLayer(index=0, shape_id=137, r=1.0, g=0.0, b=0.0),  # Red half-circle
        EmblemLayer(index=1, shape_id=217, r=0.0, g=1.0, b=0.0),  # Green Letter A
    ]
    save_emblem("my_emblem.emblem", layers)
    
    # Export to Plutonium
    from bo2_emblem import export_to_plutonium
    export_to_plutonium(layers, slot=1)

Modules:
    parser      - EmblemParser, EmblemLayer
    serializer  - EmblemSerializer
    renderer    - EmblemRenderer
    importer    - ImageImporter
    exporter    - EmblemExporter
    optimizer   - EmblemOptimizer
    ai          - EmblemAIGenerator
    ai_hermes   - Hermes AI integration
    shape_map   - SHAPE_ID_MAP, lookup functions
"""

from .parser import EmblemParser, EmblemLayer, load_emblem, load_emblem_bytes
from .serializer import EmblemSerializer, save_emblem, save_emblem_with_http, layers_to_bytes
from .renderer import EmblemRenderer, render_emblem, render_emblem_file, render_emblem_layers
from .importer import ImageImporter, import_image_to_emblem, import_image_and_render, ImportConfig
from .exporter import EmblemExporter, export_to_plutonium, list_plutonium_emblems, ExportConfig
from .optimizer import EmblemOptimizer, optimize_emblem, OptimizerConfig
from .ai import EmblemAIGenerator, generate_emblem_from_prompt, generate_emblem_complex
from .ai_hermes import (
    AIProvider,
    HermesConfig,
    EmblemConcept,
    EmblemPlan,
    HermesClient,
    AIConfigManager,
    generate_emblem,
    generate_emblem_async,
)
from .shape_map import (
    SHAPE_ID_MAP,
    get_shape_name,
    get_shape_category,
    get_shape_id,
    get_ids_by_category,
    list_categories,
    CATEGORY_ORDER,
    TOTAL_SHAPES,
)

__version__ = "1.0.0"
__author__ = "BO2 Emblem Studio"
__license__ = "MIT"

__all__ = [
    # Core classes
    "EmblemParser",
    "EmblemLayer",
    "EmblemSerializer",
    "EmblemRenderer",
    "ImageImporter",
    "EmblemExporter",
    "EmblemOptimizer",
    "EmblemAIGenerator",
    
    # AI Hermes classes
    "AIProvider",
    "HermesConfig",
    "EmblemConcept",
    "EmblemPlan",
    "HermesClient",
    "AIConfigManager",
    
    # Config classes
    "ImportConfig",
    "ExportConfig",
    "OptimizerConfig",
    
    # Convenience functions
    "load_emblem",
    "load_emblem_bytes",
    "save_emblem",
    "save_emblem_with_http",
    "layers_to_bytes",
    "render_emblem",
    "render_emblem_file",
    "render_emblem_layers",
    "import_image_to_emblem",
    "import_image_and_render",
    "export_to_plutonium",
    "list_plutonium_emblems",
    "optimize_emblem",
    "generate_emblem_from_prompt",
    "generate_emblem_complex",
    "generate_emblem",
    "generate_emblem_async",
    
    # Shape map
    "SHAPE_ID_MAP",
    "get_shape_name",
    "get_shape_category",
    "get_shape_id",
    "get_ids_by_category",
    "list_categories",
    "CATEGORY_ORDER",
    "TOTAL_SHAPES",
]

# Package metadata
__package_info__ = {
    "name": "bo2-emblem-studio",
    "version": __version__,
    "description": "Complete toolkit for BO2/Plutonium T6 emblem editing",
    "homepage": "https://github.com/yourusername/bo2-emblem-studio",
    "license": __license__,
    "python_requires": ">=3.9",
    "requires": [
        "Pillow>=9.0",
        "numpy>=1.21",
        "scipy>=1.7",
    ],
    "extras_require": {
        "gui": ["PySide6>=6.4"],
        "ai": ["aiohttp>=3.8"],
        "dev": ["pytest>=7.0", "black", "mypy"],
    },
}