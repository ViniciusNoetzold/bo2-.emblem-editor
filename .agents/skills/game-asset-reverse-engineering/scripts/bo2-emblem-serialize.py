#!/usr/bin/env python3
"""
Serialize BO2 emblem layer definitions to raw 1408-byte .emblem files.

Layer dict format:
    {
        "index": 0,           # 0-31 (layer order: lower = back)
        "shape": 137,         # shape ID (0xFFFF = empty)
        "r": 1.0, "g": 0.0, "b": 0.0, "a": 1.0,
        "x": 0.0, "y": 0.0,
        "sx": 0.0, "sy": 0.0,
        "rot": 0.0,
        "outlined": False,
        "flipped": False,
    }

Usage:
    python scripts/bo2-emblem-serialize.py layers.json output.emblem
"""

import sys
import json
import struct
from pathlib import Path
import argparse


# BO2 Constants
LAYER_SIZE = 44
NUM_LAYERS = 32
EMPTY_SHAPE = 0xFFFF
TOTAL_SIZE = LAYER_SIZE * NUM_LAYERS  # 1408


def serialize_layers(layers: list[dict]) -> bytes:
    """Serialize layer list to 1408-byte emblem blob."""
    out = bytearray(TOTAL_SIZE)

    # Fill all layers with empty sentinel first
    for i in range(NUM_LAYERS):
        struct.pack_into("<H", out, i * LAYER_SIZE, EMPTY_SHAPE)

    # Write actual layers
    for L in layers:
        idx = L["index"]
        if not 0 <= idx < NUM_LAYERS:
            raise ValueError(f"Layer index {idx} out of range 0-31")

        offset = idx * LAYER_SIZE
        struct.pack_into("<H", out, offset, L["shape"])
        # 2 bytes padding at offset+2
        struct.pack_into("<9f", out, offset + 4,
            L["r"], L["g"], L["b"], L["a"],
            L["x"], L["y"],
            L["sx"], L["sy"],
            L["rot"])
        out[offset + 40] = 1 if L.get("outlined", False) else 0
        out[offset + 41] = 1 if L.get("flipped", False) else 0
        # 2 bytes padding at offset+42

    return bytes(out)


def validate_layers(layers: list[dict]) -> list[str]:
    """Return list of validation warnings/errors."""
    errors = []
    seen_indices = set()

    for L in layers:
        # Index
        idx = L.get("index")
        if idx is None:
            errors.append("Layer missing 'index'")
            continue
        if not 0 <= idx < NUM_LAYERS:
            errors.append(f"Layer index {idx} out of range 0-31")
        if idx in seen_indices:
            errors.append(f"Duplicate layer index {idx}")
        seen_indices.add(idx)

        # Shape ID
        shape = L.get("shape", EMPTY_SHAPE)
        if not 0 <= shape <= 0xFFFF:
            errors.append(f"Layer {idx}: shape ID {shape} out of uint16 range")

        # Floats
        for field in ["r","g","b","a","x","y","sx","sy","rot"]:
            val = L.get(field, 0.0)
            if not isinstance(val, (int, float)):
                errors.append(f"Layer {idx}: {field} must be numeric")

        # Bools
        for field in ["outlined", "flipped"]:
            val = L.get(field, False)
            if not isinstance(val, bool):
                errors.append(f"Layer {idx}: {field} must be boolean")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Serialize BO2 emblem layers to .emblem file")
    parser.add_argument("input", help="JSON file with layer list")
    parser.add_argument("output", help="Output .emblem file")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, don't write")
    args = parser.parse_args()

    # Load JSON
    try:
        with open(args.input) as f:
            layers = json.load(f)
    except Exception as e:
        print(f"Error reading {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(layers, list):
        print("Error: JSON root must be a list of layer objects", file=sys.stderr)
        sys.exit(1)

    # Validate
    errors = validate_layers(layers)
    if errors:
        print("Validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    if args.validate_only:
        print("✓ Validation passed")
        return

    # Serialize
    try:
        data = serialize_layers(layers)
    except Exception as e:
        print(f"Serialization error: {e}", file=sys.stderr)
        sys.exit(1)

    # Write
    Path(args.output).write_bytes(data)
    print(f"✓ Written {len(data)} bytes to {args.output}")


if __name__ == "__main__":
    main()