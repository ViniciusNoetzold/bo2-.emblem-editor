# BO2 Emblem Format - Reverse Engineering Documentation

## Overview
This document details the complete reverse engineering of the Call of Duty: Black Ops II (BO2) / Plutonium T6 emblem file format (.emblem / .bin).

## File Format Specification

### General Structure
- **File size**: 1408 bytes exactly (after stripping HTTP headers)
- **Layer count**: 32 fixed layers
- **Layer size**: 44 bytes each
- **Total**: 32 × 44 = 1408 bytes

### Layer Structure (44 bytes)

```c
struct EmblemLayer {
    uint16_t shapeId;        // 0x00-0x01: Shape identifier (0xFFFF = empty/unused)
    uint16_t padding1;       // 0x02-0x03: 2 bytes padding
    float    r;              // 0x04-0x07: Red channel (0.0 - 1.0)
    float    g;              // 0x08-0x0B: Green channel (0.0 - 1.0)
    float    b;              // 0x0C-0x0F: Blue channel (0.0 - 1.0)
    float    a;              // 0x10-0x13: Alpha channel (0.0 - 1.0)
    float    posX;           // 0x14-0x17: X position (-1.0 to 1.0+, fraction of half-extent)
    float    posY;           // 0x18-0x1B: Y position (-1.0 to 1.0+, fraction of half-extent, +Y = DOWN)
    float    scaleX;         // 0x1C-0x1F: X scale (log2 scale, true scale = 2^scaleX)
    float    scaleY;         // 0x20-0x23: Y scale (log2 scale, true scale = 2^scaleY)
    float    rotation;       // 0x24-0x27: Rotation in degrees (0-360, clockwise positive)
    uint8_t  outlined;       // 0x28: Boolean - draw outline only
    uint8_t  flipped;        // 0x29: Boolean - horizontal flip
    uint16_t padding2;       // 0x2A-0x2B: 2 bytes padding
};
```

### Byte Layout Summary
| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0x00 | 2 | shapeId | Shape identifier (uint16, little-endian) |
| 0x02 | 2 | padding1 | Reserved |
| 0x04 | 4 | r | Red (float32, little-endian) |
| 0x08 | 4 | g | Green (float32) |
| 0x0C | 4 | b | Blue (float32) |
| 0x10 | 4 | a | Alpha (float32) |
| 0x14 | 4 | posX | X position (float32) |
| 0x18 | 4 | posY | Y position (float32) |
| 0x1C | 4 | scaleX | Log2 scale X (float32) |
| 0x20 | 4 | scaleY | Log2 scale Y (float32) |
| 0x24 | 4 | rotation | Degrees (float32) |
| 0x28 | 1 | outlined | Boolean (0/1) |
| 0x29 | 1 | flipped | Boolean (0/1) |
| 0x2A | 2 | padding2 | Reserved |
| **Total** | **44** | | |

### Key Constants
- `EMPTY_SHAPE = 65535 (0xFFFF)` - Unused/empty layer
- `NUM_LAYERS = 32`
- `LAYER_SIZE = 44`
- `FILE_SIZE = 1408`

### Coordinate System
- **Origin**: Center of emblem (0, 0)
- **Position**: Fraction of half-extent from center
  - `pos 0.5` = reaches box edge
  - Pixel offset = `pos * output_size`
- **Y-axis**: Positive = DOWN (screen coordinates)
- **Scale**: True scale = `2^scale_value` (always positive)
  - `scale 0` = 2^0 = 1.0 (fills entire box)
  - `scale -1` = 2^-1 = 0.5 (half size)
- **Rotation**: Degrees, clockwise positive
- **Layer Order**: Lower index = renders behind, higher index = renders in front

### HTTP Response Handling
The game fetches emblems via HTTP. The raw response includes headers:
```
HTTP/1.1 200 OK
Content-Type: application/octet-stream
...

[1408 bytes of emblem data]
```
**Must strip HTTP headers** before parsing: find `\r\n\r\n` and take everything after.

## Shape ID Mapping

### Categories & Ranges (Confirmed via Memory Reading)

| Category | ID Range | Count | Description |
|----------|----------|-------|-------------|
| **gear** | 0-37, 260 | 39 | Weapon/perk qualification icons |
| **ranks** | 198-216 | 19 | Military ranks |
| **tools** | 137-197 | 61 | Basic shapes (circles, squares, stars, etc.) |
| **type** | 217-252 | 36 | Letters A-Z, Numbers 0-9 |
| **emblems** | 38-136, 253-259 | 106 | Pre-made emblem icons |

### Total Confirmed Shapes: ~260+

Reference shapes stored as LA (Luminance + Alpha) PNG files in `reference_shapes/`.

## Example: BO2Example.txt Analysis

The example shows a 31-layer Toyota AE86 emblem. Each line represents one layer with hexadecimal float32 values.

Example layer (line 6):
```
AE00 0000 0000803F 0000803F 0000803F FEFC7C3E 1C257F3E 645DBCBD 810205C0 418306C0 2D5AB442 00 01 0000
```

Decoded:
- Shape ID: 0xAE00 = 44544 (little-endian: 0x00AE = 174)
- R/G/B/A: All 1.0 (0x3F800000)
- PosX: -0.147 (0x3E7CFCFE)
- PosY: 0.156 (0x3E7F251C)
- ScaleX: -0.782 (0xBDBC5D64)
- ScaleY: -5.83 (0xC0050281)
- Rotation: 47.1° (0x42B45A2D)
- Outlined: 0, Flipped: 1

## Reference Repositories Analyzed

1. **505e06b2/Black-Ops-2-Emblem-Editor** - Web-based editor emulator (Python + JS)
2. **alexkotr1/bo2-emblem-toolkit** - Proxy tool for PS5, complete parser/renderer (Python)
3. **ogarsan/Black-Ops-2-Emblem-Master** - AI-powered fork of #1 (JavaScript)
4. **davideloi55-prog/BO2-Emblem-Generator** - Image to emblem converter (JavaScript)
5. **olie304/CallOfDutyEmblemSpecs** - Format specification document

## Key Insights from bo2-emblem-toolkit (Primary Reference)

The `render.py` module contains the authoritative implementation:
- `parse_slot_bytes()` - Parses 1408-byte blob into layer dicts
- `render_png()` - Pixel-perfect renderer using reference shape glyphs
- `strip_http()` - Removes HTTP headers from game responses
- Shape ID mapping in `shape_id_map.py` with 260+ confirmed IDs
- Reference shapes are LA PNGs (white glyph + alpha channel)

## Validation Notes

The renderer was validated against live BO2 PC game engine:
- Wrote emblems into editor memory buffer at `0x0294B7A0`
- Compared game's preview render vs custom renderer
- Achieved ~0.95 registered pixel correlation on 31-layer test emblem

## Plutonium T6 Compatibility

Plutonium loads emblems from:
```
%localappdata%\Plutonium\storage\t6\players\
```

Files named: `1#emblem.emblem`, `2#emblem.emblem`, ..., `20#emblem.emblem`

Format is identical to original BO2 - 1408 bytes, 32 layers, 44 bytes each.

## Implementation Checklist

- [x] Format specification documented
- [x] Layer structure defined
- [x] Shape ID mapping catalogued
- [x] Reference shapes available (261 PNGs)
- [ ] Python parser implementation
- [ ] Python serializer implementation
- [ ] Pixel-perfect renderer
- [ ] Image-to-emblem converter
- [ ] GUI editor
- [ ] Plutonium export integration

---

*Last Updated: 2025-07-28*
*Sources: bo2-emblem-toolkit, CallOfDutyEmblemSpecs, live memory analysis*