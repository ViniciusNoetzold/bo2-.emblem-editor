---
name: bo2-modding
description: "Structured workflow for creating and integrating Call of Duty: Black Ops II Zombies mods using BO2 Mod Tools (OAT) and Plutonium T6."
version: 1.0.0
category: software-development
---
# BO2 Mod Development (Call of Duty: Black Ops II Zombies)

**Domain**: Game Modding (BO2 Zombies)  
**Trigger**: User wants to create, modify, or integrate mods for BO2 Zombies using the BO2 Mod Tools (OAT) and Plutonium T6.

## Overview
This skill provides a structured workflow for building a BO2 mod from existing base mods (e.g., T6-ZM-Expanded) and add‑on packs (e.g., Wonder Weapons). It covers workspace setup, file organization, conflict resolution, zone file updates, and building the final `.iwd` and `.ff` files using the provided `build.bat`.

## Typical Workflow
1. **Prepare Workspace**  
   - Create a clean workspace folder (e.g., `Workspace/Ultimate_Zombies_Pack/`).  
   - Establish the standard module directory tree:   
     ```
     Core/
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
   - Copy the base mod (e.g., `T6-ZM-Expanded-1.0.0`) into the workspace root, preserving its original structure.  
   - Stage any add‑on source (e.g., Wonder Weapons) in a dedicated subfolder (e.g., `WonderWeapons/src`).

2. **Integrate Add‑on Content**  
   - Move client scripts (`*.csc`) to `Weapons/<WeaponName>/clientscripts/mp/zombies/`.  
   - Move server scripts (`*.gsc`) to `Weapons/<WeaponName>/maps/mp/zombies/` (or map‑specific subfolders).  
   - Move shared scripts, models, materials, sounds, FX, and icons into appropriate subfolders under `Weapons/<WeaponName>/` or `Shared/`.  
   - Update any `#include` or `#using` statements in copied scripts to reflect new relative paths.  
   - Merge any additional `.zone` snippets into `zone_source/mod.zone`, `scripts.zone`, and `clientScripts.zone`.

3. **Resolve Conflicts & Duplicates**  
   - Use the audit reports (`identical_files.txt`, `different_files.txt`, `base_only.txt`, `merge_only.txt`) to identify overlapping files between base and addon.  
   - Decide which version to keep (usually prefer the addon for new weapons, keep base for shared systems).  
   - Remove or rename duplicates, ensuring no two assets share the same internal name.  
   - Verify that all weapon definitions (`*.wt`) have unique names and are referenced correctly in weapon tables.

4. **Update Metadata**  
   - Edit `mod.json` to reflect the new mod name, version, and any additional dependencies (e.g., extra strings, FX).  
   - Ensure the `mod_name` in `build.bat` matches the folder name under `%LOCALAPPDATA%\Plutonium\storage\t6\mods\`.

5. **Build the Mod**  
   - Verify that the OAT (Official Asset Tool) is installed at `C:\OAT` (or adjust `OAT_BASE` in `build.bat`).  
   - Run `build.bat` from the workspace root.  
   - The script will:  
     * Call `linker.exe` to produce `zone/mod.ff`.  
     * Create `mod.iwd` via PowerShell `Compress-Archive`.  
     * Copy the outputs to the Plutonium mods folder.  
   - Check console output for errors (missing assets, duplicate defines, etc.) and fix them before proceeding.

6. **Test & Iterate**  
   - Launch Plutonium, load the map, and verify that new weapons, perks, or features appear and function correctly.  
   - Look for script errors in the console (`~` key) and address any missing function or asset warnings.  
   - Repeat steps 2‑5 as needed until the build is clean and the mod works in‑game.

## Key File Patterns & Integration Points (from session)
- **Weapon Definition Files** (`.wt` / no-extension): Place in `weapons/zm/` — the linker picks them up via `file: weapons/zm/* weapons/zm/` in `mod.zone`.
- **Wonder Weapon Scripts**: Each weapon needs:
  - Server GSC: `scripts/zm/<weapon>.gsc` + `scripts/zm/<weapon>.csc` (registers via `include_weapon`, `add_limited_weapon`, `add_zombie_weapon`)
  - Client CSC: `clientscripts/mp/zombies/_zm_weap_<weapon>.csc`
  - Map GSC: `maps/mp/zombies/_zm_weap_<weapon>.gsc` (anim/behavior callbacks)
  - Zone file: `zone_source/weapons/<weapon>.zone` (models, materials, FX, xmodels, camos, sound aliases, localized strings)
- **Mystery Box Integration**: The base mod references `clientscripts\mp\zombies\_zm_weapons::weapon_box_callback` and `maps\mp\zombies\_zm_weapons::is_weapon_included`. These files **do not exist** in T6-ZM-Expanded — you must create `_zm_weapons.gsc` and `_zm_weapons.csc` with:
  - A weapon box array containing all wonder weapon names (base + upgraded variants)
  - `is_weapon_included(weapon_name)` function for map scripts to check availability
- **Anim Scripts per Map**: Map-specific anim scripts live under `scripts/zm/zm_<map>/anims_<weapon>.gsc` and are registered in `mod.zone` with `// noignore` comment.
- **Sound Aliases**: Each weapon needs a `wpn_<weapon>.all.aliases.csv` in `soundbank/` referenced via `soundbank,wpn_<weapon>.all` in `mod.zone`.
- **Localized Strings**: `.str` files in `english/localizedstrings/` referenced via `localize,<name>` in `mod.zone`.
- **Build Script Dependency**: `build.bat` uses PowerShell `Compress-Archive` for `.iwd` creation. If PowerShell is unavailable, replace with `7z` or equivalent.

## Common Pitfalls & How to Avoid Them
- **OAT Path Missing**: The build will fail with "システムネ specified path". Ensure `C:\OAT` exists and contains `linker.exe`. Edit `OAT_BASE` in `build.bat` if your installation differs.
- **Duplicate Asset Names**: Two `.asi` or `.wt` files with the same internal name cause linker errors. Use the audit diff to rename conflicting assets.
- **Incorrect Include Paths**: After moving scripts, update `#include` lines to match the new location (e.g., `#include maps/mp/zombies/_zm_weap_tesla;`).
- **Zone File Omissions**: Forgetting to add a new model/sound to `mod.zone` results in the asset being omitted from the build, causing "missing asset" errors in‑game.
- **Script Order Issues**: Some GSC scripts depend on others being loaded first; ensure `zm_*.gsc` are listed after their dependencies in `scripts.zone`.
- **Missing Mystery Box Callback File**: The base mod references `_zm_weapons::weapon_box_callback` but doesn't provide it. Create `_zm_weapons.gsc/.csc` with the weapon box array and `is_weapon_included` function.
- **PowerShell Unavailable**: `build.bat` uses `Compress-Archive` which requires PowerShell. Have a fallback (7-Zip) ready.

## Reference Materials
- See `references/audit-summary.md` for a summary of the file‑level comparison between the base T6‑ZM‑Expanded and Wonder Weapons packs (generated in this session).  
- Official BO2 Mod Tools documentation (provided with OAT) for detailed `linker.exe` flags.  
- Plutonium T6 modding wiki for scripting conventions and asset limits.

## Example Commands (for reference)
```bash
# From workspace root
./build.bat
# If PowerShell is unavailable, use the built‑in zip utility:
powershell -Command "Compress-Archive -Force -Path attachmentunique,maps,scripts,weapons -DestinationPath mod.iwd"
```

## Notes
- Keep the original `Base/` and `Merge/` directories untouched; they serve as canonical sources for future updates.  
- When updating the mod with newer versions of the base or addon, repeat the integration steps using fresh copies to avoid drift.  
- Document any custom changes (e.g., custom weapon parameters) in `Documentation/changelog.md`.