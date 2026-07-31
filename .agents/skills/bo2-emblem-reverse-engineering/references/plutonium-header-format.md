# Plutonium T6 Emblem Header Format

## Overview

Plutonium T6 stores emblems with a custom 337-byte header prepended to the standard 1408-byte BO2 emblem body. Total file size: **1745 bytes**.

This header is NOT present in standard BO2 files — it's specific to Plutonium T6's storage format.

## Header Structure (337 bytes)

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0x000 | 4 | `magic_version` | uint32 | File format version / magic |
| 0x004 | 4 | `body_size` | uint32 | Always 1408 (0x580) |
| 0x008 | 4 | `unknown1` | uint32 | Always 6 |
| 0x00C | 4 | `flags` | uint32 | Bit flags (0xFF = full?) |
| 0x010 | 4 | `unknown2` | uint32 | Always 2 |
| 0x014 | 4 | `unknown3` | uint32 | Always 3 |
| 0x018 | 8 | `emblem_name` | char[8] | ASCII name, null-terminated (e.g., "Emblem_8") |
| 0x020 | 4 | `unknown4` | uint32 | Always 0x30000 (196608) |
| 0x024 | 4 | `unknown5` | uint32 | Always 0 |
| 0x028 | 4 | `unknown6` | uint32 | Always 393216 (0x60000) |
| 0x02C | 4 | `unknown7` | uint32 | Always 0 |
| 0x030 | 4 | `unknown8` | uint32 | Always 851968 (0xD0000) |
| 0x034 | 4 | `unknown9` | uint32 | Always 0 |
| 0x038 | 4 | `unknown10` | uint32 | Always 0 |
| 0x03C | 4 | `unknown11` | uint32 | Always 0 |
| 0x040 | 297 | `padding` | bytes[297] | Zero padding + timestamp/crypto data at end |

## Header Detection Algorithm

The parser detects Plutonium headers by validating that the **last 1408 bytes** parse as valid emblem data:

```python
def detect_plutonium_header(data: bytes) -> (bytes, Optional[Header]):
    if len(data) < 1408:
        return data, None
    
    body = data[-1408:]
    header = data[:-1408]
    
    if _validate_emblem_body(body):
        return body, parse_plutonium_header(header)
    
    # Fallback: try whole data as body
    if _validate_emblem_body(data):
        return data, None
    
    # Last resort: use last 1408 bytes
    return data[-1408:], None
```

## Body Validation

```python
def _validate_emblem_body(data: bytes) -> bool:
    if len(data) != 1408:
        return False
    valid_layers = 0
    for i in range(32):
        shape_id = struct.unpack("<H", data[i*44:i*44+2])[0]
        if shape_id != 0xFFFF:
            valid_layers += 1
    return valid_layers > 0
```

## Total File Sizes

| Format | Size | Header | Body |
|--------|------|--------|------|
| Standard BO2 | 1408 | None | 1408 |
| Plutonium T6 | 1745 | 337 | 1408 |

## Parser Implementation Notes

The parser in `parser.py` uses `detect_plutonium_header()` which:
1. Checks if last 1408 bytes are valid emblem body
2. If valid, strips header and parses body
3. Returns both body and parsed `PlutoniumHeader` object
4. Falls back gracefully if detection fails

The header contains useful metadata:
- `emblem_index`: Which slot (1-20)
- `name`: Emblem name (e.g., "Emblem_8")
- `timestamp`: Unix timestamp at end of header

This allows the exporter to target specific slots by name/index.