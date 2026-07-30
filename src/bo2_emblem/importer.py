"""
BO2 Emblem Image Importer - Advanced Pipeline
==============================================
Converts images (PNG, JPEG, WebP, BMP, SVG) to BO2 emblem layers using
advanced computer vision techniques:

Pipeline:
1. Load image
2. Preprocessing (resize, denoise, enhance)
3. Background removal (GrabCut + alpha matting)
4. Edge detection (Canny + morphological operations)
5. Connected components analysis
6. Contour extraction & simplification
7. Shape feature extraction (Hu moments, Fourier descriptors, geometric properties)
8. Intelligent shape matching against 261 BO2 reference shapes
9. Layer composition with optimization
10. Export to .emblem format
"""

import os
import math
import json
import hashlib
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageOps, ImageDraw

from .parser import EmblemLayer
from .shape_map import get_ids_by_category, get_shape_name, SHAPE_ID_MAP
from .renderer import EmblemRenderer, RenderConfig


@dataclass
class ImportConfig:
    """Configuration for image import."""
    max_layers: int = 32
    target_size: int = 512
    edge_threshold: float = 0.3
    color_quantization: int = 16
    min_shape_area: float = 0.001
    shape_match_threshold: float = 0.6
    background_removal: bool = True
    invert_colors: bool = False
    denoise: bool = True
    enhance_contrast: bool = True
    use_grabcut: bool = True
    simplify_contours: bool = True
    contour_epsilon_factor: float = 0.02


@dataclass
class ShapeFeatures:
    """Computed features for a shape/contour."""
    # Geometric
    area: float = 0.0
    perimeter: float = 0.0
    centroid: Tuple[float, float] = (0.0, 0.0)
    bounding_box: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # x, y, w, h
    aspect_ratio: float = 1.0
    extent: float = 0.0  # area / bbox_area
    solidity: float = 0.0  # area / hull_area
    circularity: float = 0.0  # 4*pi*area/perimeter^2
    
    # Hu Moments (7 values, scale/translation/rotation invariant)
    hu_moments: np.ndarray = field(default_factory=lambda: np.zeros(7))
    
    # Fourier Descriptors (for shape boundary)
    fourier_descriptors: np.ndarray = field(default_factory=lambda: np.zeros(20))
    
    # Color
    mean_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # RGBA 0-1
    dominant_colors: List[Tuple[float, float, float, float]] = field(default_factory=list)
    
    # Texture
    texture_histogram: np.ndarray = field(default_factory=lambda: np.zeros(256))


@dataclass 
class ReferenceShapeData:
    """Pre-computed data for a reference shape."""
    shape_id: int
    name: str
    category: str
    image: Image.Image  # LA mode (luminance + alpha)
    features: ShapeFeatures
    contour: np.ndarray  # Contour points
    hash: str  # Perceptual hash for quick comparison


class ShapeDatabase:
    """In-memory database of all 261 BO2 reference shapes with pre-computed features."""
    
    def __init__(self, shapes_dir: str):
        self.shapes_dir = shapes_dir
        self.shapes: Dict[int, ReferenceShapeData] = {}
        self._load_all_shapes()
    
    def _load_all_shapes(self):
        """Load all reference shapes and pre-compute features."""
        print("Loading shape database...")
        loaded = 0
        for shape_id, (category, name) in SHAPE_ID_MAP.items():
            if shape_id == 0xFFFF:
                continue
            filename = f"{name}.png"
            path = os.path.join(self.shapes_dir, filename)
            
            if not os.path.exists(path):
                continue
            
            try:
                # Load as LA (luminance + alpha)
                img = Image.open(path).convert("LA")
                
                # Compute features
                features = self._compute_shape_features(img)
                
                # Get contour
                contour = self._extract_main_contour(img)
                
                # Perceptual hash
                phash = self._compute_phash(img)
                
                self.shapes[shape_id] = ReferenceShapeData(
                    shape_id=shape_id,
                    name=name,
                    category=category,
                    image=img,
                    features=features,
                    contour=contour,
                    hash=phash
                )
                loaded += 1
            except Exception as e:
                print(f"Warning: Failed to load shape {shape_id} ({name}): {e}")
        
        print(f"Loaded {loaded} reference shapes")
    
    def _compute_shape_features(self, img: Image.Image) -> ShapeFeatures:
        """Extract comprehensive features from a shape image."""
        # Convert to numpy array
        arr = np.array(img)
        lum = arr[:, :, 0].astype(np.float32) / 255.0
        alpha = arr[:, :, 1].astype(np.float32) / 255.0
        
        # Create binary mask from alpha
        mask = (alpha > 0.1).astype(np.uint8) * 255
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return ShapeFeatures()
        
        # Use largest contour
        main_contour = max(contours, key=cv2.contourArea)
        
        # Geometric properties
        area = cv2.contourArea(main_contour)
        perimeter = cv2.arcLength(main_contour, True)
        x, y, w, h = cv2.boundingRect(main_contour)
        
        # Centroid
        M = cv2.moments(main_contour)
        if M['m00'] != 0:
            cx = M['m10'] / M['m00']
            cy = M['m01'] / M['m00']
        else:
            cx, cy = x + w/2, y + h/2
        
        # Shape descriptors
        aspect_ratio = w / max(h, 1)
        extent = area / (w * h) if w * h > 0 else 0
        
        # Convex hull for solidity
        hull = cv2.convexHull(main_contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        # Circularity
        circularity = (4 * math.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Hu Moments - use MASK moments (same as reference shapes)
        mask_moments = cv2.moments(mask)
        hu = cv2.HuMoments(mask_moments).flatten()
        # Log transform for better matching
        hu = -np.sign(hu) * np.log10(np.abs(hu) + 1e-10)
        
        # Fourier Descriptors
        fourier = self._compute_fourier_descriptors(main_contour)
        
        # Color from luminance (approximate)
        mean_lum = np.mean(lum[alpha > 0.1]) if np.any(alpha > 0.1) else 0.5
        
        return ShapeFeatures(
            area=area,
            perimeter=perimeter,
            centroid=(cx / img.width, cy / img.height),  # Normalized
            bounding_box=(x / img.width, y / img.height, w / img.width, h / img.height),
            aspect_ratio=aspect_ratio,
            extent=extent,
            solidity=solidity,
            circularity=circularity,
            hu_moments=hu,
            fourier_descriptors=fourier,
            mean_color=(mean_lum, mean_lum, mean_lum, 1.0)
        )
    
    def _extract_main_contour(self, img: Image.Image) -> np.ndarray:
        """Extract the main contour from shape image."""
        arr = np.array(img)
        alpha = arr[:, :, 1]
        mask = (alpha > 10).astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            return max(contours, key=cv2.contourArea)
        return np.array([])
    
    def _compute_fourier_descriptors(self, contour: np.ndarray, n_coeffs: int = 20) -> np.ndarray:
        """Compute Fourier descriptors from contour."""
        if len(contour) < 10:
            return np.zeros(n_coeffs)
        
        # Resample contour to fixed number of points
        contour = contour.reshape(-1, 2).astype(np.float32)
        
        # Interpolate to fixed length
        from scipy.interpolate import interp1d
        try:
            t = np.arange(len(contour))
            t_new = np.linspace(0, len(contour)-1, 256)
            
            fx = interp1d(t, contour[:, 0], kind='linear')
            fy = interp1d(t, contour[:, 1], kind='linear')
            
            contour_resampled = np.column_stack([fx(t_new), fy(t_new)])
        except:
            return np.zeros(n_coeffs)
        
        # Convert to complex
        complex_contour = contour_resampled[:, 0] + 1j * contour_resampled[:, 1]
        
        # FFT
        fft = np.fft.fft(complex_contour)
        
        # Normalize by first coefficient (translation invariant)
        if abs(fft[0]) > 1e-10:
            fft = fft / fft[0]
        
        # Take magnitude (rotation invariant)
        magnitudes = np.abs(fft[1:n_coeffs+1])
        
        return magnitudes
    
    def _compute_phash(self, img: Image.Image, size: int = 32) -> str:
        """Compute perceptual hash of shape."""
        # Resize and convert to grayscale
        small = img.resize((size, size), Image.LANCZOS).convert("L")
        arr = np.array(small, dtype=np.float32)
        
        # DCT
        dct = cv2.dct(arr)
        
        # Take low-frequency components
        low_freq = dct[:8, :8]
        
        # Median threshold
        median = np.median(low_freq)
        bits = (low_freq > median).flatten()
        
        # Convert to hex
        bit_str = ''.join('1' if b else '0' for b in bits)
        hash_hex = hex(int(bit_str, 2))[2:].zfill(16)
        return hash_hex
    
    def find_best_match(self, features: ShapeFeatures, category_filter: Optional[List[str]] = None) -> Tuple[int, float]:
        """Find best matching reference shape using feature comparison."""
        best_id = 192  # Default: Full Circle
        best_score = float('inf')
        
        for shape_id, ref in self.shapes.items():
            if category_filter and ref.category not in category_filter:
                continue
            
            score = self._compare_features(features, ref.features)
            
            if score < best_score:
                best_score = score
                best_id = shape_id
        
        return best_id, best_score
    
    def _compare_features(self, f1: ShapeFeatures, f2: ShapeFeatures) -> float:
            """Compare two feature vectors. Lower = better match."""
            score = 0.0
        
            # Hu Moments (7 values, invariant to scale/translation/rotation)
            # Use Euclidean distance instead of sum of absolute differences
            if len(f1.hu_moments) == 7 and len(f2.hu_moments) == 7:
                hu_diff = np.sqrt(np.sum((f1.hu_moments - f2.hu_moments) ** 2))
                score += hu_diff * 3.0  # Reduced weight from 10 to 3
        
            # Fourier Descriptors (excellent for shape boundary matching)
            if len(f1.fourier_descriptors) > 0 and len(f2.fourier_descriptors) > 0:
                min_len = min(len(f1.fourier_descriptors), len(f2.fourier_descriptors))
                if min_len > 0:
                    fourier_diff = np.sqrt(np.sum((f1.fourier_descriptors[:min_len] - f2.fourier_descriptors[:min_len]) ** 2))
                    score += fourier_diff * 10.0  # Increased weight from 5 to 10
        
            # Geometric properties
            score += abs(f1.aspect_ratio - f2.aspect_ratio) * 2.0
            score += abs(f1.circularity - f2.circularity) * 5.0  # Increased weight
            score += abs(f1.extent - f2.extent) * 3.0
            score += abs(f1.solidity - f2.solidity) * 3.0
        
            # Normalized centroid difference
            cx1, cy1 = f1.centroid
            cx2, cy2 = f2.centroid
            score += math.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2) * 5.0
        
            return score


class ImageImporter:
    """Advanced image importer with OpenCV-based pipeline."""
    
    def __init__(self, config: Optional[ImportConfig] = None):
        self.config = config or ImportConfig()
        
        # Initialize shape database
        import sys
        if hasattr(sys, '_MEIPASS'):
            shapes_dir = os.path.join(sys._MEIPASS, "bo2_emblem", "reference_shapes")
        else:
            shapes_dir = os.path.join(
                os.path.dirname(__file__), "..", "..",
                "research", "bo2-emblem-toolkit", "reference_shapes"
            )
            if not os.path.exists(shapes_dir):
                shapes_dir = "research/bo2-emblem-toolkit/reference_shapes"
        
        self.shape_db = ShapeDatabase(shapes_dir)
        self.renderer = EmblemRenderer()
    
    def import_image(self, path: str) -> List[EmblemLayer]:
        """Import image file and convert to emblem layers using advanced pipeline."""
        # 1. Load and preprocess
        img = self._load_image(path)
        img = self._preprocess_image(img)
        
        # 2. Background removal
        if self.config.background_removal:
            img = self._remove_background_advanced(img)
        
        # 3. Edge detection and segmentation
        regions = self._segment_image_advanced(img)
        
        # 4. Match regions to shapes
        layers = self._match_shapes_advanced(regions, img)
        
        # 5. Optimize layer count
        if len(layers) > self.config.max_layers:
            layers = self._reduce_layers(layers)
        
        # 6. Re-index
        for i, layer in enumerate(layers):
            layer.index = i
        
        return layers
    
    def _load_image(self, path: str) -> Image.Image:
        """Load image from file with SVG support."""
        ext = Path(path).suffix.lower()
        
        if ext == '.svg':
            try:
                import cairosvg
                import io
                png_data = cairosvg.svg2png(url=path)
                return Image.open(io.BytesIO(png_data)).convert("RGBA")
            except ImportError:
                raise ValueError("SVG support requires cairosvg package")
        
        return Image.open(path).convert("RGBA")
    
    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """Advanced preprocessing with denoising and enhancement."""
        # Resize maintaining aspect ratio
        w, h = img.size
        if max(w, h) > self.config.target_size:
            scale = self.config.target_size / max(w, h)
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.LANCZOS)
        
        # Convert to OpenCV (RGBA -> BGR for color processing, keep alpha)
        img_array = np.array(img)
        cv_bgr = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2BGR)
        alpha = img_array[:, :, 3]
        
        # Denoise on BGR
        if self.config.denoise:
            cv_bgr = cv2.fastNlMeansDenoisingColored(cv_bgr, None, 10, 10, 7, 21)
        
        # Enhance contrast using LAB on BGR
        if self.config.enhance_contrast:
            lab = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab = cv2.merge([l, a, b])
            cv_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Invert if needed
        if self.config.invert_colors:
            cv_bgr = 255 - cv_bgr
        
        # Merge back with alpha
        result = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2RGB)
        result = np.dstack([result, alpha])
        
        return Image.fromarray(result, 'RGBA')
    
    def _remove_background_advanced(self, img: Image.Image) -> Image.Image:
        """Advanced background removal using GrabCut."""
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        h, w = cv_img.shape[:2]
        
        if self.config.use_grabcut and w > 50 and h > 50:
            # Initialize mask
            mask = np.zeros((h, w), np.uint8)
            
            # Define rectangle (slightly inset from edges)
            rect = (10, 10, w - 20, h - 20)
            
            # GrabCut models
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            # Apply GrabCut
            cv2.grabCut(cv_img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            
            # Create binary mask (0,2 = background; 1,3 = foreground)
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            
            # Apply to alpha channel
            alpha = mask2 * 255
            
            # Convert back to RGBA
            b, g, r = cv2.split(cv_img)
            result = cv2.merge([b, g, r, alpha])
            
            return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGRA2RGBA))
        else:
            # Fallback to simple corner-based removal
            return self._remove_background_simple(img)
    
    def _remove_background_simple(self, img: Image.Image) -> Image.Image:
        """Simple background removal using corner sampling."""
        arr = np.array(img)
        h, w = arr.shape[:2]
        
        # Sample corners
        corners = [
            arr[0, 0], arr[0, w-1],
            arr[h-1, 0], arr[h-1, w-1]
        ]
        
        bg_color = max(set(tuple(c[:3]) for c in corners),
                       key=lambda c: sum(1 for x in corners if tuple(x[:3]) == c))
        
        tolerance = 40
        mask = np.all(np.abs(arr[:, :, :3] - bg_color) < tolerance, axis=2)
        arr[mask, 3] = 0
        
        return Image.fromarray(arr)
    
    def _segment_image_advanced(self, img: Image.Image) -> List[Dict]:
        """Advanced segmentation using alpha channel directly."""
        alpha = np.array(img)[:, :, 3]
        
        # Use alpha channel directly for segmentation
        # Create binary mask from alpha
        alpha_mask = (alpha > 10).astype(np.uint8) * 255
        
        # Find contours directly from alpha mask (more reliable for solid shapes)
        contours, hierarchy = cv2.findContours(alpha_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and process contours
        regions = []
        h, w = alpha.shape
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.config.min_shape_area * h * w:
                continue
            
            # Simplify contour
            if self.config.simplify_contours:
                epsilon = self.config.contour_epsilon_factor * cv2.arcLength(contour, True)
                contour = cv2.approxPolyDP(contour, epsilon, True)
            
            # Get bounding box
            x, y, bw, bh = cv2.boundingRect(contour)
            
            # Get mask
            mask = np.zeros((h, w), np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            
            # Get average color in region
            mask_bool = mask > 0
            if not np.any(mask_bool):
                continue
            
            cv_img_rgba = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGRA)
            region_pixels = cv_img_rgba[mask_bool]
            avg_bgr = np.mean(region_pixels[:, :3], axis=0) / 255.0
            avg_alpha = np.mean(region_pixels[:, 3]) / 255.0
            
            # Centroid
            M = cv2.moments(contour)
            if M['m00'] != 0:
                cx = M['m10'] / M['m00'] / w * 2 - 1
                cy = M['m01'] / M['m00'] / h * 2 - 1
            else:
                cx = (x + bw/2) / w * 2 - 1
                cy = (y + bh/2) / h * 2 - 1
            
            # Compute features for this region
            features = self._compute_region_features(contour, (w, h))
            
            regions.append({
                'contour': contour,
                'mask': mask_bool,
                'color': (avg_bgr[2], avg_bgr[1], avg_bgr[0], avg_alpha),  # RGB
                'center': (cx, cy),
                'size': (bw / w, bh / h),
                'area': cv2.contourArea(contour),
                'bbox': (x, y, x + bw, y + bh),
                'features': features
            })
        
        # Sort by area (largest first)
        regions.sort(key=lambda r: r['area'], reverse=True)
        
        return regions
    
    def _compute_region_features(self, contour: np.ndarray, img_size: Tuple[int, int]) -> ShapeFeatures:
        """Compute features for a region contour."""
        w, h = img_size
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        x, y, bw, bh = cv2.boundingRect(contour)
        
        M = cv2.moments(contour)
        if M['m00'] != 0:
            cx = M['m10'] / M['m00'] / w
            cy = M['m01'] / M['m00'] / h
        else:
            cx, cy = 0.5, 0.5
        
        aspect_ratio = bw / max(bh, 1)
        extent = area / (bw * bh) if bw * bh > 0 else 0
        
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        circularity = (4 * math.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Create a mask from this contour for consistent mask-based Hu moments
        mask = np.zeros((h, w), np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        
        # Hu Moments - use MASK moments (same as reference shapes)
        mask_moments = cv2.moments(mask)
        hu = cv2.HuMoments(mask_moments).flatten()
        hu = -np.sign(hu) * np.log10(np.abs(hu) + 1e-10)
        
        # Fourier Descriptors - use normalized contour
        normalized_contour = self._normalize_contour(contour, (256, 256))
        fourier = self.shape_db._compute_fourier_descriptors(normalized_contour)
        
        return ShapeFeatures(
            area=area,
            perimeter=perimeter,
            centroid=(cx, cy),
            bounding_box=(x/w, y/h, bw/w, bh/h),
            aspect_ratio=aspect_ratio,
            extent=extent,
            solidity=solidity,
            circularity=circularity,
            hu_moments=hu,
            fourier_descriptors=fourier
        )
    
    def _normalize_contour(self, contour: np.ndarray, target_size: Tuple[int, int] = (256, 256)) -> np.ndarray:
        """Normalize contour to fit in target_size."""
        if len(contour) < 3:
            return np.zeros((1, 1, 2), dtype=np.float32)
        
        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)
        if w == 0 or h == 0:
            return np.zeros((1, 1, 2), dtype=np.float32)
        
        # Translate to origin and scale to target size
        normalized = contour.astype(np.float32)
        normalized[:, :, 0] = (normalized[:, :, 0] - x) / w * target_size[0]
        normalized[:, :, 1] = (normalized[:, :, 1] - y) / h * target_size[1]
        
        return normalized
    
    def _match_shapes_advanced(self, regions: List[Dict], img: Image.Image) -> List[EmblemLayer]:
        """Match regions to BO2 shapes using advanced feature matching."""
        layers = []
        
        for i, region in enumerate(regions[:self.config.max_layers]):
            features = region['features']
            
            # Determine best category for this region
            category = self._classify_region_category(features)
            
            # Find best matching shape
            shape_id, score = self.shape_db.find_best_match(
                features, 
                category_filter=[category] if category else None
            )
            
            # Calculate scale (log2)
            true_scale_x = max(0.01, min(8.0, region['size'][0] * 2))
            true_scale_y = max(0.01, min(8.0, region['size'][1] * 2))
            scale_x = math.log2(true_scale_x) if true_scale_x > 0 else 0
            scale_y = math.log2(true_scale_y) if true_scale_y > 0 else 0
            
            # Estimate rotation from contour
            rotation = self._estimate_rotation(region['contour'])
            
            r, g, b, a = region['color']
            cx, cy = region['center']
            
            layer = EmblemLayer(
                index=i,
                shape_id=shape_id,
                r=r, g=g, b=b, a=a,
                pos_x=cx, pos_y=cy,
                scale_x=scale_x, scale_y=scale_y,
                rotation=rotation,
                outlined=False,
                flipped=False
            )
            layers.append(layer)
        
        return layers
    
    def _classify_region_category(self, features: ShapeFeatures) -> str:
        """Classify region to determine which shape category to search."""
        # Use circularity and aspect ratio to classify
        if features.circularity > 0.7:
            return "tools"  # Circular shapes
        elif features.aspect_ratio > 2.0 or features.aspect_ratio < 0.5:
            return "tools"  # Rectangular
        elif features.solidity < 0.5:
            return "emblems"  # Complex shapes
        else:
            return "tools"
    
    def _estimate_rotation(self, contour: np.ndarray) -> float:
        """Estimate rotation angle from contour orientation."""
        if len(contour) < 5:
            return 0.0
        
        # Fit ellipse
        try:
            ellipse = cv2.fitEllipse(contour)
            angle = ellipse[2]  # Angle in degrees
            # Normalize to 0-360
            return angle % 360
        except:
            return 0.0
    
    def _reduce_layers(self, layers: List[EmblemLayer]) -> List[EmblemLayer]:
        """Reduce layers by visual importance."""
        # Sort by visual importance (alpha * area)
        layers.sort(key=lambda l: l.a * (2**l.scale_x) * (2**l.scale_y), reverse=True)
        return layers[:self.config.max_layers]


# Convenience functions
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