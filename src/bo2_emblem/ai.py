"""
BO2 Emblem AI Generator
=======================
Generates emblems from text prompts using shape composition rules.
"""

import random
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .parser import EmblemLayer
from .shape_map import (
    SHAPE_ID_MAP, get_ids_by_category, get_shape_category,
    CATEGORY_ORDER, get_shape_id
)


@dataclass
class ShapeTemplate:
    """Template for a common shape composition."""
    name: str
    category: str
    shape_id: int
    base_scale: Tuple[float, float] = (0.0, 0.0)
    color_hints: List[Tuple[float, float, float]] = None  # RGB suggestions
    common_positions: List[Tuple[float, float]] = None


# Pre-defined templates for common concepts
SHAPE_TEMPLATES = {
    # Animals
    "cat": [
        ShapeTemplate("cat_face", "tools", 192, (-0.5, -0.5), [(0.8, 0.8, 0.8)], [(0, 0)]),  # Full Circle
        ShapeTemplate("cat_ears", "tools", 145, (-1.5, -1.5), [(0.8, 0.8, 0.8)], [(-0.3, -0.4), (0.3, -0.4)]),  # Ninja Star
        ShapeTemplate("cat_eyes", "tools", 192, (-2.5, -2.0), [(0.0, 0.8, 0.0)], [(-0.15, -0.1), (0.15, -0.1)]),
        ShapeTemplate("cat_nose", "tools", 185, (-2.5, -2.5), [(1.0, 0.5, 0.5)], [(0, 0.1)]),  # Heart
        ShapeTemplate("cat_whiskers", "tools", 183, (-1.0, -3.0), [(0.6, 0.6, 0.6)], [(-0.25, 0.2), (0.25, 0.2)]),  # Curved Line
    ],
    "dog": [
        ShapeTemplate("dog_face", "tools", 192, (-0.3, -0.3), [(0.6, 0.4, 0.2)], [(0, 0)]),
        ShapeTemplate("dog_ears", "tools", 140, (-1.2, -1.0), [(0.4, 0.3, 0.1)], [(-0.3, -0.35), (0.3, -0.35)]),  # Half Heart
        ShapeTemplate("dog_nose", "tools", 192, (-2.0, -2.0), [(0.1, 0.1, 0.1)], [(0, 0.15)]),
    ],
    "skull": [
        ShapeTemplate("skull_main", "tools", 192, (-0.2, -0.2), [(0.9, 0.9, 0.9)], [(0, 0)]),
        ShapeTemplate("skull_eyes", "tools", 192, (-1.8, -1.8), [(0.0, 0.0, 0.0)], [(-0.15, -0.1), (0.15, -0.1)]),
        ShapeTemplate("skull_nose", "tools", 185, (-2.5, -1.5), [(0.0, 0.0, 0.0)], [(0, 0.1)]),  # Heart upside down
        ShapeTemplate("skull_teeth", "tools", 195, (-1.0, -2.0), [(0.9, 0.9, 0.9)], [(0, 0.3)]),  # Rectangle
    ],
    # Objects
    "gun": [
        ShapeTemplate("gun_barrel", "tools", 152, (-2.0, -0.5), [(0.2, 0.2, 0.2)], [(0, 0)]),  # Tube
        ShapeTemplate("gun_grip", "tools", 195, (-1.0, -0.8), [(0.15, 0.1, 0.05)], [(0, 0.3)]),
        ShapeTemplate("gun_trigger", "tools", 183, (-2.5, -2.5), [(0.3, 0.3, 0.3)], [(0.15, 0.35)]),
    ],
    "sword": [
        ShapeTemplate("sword_blade", "tools", 195, (-3.0, -0.3), [(0.7, 0.7, 0.8)], [(0, -0.3)]),
        ShapeTemplate("sword_hilt", "tools", 195, (-1.5, -0.5), [(0.4, 0.3, 0.1)], [(0, 0.3)]),
        ShapeTemplate("sword_guard", "tools", 194, (-1.0, -0.5), [(0.5, 0.5, 0.5)], [(0, 0.25)]),
    ],
    "heart": [
        ShapeTemplate("heart_main", "tools", 185, (0.0, 0.0), [(1.0, 0.2, 0.3)], [(0, 0)]),
    ],
    "star": [
        ShapeTemplate("star_main", "tools", 145, (0.0, 0.0), [(1.0, 0.9, 0.0)], [(0, 0)]),
    ],
    "cross": [
        ShapeTemplate("cross_vertical", "tools", 195, (-1.0, 0.5), [(0.0, 0.0, 0.0)], [(0, 0)]),
        ShapeTemplate("cross_horizontal", "tools", 195, (0.5, -1.0), [(0.0, 0.0, 0.0)], [(0, 0)]),
    ],
    "circle": [
        ShapeTemplate("circle_main", "tools", 192, (0.0, 0.0), [(0.0, 0.5, 1.0)], [(0, 0)]),
    ],
    "square": [
        ShapeTemplate("square_main", "tools", 196, (0.0, 0.0), [(0.0, 0.5, 1.0)], [(0, 0)]),
    ],
    "triangle": [
        ShapeTemplate("triangle_main", "tools", 187, (0.0, 0.0), [(0.0, 0.5, 1.0)], [(0, 0)]),
    ],
    # Text-based
    "initials": [],  # Would use type shapes
    # Gaming
    "controller": [
        ShapeTemplate("controller_body", "tools", 196, (-0.3, -0.5), [(0.1, 0.1, 0.1)], [(0, 0)]),
        ShapeTemplate("controller_stick_l", "tools", 192, (-2.0, -2.0), [(0.3, 0.3, 0.3)], [(-0.2, 0.1)]),
        ShapeTemplate("controller_stick_r", "tools", 192, (-2.0, -2.0), [(0.3, 0.3, 0.3)], [(0.2, 0.1)]),
        ShapeTemplate("controller_dpad", "tools", 194, (-1.5, -1.5), [(0.3, 0.3, 0.3)], [(0, -0.15)]),
        ShapeTemplate("controller_buttons", "tools", 192, (-2.5, -2.5), [(0.8, 0.2, 0.2), (0.2, 0.8, 0.2), (0.2, 0.2, 0.8), (0.8, 0.8, 0.2)], [(0.15, -0.1), (0.2, -0.05), (0.25, -0.15), (0.2, -0.2)]),
    ],
}


class EmblemAIGenerator:
    """Generates emblems from text prompts."""
    
    def __init__(self):
        self.templates = SHAPE_TEMPLATES
        self._load_keywords()
    
    def _load_keywords(self):
        """Map keywords to templates."""
        self.keyword_map = {
            # Animals
            "cat": "cat", "kitten": "cat", "kitty": "cat",
            "dog": "dog", "puppy": "dog", "pup": "dog",
            "skull": "skull", "skeleton": "skull", "bone": "skull",
            # Objects
            "gun": "gun", "pistol": "gun", "rifle": "gun", "weapon": "gun",
            "sword": "sword", "blade": "sword", "knife": "sword",
            "heart": "heart", "love": "heart",
            "star": "star",
            "cross": "cross",
            "circle": "circle", "round": "circle",
            "square": "square", "box": "square",
            "triangle": "triangle",
            # Gaming
            "controller": "controller", "gamepad": "controller", "gaming": "controller",
        }
    
    def parse_prompt(self, prompt: str) -> List[str]:
        """Extract concepts from prompt."""
        prompt = prompt.lower()
        concepts = []
        
        for keyword, template in self.keyword_map.items():
            if keyword in prompt:
                concepts.append(template)
        
        # Remove duplicates preserving order
        seen = set()
        unique = []
        for c in concepts:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        
        return unique
    
    def generate_from_prompt(self, prompt: str, max_layers: int = 32) -> List[EmblemLayer]:
        """Generate emblem layers from text prompt."""
        concepts = self.parse_prompt(prompt)
        
        if not concepts:
            # Default: simple geometric
            concepts = ["circle"]
        
        all_layers = []
        layer_index = 0
        
        for concept in concepts:
            if concept not in self.templates:
                continue
            
            templates = self.templates[concept]
            
            for tmpl in templates:
                if layer_index >= max_layers:
                    break
                
                # Add some randomization for variety
                pos_x, pos_y = tmpl.common_positions[0] if tmpl.common_positions else (0, 0)
                pos_x += random.uniform(-0.02, 0.02)
                pos_y += random.uniform(-0.02, 0.02)
                
                scale_x, scale_y = tmpl.base_scale
                scale_x += random.uniform(-0.1, 0.1)
                scale_y += random.uniform(-0.1, 0.1)
                
                # Pick color
                if tmpl.color_hints:
                    r, g, b = random.choice(tmpl.color_hints)
                else:
                    r, g, b = random.random(), random.random(), random.random()
                
                # Small rotation variation
                rotation = random.uniform(-5, 5)
                
                layer = EmblemLayer(
                    index=layer_index,
                    shape_id=tmpl.shape_id,
                    r=r, g=g, b=b, a=1.0,
                    pos_x=pos_x, pos_y=pos_y,
                    scale_x=scale_x, scale_y=scale_y,
                    rotation=rotation,
                    outlined=False,
                    flipped=False
                )
                all_layers.append(layer)
                layer_index += 1
        
        return all_layers
    
    def generate_complex(self, prompt: str, style: str = "default") -> List[EmblemLayer]:
        """Generate more complex emblems with multiple concepts."""
        concepts = self.parse_prompt(prompt)
        
        # Add style variations
        style_modifiers = {
            "neon": {"color_boost": 1.2, "glow": True},
            "minimal": {"layers": "few", "simple": True},
            "detailed": {"layers": "many", "complex": True},
            "monochrome": {"single_color": True},
            "default": {}
        }
        
        style_config = style_modifiers.get(style, {})
        
        layers = self.generate_from_prompt(prompt)
        
        # Apply style modifications
        if style_config.get("single_color"):
            # Use single hue for all layers
            hue = random.random()
            for layer in layers:
                # Convert hue to RGB (simplified)
                layer.r = hue
                layer.g = hue * 0.7
                layer.b = hue * 0.3
        
        return layers
    
    def suggest_prompts(self) -> List[str]:
        """Return list of example prompts."""
        return [
            "cat",
            "dog",
            "skull",
            "heart",
            "star",
            "gun",
            "sword",
            "cross",
            "circle",
            "triangle",
            "controller",
            "neon cat",
            "minimal heart",
            "detailed skull",
            "monochrome sword",
            "gaming controller",
        ]


def generate_emblem_from_prompt(prompt: str, max_layers: int = 32) -> List[EmblemLayer]:
    """Convenience function to generate emblem from prompt."""
    generator = EmblemAIGenerator()
    return generator.generate_from_prompt(prompt, max_layers)


def generate_emblem_complex(prompt: str, style: str = "default") -> List[EmblemLayer]:
    """Convenience function for complex generation."""
    generator = EmblemAIGenerator()
    return generator.generate_complex(prompt, style)