# Call of Duty: Black Ops II (Plutonium T6) — .emblem / .bin Format Specification

## Overview

| Property | Value |
|----------|-------|
| **File Extension** | `.emblem` (Plutonium), `.bin` (original/toolkit) |
| **Size** | 1408 bytes exactly |
| **Layers** | 32 fixed slots |
| **Layer Size** | 44 bytes each |
| **Endianness** | Little-endian (`<` in Python struct) |
| **Magic/Signature** | None (identified by size + structure) |

## Storage Location

```
%localappdata%\Plutonium\storage\t6\players\
  1#emblem.emblem
  2#emblem.emblem
  ...
  N#emblem.emblem
```

Copying `.emblem` files here makes them appear in-game immediately.

---

## Binary Layout

```
Offset  | Size | Description
--------|------|------------
0x0000  | 44   | Layer 0
0x002C  | 44   | Layer 1
...     | ...  | ...
0x057C  | 44   | Layer 31
0x0580  | —    | End of file (1408 bytes)
```

### Layer Structure (44 bytes)

```c
struct EmblemLayer {
    uint16_t shapeId;        // 0x00–0x01: Shape identifier (0xFFFF = empty/unused)
    uint16_t pad1;           // 0x02–0x03: Padding (always 0x0000)
    float    r;              // 0x04–0x07: Red   (0.0–1.0)
    float    g;              // 0x08–0x0B: Green (0.0–1.0)
    float    b;              // 0x0C–0x0F: Blue  (0.0–1.0)
    float    a;              // 0x10–0x13: Alpha (0.0–1.0)
    float    posX;           // 0x14–0x17: X position (fraction of half-extent; + = right)
    float    posY;           // 0x18–0x1B: Y position (fraction of half-extent; + = DOWN)
    float    scaleX;         // 0x1C–0x1F: X scale (raw; true_scale = 2**raw)
    float    scaleY;         // 0x20–0x23: Y scale (raw; true_scale = 2**raw)
    float    rotation;       // 0x24–0x27: Rotation (degrees, clockwise-positive)
    uint8_t  outlined;       // 0x28: 1 = stroke only, 0 = filled
    uint8_t  flipped;        // 0x29: 1 = mirror horizontally, 0 = normal
    uint16_t pad2;           // 0x2A–0x2B: Padding (always 0x0000)
};
```

**Total**: 2 + 2 + 9×4 + 1 + 1 + 2 = **44 bytes**

---

## Rendering Rules

1. **Layer Order**: Index 0 renders **furthest back**; index 31 renders **frontmost**
2. **Coordinate System**:
   - Origin = center of emblem canvas
   - `posX = 0.5` → right edge; `posX = -0.5` → left edge
   - `posY = 0.5` → bottom edge; `posY = -0.5` → top edge
   - Values can exceed ±1.0 (off-screen)
3. **Scale**: True scale = `2 ** raw_scale`
   - `raw = 0` → 1× (fills canvas)
   - `raw = -1` → 0.5×
   - `raw = 1` → 2×
4. **Rotation**: Degrees, clockwise-positive
5. **Outlined**: If `outlined=1`, render only a ~3px stroke along glyph edge
6. **Flipped**: Horizontal mirror (independent of scale sign; scale is always positive)
7. **Empty Layer**: `shapeId == 0xFFFF` → skip entirely

---

## Shape ID Mapping (Confirmed via Live Memory Read)

Source: `alexkotr1/bo2-emblem-toolkit/emblemtool/shapes/shape_id_map.py`

| Range | Category | Count | Notes |
|-------|----------|-------|-------|
| 0–37 | `gear` | 38 | Weapon/perk qualification icons |
| 38–136 | `emblems` | 99 | Pre-made emblem icons (block 1) |
| 137–197 | `tools` | 61 | Basic shapes (circle, square, star, etc.) |
| 198–216 | `ranks` | 19 | Rank insignia |
| 217–252 | `type` | 36 | Letters A–Z + 0–9 |
| 253–259 | `emblems` | 7 | Pre-made emblem icons (block 2) |
| 260 | `gear` | 1 | Peacekeeper Qualified (DLC) |
| 65535 (0xFFFF) | — | — | **Empty/unused layer sentinel** |

**Total Confirmed**: ~261 unique shape IDs

---

## Reference Glyphs

Located in `alexkotr1/bo2-emblem-toolkit/reference_shapes/` as PNG (LA mode: luminance + alpha, white glyph on transparent).

Naming: `Category/Name.png` → e.g., `tools/Half Circle.png`, `emblems/Triple Kill.png`

---

## 505e06b2/Black-Ops-2-Emblem-Editor Example Format

Their `created emblems/*/code.txt` files are **base64(zlib(1408-byte raw))**.

```python
import base64, zlib

def decode_505e06b2(text: str) -> bytes:
    raw = base64.b64decode(text.strip())
    return zlib.decompress(raw)  # → 1408 bytes
```

---

## Python Parser/Serializer

```python
import struct

LAYER_SIZE = 44
NUM_LAYERS = 32
EMPTY_SHAPE = 0xFFFF

def parse_embl(emblem_bytes: bytes) -> list[dict]:
    assert len(emblem_bytes) == 1408
    layers = []
    for i in range(NUM_LAYERS):
        rec = emblem_bytes[i*LAYER_SIZE:(i+1)*LAYER_SIZE]
        shape_id = struct.unpack("<H", rec[0:2])[0]
        if shape_id == EMPTY_SHAPE:
            continue
        f = struct.unpack("<9f", rec[4:40])
        outlined, flipped = rec[40], rec[41]
        layers.append({
            "index": i,
            "shape": shape_id,
            "r": f[0], "g": f[1], "b": f[2], "a": f[3],
            "x": f[4], "y": f[5],
            "sx": f[6], "sy": f[7],
            "rot": f[8],
            "outlined": bool(outlined),
            "flipped": bool(flipped),
        })
    return layers

def serialize_embl(layers: list[dict]) -> bytes:
    out = bytearray(1408)
    used_indices = {L["index"] for L in layers}
    # Fill empty layers
    for i in range(NUM_LAYERS):
        if i not in used_indices:
            struct.pack_into("<H", out, i*LAYER_SIZE, EMPTY_SHAPE)
    # Write used layers
    for L in layers:
        i = L["index"]
        struct.pack_into("<H", out, i*LAYER_SIZE, L["shape"])
        struct.pack_into("<9f", out, i*LAYER_SIZE + 4,
            L["r"], L["g"], L["b"], L["a"],
            L["x"], L["y"], L["sx"], L["sy"], L["rot"])
        out[i*LAYER_SIZE + 40] = 1 if L["outlined"] else 0
        out[i*LAYER_SIZE + 41] = 1 if L["flipped"] else 0
    return bytes(out)
```

---

## Validation Checklist

- [ ] File size == 1408 bytes
- [ ] All 32 layer slots accounted for
- [ ] Unused layers have `shapeId == 0xFFFF`
- [ ] All floats are valid IEEE 754 (not NaN/inf)
- [ ] `posX`, `posY` typically in [-2, 2] range
- [ ] `scaleX`, `scaleY` typically in [-3, 2] (2**raw)
- [ ] `rotation` in [0, 360]
- [ ] `outlined`, `flipped` ∈ {0, 1}
- [ ] Round-trip: `serialize(parse(data)) == data`

---

## Related Formats

| Game | Format | Size | Layers | Notes |
|------|--------|------|--------|-------|
| BO3 | `.emblem` | 6144 | 64 | Two colors per layer (gradients), material IDs |
| BO4 | `.emblem` | 6144 | 64 | Similar to BO3 |
| WWII | — | — | — | Different engine |
| MW2019 | — | — | — | Different engine |

See `olie304/CallOfDutyEmblemSpecs` for BO3/BO4 specs.