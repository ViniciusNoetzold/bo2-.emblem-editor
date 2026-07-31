# Asset Discovery Checklist

Use this when starting research on a new game's asset formats.

## 1. Identify the Target

- [ ] Game title, engine, platform(s)
- [ ] Official modding support? (Steam Workshop, official tools, SDK)
- [ ] Community modding scene? (Discord, forums, GitHub orgs)
- [ ] Target file types: save files, assets, network packets, memory structures

## 2. GitHub Reconnaissance

**Search Queries** (use GitHub API or web):
- `filename:.ext game-name`
- `extension:ext game-name`
- `game-name modding`
- `game-name reverse engineering`
- `game-name parser`
- `game-name editor`
- `topic:game-name topic:modding`
- `topic:game-name topic:reverse-engineering`

**Repositories to Collect**:
- [ ] Format specifications / docs
- [ ] Parsers / readers (any language)
- [ ] Editors / viewers (GUI or CLI)
- [ ] Asset packs / examples
- [ ] Memory addresses / offset tables
- [ ] Tooling: extractors, packers, converters

**For Each Repo**:
- [ ] Clone / download
- [ ] Extract format docs (README, docs/, wiki, code comments)
- [ ] Extract reference implementations (parsers, structs)
- [ ] Extract example assets
- [ ] Note license / attribution requirements

## 3. Community Forums & Wikis

| Platform | Search Terms | Notes |
|----------|--------------|-------|
| Official Forum | `ext format`, `save file`, `asset` | Often requires login |
| Reddit (r/gamemodding, r/gamename) | `format`, `reverse`, `parser` | Check wiki/pages |
| Discord | `#modding`, `#reverse-engineering`, `#datamining` | Ask for invites; search history |
| Steam Community | Guides, Workshop discussions | Workshop often has tools |
| Nexus Mods | File descriptions, posts | Download sample mods |
| ModDB / GameBanana | Downloads, forums | Older games |
| UnknownCheats / MPGH | `struct`, `offset`, `dump` | Game hacking focus but has RE |
| Wiki (Fandom, Gamepedia) | `File format`, `Modding` | Sometimes has specs |

## 4. Archive & Search Engines

- [ ] **Internet Archive** (archive.org) — search for dead forum links, old tools
- [ ] **Wayback Machine** — specific forum threads that 404
- [ ] **Google/Bing/DuckDuckGo** — `filetype:ext game-name`, `site:forum.url ext`
- [ ] **GitHub Gists** — often have quick parsers/snippets

## 5. Sample Collection

**Minimum Viable Set**:
- [ ] Empty/minimal valid file
- [ ] Simple/single-entity file
- [ ] Complex/maxed file
- [ ] Corrupted/invalid (for error handling)

**For Each Sample**:
- [ ] SHA256 hash
- [ ] Source (URL, author, date)
- [ ] Known-good render / in-game appearance
- [ ] Hex dump (first 256 bytes + full)

## 6. Binary Analysis

**Tools**:
- [ ] 010 Editor / ImHex / Synalyze It! (template-based)
- [ ] `xxd`, `hexdump`, `binwalk` (CLI)
- [ ] Custom Python scripts (struct, construct, kaitai)

**Process**:
1. [ ] Align multiple samples side-by-side (diff)
2. [ ] Identify fixed headers / magic / version
3. [ ] Find repeating structures (layer/entity records)
4. [ ] Correlate with known values (change one thing in-game, re-dump)
5. [ ] Build struct definitions
6. [ ] Write parser → test round-trip on all samples

## 7. Live Validation (Critical)

- [ ] **Memory read** while game runs (Cheat Engine, custom dumper, Frida)
- [ ] **Write test** — modify memory, observe in-game change
- [ ] **Inject test** — write crafted bytes, verify game reads correctly
- [ ] Cross-reference community specs vs. live behavior

## 8. Documentation Output

- [ ] `FORMAT.md` — Complete spec with structs, enums, constants, diagrams
- [ ] `parser.py` — Reference implementation with round-trip tests
- [ ] `renderer.py` — Visualization for verification
- [ ] `samples/` — Curated examples with metadata JSON
- [ ] `index.json` — Asset database (if collecting community assets)

## 9. Packaging for Reuse

- [ ] Add to skill references: `references/<game>-<format>.md`
- [ ] Add parser template: `templates/<game>-<format>-parser.py`
- [ ] Add discovery notes: `references/<game>-discovery-notes.md`
- [ ] Update skill's game-specific notes section

## Red Flags (Stop & Investigate)

- ⚠️ Only one source for format info → validate independently
- ⚠️ Parser fails on "simple" files → spec incomplete
- ⚠️ Community specs disagree → live memory read required
- ⚠️ Encryption/compression unknown → check network traffic or memory
- ⚠️ Assets don't load in-game → wrong path, wrong format, version mismatch