# Game Asset Format Specification Template

Use this template when documenting a new game file format.

---

# {{GAME_TITLE}} — {{FORMAT_NAME}} Format Specification

## Overview

| Property | Value |
|----------|-------|
| **Game** | {{GAME_TITLE}} |
| **Format** | {{FORMAT_NAME}} (`.{{EXT}}`) |
| **Engine** | {{ENGINE}} |
| **Platform(s)** | {{PLATFORMS}} |
| **File Size** | {{SIZE}} bytes (fixed) / variable |
| **Endianness** | Little / Big |
| **Magic/Signature** | `{{MAGIC_HEX}}` / None |
| **Version Field** | Offset {{VERSION_OFFSET}}, {{VERSION_SIZE}} bytes |

## Storage / Network Location

```
{{PATH_DESCRIPTION}}
{{EXAMPLE_PATHS}}
```

---

## Binary Layout

### Header (if any)

```
Offset  | Size | Type | Description
--------|------|------|------------
0x{{OFFSET}} | {{SIZE}} | {{TYPE}} | {{DESC}}
...
```

### Main Structure

```
{{STRUCT_DESCRIPTION}}
```

```c
struct {{STRUCT_NAME}} {
    {{FIELD_DEFINITIONS}}
};
```

### Repeating Records (layers, entities, chunks)

| Field | Offset | Size | Type | Description |
|-------|--------|------|------|-------------|
| {{FIELD}} | {{OFFSET}} | {{SIZE}} | {{TYPE}} | {{DESC}} |
| ... | ... | ... | ... | ... |

**Record Size**: {{RECORD_SIZE}} bytes  
**Count**: {{COUNT}} (fixed) / Variable (count at {{COUNT_OFFSET}})

---

## Semantic Rules

### Rendering / Interpretation Order
- {{ORDER_RULE}}

### Coordinate System
- Origin: {{ORIGIN}}
- Axes: {{AXES}}
- Units: {{UNITS}}

### Special Values
| Value | Meaning |
|-------|---------|
| {{VALUE}} | {{MEANING}} |

### Scale / Transform Formulas
- {{FORMULA}}

---

## Reference Data

### Enum / ID Mappings

| ID Range | Category | Count | Source |
|----------|----------|-------|--------|
| {{RANGE}} | {{CAT}} | {{COUNT}} | {{SOURCE}} |

### External Assets
- {{ASSET_DESCRIPTION}}: {{PATH}}

---

## Validation

### Required Checks
- [ ] File size {{SIZE_CHECK}}
- [ ] Magic bytes match
- [ ] Version supported
- [ ] All records valid
- [ ] Sentinel values correct
- [ ] Round-trip: `serialize(parse(data)) == data`

### Typical Value Ranges
| Field | Min | Max | Notes |
|-------|-----|-----|-------|
| {{FIELD}} | {{MIN}} | {{MAX}} | {{NOTES}} |

---

## Known Implementations

| Repo / Tool | Language | Status | Notes |
|-------------|----------|--------|-------|
| {{REPO}} | {{LANG}} | {{STATUS}} | {{NOTES}} |

---

## Sample Files

| Name | Description | SHA256 | Source |
|------|-------------|--------|--------|
| {{NAME}} | {{DESC}} | {{HASH}} | {{URL}} |

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| {{DATE}} | {{AUTHOR}} | Initial specification |

---

## Appendix: Hex Dump Example

```
{{HEX_DUMP}}
```