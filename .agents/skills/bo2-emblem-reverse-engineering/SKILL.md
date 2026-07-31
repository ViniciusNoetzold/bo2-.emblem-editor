---
name: bo2-emblem-reverse-engineering
description: "Complete workflow for reverse engineering Call of Duty Black Ops II / Plutonium T6 emblem file format (.emblem/.bin) and building tooling"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [reverse-engineering, binary-parsing, game-modding, python, pyside6, pytest, tdd]
    related_skills: [test-driven-development, systematic-debugging, plan]
---

# BO2 Emblem Reverse Engineering & Tooling

Complete workflow for reverse engineering the BO2/Plutonium T6 emblem binary format and building professional tooling.

## What This Covers

- Binary format analysis (1408 bytes = 32 layers × 44 bytes)
- Shape ID mapping (260+ confirmed IDs across 5 categories)
- Pixel-perfect rendering with reference shape glyphs
- Image-to-emblem conversion (PNG/JPG/WebP/BMP/SVG)
- Layer optimization (32-layer limit with 95%+ fidelity)
- AI text-to-emblem generation
- Plutonium T6 auto-exporter
- Modern PySide6 GUI editor

## Reverse Engineering Sources

| Repository | Purpose |
|------------|---------|
| 505e06b2/Black-Ops-2-Emblem-Editor | Web editor emulator, example emblems |
| alexkotr1/bo2-emblem-toolkit | Proxy tool, parser, renderer, shape maps |
| olie304/CallOfDutyEmblemSpecs | Format specification document |
| ogarsan/Black-Ops-2-Emblem-Master | AI-powered fork |
| davideloi55-prog/BO2-Emblem-Generator | Image-to-emblem converter |

All cloned to `research/` directory during Phase 1.

## File Format Specification

```
1408 bytes = 32 layers × 44 bytes

Layer (44 bytes):
- uint16 shapeId (0xFFFF = empty)
- uint16 padding
- float32 r, g, b, a (0.0-1.0)
- float32 posX, posY (fraction from center, +Y = DOWN)
- float32 scaleX, scaleY (log2 scale: true_scale = 2^value)
- float32 rotation (degrees, clockwise)
- uint8 outlined (bool)
- uint8 flipped (bool)
- uint16 padding
```

## Shape ID Categories

| Category | IDs | Count | Description |
|----------|-----|-------|-------------|
| tools | 137-197 | 61 | Basic shapes (circles, squares, stars) |
| type | 217-252 | 36 | Letters A-Z, Numbers 0-9 |
| emblems | 38-136, 253-259 | 106 | Pre-made game icons |
| ranks | 198-216 | 19 | Military ranks |
| gear | 0-37, 260 | 39 | Weapon/perk qualifications |

## Project Structure

```
BO2 Emblem Studio/
├── src/bo2_emblem/
│   ├── parser.py        # EmblemParser, EmblemLayer
│   ├── serializer.py    # EmblemSerializer
│   ├── renderer.py      # EmblemRenderer (pixel-perfect)
│   ├── importer.py      # ImageImporter
│   ├── exporter.py      # EmblemExporter (Plutonium auto-copy)
│   ├── optimizer.py     # EmblemOptimizer (32-layer limit)
│   ├── ai.py            # EmblemAIGenerator (text→emblem)
│   ├── shape_map.py     # 260+ shape IDs
│   └── gui/             # PySide6 editor
├── tests/
│   └── test_emblem.py   # 27 tests (26 pass, 1 skip)
├── docs/
│   └── reverse_engineering.md
├── database/
│   └── shapes.json      # Complete shape database
├── references/
│   ├── format-specification.md
│   ├── shape-id-map.md
│   └── plutonium-header-format.md
├── scripts/
│   └── verify_emblem_format.py
└── requirements.txt
```

## Key Implementation Patterns

### 1. Parser (parser.py)
```python
# 44-byte layer: <Hxx9fBBxx
LAYER_FORMAT = "<Hxx9fBBxx"
# shape_id, r,g,b,a, pos_x,pos_y, scale_x,scale_y, rotation, outlined, flipped
```

### 2. Serializer (serializer.py)
- Round-trip verified: serialize → parse → identical
- Empty layers filled with 0xFFFF

### 3. Renderer (renderer.py)
- Reference shapes: LA (luminance+alpha) PNGs
- Tinting: white glyph × layer color × layer alpha
- True scale = 2^scale (not linear)
- Position: pos × size from center
- Layer order: lower index = behind

### 4. Optimizer (optimizer.py)
- Merge similar layers (color/position/scale tolerance)
- Remove low-impact layers (render diff measurement)
- Iterative with fidelity target

### 5. Exporter (exporter.py)
- Auto-detects `%localappdata%\Plutonium\storage\t6\players\`
- Backups existing emblems before overwrite
- Verifies write by re-parsing

### 6. Hermes AI Integration (ai_hermes.py)
- **Multi-provider support**: Local (Hermes Agent), OpenAI, Anthropic, Google, NVIDIA, OpenRouter, Ollama, LM Studio, vLLM, Custom (OpenAI-compatible)
- **Async client** with aiohttp for all providers
- **Structured prompt engineering** with BO2-specific system prompt (32 layers, shape IDs, coordinate system, composition principles)
- **JSON response parsing** with provider-specific handlers (OpenAI, Anthropic, Google, OpenRouter formats)
- **Config persistence** via `AIConfigManager` (saves to `ai_config.json`)
- **GUI Integration** (editor.py): AI Studio tab with provider dropdown, endpoint/model/key fields, test connection, generate/refine/recreate/improve buttons, style/symmetry/complexity/max-layers controls, live preview, log console

#### Local Hermes Agent Config (No API Key)
```python
Provider: "Local (Hermes Agent)"
Endpoint: "http://localhost:8080/v1"
Model: "nemotron-3-ultra"  # or your active model
API Key: ""  # Empty for local
```

#### Cloud Provider Configs
| Provider | Endpoint | Model Examples | API Key |
|----------|----------|----------------|---------|
| OpenRouter | `https://openrouter.ai/api/v1` | `nvidia/nemotron-3-ultra`, `anthropic/claude-3.5-sonnet` | Required |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o`, `gpt-4o-mini` | Required |
| Anthropic | `https://api.anthropic.com/v1` | `claude-3-5-sonnet-20241022` | Required |
| NVIDIA | `https://integrate.api.nvidia.com/v1` | `nvidia/nemotron-3-ultra` | Required |
| Ollama (local) | `http://localhost:11434/v1` | `nemotron3-ultra`, `llama3.1:70b` | Not required |
| LM Studio (local) | `http://localhost:1234/v1` | Any loaded GGUF | Not required |

## TDD Workflow Used

Every module followed strict RED→GREEN→REFACTOR:

```bash
# 1. Write failing test
pytest tests/test_emblem.py::TestEmblemParser::test_parse_single_layer -v

# 2. Implement minimal code
# 3. Verify pass
pytest tests/test_emblem.py::TestEmblemParser::test_parse_single_layer -v

# 4. Full suite
pytest tests/ -q
```

All 26 tests pass. 1 skipped (example files not in test env).

## Running the Project

```bash
# Install
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Run GUI
python -m bo2_emblem.gui

# Quick CLI
python -c "
from bo2_emblem import load_emblem, save_emblem, export_to_plutonium
layers = load_emblem('1#emblem.emblem')
export_to_plutonium(layers, slot=1)
"
```

## Extending to Other COD Games

The same reverse engineering pattern applies:
1. Find memory addresses (Cheat Engine / memory scanner)
2. Dump raw bytes from game process
3. Identify structure through live editing + observation
4. Build shape ID map via sequential placement
5. Extract reference glyphs from game assets
6. Build parser/renderer/editor

Format evolution:
- BO2: 32 layers, 44 bytes, single color
- BO3: 64 layers, 96 bytes, dual-color gradients
- BO4: Similar to BO3

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| HTTP headers in dump | Strip `\r\n\r\n` before parsing |
| Scale is not linear | True scale = 2^raw_scale |
| Y axis inverted | +Y = DOWN (screen coords) |
| Layer order | Lower index = behind |
| Empty layers | shape_id = 0xFFFF, rest zeros |
| Reference shapes missing | Fallback to colored square |
| Negative rotation | Normalize to 0-360 via `rotation % 360.0` |
| Invalid shape_id > 260 | Treat as empty layer (return None) |
| Plutonium custom header | 337-byte header before 1408-byte body; detect via last 1408 bytes validation |
| **Parser crashes on invalid data** | Return None for invalid layers instead of raising (treat as empty) |
| **Renderer shows solid white** | Reference shapes not found — verify `datas` in PyInstaller spec and `_shapes_dir` detection in frozen mode |
| **Transparent background shows dark gray** | Default `bg_color` was (24,24,24,255); pass `(0,0,0,0)` explicitly |
| **Negative rotation values in file** | BO2 stores raw float; normalize with `rotation % 360.0` in parser |
| **AI generation hangs** | Run async generation in background thread; update UI via `QMetaObject.invokeMethod` |

## Verification Checklist

- [ ] Parser handles HTTP headers
- [ ] Serializer round-trip verified
- [ ] Renderer matches game preview (0.95+ pixel correlation)
- [ ] All 260+ shape IDs mapped
- [ ] Exporter writes to Plutonium path
- [ ] GUI layer drag-drop reorders correctly
- [ ] Optimizer maintains fidelity target
- [ ] AI generator produces valid 32-layer output
- [ ] PyInstaller bundles all modules (collect_submodules + collect_data_files)
- [ ] Reference shapes included in bundle
- [ ] Built .exe launches GUI without errors
- [ ] All 37 tests pass