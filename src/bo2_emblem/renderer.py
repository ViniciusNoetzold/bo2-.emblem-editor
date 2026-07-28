"""
BO2 Emblem Renderer
===================
Pixel-perfect renderer for BO2 emblems using reference shape glyphs.
Based on bo2-emblem-toolkit's render.py implementation.
"""

import io
import os
from typing import List, Optional, Tuple
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageFilter

from .parser import EmblemLayer
from .shape_map import SHAPE_ID_MAP, get_shape_category


@dataclass
class RenderConfig:
    """Configuration for rendering."""
    size: int = 512
    bg_color: Tuple[int, int, int, int] = (24, 24, 24, 255)
    shapes_dir: Optional[str] = None


class EmblemRenderer:
    """Renders BO2 emblem layers to PNG images."""
    
    # Geometry constants (calibrated against live BO2 PC editor)
    EMPTY_SHAPE = 0xFFFF
    
    def __init__(self, config: Optional[RenderConfig] = None):
        self.config = config or RenderConfig()
        self._shape_cache = {}
        self._shapes_dir = self.config.shapes_dir
        
        # Auto-detect shapes directory
        if self._shapes_dir is None:
            # Check research/bo2-emblem-toolkit/reference_shapes
            research_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", 
                "research", "bo2-emblem-toolkit", "reference_shapes"
            )
            if os.path.exists(research_dir):
                self._shapes_dir = research_dir
    
    def _load_shape_image(self, shape_id: int) -> Optional[Image.Image]:
        """Load reference shape image as LA (luminance + alpha)."""
        if shape_id in self._shape_cache:
            return self._shape_cache[shape_id]
        
        if shape_id not in SHAPE_ID_MAP:
            self._shape_cache[shape_id] = None
            return None
        
        category, name = SHAPE_ID_MAP[shape_id]
        filename = f"{name}.png"
        
        if self._shapes_dir:
            path = os.path.join(self._shapes_dir, filename)
        else:
            path = None
        
        if path and os.path.exists(path):
            try:
                img = Image.open(path).convert("LA")
                self._shape_cache[shape_id] = img
                return img
            except Exception:
                pass
        
        self._shape_cache[shape_id] = None
        return None
    
    def _tinted_shape(self, shape_id: int, r: float, g: float, b: float, a: float) -> Optional[Image.Image]:
        """Apply color tint to white/alpha glyph."""
        img = self._load_shape_image(shape_id)
        if img is None:
            return None
        
        lum, alpha = img.split()
        
        # Clamp alpha
        a = max(0.0, min(1.0, a))
        
        rgba = Image.merge("RGBA", (
            lum.point(lambda p: int(r * 255)),
            lum.point(lambda p: int(g * 255)),
            lum.point(lambda p: int(b * 255)),
            alpha.point(lambda p: int(p * a)),
        ))
        return rgba
    
    def _outline_rgba(self, rgba: Image.Image, stroke_px: float) -> Image.Image:
        """Convert filled shape to outline stroke."""
        r, g, b, a = rgba.split()
        radius = max(1, int(round(stroke_px / 2)))
        k = 2 * radius + 1
        dilated = a.filter(ImageFilter.MaxFilter(k))
        eroded = a.filter(ImageFilter.MinFilter(k))
        edge = ImageChops.subtract(dilated, eroded)
        return Image.merge("RGBA", (r, g, b, edge))
    
    def render_png(self, layers: List[EmblemLayer], 
                   size: Optional[int] = None,
                   bg_color: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """
        Render emblem layers to PIL Image.
        
        Args:
            layers: List of EmblemLayer objects
            size: Output size in pixels (default: config.size)
            bg_color: Background color as RGBA tuple (default: config.bg_color)
            
        Returns:
            PIL Image in RGBA mode
        """
        size = size or self.config.size
        bg_color = bg_color or self.config.bg_color
        
        canvas = Image.new("RGBA", (size, size), bg_color)
        cx = cy = size / 2
        
        # Geometry: unit = size, base_px = size
        # pos 0.5 = edge, offset_px = pos * size
        # true_scale = 2**scale, so scale 0 = 1.0 = full box
        unit = size
        base_px = size
        
        # Sort by index (lower = behind, higher = front)
        sorted_layers = sorted(layers, key=lambda l: l.index)
        
        for layer in sorted_layers:
            shape_id = layer.shape_id
            
            # Calculate true scale (always positive)
            w = max(1, int((2 ** layer.scale_x) * base_px))
            h = max(1, int((2 ** layer.scale_y) * base_px))
            
            # Get tinted shape
            tinted = self._tinted_shape(shape_id, layer.r, layer.g, layer.b, layer.a)
            placeholder = tinted is None
            
            if placeholder:
                # Fallback: colored square
                a = max(0.0, min(1.0, layer.a))
                tinted = Image.new("RGBA", (256, 256), (
                    int(layer.r * 255), int(layer.g * 255), 
                    int(layer.b * 255), int(a * 255)
                ))
            
            # Apply flip
            if layer.flipped:
                tinted = tinted.transpose(Image.FLIP_LEFT_RIGHT)
            
            # Resize
            resized = tinted.resize((w, h), Image.LANCZOS)
            
            # Apply outline if needed (not for placeholders)
            if layer.outlined and not placeholder:
                # Stroke width ~3px in game's ~355px preview = size/118
                stroke_px = size / 118.0
                resized = self._outline_rgba(resized, stroke_px)
            
            # Rotate (negative because PIL rotates counter-clockwise)
            rotated = resized.rotate(-layer.rotation, expand=True, resample=Image.BICUBIC)
            
            # Position: pos * unit from center
            x = cx + layer.pos_x * unit - rotated.width / 2
            y = cy + layer.pos_y * unit - rotated.height / 2
            
            # Composite onto canvas
            canvas.alpha_composite(rotated, (int(x), int(y)))
        
        return canvas
    
    def render_to_bytes(self, layers: List[EmblemLayer], 
                        size: Optional[int] = None,
                        bg_color: Optional[Tuple[int, int, int, int]] = None) -> bytes:
        """Render emblem to PNG bytes."""
        img = self.render_png(layers, size, bg_color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    
    def render_to_file(self, layers: List[EmblemLayer], 
                       output_path: str,
                       size: Optional[int] = None,
                       bg_color: Optional[Tuple[int, int, int, int]] = None) -> None:
        """Render emblem to PNG file."""
        img = self.render_png(layers, size, bg_color)
        img.save(output_path, format="PNG")
    
    def render_comparison(self, layers1: List[EmblemLayer], 
                          layers2: List[EmblemLayer],
                          size: int = 512,
                          output_path: Optional[str] = None) -> Image.Image:
        """Render two emblems side by side for comparison."""
        img1 = self.render_png(layers1, size)
        img2 = self.render_png(layers2, size)
        
        combined = Image.new("RGBA", (size * 2 + 10, size), (0, 0, 0, 0))
        combined.paste(img1, (0, 0))
        combined.paste(img2, (size + 10, 0))
        
        if output_path:
            combined.save(output_path)
        
        return combined


def render_emblem(layers: List[EmblemLayer], size: int = 512, 
                  output_path: Optional[str] = None,
                  bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0)) -> Image.Image:
    """Convenience function to render emblem."""
    renderer = EmblemRenderer(RenderConfig(size=size, bg_color=bg_color))
    img = renderer.render_png(layers, size, bg_color)
    if output_path:
        img.save(output_path)
    return img


def render_emblem_file(input_path: str, output_path: str, size: int = 512,
                       bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0)) -> Image.Image:
    """Render emblem from .emblem file to PNG."""
    from .parser import EmblemParser
    layers = EmblemParser.parse_file(input_path)
    return render_emblem(layers, size, output_path, bg_color)


def render_emblem_layers(layers: List[EmblemLayer], size: int = 512,
                         output_path: Optional[str] = None,
                         bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0)) -> bytes:
    """Convenience function to render layers to PNG bytes."""
    renderer = EmblemRenderer()
    return renderer.render_to_bytes(layers, size, bg_color)