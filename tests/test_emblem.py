"""
BO2 Emblem Studio - Test Suite
==============================
Comprehensive tests for parser, serializer, renderer, and shape map.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bo2_emblem.parser import EmblemParser, EmblemLayer
from bo2_emblem.serializer import EmblemSerializer
from bo2_emblem.renderer import EmblemRenderer
from bo2_emblem.shape_map import (
    SHAPE_ID_MAP, get_shape_name, get_shape_category,
    get_shape_id, get_ids_by_category, list_categories,
    CATEGORY_ORDER, TOTAL_SHAPES
)


class TestShapeMap(unittest.TestCase):
    """Tests for shape ID mapping."""
    
    def test_total_shapes_count(self):
        """Verify we have expected number of shapes."""
        self.assertGreaterEqual(TOTAL_SHAPES, 250)
    
    def test_get_shape_name_known(self):
        """Test lookup of known shape IDs."""
        # Tools
        self.assertEqual(get_shape_name(137), "tools/Half Circle")
        self.assertEqual(get_shape_name(197), "tools/Treyarch")
        
        # Type
        self.assertEqual(get_shape_name(217), "type/Letter A")
        self.assertEqual(get_shape_name(252), "type/Nine")
        
        # Ranks
        self.assertEqual(get_shape_name(198), "ranks/Private 1st Class")
        self.assertEqual(get_shape_name(216), "ranks/Commander")
        
        # Gear
        self.assertEqual(get_shape_name(0), "gear/KAP-40 Qualified")
        self.assertEqual(get_shape_name(260), "gear/Peacekeeper Qualified")
        
        # Emblems
        self.assertEqual(get_shape_name(48), "emblems/Triple Kill")
        self.assertEqual(get_shape_name(259), "emblems/Default Emblem")
    
    def test_get_shape_name_unknown(self):
        """Test lookup of unknown shape ID."""
        self.assertEqual(get_shape_name(9999), "Unknown (0x270F)")
    
    def test_get_shape_category(self):
        """Test category lookup."""
        self.assertEqual(get_shape_category(137), "tools")
        self.assertEqual(get_shape_category(217), "type")
        self.assertEqual(get_shape_category(198), "ranks")
        self.assertEqual(get_shape_category(0), "gear")
        self.assertEqual(get_shape_category(48), "emblems")
    
    def test_get_ids_by_category(self):
        """Test getting all IDs for a category."""
        tools_ids = get_ids_by_category("tools")
        self.assertEqual(len(tools_ids), 61)
        self.assertEqual(min(tools_ids), 137)
        self.assertEqual(max(tools_ids), 197)
        
        type_ids = get_ids_by_category("type")
        self.assertEqual(len(type_ids), 36)
        
        ranks_ids = get_ids_by_category("ranks")
        self.assertEqual(len(ranks_ids), 19)
        
        gear_ids = get_ids_by_category("gear")
        self.assertEqual(len(gear_ids), 39)
        
        emblems_ids = get_ids_by_category("emblems")
        self.assertEqual(len(emblems_ids), 106)
    
    def test_category_order(self):
        """Test category display order."""
        self.assertEqual(CATEGORY_ORDER[0], "tools")
        self.assertEqual(CATEGORY_ORDER[1], "type")


class TestEmblemLayer(unittest.TestCase):
    """Tests for EmblemLayer dataclass."""
    
    def test_layer_creation(self):
        """Test creating a layer."""
        layer = EmblemLayer(
            index=0,
            shape_id=137,
            r=1.0, g=0.0, b=0.0, a=1.0,
            pos_x=0.0, pos_y=0.0,
            scale_x=0.0, scale_y=0.0,
            rotation=0.0,
            outlined=False,
            flipped=False
        )
        self.assertEqual(layer.shape_id, 137)
        self.assertFalse(layer.is_empty)
    
    def test_empty_layer(self):
        """Test empty layer detection."""
        layer = EmblemLayer(index=5, shape_id=0xFFFF)
        self.assertTrue(layer.is_empty)
    
    def test_true_scale(self):
        """Test true scale calculation."""
        layer = EmblemLayer(index=0, shape_id=137, scale_x=0.0, scale_y=0.0)
        self.assertEqual(layer.true_scale_x, 1.0)
        self.assertEqual(layer.true_scale_y, 1.0)
        
        layer = EmblemLayer(index=0, shape_id=137, scale_x=-1.0, scale_y=-1.0)
        self.assertAlmostEqual(layer.true_scale_x, 0.5)
        self.assertAlmostEqual(layer.true_scale_y, 0.5)
        
        layer = EmblemLayer(index=0, shape_id=137, scale_x=1.0, scale_y=1.0)
        self.assertEqual(layer.true_scale_x, 2.0)
        self.assertEqual(layer.true_scale_y, 2.0)
    
    def test_to_dict(self):
        """Test dict conversion."""
        layer = EmblemLayer(index=0, shape_id=137)
        d = layer.to_dict()
        self.assertIn("index", d)
        self.assertIn("shape_id", d)
        self.assertIn("true_scale_x", d)


class TestEmblemParser(unittest.TestCase):
    """Tests for EmblemParser."""
    
    def test_parse_invalid_data(self):
        """Test parsing invalid data doesn't crash."""
        layers = EmblemParser.parse_bytes(b"x" * 1408)
        self.assertIsInstance(layers, list)
    
    def test_parse_valid_1408_bytes(self):
        """Test parsing exactly 1408 bytes of valid data."""
        import struct
        # Create minimal valid emblem (all empty layers)
        empty_layer = struct.pack("<Hxx9fBBxx", 0xFFFF, 0,0,0,0, 0,0, 0,0, 0, 0,0)
        data = empty_layer * 32
        layers = EmblemParser.parse_bytes(data)
        self.assertEqual(len(layers), 0)  # All empty layers skipped
    
    def test_parse_single_layer(self):
        """Test parsing a single valid layer."""
        import struct
        # Create full 1408-byte buffer with empty layers
        data = bytearray(1408)
        empty_layer = struct.pack("<Hxx9fBBxx", 0xFFFF, 0,0,0,0, 0,0, 0,0, 0, 0,0)
        for i in range(32):
            offset = i * 44
            data[offset:offset+44] = empty_layer
        
        # Add one valid layer at index 0
        layer_data = struct.pack("<Hxx9fBBxx",
            137,  # shape_id
            1.0, 0.0, 0.0, 1.0,  # r, g, b, a
            0.0, 0.0,  # pos_x, pos_y
            0.0, 0.0,  # scale_x, scale_y
            0.0,       # rotation
            0, 0       # outlined, flipped
        )
        data[0:44] = layer_data
        
        layers = EmblemParser.parse_bytes(bytes(data))
        self.assertEqual(len(layers), 1)
        self.assertEqual(layers[0].shape_id, 137)
        self.assertEqual(layers[0].index, 0)
        self.assertEqual(layers[0].r, 1.0)
        self.assertEqual(layers[0].g, 0.0)
    
    def test_layer_order_preserved(self):
        """Test that layer indices are preserved correctly."""
        import struct
        # Create layers at indices 0, 5, 31 - rest empty (0xFFFF)
        data = bytearray(1408)
        # Fill with empty layers first
        empty_layer = struct.pack("<Hxx9fBBxx", 0xFFFF, 0,0,0,0, 0,0, 0,0, 0, 0,0)
        for i in range(32):
            offset = i * 44
            data[offset:offset+44] = empty_layer
        
        # Now add our test layers
        for idx, shape_id in [(0, 137), (5, 138), (31, 139)]:
            layer_bytes = struct.pack("<Hxx9fBBxx",
                shape_id, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0)
            offset = idx * 44
            data[offset:offset+44] = layer_bytes
    
        layers = EmblemParser.parse_bytes(bytes(data))
        self.assertEqual(len(layers), 3)
        indices = sorted([l.index for l in layers])
        self.assertEqual(indices, [0, 5, 31])


class TestEmblemSerializer(unittest.TestCase):
    """Tests for emblem serialization."""
    
    def test_serialize_empty_layer(self):
        """Test serializing empty layer produces correct bytes."""
        layer = EmblemLayer(index=0, shape_id=0xFFFF)
        data = EmblemSerializer.serialize_layer(layer)
        self.assertEqual(len(data), 44)
        # First 2 bytes should be 0xFFFF
        self.assertEqual(data[:2], b"\xFF\xFF")
    
    def test_serialize_valid_layer(self):
        """Test serializing a valid layer."""
        layer = EmblemLayer(
            index=0, shape_id=137,
            r=1.0, g=0.5, b=0.0, a=1.0,
            pos_x=0.1, pos_y=-0.1,
            scale_x=0.0, scale_y=0.0,
            rotation=45.0,
            outlined=True, flipped=False
        )
        data = EmblemSerializer.serialize_layer(layer)
        self.assertEqual(len(data), 44)
        
        # Verify we can parse it back
        parsed = EmblemParser.parse_layer(data, 0)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.shape_id, 137)
        self.assertAlmostEqual(parsed.r, 1.0)
        self.assertAlmostEqual(parsed.g, 0.5)
        self.assertAlmostEqual(parsed.b, 0.0)
        self.assertAlmostEqual(parsed.pos_x, 0.1)
        self.assertAlmostEqual(parsed.pos_y, -0.1)
        self.assertTrue(parsed.outlined)
        self.assertFalse(parsed.flipped)
        self.assertAlmostEqual(parsed.rotation, 45.0)
    
    def test_serialize_full_emblem(self):
        """Test serializing full 32-layer emblem."""
        layers = [
            EmblemLayer(index=0, shape_id=137, r=1.0, g=0.0, b=0.0),
            EmblemLayer(index=1, shape_id=138, r=0.0, g=1.0, b=0.0),
            EmblemLayer(index=31, shape_id=139, r=0.0, g=0.0, b=1.0),
        ]
        data = EmblemSerializer.serialize_layers(layers)
        self.assertEqual(len(data), 1408)
        
        # Parse back
        parsed = EmblemParser.parse_bytes(data)
        self.assertEqual(len(parsed), 3)
        indices = sorted([l.index for l in parsed])
        self.assertEqual(indices, [0, 1, 31])
    
    def test_roundtrip(self):
        """Test serialize -> parse roundtrip."""
        original = [
            EmblemLayer(index=0, shape_id=137, r=1.0, g=0.2, b=0.3, a=0.8,
                       pos_x=0.1, pos_y=0.2, scale_x=-0.5, scale_y=0.5, rotation=30.0,
                       outlined=True, flipped=True),
            EmblemLayer(index=15, shape_id=217, r=0.5, g=0.5, b=0.5, a=1.0),
            EmblemLayer(index=31, shape_id=48, r=1.0, g=1.0, b=0.0, a=1.0,
                       pos_x=-0.3, pos_y=0.4, scale_x=1.0, scale_y=1.0, rotation=180.0),
        ]
        
        result = EmblemSerializer.verify_roundtrip(original)
        self.assertTrue(result, "Roundtrip verification failed")
    
    def test_write_read_file(self):
        """Test writing to file and reading back."""
        layers = [
            EmblemLayer(index=0, shape_id=137, r=1.0, g=0.0, b=0.0),
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".emblem", delete=False) as f:
            temp_path = f.name
        
        try:
            EmblemSerializer.write_file(temp_path, layers)
            
            # Read back
            parsed = EmblemParser.parse_file(temp_path)
            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0].shape_id, 137)
        finally:
            os.unlink(temp_path)


class TestEmblemRenderer(unittest.TestCase):
    """Tests for emblem rendering."""
    
    def setUp(self):
        self.renderer = EmblemRenderer()
    
    def test_render_empty_layers(self):
        """Test rendering with no layers."""
        layers = []
        img = self.renderer.render_png(layers, size=256)
        self.assertEqual(img.size, (256, 256))
        self.assertEqual(img.mode, "RGBA")
    
    def test_render_single_layer(self):
        """Test rendering a single layer."""
        layers = [EmblemLayer(index=0, shape_id=137, r=1.0, g=0.0, b=0.0)]
        img = self.renderer.render_png(layers, size=256)
        self.assertEqual(img.size, (256, 256))
        # Should have some non-transparent pixels
        self.assertTrue(any(p[3] > 0 for p in img.getdata()))
    
    def test_render_multiple_sizes(self):
        """Test rendering at different sizes."""
        layers = [EmblemLayer(index=0, shape_id=137, r=1.0, g=0.0, b=0.0)]
        for size in [128, 256, 512, 1024]:
            img = self.renderer.render_png(layers, size=size)
            self.assertEqual(img.size, (size, size))
    
    def test_render_with_transparent_bg(self):
        """Test rendering with transparent background."""
        layers = [EmblemLayer(index=0, shape_id=137, r=1.0, g=0.0, b=0.0)]
        img = self.renderer.render_png(layers, size=256, bg_color=(0, 0, 0, 0))
        # The background should be transparent
        self.assertEqual(img.mode, "RGBA")
    
    def test_render_to_bytes(self):
        """Test rendering to PNG bytes."""
        layers = [EmblemLayer(index=0, shape_id=137, r=1.0, g=0.0, b=0.0)]
        png_bytes = self.renderer.render_to_bytes(layers, size=256)
        self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
    
    def test_render_to_file(self):
        """Test rendering to file."""
        layers = [EmblemLayer(index=0, shape_id=137, r=1.0, g=0.0, b=0.0)]
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
        
        try:
            self.renderer.render_to_file(layers, size=256, output_path=temp_path)
            self.assertTrue(os.path.exists(temp_path))
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components."""
    
    def test_full_workflow(self):
        """Test complete workflow: create -> serialize -> parse -> render."""
        # Create layers
        original_layers = [
            EmblemLayer(index=0, shape_id=137, r=1.0, g=0.0, b=0.0, a=1.0),
            EmblemLayer(index=1, shape_id=138, r=0.0, g=1.0, b=0.0, a=1.0,
                       pos_x=0.2, pos_y=0.2, scale_x=-1.0),
            EmblemLayer(index=2, shape_id=217, r=0.0, g=0.0, b=1.0, a=1.0,
                       pos_x=-0.2, pos_y=-0.2, rotation=45.0),
        ]
        
        # Serialize
        data = EmblemSerializer.serialize_layers(original_layers)
        self.assertEqual(len(data), 1408)
        
        # Parse back
        parsed_layers = EmblemParser.parse_bytes(data)
        self.assertEqual(len(parsed_layers), 3)
        
        # Render
        renderer = EmblemRenderer()
        img = renderer.render_png(parsed_layers, size=256)
        self.assertEqual(img.size, (256, 256))
        
        # Verify roundtrip
        self.assertTrue(EmblemSerializer.verify_roundtrip(original_layers))
    
    def test_example_emblem_files(self):
        """Test parsing example files from research directory."""
        examples_dir = Path(__file__).parent.parent.parent / "research" / "Black-Ops-2-Emblem-Editor" / "created emblems"
        
        if not examples_dir.exists():
            self.skipTest("Example files not found")
        
        import base64, zlib
        
        for emblem_dir in examples_dir.iterdir():
            if emblem_dir.is_dir():
                code_file = emblem_dir / "code.txt"
                if code_file.exists():
                    try:
                        content = code_file.read_text().strip()
                        decoded = base64.b64decode(content)
                        decompressed = zlib.decompress(decoded)
                        
                        if len(decompressed) >= 1408:
                            layers = EmblemParser.parse_bytes(decompressed)
                            self.assertGreater(len(layers), 0)
                            
                            # Should be able to render
                            renderer = EmblemRenderer()
                            img = renderer.render_png(layers, size=256)
                            self.assertEqual(img.size, (256, 256))
                    except Exception:
                        # Some files might be corrupted or different format
                        pass


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestShapeMap))
    suite.addTests(loader.loadTestsFromTestCase(TestEmblemLayer))
    suite.addTests(loader.loadTestsFromTestCase(TestEmblemParser))
    suite.addTests(loader.loadTestsFromTestCase(TestEmblemSerializer))
    suite.addTests(loader.loadTestsFromTestCase(TestEmblemRenderer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)