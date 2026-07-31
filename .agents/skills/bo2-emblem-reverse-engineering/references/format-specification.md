# BO2/Plutonium T6 Emblem Format Specification

## Overview

This document provides the complete binary format specification for Call of Duty: Black Ops II (BO2) / Plutonium T6 emblem files (.emblem / .bin).

## File Structure

- **Total Size**: 1408 bytes exactly
- **Layers**: 32 fixed layers
- **Layer Size**: 44 bytes each
- **Format**: Little-endian binary

## Layer Structure (44 bytes)

```
Offset  Size  Field           Type        Description
------  ----  -----           ----        -----------
0x00    2     shape_id        uint16      Shape identifier (0xFFFF = empty)
0x02    2     padding1        uint16      Reserved
0x04    4     r               float32     Red channel (0.0 - 1.0)
0x08    4     g               float32     Green channel (0.0 - 1.0)
0x0C    4     b               float32     Blue channel (0.0 - 1.0)
0x10    4     a               float32     Alpha channel (0.0 - 1.0)
0x14    4     pos_x           float32     X position (fraction from center)
0x18    4     pos_y           float32     Y position (fraction from center, +Y = DOWN)
0x1C    4     scale_x         float32     Log2 X scale (true_scale = 2^value)
0x20    4     scale_y         float32     Log2 Y scale (true_scale = 2^value)
0x24    4     rotation        float32     Rotation in degrees (clockwise)
0x28    1     outlined        uint8       Boolean: draw outline only
0x29    1     flipped         uint8       Boolean: horizontal flip
0x2A    2     padding2        uint16      Reserved
```

**Struct format**: `<Hxx9fBBxx` (2 + 2 + 36 + 1 + 1 + 2 = 44)

## Key Constants

| Constant | Value | Description |
|----------|-------|-------------|
| EMPTY_SHAPE | 0xFFFF (65535) | Empty/unused layer marker |
| NUM_LAYERS | 32 | Fixed layer count |
| LAYER_SIZE | 44 | Bytes per layer |
| FILE_SIZE | 1408 | Total file size |

## Coordinate System

- **Origin**: Center of emblem (0, 0)
- **Position**: Fraction of half-extent from center
  - pos 0.5 = reaches box edge
  - Pixel offset = pos × output_size
- **Y-axis**: Positive = DOWN (screen coordinates)
- **Scale**: True scale = 2^scale_value (always positive)
  - scale 0 = 2^0 = 1.0 (fills entire box)
  - scale -1 = 2^-1 = 0.5 (half size)
- **Rotation**: Degrees, clockwise positive
- **Layer Order**: Lower index = renders behind, higher index = in front

## HTTP Response Handling

Game fetches emblems via HTTP. Raw response includes headers:

```
HTTP/1.1 200 OK
Content-Type: application/octet-stream
...

[1408 bytes of emblem data]
```

**Must strip HTTP headers** before parsing: find `\r\n\r\n` and take everything after.

## Shape ID Categories

| Category | ID Range | Count | Description |
|----------|----------|-------|-------------|
| gear | 0-37, 260 | 39 | Weapon/perk qualifications |
| ranks | 198-216 | 19 | Military ranks |
| tools | 137-197 | 61 | Basic shapes |
| type | 217-252 | 36 | Letters A-Z, Numbers 0-9 |
| emblems | 38-136, 253-259 | 106 | Pre-made icons |

**Total Confirmed**: ~260+ shapes

## Reference Shapes

Stored as LA (Luminance + Alpha) PNG files in `reference_shapes/`.
Each is a white glyph with alpha channel for tinting.

## Plutonium T6 Compatibility

Plutonium loads emblems from:
```
%localappdata%\Plutonium\storage\t6\players\
```

Files named: `1#emblem.emblem`, `2#emblem.emblem`, ..., `20#emblem.emblem`

Format is identical to original BO2.