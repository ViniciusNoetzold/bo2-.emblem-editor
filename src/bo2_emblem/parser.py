"""
BO2 Emblem Parser
=================
Parses .emblem/.bin files (1408 bytes = 32 layers × 44 bytes)
"""

import struct
from dataclasses import dataclass, field
from typing import List, Optional, BinaryIO
from pathlib import Path


@dataclass
class EmblemLayer:
    """Represents a single layer in a BO2 emblem."""
    index: int                    # Layer index (0-31), lower = further back
    shape_id: int                 # Shape ID (0xFFFF = empty)
    
    # Color (RGBA, 0.0-1.0)
    r: float = 1.0
    g: float = 1.0
    b: float = 1.0
    a: float = 1.0
    
    # Position (fraction of half-extent from center, +Y = DOWN)
    pos_x: float = 0.0
    pos_y: float = 0.0
    
    # Scale (TRUE scale = 2**scale, always positive)
    scale_x: float = 0.0
    scale_y: float = 0.0
    
    # Rotation in degrees (clockwise positive)
    rotation: float = 0.0
    
    # Flags
    outlined: bool = False
    flipped: bool = False
    
    # Constants
    EMPTY_SHAPE = 0xFFFF
    LAYER_SIZE = 44
    
    @property
    def is_empty(self) -> bool:
        return self.shape_id == self.EMPTY_SHAPE
    
    @property
    def true_scale_x(self) -> float:
        """Actual scale multiplier (2**scale_x)."""
        return 2.0 ** self.scale_x
    
    @property
    def true_scale_y(self) -> float:
        """Actual scale multiplier (2**scale_y)."""
        return 2.0 ** self.scale_y
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "shape_id": self.shape_id,
            "r": self.r, "g": self.g, "b": self.b, "a": self.a,
            "pos_x": self.pos_x, "pos_y": self.pos_y,
            "scale_x": self.scale_x, "scale_y": self.scale_y,
            "rotation": self.rotation,
            "outlined": self.outlined,
            "flipped": self.flipped,
            "true_scale_x": self.true_scale_x,
            "true_scale_y": self.true_scale_y,
        }


class EmblemParser:
    """Parses BO2 emblem binary format."""
    
    NUM_LAYERS = 32
    LAYER_SIZE = 44
    FILE_SIZE = NUM_LAYERS * LAYER_SIZE  # 1408 bytes
    EMPTY_SHAPE = 0xFFFF
    
    # Struct format: <H 2x 9f BB 2x = 2 + 2 + 36 + 1 + 1 + 2 = 44
    LAYER_FORMAT = "<Hxx9fBBxx"
    
    @classmethod
    def strip_http(cls, data: bytes) -> bytes:
        """Remove HTTP headers if present (finds \\r\\n\\r\\n)."""
        idx = data.find(b"\r\n\r\n")
        return data[idx + 4:] if idx >= 0 else data
    
    @classmethod
    def parse_layer(cls, data: bytes, index: int) -> Optional[EmblemLayer]:
        """Parse a single 44-byte layer record."""
        if len(data) < cls.LAYER_SIZE:
            return None
            
        # Unpack: uint16 shape_id, 2 padding, 9 floats, 2 bytes (outlined, flipped), 2 padding
        unpacked = struct.unpack(cls.LAYER_FORMAT, data[:cls.LAYER_SIZE])
        
        shape_id = unpacked[0]
        if shape_id == cls.EMPTY_SHAPE:
            return None
            
        # 9 floats: R, G, B, A, posX, posY, scaleX, scaleY, rotation
        r, g, b, a = unpacked[1:5]
        pos_x, pos_y = unpacked[5:7]
        scale_x, scale_y = unpacked[7:9]
        rotation = unpacked[9]
        outlined = bool(unpacked[10])
        flipped = bool(unpacked[11])
        
        return EmblemLayer(
            index=index,
            shape_id=shape_id,
            r=r, g=g, b=b, a=a,
            pos_x=pos_x, pos_y=pos_y,
            scale_x=scale_x, scale_y=scale_y,
            rotation=rotation,
            outlined=outlined,
            flipped=flipped,
        )
    
    @classmethod
    def parse_bytes(cls, data: bytes) -> List[EmblemLayer]:
        """Parse emblem from raw bytes (handles HTTP headers)."""
        body = cls.strip_http(data)
        layers = []
        
        for i in range(min(cls.NUM_LAYERS, len(body) // cls.LAYER_SIZE)):
            offset = i * cls.LAYER_SIZE
            layer_data = body[offset:offset + cls.LAYER_SIZE]
            layer = cls.parse_layer(layer_data, i)
            if layer:
                layers.append(layer)
                
        return layers
    
    @classmethod
    def parse_file(cls, filepath: str) -> List[EmblemLayer]:
        """Parse emblem from file."""
        with open(filepath, "rb") as f:
            data = f.read()
        return cls.parse_bytes(data)
    
    @classmethod
    def validate_file(cls, filepath: str) -> dict:
        """Validate emblem file and return info."""
        with open(filepath, "rb") as f:
            data = f.read()
            
        body = cls.strip_http(data)
        
        info = {
            "file_size": len(data),
            "body_size": len(body),
            "expected_size": cls.FILE_SIZE,
            "is_valid": len(body) >= cls.FILE_SIZE,
            "layer_count": 0,
            "empty_layers": 0,
            "errors": []
        }
        
        if len(body) < cls.FILE_SIZE:
            info["errors"].append(f"File too small: {len(body)} bytes, expected {cls.FILE_SIZE}")
            return info
            
        layers = cls.parse_bytes(body)
        info["layer_count"] = len(layers)
        info["empty_layers"] = cls.NUM_LAYERS - len(layers)
        
        return info


# Convenience functions
def load_emblem(filepath: str) -> List[EmblemLayer]:
    """Load and parse an emblem file."""
    return EmblemParser.parse_file(filepath)


def load_emblem_bytes(data: bytes) -> List[EmblemLayer]:
    """Parse emblem from raw bytes."""
    return EmblemParser.parse_bytes(data)