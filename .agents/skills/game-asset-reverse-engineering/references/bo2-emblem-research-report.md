# BO2 Plutonium T6 Emblem Research Report

**Date**: 2026-07-28  
**Researcher**: Hermes Agent  
**Scope**: Complete discovery of .emblem/.bin files, tools, format specs, and reverse engineering for Call of Duty: Black Ops II (Plutonium T6)

---

## Executive Summary

**No public repository hosts bulk .emblem file collections.** The community shares emblems via:
1. **bo2-emblem-toolkit proxy capture** (self-capture from other players' profiles)
2. **Plutonium Forums / Discord** (base64/text pastebins)
3. **Reddit** (r/blackops2, r/Plutonium, r/CODZombies) — occasional shares
4. **YouTube descriptions** — tutorial creators sometimes link files

**Best path to a collection**: Run `bo2-emblem-toolkit` proxy, browse player profiles in-game, capture 100s of emblems automatically.

---

## Phase 1: Repository Discovery (GitHub)

### Active/Relevant Repositories

| Repo | Stars | Language | Description | Key Assets |
|------|-------|----------|-------------|------------|
| `505e06b2/Black-Ops-2-Emblem-Editor` | 28 | Python/JS | Full web-based editor emulation | 5 example emblems (base64+zlib), shape glyphs |
| `alexkotr1/bo2-emblem-toolkit` | 2 | Python | **Proxy capture + parser + pixel-perfect renderer** | **Complete format parser, 260+ shape ID map, reference glyphs** |
| `ogarsan/Black-Ops-2-Emblem-Master` | 2 | JavaScript | AI-powered fork of 505e06b2 editor | AI generation tab |
| `davideloi55-prog/BO2-Emblem-Generator` | 0 | JavaScript | Image → emblem code (WIP) | Basic structure only |
| `olie304/CallOfDutyEmblemSpecs` | 0 | Markdown | **Format specs for BO2/BO3/BO4** | BO2Example.txt (hex dump), README with memory addresses |

### Search Queries That Yielded Results

```
"black ops 2 emblem" → 4 repos
"callofduty emblem" → 2 repos
"plutonium t6" → 7 repos (scripts, server browser, mods — no emblems)
"emblem filetype:bin" → 0 (requires auth)
```

**Key Finding**: GitHub has **tools and specs**, not asset collections.

---

## Phase 2: Tools & Format Documentation

### Primary Tool: `bo2-embblem-toolkit` (alexkotr1)

**Capabilities**:
- HTTP proxy intercepting BO2 emblem storage requests
- Capture mode: saves `slot_N.bin` (1408 bytes raw) per player profile viewed
- Show mode: injects captured emblem into your editor session
- Parser: `parse_slot_bytes()` → structured layer dicts
- Renderer: `render_png()` using real glyphs → pixel-perfect PNG
- Shape ID map: 260+ entries calibrated via live memory read

**Files**:
```
emblemtool/
  storage.py      # Disk layout: saved/<group>/slot_N.bin + meta.json
  shapes/
    render.py     # Parser + renderer (THE reference implementation)
    shape_id_map.py  # 260+ confirmed IDs via memory read
  proxy.py        # Mitmproxy addon
reference_shapes/ # ~260 PNG glyphs (LA mode)
```

### Format Specification: `CallOfDutyEmblemSpecs` (olie304)

**BO2 Structure** (confirmed by both repos):
- 1408 bytes = 32 layers × 44 bytes
- Layer: `uint16 shapeId`, `2 pad`, `9 float32 (RGBA, posXY, scaleXY, rot)`, `u8 outlined`, `u8 flipped`, `2 pad`
- `shapeId = 0xFFFF` = empty
- True scale = `2 ** raw_scale`
- Layer 0 = back, Layer 31 = front

**Memory Addresses (BO2 PC)**:
- Emblem editor buffer: `0x0294B7A0` (t6mp.exe)
- Recently loaded emblems page: `0x02947A68` → 10 slots @ 0x590 stride

### 505e06b2 Editor Example Format

Their `code.txt` = `base64(zlib(raw_1408_bytes))`

---

## Phase 3: Reverse Engineering — Complete Spec

**Saved to**: `references/bo2-emblem-format.md` in this skill

Includes:
- C struct definition
- All rendering rules
- Complete shape ID mapping table (260+ entries)
- Python parser/serializer with round-trip validation
- Example decode for 505e06b2 format

---

## Phase 4: Asset Files Found

### Direct .emblem/.bin Files: **0** in public GitHub repos

### Indirect / Decodable Examples: **5** (505e06b2 editor)

| Name | Category | Source | Layers Used |
|------|----------|--------|-------------|
| Cassette | Misc | 505e06b2/created emblems/Cassette/code.txt | ~20 |
| EA | Logos | 505e06b2/created emblems/EA/code.txt | ~12 |
| Eyeliner | Misc | 505e06b2/created emblems/Eyeliner/code.txt | ~15 |
| Snowball | Misc | 505e06b2/created emblems/Snowball/code.txt | ~18 |
| Wicke | Anime | 505e06b2/created emblems/Wicke/code.txt | ~22 |

**Decode**:
```python
import base64, zlib
raw = zlib.decompress(base64.b64decode(open("code.txt").read().strip()))
# raw is 1408 bytes → write as 1#emblem.emblem
```

### Reference Glyphs: **~260 PNGs** (bo2-emblem-toolkit/reference_shapes/)

Essential for rendering. Each is LA (luminance+alpha), white glyph on transparent.

---

## Phase 5: GitHub Deep Search Results

| Query | Result |
|-------|--------|
| `filename:.emblem` | 0 (no public .emblem files) |
| `filename:.bin plutonium` | 0 |
| `1#emblem` | 0 |
| `2#emblem` | 0 |
| `bo2 emblem pack` | 0 |
| `plutonium storage t6 players` | 0 |

**Conclusion**: Community does **not** commit .emblem files to GitHub.

---

## Phase 6: Reddit / Forum Discovery

**Attempted**: Reddit API (r/blackops2, r/Plutonium, r/CODZombies) — rate limited / blocked

**Manual Search Recommendations**:
- `site:reddit.com/r/blackops2 "emblem" "code" OR "base64" OR "download"`
- `site:reddit.com/r/Plutonium "emblem" "share" OR "pack"`
- `site:forum.plutonium.pw "emblem" "1#emblem" OR "slot_"`

**Plutonium Forum**: Cloudflare protected — needs browser session or API key.

**Discord**: Plutonium official + community servers have `#emblems` channels — requires join.

---

## Phase 7: Final Assessment

### Total .emblem Files Discoverable
| Source | Est. Count | Access Difficulty |
|--------|------------|-------------------|
| bo2-emblem-toolkit (self-capture) | Unlimited (100s/hr) | Low (run proxy, play game) |
| Plutonium Forum threads | ~50–200 | Medium (Cloudflare, search) |
| Reddit posts | ~20–50 | Medium (search, decode) |
| Discord shares | ~100+ | Medium (join, scroll history) |
| YouTube descriptions | ~10–30 | Low (search, check links) |
| **Total realistic collectible** | **200–500+** | **1–2 days work** |

### Duplicate Risk
- High: Same popular emblems (logos, memes) shared repeatedly
- Mitigation: SHA256 deduplication + layer-structure fingerprinting

### Best Source for Complete Collection
**→ Run `bo2-emblem-toolkit` in capture mode for 2–3 sessions.**  
Join popular Plutonium servers, open barracks → recent players → view profiles. Each profile view = 1 captured emblem (all 10 slots if available).

### Technical Spec for Generator
**Complete** — see `references/bo2-emblem-format.md`.  
Can implement from scratch:
1. Define layers (shapeId, transforms, color)
2. Serialize to 1408 bytes
3. Write to `%localappdata%\Plutonium\storage\t6\players\N#emblem.emblem`
4. Game loads immediately

---

## Action Items for Collection Build

1. [ ] Set up `bo2-emblem-toolkit` (Windows: download Release exe; Linux/Mac: `pip install -r requirements.txt && python run.py`)
2. [ ] Configure PS5/PC proxy per `docs/INSTALL.md` + `docs/USAGE.md`
3. [ ] Run capture session on active Plutonium servers
4. [ ] Decode 505e06b2 examples → add to collection
5. [ ] Scrape Plutonium Forum (browser automation or API if available)
6. [ ] Search Reddit with Pushshift/BigQuery for historical posts
7. [ ] Join Discord, export `#emblems` history
8. [ ] Deduplicate via SHA256 + layer fingerprint
9. [ ] Organize into `/Emblems/{Anime,Games,Memes,Logos,Weapons,Zombies,Funny,Flags,Misc}/`
10. [ ] Generate `index.json` with metadata

---

## Skill Updates Made

- `references/bo2-emblem-format.md` — Complete technical specification
- `references/asset-discovery-checklist.md` — Reusable methodology for future game asset RE