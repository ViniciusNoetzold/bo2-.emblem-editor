#!/usr/bin/env python3
"""
Decode 505e06b2 Black-Ops-2-Emblem-Editor base64+zlib examples to raw .emblem files.

Usage:
    python scripts/bo2-emblem-decode.py <input.txt> [output.emblem]
    python scripts/bo2-emblem-decode.py --batch created_emblems/ output_dir/
"""

import sys
import base64
import zlib
from pathlib import Path
import argparse


def decode_emblem_file(input_path: Path, output_path: Path) -> bool:
    """Decode a single code.txt (base64+zlib) to raw .emblem (1408 bytes)."""
    try:
        text = input_path.read_text().strip()
        if not text:
            print(f"  ⚠ Empty file: {input_path}")
            return False

        # Decode base64 → zlib decompress
        compressed = base64.b64decode(text)
        raw = zlib.decompress(compressed)

        # Validate size
        if len(raw) != 1408:
            print(f"  ⚠ Unexpected size {len(raw)} bytes (expected 1408): {input_path}")
            # Still write it for inspection
        else:
            print(f"  ✓ Decoded {len(raw)} bytes")

        output_path.write_bytes(raw)
        return True

    except base64.binascii.Error as e:
        print(f"  ✗ Base64 decode error: {input_path} — {e}")
    except zlib.error as e:
        print(f"  ✗ Zlib decompress error: {input_path} — {e}")
    except Exception as e:
        print(f"  ✗ Error: {input_path} — {e}")
    return False


def batch_decode(input_dir: Path, output_dir: Path) -> int:
    """Decode all code.txt files in subdirectories of input_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for code_txt in input_dir.rglob("code.txt"):
        # Use parent directory name as base filename
        emblem_name = code_txt.parent.name
        # Sanitize
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in emblem_name)
        out_file = output_dir / f"{safe_name}.emblem"

        print(f"Decoding: {code_txt.relative_to(input_dir)}")
        if decode_emblem_file(code_txt, out_file):
            count += 1

    return count


def main():
    parser = argparse.ArgumentParser(description="Decode BO2 emblem base64+zlib files")
    parser.add_argument("input", help="Input file (code.txt) or directory (for batch)")
    parser.add_argument("output", nargs="?", help="Output .emblom file or directory")
    parser.add_argument("--batch", action="store_true", help="Batch mode: input=dir, output=dir")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output) if args.output else None

    if args.batch or in_path.is_dir():
        if not out_path:
            out_path = in_path.parent / "decoded_emblems"
        decoded = batch_decode(in_path, out_path)
        print(f"\nDecoded {decoded} emblems to {out_path}")
    else:
        if not out_path:
            out_path = in_path.with_suffix(".emblem")
        if decode_emblem_file(in_path, out_path):
            print(f"Written: {out_path}")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()