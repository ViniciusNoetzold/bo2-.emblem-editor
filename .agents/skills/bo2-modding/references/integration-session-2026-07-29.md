# Integration Session: Ultimate Zombies Pack (2026-07-29)

## Context
- **Base**: T6-ZM-Expanded-1.0.0 (comprehensive Zombies expansion mod)
- **Addon**: Wonder Weapons Pack T6ZM-1.4 (ThunderGun, Winter's Howl/FreezeGun, Tesla Gun + upgraded variants)
- **Target**: Single playable mod for Plutonium T6

## Key Discoveries

### File Structure Mapping
| Asset Type | Base Location | Wonder Weapons Source | Final Location |
|------------|---------------|----------------------|----------------|
| WeaponDefs | `weapons/zm/` | `src/weapons/zm/` | `weapons/zm/` (6 files: 3 base + 3 upgraded) |
| Server GSC | `scripts/zm/` | `src/scripts/zm/` | `scripts/zm/` |
| Client CSC | `clientscripts/mp/zombies/` | `src/clientscripts/mp/zombies/` | `clientscripts/mp/zombies/` |
| Map GSC | `maps/mp/zombies/` | `src/maps/mp/zombies/` | `maps/mp/zombies/` |
| Zone Files | `zone_source/weapons/` | `src/zone_source/weapons/` | `zone_source/weapons/` |
| Soundbanks | `soundbank/` | `src/soundbank/` | `soundbank/` |
| Localized Strings | `english/localizedstrings/` | `src/english/localizedstrings/` | `english/localizedstrings/` |
| FX | `fx/` | `fx/` | `fx/` |
| Images | `images/` | `images/` | `images/` |
| XAnim | `xanim/` | `xanim/` | `xanim/` |
| AnimTrees | `animtrees/` | `animtrees/` | `animtrees/` |
| AnimStateDefs | `animstatedefs/` | `animstatedefs/` | `animstatedefs/` |
| Camo | `camo/` | `camo/` | `camo/` |

### Missing Critical Files in Base Mod
The base T6-ZM-Expanded **does not contain** `_zm_weapons.gsc` or `_zm_weapons.csc` despite referencing them:
- `clientscripts\mp\zombies\_zm_weapons::weapon_box_callback` (mystery box)
- `maps\mp\zombies\_zm_weapons::is_weapon_included` (weapon availability checks)
- `maps\mp\zombies\_zm_weapons::is_weapon_upgraded`
- `maps\mp\zombies\_zm_weapons::take_fallback_weapon`

**Solution**: Create these files with the weapon box array containing all 6 wonder weapons.

### Weapon Registration Pattern (from Wonder Weapons)
Each wonder weapon GSC follows this pattern:
```gsc
#include maps\mp\zombies\_zm_utility;
#include maps\mp\zombies\_zm_weapons;

init() {
    precachestring(&"ZOMBIE_WEAPON_<WEAPON>");
    precacheitem("<weapon>_zm");
    precacheitem("<weapon>_upgraded_zm");
    include_weapon("<weapon>_zm");
    add_limited_weapon("<weapon>_zm", 1); // box limit
    add_zombie_weapon("<weapon>_zm", "<weapon>_upgraded_zm", &"ZOMBIE_WEAPON_<WEAPON>", 10, "<type>", "", undefined);
    maps\mp\zombies\_zm_weap_<weapon>::init();
}
```

### Zone File Requirements
Each weapon needs a `zone_source/weapons/<weapon>.zone` with:
- `script,maps/mp/zombies/_zm_weap_<weapon>.gsc`
- `script,clientscripts/mp/zombies/_zm_weap_<weapon>.csc`
- `xmodel` entries for view/world models
- `material` entries for camos, effects
- `rawfile` for rumble
- `camo,<camo_name>`
- `localize,<string_name>`

Upgraded variants can reuse the same zone content (same models/materials/sounds).

### mod.zone Updates Needed
Add explicit blocks for each weapon (base + upgraded):
```
include,weapons/<weapon>_zm
include,weapons/<weapon>_upgraded_zm
soundbank,wpn_<weapon>.all
script,scripts/zm/<weapon>.csc
script,scripts/zm/<weapon>.gsc
localize,<weapon>
rawfile,animtrees/... (6 maps)
rawfile,animstatedefs/... (6 maps)
script,scripts/zm/zm_<map>/anims_<weapon>.gsc // noignore
```

### Build System Notes
- `build.bat` expects OAT at `C:\OAT\linker.exe`
- Uses PowerShell `Compress-Archive` for `.iwd` creation (fails if PowerShell unavailable)
- Copies outputs to `%LOCALAPPDATA%\Plutonium\storage\t6\<mod_name>\`
- Mod name in `build.bat`: `zm_expanded` (must match folder name)

## Conflicts Resolved (Prefer Wonder Weapons Version)
- All 6 weapon definition files: overwrote base with Wonder Weapons versions
- All GSC/CSC scripts: overwrote with Wonder Weapons versions
- Soundbanks: replaced with Wonder Weapons versions
- Localized strings: replaced with Wonder Weapons versions
- Zone files: merged (kept base structure, added upgraded variants)

## Remaining Work for Playable Build
1. Add `freeze.gsc`, `teslagun.gsc`, `thundergun.gsc` to `scripts.zone`
2. Create `_zm_weapons.gsc` and `_zm_weapons.csc` with mystery box array
3. Verify `mod.json` references
4. Run build (requires OAT installation)

## Files Modified in This Session
- `zone_source/mod.zone` — added 6 weapon blocks with all references
- `zone_source/weapons/freezegun_upgraded_zm.zone` — created
- `zone_source/weapons/tesla_gun_upgraded_zm.zone` — created
- `zone_source/weapons/thundergun_upgraded_zm.zone` — created
- All asset folders copied from Wonder Weapons to workspace root