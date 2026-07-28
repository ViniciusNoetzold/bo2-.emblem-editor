"""
BO2 Shape ID Map
================
Complete mapping of shape IDs to names and categories.
Based on reverse engineering from bo2-emblem-toolkit and live memory analysis.
"""

# Shape ID -> (Category, Name)
SHAPE_ID_MAP = {
    # GEAR (weapons/perks) - IDs 0-37, 260
    0: ("gear", "KAP-40 Qualified"),
    1: ("gear", "Tac-45 Qualified"),
    2: ("gear", "B23R Qualified"),
    3: ("gear", "Executioner Qualified"),
    4: ("gear", "Five-seven Qualified"),
    5: ("gear", "MP7 Qualified"),
    6: ("gear", "Skorpion EVO Qualified"),
    7: ("gear", "PDW-57 Qualified"),
    8: ("gear", "Chicom CQB Qualified"),
    9: ("gear", "MSMC Qualified"),
    10: ("gear", "Vector K10 Qualified"),
    11: ("gear", "M8A1 Qualified"),
    12: ("gear", "SCAR-H Qualified"),
    13: ("gear", "AN-94 Qualified"),
    14: ("gear", "SWAT-556 Qualified"),
    15: ("gear", "Type 25 Qualified"),
    16: ("gear", "FAL OSW Qualified"),
    17: ("gear", "SMR Qualified"),
    18: ("gear", "M27 Qualified"),
    19: ("gear", "MTAR Qualified"),
    20: ("gear", "Mk 48 Qualified"),
    21: ("gear", "QBB LSW Qualified"),
    22: ("gear", "LSAT Qualified"),
    23: ("gear", "HAMR Qualified"),
    24: ("gear", "Ballista Qualified"),
    25: ("gear", "SVU-AS Qualified"),
    26: ("gear", "DSR 50 Qualified"),
    27: ("gear", "XPR-50 Qualified"),
    28: ("gear", "R870 MCS Qualified"),
    29: ("gear", "M1216 Qualified"),
    30: ("gear", "S12 Qualified"),
    31: ("gear", "KSG Qualified"),
    32: ("gear", "SMAW Qualified"),
    33: ("gear", "FHJ-18 AA Qualified"),
    34: ("gear", "RPG Qualified"),
    35: ("gear", "Assault Shield Qualified"),
    36: ("gear", "Crossbow Qualified"),
    37: ("gear", "Ballistic Knife Qualified"),
    260: ("gear", "Peacekeeper Qualified"),  # DLC weapon
    
    # RANKS - IDs 198-216
    198: ("ranks", "Private 1st Class"),
    199: ("ranks", "Lance Corporal"),
    200: ("ranks", "Corporal"),
    201: ("ranks", "Sergeant"),
    202: ("ranks", "Staff Sergeant"),
    203: ("ranks", "Gunnery Sergeant"),
    204: ("ranks", "Master Sergeant"),
    205: ("ranks", "Master Gunnery Sergeant"),
    206: ("ranks", "Second Lieutenant"),
    207: ("ranks", "Lieutenant"),
    208: ("ranks", "Captain"),
    209: ("ranks", "Major"),
    210: ("ranks", "Lt. Colonel"),
    211: ("ranks", "Colonel"),
    212: ("ranks", "Brigadier General"),
    213: ("ranks", "Major General"),
    214: ("ranks", "Lt. General"),
    215: ("ranks", "General"),
    216: ("ranks", "Commander"),
    
    # TOOLS (basic shapes) - IDs 137-197
    137: ("tools", "Half Circle"),
    138: ("tools", "Quarter Circle"),
    139: ("tools", "Half Heart"),
    140: ("tools", "Cone"),
    141: ("tools", "Thimble"),
    142: ("tools", "Kiss"),
    143: ("tools", "Scribble"),
    144: ("tools", "Round Square"),
    145: ("tools", "Ninja Star"),
    146: ("tools", "Half Star"),
    147: ("tools", "Shuriken"),
    148: ("tools", "Half Shuriken"),
    149: ("tools", "Lamp Shade"),
    150: ("tools", "Pyramid"),
    151: ("tools", "Half Tube"),
    152: ("tools", "Tube"),
    153: ("tools", "Golf Flag"),
    154: ("tools", "Tongue"),
    155: ("tools", "Broken Column"),
    156: ("tools", "Visor"),
    157: ("tools", "Bone"),
    158: ("tools", "Armchair"),
    159: ("tools", "Oven Mitt"),
    160: ("tools", "Wind Sock"),
    161: ("tools", "Podium"),
    162: ("tools", "Pie Slice"),
    163: ("tools", "Flashlight"),
    164: ("tools", "Scoop"),
    165: ("tools", "Flag Breeze"),
    166: ("tools", "Flag No Wind"),
    167: ("tools", "Axe"),
    168: ("tools", "Fedora"),
    169: ("tools", "Rock"),
    170: ("tools", "Bike Ramp"),
    171: ("tools", "Rock Shadow"),
    172: ("tools", "Half Column"),
    173: ("tools", "Monolith"),
    174: ("tools", "Top Hat"),
    175: ("tools", "Igloo"),
    176: ("tools", "Mane"),
    177: ("tools", "Swoop"),
    178: ("tools", "Shield"),
    179: ("tools", "Paint Splash"),
    180: ("tools", "Pillow"),
    181: ("tools", "Asterisk Full"),
    182: ("tools", "Biohazard"),
    183: ("tools", "Curved Line"),
    184: ("tools", "Smile Outline"),
    185: ("tools", "Heart"),
    186: ("tools", "Ice Star"),
    187: ("tools", "Triangle Wide"),
    188: ("tools", "Tent"),
    189: ("tools", "Half Short Hair"),
    190: ("tools", "Half Mustache"),
    191: ("tools", "Half Long Hair"),
    192: ("tools", "Full Circle"),
    193: ("tools", "Circle 02"),
    194: ("tools", "Diamond"),
    195: ("tools", "Rectangle Medium"),
    196: ("tools", "Square Full"),
    197: ("tools", "Treyarch"),
    
    # TYPE (letters/numbers) - IDs 217-252
    217: ("type", "Letter A"),
    218: ("type", "Letter B"),
    219: ("type", "Letter C"),
    220: ("type", "Letter D"),
    221: ("type", "Letter E"),
    222: ("type", "Letter F"),
    223: ("type", "Letter G"),
    224: ("type", "Letter H"),
    225: ("type", "Letter I"),
    226: ("type", "Letter J"),
    227: ("type", "Letter K"),
    228: ("type", "Letter L"),
    229: ("type", "Letter M"),
    230: ("type", "Letter N"),
    231: ("type", "Letter O"),
    232: ("type", "Letter P"),
    233: ("type", "Letter Q"),
    234: ("type", "Letter R"),
    235: ("type", "Letter S"),
    236: ("type", "Letter T"),
    237: ("type", "Letter U"),
    238: ("type", "Letter V"),
    239: ("type", "Letter W"),
    240: ("type", "Letter X"),
    241: ("type", "Letter Y"),
    242: ("type", "Letter Z"),
    243: ("type", "Zero"),
    244: ("type", "One"),
    245: ("type", "Two"),
    246: ("type", "Three"),
    247: ("type", "Four"),
    248: ("type", "Five"),
    249: ("type", "Six"),
    250: ("type", "Seven"),
    251: ("type", "Eight"),
    252: ("type", "Nine"),
    
    # EMBLEMS (pre-made icons) - IDs 38-136, 253-259
    38: ("emblems", "Crushing Victory"),
    39: ("emblems", "Crushing Victory "),
    40: ("emblems", "Crushing Victory  "),
    41: ("emblems", "Crushing Victory   "),
    42: ("emblems", "Crushing Victory    "),
    43: ("emblems", "Shutout"),
    44: ("emblems", "Shutout "),
    45: ("emblems", "Crushing Victory     "),  # 5 trailing spaces
    46: ("emblems", "Annihilation Victory"),
    47: ("emblems", "Relentless"),
    48: ("emblems", "Triple Kill"),
    49: ("emblems", "Avenger"),
    50: ("emblems", "Savior"),
    51: ("emblems", "Unstoppable"),
    52: ("emblems", "Ninja"),
    53: ("emblems", "Last Man Standing"),
    54: ("emblems", "The Finisher"),
    55: ("emblems", "Shutout Round"),
    56: ("emblems", "Bomb Protector"),
    57: ("emblems", "Interruption"),
    58: ("emblems", "Bomb Protector "),
    59: ("emblems", "Interruption "),
    60: ("emblems", "Super Star"),
    61: ("emblems", "Double Denied"),
    62: ("emblems", "Bravo Hot"),
    63: ("emblems", "Alpha Lockdown"),
    64: ("emblems", "Bravo Lockdown"),
    65: ("emblems", "Charlie Lockdown"),
    66: ("emblems", "Synchronized Attack"),
    67: ("emblems", "Point Man"),
    68: ("emblems", "Zone Sweep"),
    69: ("emblems", "Trick Shot"),
    70: ("emblems", "Clean House"),
    71: ("emblems", "Slice 'n Dice"),
    72: ("emblems", "Wet Work"),
    73: ("emblems", "Situation Critical"),
    74: ("emblems", "Far Sighted"),
    75: ("emblems", "Tick Tick Boom"),
    76: ("emblems", "Pistoleer"),
    77: ("emblems", "Say Hello"),
    78: ("emblems", "Headhunter"),
    79: ("emblems", "Sharpshooter"),
    80: ("emblems", "Close Quarters Expert"),
    81: ("emblems", "Counter Trapper"),
    82: ("emblems", "Surprise Package"),
    83: ("emblems", "Counter Hacker"),  # Same image as 48
    84: ("emblems", "Aircraft Hunter"),
    85: ("emblems", "Clean Sweep"),
    86: ("emblems", "Grab n Go"),
    87: ("emblems", "Protected Kill"),
    88: ("emblems", "Close Call"),
    89: ("emblems", "Arch Nemesis"),
    90: ("emblems", "Circus Act"),
    91: ("emblems", "Found Kills"),
    92: ("emblems", "Short Fuse"),
    93: ("emblems", "High Voltage"),
    94: ("emblems", "Follow Through"),
    95: ("emblems", "Stick Around"),
    96: ("emblems", "Interruption"),
    97: ("emblems", "Brutal Killer"),
    98: ("emblems", "Fury Killer"),
    99: ("emblems", "Frenzy Killer"),
    100: ("emblems", "Super Killer"),
    101: ("emblems", "All Clear"),
    102: ("emblems", "Assisted Homicide"),
    103: ("emblems", "Backdraft"),
    104: ("emblems", "Guerilla Warfare"),
    105: ("emblems", "Vandalism"),
    106: ("emblems", "Action Hero"),
    107: ("emblems", "Commando"),
    108: ("emblems", "Perk Greed"),
    109: ("emblems", "Danger Close"),
    110: ("emblems", "Overkill"),
    111: ("emblems", "Gunfighter"),
    112: ("emblems", "Killjoy"),
    113: ("emblems", "Pest Control"),
    114: ("emblems", "Drones Eliminated"),
    115: ("emblems", "Dog Pound"),
    116: ("emblems", "Down Dog"),
    117: ("emblems", "Opportunistic"),
    118: ("emblems", "Maximum Payload"),
    119: ("emblems", "Anti-Swatter"),
    120: ("emblems", "Threat Neutralized"),
    121: ("emblems", "Special Delivery"),
    122: ("emblems", "RC Multi Bomber"),
    123: ("emblems", "Heavy Cover"),
    124: ("emblems", "Thumper"),
    125: ("emblems", "Shredder"),
    126: ("emblems", "Focus Fire"),
    127: ("emblems", "Tracker"),
    128: ("emblems", "Guide Dogs"),
    129: ("emblems", "Hard Counter"),
    130: ("emblems", "Overcooked"),
    131: ("emblems", "Cancelled Out"),
    132: ("emblems", "Make It Rain"),
    133: ("emblems", "Got Your Back"),
    134: ("emblems", "Small Game Hunter"),
    135: ("emblems", "Big Game Hunter"),
    136: ("emblems", "Thief"),
    # Block 2: 253-259
    253: ("emblems", "Merciless"),
    254: ("emblems", "Ruthless"),
    255: ("emblems", "Hard to Kill"),
    256: ("emblems", "Invincible"),
    257: ("emblems", "Elite Member"),
    258: ("emblems", "Elite Founder"),
    259: ("emblems", "Default Emblem"),
    
    # EMPTY/UNUSED
    65535: ("empty", "Empty Layer"),
}


# Reverse lookups
NAME_TO_ID = {f"{cat}/{name}": sid for sid, (cat, name) in SHAPE_ID_MAP.items()}
CATEGORY_TO_IDS = {}
for sid, (cat, name) in SHAPE_ID_MAP.items():
    if cat not in CATEGORY_TO_IDS:
        CATEGORY_TO_IDS[cat] = []
    CATEGORY_TO_IDS[cat].append(sid)


def get_shape_name(shape_id: int) -> str:
    """Get shape name for ID, or 'Unknown'."""
    if shape_id in SHAPE_ID_MAP:
        cat, name = SHAPE_ID_MAP[shape_id]
        return f"{cat}/{name}"
    return f"Unknown (0x{shape_id:04X})"


def get_shape_category(shape_id: int) -> str:
    """Get category for shape ID."""
    if shape_id in SHAPE_ID_MAP:
        return SHAPE_ID_MAP[shape_id][0]
    return "unknown"


def get_shape_id(category: str, name: str) -> int:
    """Look up shape ID by category and name."""
    key = f"{category}/{name}"
    return NAME_TO_ID.get(key, 0xFFFF)


def get_ids_by_category(category: str) -> list:
    """Get all shape IDs for a category."""
    return CATEGORY_TO_IDS.get(category, [])


def list_categories() -> list:
    """List all available categories."""
    return list(CATEGORY_TO_IDS.keys())


# Category display names
CATEGORY_DISPLAY = {
    "gear": "⚔️ Gear (Weapons/Perks)",
    "ranks": "🎖️ Ranks",
    "tools": "🔧 Tools (Basic Shapes)",
    "type": "🔤 Type (Letters/Numbers)",
    "emblems": "⭐ Emblems (Pre-made Icons)",
    "empty": "⬜ Empty",
}

# Categories in preferred UI order
CATEGORY_ORDER = ["tools", "type", "emblems", "gear", "ranks"]


def get_category_display(category: str) -> str:
    return CATEGORY_DISPLAY.get(category, category.title())


# Statistics
TOTAL_SHAPES = len([k for k in SHAPE_ID_MAP.keys() if k != 65535])
SHAPES_BY_CATEGORY = {cat: len(ids) for cat, ids in CATEGORY_TO_IDS.items()}