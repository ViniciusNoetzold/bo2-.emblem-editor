#!/usr/bin/env python3
"""
BO2 Emblem Format Verification Script
======================================
Quick validation of parser/serializer roundtrip and basic functionality.
Run from project root: python scripts/verify_emblem_format.py
"""

import sys
import struct
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bo2_emblem.parser import EmblemParser, EmblemLayer
from bo2_emblem.serializer import EmblemSerializer


def create_test_emblem():
    """Create a test emblem with known values."""
    return [
        EmblemLayer(
            index=0, shape_id=137,  # Half Circle
            r=1.0, g=0.0, b=0.0, a=1.0,
            pos_x=0.0, pos_y=0.0,
            scale_x=0.0, scale_y=0.0,
            rotation=0.0,
            outlined=False, flipped=False
        ),
        EmblemLayer(
            index=1, shape_id=217,  # Letter A
            r=0.0, g=1.0, b=0.0, a=1.0,
            pos_x=0.2, pos_y=-0.2,
            scale_x=-1.0, scale_y=-1.0,
            rotation=45.0,
            outlined=True, flipped=False
        ),
        EmblemLayer(
            index=31, shape_id=48,  # Triple Kill
            r=1.0, g=1.0, b=0.0, a=1.0,
            pos_x=-0.3, pos_y=0.3,
            scale_x=1.0, scale_y=1.0,
            rotation=180.0,
            outlined=False, flipped=True
        ),
    ]


def test_roundtrip():
    """Test serialize -> parse roundtrip."""
    print("Testing roundtrip...")
    
    original = create_test_emblem()
    
    # Serialize
    data = EmblemSerializer.serialize_layers(original)
    print(f"  Serialized: {len(data)} bytes (expected 1408)")
    assert len(data) == 1408
    
    # Parse back
    parsed = EmblemParser.parse_bytes(data)
    print(f"  Parsed layers: {len(parsed)} (expected 3)")
    assert len(parsed) == 3
    
    # Compare
    orig_dict = {l.index: l for l in original}
    for p in parsed:
        o = orig_dict[p.index]
        assert p.shape_id == o.shape_id, f"shape_id mismatch: {p.shape_id} != {o.shape_id}"
        assert abs(p.r - o.r) < 1e-5, f"r mismatch: {p.r} != {o.r}"
        assert abs(p.g - o.g) < 1e-5, f"g mismatch: {p.g} != {o.g}"
        assert abs(p.b - o.b) < 1e-5, f"b mismatch: {p.b} != {o.b}"
        assert abs(p.a - o.a) < 1e-5, f"a mismatch: {p.a} != {o.a}"
        assert abs(p.pos_x - o.pos_x) < 1e-5, f"pos_x mismatch: {p.pos_x} != {o.pos_x}"
        assert abs(p.pos_y - o.pos_y) < 1e-5, f"pos_y mismatch: {p.pos_y} != {o.pos_y}"
        assert abs(p.scale_x - o.scale_x) < 1e-5, f"scale_x mismatch: {p.scale_x} != {o.scale_x}"
        assert abs(p.scale_y - o.scale_y) < 1e-5, f"scale_y mismatch: {p.scale_y} != {o.scale_y}"
        assert abs(p.rotation - o.rotation) < 1e-5, f"rotation mismatch: {p.rotation} != {o.rotation}"
        assert p.outlined == o.outlined, f"outlined mismatch: {p.outlined} != {o.outlined}"
        assert p.flipped == o.flipped, f"flipped mismatch: {p.flipped} != {o.flipped}"
    
    print("  ✓ Roundtrip verified")
    return True


def test_empty_layers():
    """Test that empty layers are handled correctly."""
    print("Testing empty layers...")
    
    # Create data with all empty layers (0xFFFF)
    empty_layer = struct.pack("<Hxx9fBBxx", 0xFFFF, 0,0,0,0, 0,0, 0,0, 0, 0,0)
    data = empty_layer * 32
    
    parsed = EmblemParser.parse_bytes(data)
    assert len(parsed) == 0, f"Expected 0 layers, got {len(parsed)}"
    print("  ✓ Empty layers skipped correctly")
    return True


def test_verify_method():
    """Test EmblemSerializer.verify_roundtrip method."""
    print("Testing verify_roundtrip...")
    
    original = create_test_emblem()
    result = EmblemSerializer.verify_roundtrip(original)
    assert result, "verify_roundtrip should return True"
    print("  ✓ verify_roundtrip works")
    return True


def test_file_io(tmp_path):
    """Test file write/read."""
    print("Testing file I/O...")
    
    original = create_test_emblem()
    test_file = tmp_path / "test.emblem"
    
    # Write
    EmblemSerializer.write_file(str(test_file), original)
    assert test_file.exists()
    assert test_file.stat().st_size == 1408
    
    # Read back
    parsed = EmblemParser.parse_file(str(test_file))
    assert len(parsed) == 3
    
    print("  ✓ File I/O works")
    return True


def test_http_headers_stripping():
    """Test that HTTP headers are stripped."""
    print("Testing HTTP header stripping...")
    
    # Create valid emblem data
    original = create_test_emblem()
    body = EmblemSerializer.serialize_layers(original)
    
    # Add HTTP headers
    http_response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/octet-stream\r\n"
        b"Content-Length: 1408\r\n"
        b"\r\n"
    ) + body
    
    # Should parse correctly
    parsed = EmblemParser.parse_bytes(http_response)
    assert len(parsed) == 3
    print("  ✓ HTTP headers stripped correctly")
    return True


def test_layer_ordering():
    """Test that layer indices are preserved and ordering works."""
    print("Testing layer ordering...")
    
    # Create layers at specific indices
    layers = [
        EmblemLayer(index=5, shape_id=137, r=1.0, g=0, b=0),
        EmblemLayer(index=0, shape_id=138, r=0, g=1.0, b=0),
        EmblemLayer(index=31, shape_id=139, r=0, g=0, b=1.0),
    ]
    
    data = EmblemSerializer.serialize_layers(layers)
    parsed = EmblemParser.parse_bytes(data)
    
    indices = [l.index for l in parsed]
    assert indices == [0, 5, 31], f"Expected [0, 5, 31], got {indices}"
    
    # Verify order preserved (lower index = behind)
    print("  ✓ Layer ordering preserved")
    return True


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("BO2 Emblem Format Verification")
    print("=" * 60)
    
    tests = [
        test_roundtrip,
        test_empty_layers,
        test_verify_method,
        test_layer_ordering,
        test_http_headers_stripping,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
    
    # File I/O needs temp dir
    import tempfile
    try:
        with tempfile.TemporaryDirectory() as tmp:
            test_file_io(Path(tmp))
        passed += 1
    except Exception as e:
        print(f"  ✗ File I/O FAILED: {e}")
        failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All verification tests passed!")
        return 0
    else:
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())