"""
BO2 Emblem Optimizer
====================
Optimizes emblems by reducing layer count while maintaining visual fidelity.

Goal: Reduce 80+ layers to 32 layers with 95%+ fidelity.
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from copy import deepcopy

import numpy as np
from PIL import Image

from .parser import EmblemLayer
from .renderer import EmblemRenderer
from .shape_map import get_ids_by_category


@dataclass
class OptimizerConfig:
    """Configuration for optimization."""
    target_layers: int = 32
    fidelity_threshold: float = 0.95
    max_iterations: int = 100
    color_merge_tolerance: float = 0.02
    position_merge_tolerance: float = 0.01
    scale_merge_tolerance: float = 0.05


class EmblemOptimizer:
    """Optimizes emblem layers for 32-layer limit."""
    
    def __init__(self, config: Optional[OptimizerConfig] = None):
        self.config = config or OptimizerConfig()
        self.renderer = EmblemRenderer()
        self._render_cache = {}
    
    def _render_key(self, layers: List[EmblemLayer], size: int = 256) -> Tuple:
        """Create cache key for layer list."""
        key_parts = [size]
        for l in sorted(layers, key=lambda x: x.index):
            key_parts.extend([
                l.index, l.shape_id,
                round(l.r, 4), round(l.g, 4), round(l.b, 4), round(l.a, 4),
                round(l.pos_x, 4), round(l.pos_y, 4),
                round(l.scale_x, 4), round(l.scale_y, 4),
                round(l.rotation, 4),
                l.outlined, l.flipped
            ])
        return tuple(key_parts)
    
    def render_to_array(self, layers: List[EmblemLayer], size: int = 256) -> np.ndarray:
        """Render layers to numpy array for comparison."""
        key = self._render_key(layers, size)
        if key in self._render_cache:
            return self._render_cache[key]
        
        img = self.renderer.render_png(layers, size=size, bg_color=(0, 0, 0, 0))
        arr = np.array(img)
        self._render_cache[key] = arr
        return arr
    
    def calculate_fidelity(self, original: List[EmblemLayer], 
                          optimized: List[EmblemLayer],
                          size: int = 256) -> float:
        """Calculate visual fidelity between two emblems (0-1)."""
        orig_arr = self.render_to_array(original, size)
        opt_arr = self.render_to_array(optimized, size)
        
        # Compare alpha channels (where either has content)
        orig_alpha = orig_arr[:, :, 3]
        opt_alpha = opt_arr[:, :, 3]
        
        # Pixels where either has content
        mask = (orig_alpha > 0) | (opt_alpha > 0)
        
        if not np.any(mask):
            return 1.0
        
        # Compare RGB where mask is true
        orig_rgb = orig_arr[:, :, :3][mask].astype(float) / 255.0
        opt_rgb = opt_arr[:, :, :3][mask].astype(float) / 255.0
        
        # Mean squared error
        mse = np.mean((orig_rgb - opt_rgb) ** 2)
        
        # Convert to fidelity (1 = perfect)
        fidelity = max(0.0, 1.0 - math.sqrt(mse))
        
        return fidelity
    
    def merge_similar_layers(self, layers: List[EmblemLayer]) -> List[EmblemLayer]:
        """Merge layers with similar properties."""
        if len(layers) <= 1:
            return layers
        
        merged = []
        used = [False] * len(layers)
        
        for i, layer1 in enumerate(layers):
            if used[i]:
                continue
            
            # Find similar layers
            group = [layer1]
            used[i] = True
            
            for j, layer2 in enumerate(layers):
                if used[j] or i == j:
                    continue
                
                if self._layers_similar(layer1, layer2):
                    group.append(layer2)
                    used[j] = True
            
            # Merge group into single layer
            if len(group) > 1:
                merged_layer = self._merge_layer_group(group)
                merged.append(merged_layer)
            else:
                merged.append(layer1)
        
        # Re-index
        for idx, layer in enumerate(merged):
            layer.index = idx
        
        return merged
    
    def _layers_similar(self, l1: EmblemLayer, l2: EmblemLayer) -> bool:
        """Check if two layers can be merged."""
        if l1.shape_id != l2.shape_id:
            return False
        
        if l1.outlined != l2.outlined or l1.flipped != l2.flipped:
            return False
        
        # Color similarity
        color_diff = math.sqrt(
            (l1.r - l2.r)**2 + (l1.g - l2.g)**2 + 
            (l1.b - l2.b)**2 + (l1.a - l2.a)**2
        )
        if color_diff > self.config.color_merge_tolerance:
            return False
        
        # Position similarity
        pos_diff = math.sqrt((l1.pos_x - l2.pos_x)**2 + (l1.pos_y - l2.pos_y)**2)
        if pos_diff > self.config.position_merge_tolerance:
            return False
        
        # Scale similarity
        scale_diff = math.sqrt((l1.scale_x - l2.scale_x)**2 + (l1.scale_y - l2.scale_y)**2)
        if scale_diff > self.config.scale_merge_tolerance:
            return False
        
        # Rotation similarity
        rot_diff = abs(l1.rotation - l2.rotation) % 360
        rot_diff = min(rot_diff, 360 - rot_diff)
        if rot_diff > 2.0:  # 2 degree tolerance
            return False
        
        return True
    
    def _merge_layer_group(self, layers: List[EmblemLayer]) -> EmblemLayer:
        """Merge a group of similar layers into one."""
        # Average all properties
        avg_r = sum(l.r for l in layers) / len(layers)
        avg_g = sum(l.g for l in layers) / len(layers)
        avg_b = sum(l.b for l in layers) / len(layers)
        avg_a = sum(l.a for l in layers) / len(layers)
        
        avg_pos_x = sum(l.pos_x for l in layers) / len(layers)
        avg_pos_y = sum(l.pos_y for l in layers) / len(layers)
        
        avg_scale_x = sum(l.scale_x for l in layers) / len(layers)
        avg_scale_y = sum(l.scale_y for l in layers) / len(layers)
        
        avg_rotation = sum(l.rotation for l in layers) / len(layers)
        
        # Use first layer's shape and flags
        base = layers[0]
        
        return EmblemLayer(
            index=base.index,
            shape_id=base.shape_id,
            r=avg_r, g=avg_g, b=avg_b, a=avg_a,
            pos_x=avg_pos_x, pos_y=avg_pos_y,
            scale_x=avg_scale_x, scale_y=avg_scale_y,
            rotation=avg_rotation,
            outlined=base.outlined,
            flipped=base.flipped
        )
    
    def remove_low_impact_layers(self, layers: List[EmblemLayer],
                                 original_render: np.ndarray,
                                 size: int = 256) -> List[EmblemLayer]:
        """Remove layers that contribute least to visual output."""
        if len(layers) <= self.config.target_layers:
            return layers
        
        # Calculate impact of each layer
        impacts = []
        
        for i, layer in enumerate(layers):
            # Render without this layer
            test_layers = [l for j, l in enumerate(layers) if j != i]
            test_render = self.render_to_array(test_layers, size)
            
            # Calculate difference
            diff = np.mean(np.abs(original_render.astype(float) - test_render.astype(float)))
            impacts.append((diff, i, layer))
        
        # Sort by impact (lowest first)
        impacts.sort(key=lambda x: x[0])
        
        # Keep highest impact layers
        keep_count = self.config.target_layers
        keep_indices = set(idx for _, idx, _ in impacts[-keep_count:])
        
        result = [l for i, l in enumerate(layers) if i in keep_indices]
        
        # Re-index
        for idx, layer in enumerate(result):
            layer.index = idx
        
        return result
    
    def substitute_complex_shapes(self, layers: List[EmblemLayer]) -> List[EmblemLayer]:
        """Replace complex multi-shape combinations with simpler alternatives."""
        # For now, just return as-is
        # Future: detect patterns like "circle + circle = donut" -> use single donut shape
        return layers
    
    def optimize(self, layers: List[EmblemLayer]) -> List[EmblemLayer]:
        """Main optimization pipeline."""
        print(f"Optimizing {len(layers)} layers -> target {self.config.target_layers}")
        
        # Render original for fidelity checking
        original_render = self.render_to_array(layers)
        original_fidelity = self.calculate_fidelity(layers, layers)
        print(f"Original fidelity (self): {original_fidelity:.4f}")
        
        current = deepcopy(layers)
        
        # Step 1: Merge similar layers
        current = self.merge_similar_layers(current)
        print(f"After merging similar: {len(current)} layers")
        
        # Step 2: Substitute complex shapes
        current = self.substitute_complex_shapes(current)
        
        # Step 3: If still over limit, remove low-impact layers
        if len(current) > self.config.target_layers:
            current = self.remove_low_impact_layers(current, original_render)
            print(f"After removing low impact: {len(current)} layers")
        
        # Verify fidelity
        fidelity = self.calculate_fidelity(layers, current)
        print(f"Final fidelity: {fidelity:.4f} ({fidelity*100:.1f}%)")
        
        if fidelity < self.config.fidelity_threshold:
            print(f"WARNING: Fidelity {fidelity:.4f} below threshold {self.config.fidelity_threshold}")
        
        return current
    
    def optimize_iterative(self, layers: List[EmblemLayer]) -> List[EmblemLayer]:
        """Iterative optimization with feedback loop."""
        best = deepcopy(layers)
        best_fidelity = 1.0
        
        original_render = self.render_to_array(layers)
        
        for iteration in range(self.config.max_iterations):
            print(f"\nIteration {iteration + 1}/{self.config.max_iterations}")
            
            current = self.optimize(best)
            fidelity = self.calculate_fidelity(layers, current)
            
            if fidelity >= self.config.fidelity_threshold:
                best = current
                best_fidelity = fidelity
                print(f"Target fidelity reached: {fidelity:.4f}")
                break
            
            if fidelity > best_fidelity:
                best = current
                best_fidelity = fidelity
                print(f"New best fidelity: {fidelity:.4f}")
            else:
                # Try more aggressive merging
                self.config.color_merge_tolerance *= 1.1
                self.config.position_merge_tolerance *= 1.1
                print(f"Increasing tolerances...")
        
        print(f"\nOptimization complete. Final: {len(best)} layers, fidelity: {best_fidelity:.4f}")
        return best


def optimize_emblem(layers: List[EmblemLayer], 
                    target_layers: int = 32,
                    fidelity_threshold: float = 0.95) -> List[EmblemLayer]:
    """Convenience function to optimize emblem."""
    config = OptimizerConfig(
        target_layers=target_layers,
        fidelity_threshold=fidelity_threshold
    )
    optimizer = EmblemOptimizer(config)
    return optimizer.optimize(layers)