"""
BO2 Emblem Image Importer
=========================
Converts images (PNG, JPEG, WebP, BMP, SVG) to BO2 emblem layers.
Uses edge detection, color quantization, and shape matching.
"""

import os
import math
from typing import List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageDraw

from .parser import EmblemLayer
from .shape_map import get_ids_by_category, get_shape_id
from .renderer import EmblemRenderer


@dataclass
class ImportConfig:
    """Configuration for image import."""
    max_layers: int = 32
    target_size: int = 256
    edge_threshold: float = 0.3
    color_quantization: int = 16
    min_shape_area: float = 0.001
    shape_match_threshold: float = 0.7
    background_removal: bool = True
    invert_colors: bool = False


class ImageImporter:
    """Imports images and converts to BO2 emblem layers."""
    
    def __init__(self, config: Optional[ImportConfig] = None):
        self.config = config or ImportConfig()
        self.renderer = EmblemRenderer()
        self._shape_cache = {}
    
    def import_image(self, path: str) -> List[EmblemLayer]:
        """Import image file and convert to emblem layers."""
        # Load and preprocess image
        img = self._load_image(path)
        img = self._preprocess_image(img)
        
        # Analyze image
        regions = self._segment_image(img)
        
        # Match regions to shapes
        layers = self._match_shapes(regions)
        
        # Optimize to max layers
        if len(layers) > self.config.max_layers:
            layers = self._reduce_layers(layers)
        
        return layers
    
    def _load_image(self, path: str) -> Image.Image:
        """Load image from file."""
        ext = Path(path).suffix.lower()
        
        if ext == '.svg':
            # Convert SVG to PNG first
            try:
                import cairosvg
                import io
                png_data = cairosvg.svg2png(url=path)
                return Image.open(io.BytesIO(png_data)).convert("RGBA")
            except ImportError:
                raise ValueError("SVG support requires cairosvg package")
        
        img = Image.open(path).convert("RGBA")
        return img
    
    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """Preprocess image for analysis."""
        # Resize to target size
        img = img.resize((self.config.target_size, self.config.target_size), 
                        Image.LANCZOS)
        
        # Remove background if configured
        if self.config.background_removal:
            img = self._remove_background(img)
        
        # Invert if needed
        if self.config.invert_colors:
            img = ImageOps.invert(img.convert("RGB")).convert("RGBA")
        
        return img
    
    def _remove_background(self, img: Image.Image) -> Image.Image:
        """Simple background removal using corner sampling."""
        arr = np.array(img)
        h, w = arr.shape[:2]
        
        # Sample corners to detect background color
        corners = [
            arr[0, 0], arr[0, w-1],
            arr[h-1, 0], arr[h-1, w-1]
        ]
        
        # Find most common corner color
        bg_color = max(set(tuple(c[:3]) for c in corners), 
                       key=lambda c: sum(1 for x in corners if tuple(x[:3]) == c))
        
        # Make similar colors transparent
        tolerance = 30
        mask = np.all(np.abs(arr[:, :, :3] - bg_color) < tolerance, axis=2)
        arr[mask, 3] = 0
        
        return Image.fromarray(arr)
    
    def _segment_image(self, img: Image.Image) -> List[dict]:
        """Segment image into colored regions."""
        arr = np.array(img)
        h, w = arr.shape[:2]
        
        # Convert to HSV for better color segmentation
        hsv = Image.fromarray(arr[:, :, :3]).convert("HSV")
        hsv_arr = np.array(hsv)
        
        # Quantize colors
        n_colors = self.config.color_quantization
        img_quantized = img.convert("P", palette=Image.ADAPTIVE, colors=n_colors)
        quantized_arr = np.array(img_quantized)
        
        # Find connected components for each color
        regions = []
        unique_colors = np.unique(quantized_arr)
        
        for color_idx in unique_colors:
            mask = (quantized_arr == color_idx)
            if np.sum(mask) < self.config.min_shape_area * h * w:
                continue
            
            # Get bounding box
            rows = np.any(mask, axis=1)
            cols = np.any(mask, axis=0)
            if not np.any(rows) or not np.any(cols):
                continue
            
            y_min, y_max = np.where(rows)[0][[0, -1]]
            x_min, x_max = np.where(cols)[0][[0, -1]]
            
            # Get average color in region
            region_pixels = arr[mask]
            avg_color = np.mean(region_pixels[:, :3], axis=0) / 255.0
            avg_alpha = np.mean(region_pixels[:, 3]) / 255.0
            
            # Center position (normalized to -1..1)
            cx = (x_min + x_max) / 2 / w * 2 - 1
            cy = (y_min + y_max) / 2 / h * 2 - 1
            
            # Scale (relative to image size)
            width = (x_max - x_min) / w
            height = (y_max - y_min) / h
            
            regions.append({
                'mask': mask,
                'color': (avg_color[0], avg_color[1], avg_color[2], avg_alpha),
                'center': (cx, cy),
                'size': (width, height),
                'area': np.sum(mask),
                'bbox': (x_min, y_min, x_max, y_max)
            })
        
        # Sort by area (largest first)
        regions.sort(key=lambda r: r['area'], reverse=True)
        
        return regions
    
    def _match_shapes(self, regions: List[dict]) -> List[EmblemLayer]:
        """Match image regions to BO2 shapes."""
        layers = []
        
        # Get available tool shapes (basic geometric shapes)
        tool_ids = get_ids_by_category("tools")
        
        # Shape templates for matching
        shape_templates = {
            'circle': [192, 193],  # Full Circle, Circle 02
            'square': [196],       # Square Full
            'rectangle': [195],    # Rectangle Medium
            'diamond': [194],      # Diamond
            'triangle': [187],     # Triangle Wide
            'heart': [139],  # Half Heart
            'star': [145, 146],   # Ninja Star, Half Star
            'curved': [137, 138, 139],  # Half Circle, Quarter Circle, Half Heart
            'star': [145, 146, 147],    # Ninja Star, Half Star, Shuriken
        }
        
        for i, region in enumerate(regions[:self.config.max_layers]):
            # Find best matching shape
            shape_id = self._find_best_shape(region, tool_ids)
            
            # Calculate scale (log2 of true scale)
            # True scale = 2**scale, so scale = log2(true_scale)
            true_scale_x = region['size'][0] * 2  # Normalize to 0..1 -> scale factor
            true_scale_y = region['size'][1] * 2
            
            # Clamp to reasonable range
            true_scale_x = max(0.01, min(8.0, true_scale_x))
            true_scale_y = max(0.01, min(8.0, true_scale_y))
            
            scale_x = math.log2(true_scale_x) if true_scale_x > 0 else 0
            scale_y = math.log2(true_scale_y) if true_scale_y > 0 else 0
            
            r, g, b, a = region['color']
            cx, cy = region['center']
            
            layer = EmblemLayer(
                index=i,
                shape_id=shape_id,
                r=r, g=g, b=b, a=a,
                pos_x=cx, pos_y=cy,
                scale_x=scale_x, scale_y=scale_y,
                rotation=0.0,
                outlined=False,
                flipped=False
            )
            layers.append(layer)
        
        return layers
    
    def _find_best_shape(self, region: dict, tool_ids: List[int]) -> int:
        """Find best matching BO2 shape for a region."""
        # Simple heuristic based on region aspect ratio and shape
        aspect = region['size'][0] / max(region['size'][1], 0.001)
        
        # For now, use basic shapes
        if 0.8 <= aspect <= 1.2:
            # Roughly square - use circle or square
            return 192  # Full Circle
        elif aspect > 2:
            # Wide - use rectangle
            return 195  # Rectangle Medium
        elif aspect < 0.5:
            # Tall - use rectangle
            return 195  # Rectangle Medium
        else:
            # Default to circle
            return 192  # Full Circle
    
    def _reduce_layers(self, layers: List[EmblemLayer]) -> List[EmblemLayer]:
        """Reduce layers to max_layers by merging similar ones."""
        # Sort by visual importance (alpha * area)
        layers.sort(key=lambda l: l.a * (2**l.scale_x) * (2**l.scale_y), reverse=True)
        
        # Keep top max_layers
        return layers[:self.config.max_layers]


def import_image_to_emblem(path: str, config: Optional[ImportConfig] = None) -> List[EmblemLayer]:
    """Convenience function to import image to emblem layers."""
    importer = ImageImporter(config)
    return importer.import_image(path)


def import_image_and_render(path: str, output_path: str, 
                           config: Optional[ImportConfig] = None,
                           size: int = 512) -> bytes:
    """Import image and render to PNG in one step."""
    layers = import_image_to_emblem(path, config)
    from .renderer import render_emblem
    return render_emblem(layers, size=size, output_path=output_path)