---
name: game-asset-reverse-engineering
description: Class-level skill for reverse engineering game file formats, locating game assets, and building parsers/renderers for modding research. Covers binary format analysis, memory reading, community asset discovery, and documentation workflows.
category: security
tags:
  - reverse-engineering
  - game-modding
  - binary-formats
  - file-format-analysis
  - game-assets
  - osint
---

# Game Asset Reverse Engineering

A class-level skill for systematically reverse engineering game file formats, discovering community-shared assets, and building tooling for analysis and generation.

## When to Use This Skill

- Reverse engineering unknown binary game formats (save files, assets, network packets)
- Locating community-shared game assets (emblems, maps, models, textures)
- Building parsers, renderers, or generators for game formats
- Documenting format specifications for modding communities
- Analyzing game memory for live asset extraction

## Core Workflow

### Phase 1: Asset Discovery (OSINT)
1. **GitHub/API Search** — Search repositories for format parsers, editors, specs:
   - `filename:.ext` + game name
   - `extension:ext` + keywords
   - Repository topics: `game-name`, `modding`, `reverse-engineering`
2. **Community Forums** — Official/Unofficial forums, Discord, Reddit, Steam Community
3. **Archive Sites** — Internet Archive, Wayback Machine for dead links
4. **Memory Analysis** — Live game memory reading for format validation

### Phase 2: Format Analysis
1. **Sample Collection** — Gather diverse samples (empty, minimal, complex, maxed)
2. **Hex Diffing** — Compare samples to identify structure (010 Editor, ImHex, custom scripts)
3. **Known-Value Injection** — Write known values to game memory, capture output
4. **Cross-Reference** — Compare against existing specs (GitHub, wikis, papers)
5. **Validator** — Build round-trip parser → serializer → verify identical bytes

### Phase 3: Tooling
1. **Parser** — Read format into structured objects
2. **Renderer** — Visualize (images, 3D, text) for verification
3. **Generator** — Create valid files from high-level descriptions
4. **Editor** — Interactive modification (optional)

### Phase 4: Documentation & Distribution
1. **Spec Document** — Markdown with structs, enums, constants, examples
2. **Reference Assets** — Curated sample files + expected renders
3. **Index/Database** — Organized collection with metadata (source, author, tags)

## Key Techniques

### Binary Format Discovery
```python
# Round-trip validation pattern
def test_roundtrip(sample_paths):
    for path in sample_paths:
        original = read_bytes(path)
        parsed = parse(original)
        serialized = serialize(parsed)
        assert original == serialized, f"Mismatch: {path}"
```

### Shape/Asset ID Mapping
- Use **live memory read** while cycling through in-game asset picker
- Log `(display_name, asset_id)` pairs
- Build `known_ids = {id: "Category/Name"}` mapping
- Validate against reference renders

### Community Asset Handling
- **Never trust single source** — cross-reference multiple dumps
- **Decode pipelines** — Common: base64 → zlib → raw binary
- **Deduplication** — SHA256 + structural comparison (layer count, shape IDs)
- **Attribution** — Preserve source URL, author, license if stated

## Pitfalls & Gotchas

| Pitfall | Mitigation |
|---------|------------|
| Cloudflare on forums | Use API endpoints, RSS, or manual browser session cookies |
| Rate limits on GitHub API | Use authenticated requests, cache results, batch queries |
| Incomplete format specs | Validate against LIVE game engine, not just other tools |
| Endianness assumptions | Test with known values; BO2 uses little-endian (`<` in struct) |
| Float encoding | IEEE 754; verify scale/log2 relationships (BO2: `true_scale = 2**raw`) |
| Padding/alignment | Always account for explicit padding bytes in structs |
| Max layer/entity counts | Hard limits (BO2: 32 layers); unused = sentinel value (0xFFFF) |

## Game-Specific Notes: Call of Duty Black Ops II (Plutonium T6)

### .emblem/.bin

**Format**: 1408 bytes = 32 layers × 44 bytes
```c
struct Layer {
    uint16 shapeId;      // 0xFFFF = empty
    uint16 pad1;
    float r,g,b,a;       // 0.0–1.0
    float posX,posY;     // fraction of half-extent; +Y = down
    float scaleX,scaleY; // true_scale = 2**raw
    float rotation;      // degrees, CW (NEGATIVE VALUES ALLOWED, normalize with % 360)
    uint8 outlined;      // bool: stroke only
    uint8 flipped;       // bool: mirror X
    uint16 pad2;
}
```

**Render Order**: Lower index = further back

**Shape Categories** (confirmed via memory read):
- `gear` (0–37, 260): Weapon/perk icons
- `ranks` (198–216): Rank insignia
- `tools` (137–197): Basic shapes
- `type` (217–252): Letters/numbers
- `emblems` (38–136, 253–259): Pre-made icons

**Storage Path**: `%localappdata%\Plutonium\storage\t6\players\`
**File Naming**: `1#emblem.emblem`, `2#emblem.emblem`, …

### Plutonium T6 Storage Header (337 bytes)
Plutonium wraps the 1408-byte emblem body in a custom header:
```c
struct PlutoniumHeader {
    uint32 magic_version;    // 0x00000580 (1408) at offset 4
    uint32 unknown1;         // 0x00000006
    uint32 unknown2;         // 0x000000FF
    uint32 unknown3;         // 0x00000002
    uint32 unknown4;         // 0x00000003
    char name[13];           // "Emblem_N" null-terminated (offset 0x18)
    uint16 layer_count;      // 0x0003 (offset 0x25)
    uint32 unknown5;         // 0x00000000
    uint32 unknown6;         // 0x00060000
    uint32 unknown7;         // 0x00000000
    uint32 unknown8;         // 0x000D0000
    uint64 timestamp;        // FILETIME at offset 0x34
    // ... padding to 337 bytes
}
```
**Critical**: Parser must detect and strip this header. Use "last 1408 bytes" fallback if header detection fails. Slot 7 (created by our editor) has NO header — raw 1408 bytes.

### Key Format Constants (Validated)
- **Scale formula**: `true_scale = 2.0 ** scale_raw` (scale_raw = 0.0 → 1.0×; -1.0 → 0.5×)
- **Position formula**: `pixel = center + pos * canvas_size` (pos 0.0 = center, ±0.5 = edge)
- **Rotation**: Degrees clockwise, negative values allowed → **preserve as-is, do NOT normalize** (accept -360 to 360 range; normalizing -25° → 335° breaks round-trip binary compatibility)
- **Layer limit**: 32 (indices 0–31), empty = shape_id 0xFFFF
- **Render order**: Index 0 = back, Index 31 = front
- **Shape IDs**: 0–260 confirmed, max valid = 260 (261 shapes total)

**Key Repositories**:
- `alexkotr1/bo2-emblem-toolkit` — Proxy capture, parser, renderer, shape_id_map.py (260+ IDs), reference_shapes/
- `505e06b2/Black-Ops-2-Emblem-Editor` — Web editor, base64+zlib example emblems
- `olie304/CallOfDutyEmblemSpecs` — Format specification (BO2/BO3/BO4)
- `ogarsan/Black-Ops-2-Emblem-Master` — AI-assisted fork

**Decoding 505e06b2 Examples**:
```python
import base64, zlib
raw = base64.b64decode(text.strip())
emblem = zlib.decompress(raw)  # 1408 bytes
```

## Mod Audit and Merge Workflow for Plutonium T6 Zombies

### Overview
When creating a unified mod pack (e.g., Ultimate Zombies Pack) from multiple base mods (like T6-ZM-Expanded and Wonder Weapons), follow a structured, non-destructive process to preserve original sources and build a clean, modular workspace.

### Step‑by‑step Procedure

1. **Preserve Originals**  
   - Never modify the original `Base/` or `Merge/` directories.  
   - Treat them as immutable references.

2. **Create a Clean Workspace**  
   - Make a new directory `Workspace/Ultimate_Zombies_Pack/`.  
   - All further work (audit, merging, building) occurs inside this workspace.

3. **Audit Both Projects**  
   - Enumerate all files in each project (scripts, GSC/CSC, assets, sounds, materials, models, animations, weapondefs, attachments, aliases, fastfiles, includes, callbacks, clientfields, weapon tables, mystery box, wall buys, pack‑a‑punch, perk systems, buildables, easter eggs, powerups).  
   - Categorize by type (see the `references/plutonium-t6-mod-audit-checklist.md` for a detailed checklist).  
   - Produce lists: `base_files.txt`, `merge_files.txt`, `identical.txt`, `different.txt`, `base_only.txt`, `merge_only.txt`.

4. **Compare and Identify Conflicts**  
   - Use content hashing (SHA‑256) to find identical files.  
   - Flag files with same relative path but different content as *conflicts*.  
   - List files present only in one side as *unique assets*.  
   - Document duplicate assets, duplicate weaponDefs, duplicate aliases, duplicate sound aliases, duplicate scripts/includes/callbacks/clientfields, etc., as outlined in the original mission brief.

5. **Design a Modular Architecture**  
   - Adopt a folder structure such as:  
     ```
     Core/
     Modules/
       Weapons/
       WonderWeapons/
       Perks/
       Buildables/
       Powerups/
       MysteryBox/
       WallBuys/
       PackAPunch/
       Maps/
     Shared/
     Config/
     Tools/
     Output/
     Documentation/
     ```
   - Place shared/common assets (e.g., shared scripts, common assets) under `Shared/`.  
   - Each major feature (e.g., a wonder weapon) gets its own subfolder under the appropriate module.

6. **Integrate Without Breaking References**  
   - For each asset type, decide which source to keep when duplicates exist, or merge content manually.  
   - Update all references (includes, aliases, weapon tables, model paths) to point to the new locations under the workspace.  
   - Preserve original file names where possible to avoid breaking existing references; otherwise, update all dependent files.

7. **Validate Incrementally**  
   - After each major change (e.g., after importing weapons, after adding a wonder weapon), run the mod’s build process (using BO2 Mod Tools) and verify:  
     - No script syntax errors.  
     - No missing asset warnings.  
     - Weapon definitions load correctly.  
     - No duplicate alias or clientfield errors.  
   - If errors appear, resolve them before proceeding.

8. **Achieve a Clean Build**  
   - Iterate until the project compiles with zero warnings/errors.  
   - Keep a build log (`Build_Report.md`) capturing any warnings and how they were resolved.

9. **Generate Documentation**  
   - Produce the following markdown files in `Documentation/`:  
     - `README.md` – overview and installation.  
     - `Architecture.md` – description of the modular layout.  
     - `Merge_Report.md` – summary of what was taken from each source.  
     - `Conflict_Report.md` – list of conflicts and how they were resolved.  
     - `Assets_Report.md` – counts of models, textures, sounds, etc.  
     - `Build_Report.md` – final build output and any lingering warnings.  
     - `TODO.md` – known issues or planned future enhancements.  
     - `Changelog.md` – per‑version notes.

10. **Preserve Compatibility**  
    - Ensure the final mod remains compatible with the base T6‑ZM‑Expanded mechanics unless intentional changes are documented.  
    - Do not remove existing functionality; only extend or override as needed.

### Pitfalls & Gotchas

| Pitfall | Mitigation |
|---------|------------|
| Accidentally editing source folders | Always work inside the workspace; treat Base/ and Merge/ as read‑only. |
| Broken script includes after moving files | Update `#include` statements using a scripted search‑replace (see `scripts/update_includes.py`). |
| Duplicate weaponDefs causing load failures | Keep one canonical version; rename duplicates with a unique prefix and update all references. |
| Missing assets after merge | Verify that every referenced model/sound/material exists in the final `Output/` or is packaged into the final `.ff`. |
| Build tool path issues | Use absolute paths or ensure the Mod Tools environment variables are set; document in `Tools/README.md`. |
| Forgetting to update `mod.json` | Regenerate or manually edit `mod.json` to reflect the new mod name, version, and dependencies. |

### Automation Helpers
- **Audit Script**: `scripts/audit_mods.py` – generates the file lists and comparison reports.  
- **Include Updater**: `scripts/update_includes.py` – rewrites `#include` paths after moving files.  
- **Duplicate Detector**: `scripts/find_duplicates.py` – spots duplicate asset` – spots duplicate asset names across folders.

## References

- `references/bo2-emblem-format.md` — Complete BO2 .emblem/.bin specification
- `references/asset-discovery-checklist.md` — Checklist for new game asset research
- `references/binary-analysis-patterns.md` — Reusable patterns for format discovery

## Templates

- `templates/format-spec.md` — Starter template for documenting a new format
- `templates/parser-skeleton.py` — Minimal parser with round-trip test
- `templates/asset-index.json` — Schema for asset collection index

## Scripts

- `scripts/bo2-emblem-decode.py` — Decode 505e06b2 base64+zlib examples
- `scripts/bo2-emblem-serialize.py` — Serialize layer dicts → 1408-byte .emblem
- `scripts/shape-id-extract.py` — Extract known_ids from shape_id_map.py