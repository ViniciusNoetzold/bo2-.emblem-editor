"""
Real Emblem Integration Tests
=============================
Tests using actual BO2/Plutonium T6 .emblem files.
No mocks - only real files from the game.
"""

import os
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from bo2_emblem.parser import load_emblem, EmblemParser
from bo2_emblem.serializer import EmblemSerializer
from bo2_emblem.renderer import render_emblem
from bo2_emblem.exporter import EmblemExporter
from bo2_emblem.ai import EmblemAIGenerator
from bo2_emblem.shape_map import SHAPE_ID_MAP, get_shape_name


# Test files directory
TEST_EMBLEMS_DIR = r"E:\BO2 Emblem Studio\Exemplos de .emblem"
TEST_FILES = [f"{i}#emblem.emblem" for i in range(1, 8)]


class TestRealEmblems(unittest.TestCase):
    """Tests using actual BO2/Plutonium emblem files."""
    
    @classmethod
    def setUpClass(cls):
        """Verify all test files exist."""
        for fname in TEST_FILES:
            path = os.path.join(TEST_EMBLEMS_DIR, fname)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Test file not found: {path}")
    
    def test_all_files_open_without_error(self):
        """All 7 files must open without any exception."""
        for fname in TEST_FILES:
            path = os.path.join(TEST_EMBLEMS_DIR, fname)
            with self.subTest(file=fname):
                layers, header = load_emblem(path)
                self.assertIsInstance(layers, list)
                self.assertGreater(len(layers), 0)
                self.assertLessEqual(len(layers), 32)
    
    def test_all_files_render_correctly(self):
        """All 7 files must render to non-empty, non-transparent images."""
        for fname in TEST_FILES:
            path = os.path.join(TEST_EMBLEMS_DIR, fname)
            with self.subTest(file=fname):
                layers, _ = load_emblem(path)
                
                # Render to PNG
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                    temp_path = f.name
                
                try:
                    render_emblem(layers, size=512, output_path=temp_path, bg_color=(0, 0, 0, 0))
                    
                    # Verify file exists and has content
                    self.assertTrue(os.path.exists(temp_path))
                    self.assertGreater(os.path.getsize(temp_path), 0)
                    
                    # Verify image content
                    img = Image.open(temp_path)
                    self.assertEqual(img.size, (512, 512))
                    self.assertEqual(img.mode, "RGBA")
                    
                    # Check not all transparent
                    pixels = list(img.getdata())
                    non_transparent = sum(1 for p in pixels if p[3] > 0)
                    self.assertGreater(non_transparent, 0, f"{fname}: preview is completely transparent")
                    
                    # Check not single color
                    unique_colors = set(p[:3] for p in pixels if p[3] > 0)
                    self.assertGreater(len(unique_colors), 1, f"{fname}: preview appears to be single color")
                    
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
    
    def test_all_files_save_roundtrip(self):
        """Save and reload must produce identical layer data."""
        for fname in TEST_FILES:
            path = os.path.join(TEST_EMBLEMS_DIR, fname)
            with self.subTest(file=fname):
                # Load original
                layers1, _ = load_emblem(path)
                
                # Serialize
                body = EmblemSerializer.serialize_layers(layers1)
                
                # Load serialized
                layers2 = EmblemParser.parse_bytes(body)
                
                # Compare layer count
                self.assertEqual(len(layers1), len(layers2), 
                    f"{fname}: layer count mismatch {len(layers1)} vs {len(layers2)}")
                
                # Compare each layer
                for l1, l2 in zip(layers1, layers2):
                    self.assertEqual(l1.shape_id, l2.shape_id, f"{fname}: shape_id mismatch")
                    self.assertAlmostEqual(l1.r, l2.r, places=6)
                    self.assertAlmostEqual(l1.g, l2.g, places=6)
                    self.assertAlmostEqual(l1.b, l2.b, places=6)
                    self.assertAlmostEqual(l1.a, l2.a, places=6)
                    self.assertAlmostEqual(l1.pos_x, l2.pos_x, places=6)
                    self.assertAlmostEqual(l1.pos_y, l2.pos_y, places=6)
                    self.assertAlmostEqual(l1.scale_x, l2.scale_x, places=6)
                    self.assertAlmostEqual(l1.scale_y, l2.scale_y, places=6)
                    self.assertAlmostEqual(l1.rotation, l2.rotation, places=6)
                    self.assertEqual(l1.outlined, l2.outlined)
                    self.assertEqual(l1.flipped, l2.flipped)
    
    def test_all_files_binary_roundtrip(self):
        """Serialized body must match original file body byte-for-byte."""
        for fname in TEST_FILES:
            path = os.path.join(TEST_EMBLEMS_DIR, fname)
            with self.subTest(file=fname):
                layers, _ = load_emblem(path)
                body = EmblemSerializer.serialize_layers(layers)
                
                with open(path, 'rb') as f:
                    orig = f.read()
                orig_body = orig[-1408:] if len(orig) >= 1408 else orig
                
                self.assertEqual(body, orig_body,
                    f"{fname}: body mismatch after stripping header")
    
    def test_all_shape_ids_exist_in_shape_map(self):
        """Every shape_id found in real emblems must exist in SHAPE_ID_MAP."""
        all_shape_ids = set()
        for fname in TEST_FILES:
            path = os.path.join(TEST_EMBLEMS_DIR, fname)
            layers, _ = load_emblem(path)
            for layer in layers:
                all_shape_ids.add(layer.shape_id)
        
        missing = []
        for sid in all_shape_ids:
            if sid not in SHAPE_ID_MAP:
                missing.append(sid)
        
        self.assertEqual(len(missing), 0, 
            f"Shape IDs not in SHAPE_ID_MAP: {missing}")
    
    def test_plutonium_header_detection(self):
        """Parser should detect Plutonium header and extract info."""
        # Expected header names for each file (from actual file contents)
        expected_names = {
            "1#emblem.emblem": "Emblem_8",
            "2#emblem.emblem": "Emblem_7",
            "3#emblem.emblem": "Emblem_4",
            "4#emblem.emblem": "Emblem_6",
            "5#emblem.emblem": "Emblem_5",
            "6#emblem.emblem": "Emblem_6",
        }
        
        for fname in TEST_FILES:
            if fname == "7#emblem.emblem":
                continue  # Pure 1408 bytes, no header
            path = os.path.join(TEST_EMBLEMS_DIR, fname)
            with self.subTest(file=fname):
                layers, header = load_emblem(path)
                self.assertIsNotNone(header, f"{fname}: expected Plutonium header")
                self.assertEqual(header.name, expected_names[fname])
                self.assertEqual(len(layers), 32, f"{fname}: expected 32 layers")
    
    def test_exporter_creates_valid_files(self):
        """Exporter should create valid .emblem files."""
        for fname in TEST_FILES:
            path = os.path.join(TEST_EMBLEMS_DIR, fname)
            with self.subTest(file=fname):
                layers, _ = load_emblem(path)
                
                with tempfile.NamedTemporaryFile(suffix='.emblem', delete=False) as f:
                    temp_path = f.name
                
                try:
                    exporter = EmblemExporter()
                    # Export to temp location (not actual Plutonium dir)
                    exporter.export_layers(layers, 1, Path(temp_path))
                    
                    # Verify exported file
                    self.assertTrue(os.path.exists(temp_path))
                    self.assertEqual(os.path.getsize(temp_path), 1408)
                    
                    # Verify it can be loaded
                    layers2, _ = load_emblem(temp_path)
                    self.assertEqual(len(layers2), len(layers))
                    
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
    
    def test_negative_rotations_preserved(self):
        """Negative rotation values should be preserved (not normalized to 0-360)."""
        # File 7 has layers with negative rotations (-25, -30)
        path = os.path.join(TEST_EMBLEMS_DIR, "7#emblem.emblem")
        layers, _ = load_emblem(path)
        
        # Check that negative rotations are preserved
        negative_rotations = [l for l in layers if l.rotation < 0]
        self.assertGreater(len(negative_rotations), 0, "Expected negative rotations in 7#emblem")
        
        # Roundtrip should preserve them
        body = EmblemSerializer.serialize_layers(layers)
        layers2 = EmblemParser.parse_bytes(body)
        
        for l1, l2 in zip(layers, layers2):
            self.assertAlmostEqual(l1.rotation, l2.rotation, places=5,
                msg=f"Rotation not preserved: {l1.rotation} -> {l2.rotation}")
    
    def test_shape_map_coverage(self):
        """Verify SHAPE_ID_MAP covers all shapes in real emblems."""
        all_shape_ids = set()
        for fname in TEST_FILES:
            path = os.path.join(TEST_EMBLEMS_DIR, fname)
            layers, _ = load_emblem(path)
            for layer in layers:
                all_shape_ids.add(layer.shape_id)
        
        for sid in all_shape_ids:
            name = get_shape_name(sid)
            self.assertNotIn("Unknown", name, f"Shape ID {sid} has no name in shape_map")


if __name__ == "__main__":
    unittest.main(verbosity=2)