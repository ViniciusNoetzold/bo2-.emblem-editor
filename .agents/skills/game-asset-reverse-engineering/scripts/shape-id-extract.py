#!/usr/bin/env python3
"""
Extract known_ids mapping from alexkotr1/bo2-emblem-toolkit's shape_id_map.py.

Outputs a clean JSON mapping: {shape_id: "Category/Name"}

Usage:
    python scripts/shape-id-extract.py [shape_id_map.py] [output.json]
"""

import sys
import json
import re
from pathlib import Path
import argparse


def extract_known_ids(source_path: Path) -> dict[int, str]:
    """Parse shape_id_map.py and extract the known_ids dictionary."""
    content = source_path.read_text(encoding="utf-8")

    # Find the known_ids dict building - it's built incrementally
    # Pattern: known_ids[ID] = "Category/Name"  OR  known_ids.update({ID: "Category/Name", ...})
    known_ids = {}

    # Match direct assignments: known_ids[123] = "tools/Half Circle"
    for match in re.finditer(r'known_ids\[(\d+)\]\s*=\s*"([^"]+)"', content):
        shape_id = int(match.group(1))
        name = match.group(2)
        known_ids[shape_id] = name

    # Match update() calls with dict literals
    for match in re.finditer(r'known_ids\.update\(\{([^}]+)\}\)', content, re.DOTALL):
        dict_content = match.group(1)
        # Parse {id: "name", ...}
        for kv_match in re.finditer(r'(\d+)\s*:\s*"([^"]+)"', dict_content):
            shape_id = int(kv_match.group(1))
            name = kv_match.group(2)
            known_ids[shape_id] = name

    # Match comprehensions: {i: f"tools/{name}" for i, name in enumerate(list, start=X)}
    for match in re.finditer(
        r'known_ids\.update\(\{i: f"([^"]+)/\{name\}" for i, name in enumerate\(([^,]+),\s*start=(\d+)\)\}',
        content
    ):
        category = match.group(1)
        list_name = match.group(2).strip()
        start = int(match.group(3))

        # Find the list definition
        list_match = re.search(rf'{list_name}\s*=\s*\[([^\]]+)\]', content, re.DOTALL)
        if list_match:
            items_str = list_match.group(1)
            # Parse list items (quoted strings, possibly with commas)
            items = re.findall(r'"([^"]*)"', items_str)
            for i, name in enumerate(items):
                shape_id = start + i
                known_ids[shape_id] = f"{category}/{name}"

    return known_ids


def main():
    parser = argparse.ArgumentParser(description="Extract BO2 shape ID mapping from shape_id_map.py")
    parser.add_argument("input", nargs="?", default="emblemtool/shapes/shape_id_map.py",
                        help="Path to shape_id_map.py (default: emblemtool/shapes/shape_id_map.py)")
    parser.add_argument("output", nargs="?", default="shape_ids.json",
                        help="Output JSON file (default: shape_ids.json)")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        print(f"Error: {in_path} not found", file=sys.stderr)
        print("Clone alexkotr1/bo2-emblem-toolkit first, or provide path to shape_id_map.py", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {in_path}...")
    known_ids = extract_known_ids(in_path)

    print(f"Extracted {len(known_ids)} shape IDs")

    # Group by category for summary
    categories = {}
    for sid, name in sorted(known_ids.items()):
        cat = name.split("/")[0]
        categories[cat] = categories.get(cat, 0) + 1

    print("\nBy category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    # Write JSON
    out_path.write_text(json.dumps(known_ids, indent=2, ensure_ascii=False))
    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()