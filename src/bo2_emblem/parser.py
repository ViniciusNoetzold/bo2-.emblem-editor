"""
BO2 Emblem Parser - Robust parser with validation
=================================================
Parses .emblem/.bin files (1408 bytes = 32 layers × 44 bytes)
Supports both raw emblem files and Plutonium T6 storage format (with custom header)
"""

import struct
from dataclasses import dataclass, field
from typing import List, Optional, BinaryIO, Tuple
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


@dataclass
class PlutoniumHeader:
    """Parsed Plutonium T6 emblem header."""
    magic: int
    version_major: int
    version_minor: int
    unknown1: int
    unknown2: int
    unknown3: int
    emblem_index: int
    name: str
    layer_count: int
    unknown4: int
    unknown5: int
    unknown6: int
    timestamp: int
    raw_header: bytes


class ParseError(Exception):
    """Raised when parsing fails with detailed context."""
    def __init__(self, message: str, offset: int = None, layer: int = None, field: str = None, value=None):
        self.offset = offset
        self.layer = layer
        self.field = field
        self.value = value
        
        details = []
        if offset is not None:
            details.append(f"offset=0x{offset:04X}")
        if layer is not None:
            details.append(f"layer={layer}")
        if field is not None:
            details.append(f"field={field}")
        if value is not None:
            details.append(f"value={value!r}")
        
        detail_str = f" ({', '.join(details)})" if details else ""
        super().__init__(f"{message}{detail_str}")


class EmblemParser:
    """Parses BO2 emblem binary format with robust validation."""
    
    NUM_LAYERS = 32
    LAYER_SIZE = 44
    FILE_SIZE = NUM_LAYERS * LAYER_SIZE  # 1408 bytes
    EMPTY_SHAPE = 0xFFFF
    
    # Struct format: <H 2x 9f BB 2x = 2 + 2 + 36 + 1 + 1 + 2 = 44
    LAYER_FORMAT = "<Hxx9fBBxx"
    
    @classmethod
    def strip_http(cls, data: bytes) -> bytes:
        """Remove HTTP headers if present (finds \r\n\r\n)."""
        idx = data.find(b"\r\n\r\n")
        return data[idx + 4:] if idx >= 0 else data
    
    @classmethod
    def detect_plutonium_header(cls, data: bytes) -> Tuple[bytes, Optional[PlutoniumHeader]]:
        """
        Detect and parse Plutonium T6 custom header.
        Returns (body, header) where header is None if no Plutonium header found.
        """
        if len(data) < 1408:
            return data, None
        
        # Check if the last 1408 bytes parse as valid emblem data
        body = data[-1408:]
        header = data[:-1408]
        
        if len(header) == 0:
            return data, None
        
        # Try to parse the last 1408 bytes as emblem data
        if cls._validate_emblem_body(body):
            return body, cls._parse_plutonium_header(header)
        
        # If that fails, try the whole data
        if cls._validate_emblem_body(data):
            return data, None
        
        # Fallback: return last 1408 bytes anyway
        return body, None
    
    @classmethod
    def _validate_emblem_body(cls, data: bytes) -> bool:
        """Quick validation that data looks like valid emblem body."""
        if len(data) != 1408:
            return False
        
        try:
            # Check that at least some layers have valid shape IDs (not all 0xFFFF)
            valid_layers = 0
            for i in range(32):
                offset = i * 44
                layer_data = data[offset:offset + 44]
                if len(layer_data) < 44:
                    return False
                shape_id = struct.unpack("<H", layer_data[:2])[0]
                if shape_id != 0xFFFF:
                    valid_layers += 1
            # At least one non-empty layer expected
            return valid_layers > 0
        except Exception:
            return False
    
    @classmethod
    def _parse_plutonium_header(cls, header: bytes) -> Optional[PlutoniumHeader]:
        """Parse the 337-byte Plutonium header."""
        if len(header) != 337:
            return None
        
        try:
            # Parse header fields based on observed format
            # Offset 0: magic/version (4 bytes)
            magic = struct.unpack("<I", header[0:4])[0]
            # Offset 4: version info (4 bytes)
            version_info = struct.unpack("<I", header[4:8])[0]
            version_major = (version_info >> 16) & 0xFFFF
            version_minor = version_info & 0xFFFF
            
            # Offset 8: unknown flags (3 x 4 bytes)
            unknown1 = struct.unpack("<I", header[8:12])[0]
            unknown2 = struct.unpack("<I", header[12:16])[0]
            unknown3 = struct.unpack("<I", header[16:20])[0]
            
            # Offset 20: emblem index (4 bytes)
            emblem_index = struct.unpack("<I", header[20:24])[0]
            
            # Offset 24: name (null-terminated string, up to 13 bytes)
            name_end = header[24:].find(b'\x00')
            if name_end >= 0:
                name = header[24:24+name_end].decode('ascii', errors='replace')
            else:
                name = header[24:37].decode('ascii', errors='replace')
            
            # Offset 37: layer count (2 bytes) + padding
            layer_count = struct.unpack("<H", header[37:39])[0]
            
            # Offset 39: more unknowns
            unknown4 = struct.unpack("<I", header[39:43])[0] if len(header) >= 43 else 0
            unknown5 = struct.unpack("<I", header[43:47])[0] if len(header) >= 47 else 0
            unknown6 = struct.unpack("<I", header[47:51])[0] if len(header) >= 51 else 0
            
            # Timestamp at offset 52 (8 bytes)
            timestamp = struct.unpack("<Q", header[52:60])[0] if len(header) >= 60 else 0
            
            return PlutoniumHeader(
                magic=magic,
                version_major=version_major,
                version_minor=version_minor,
                unknown1=unknown1,
                unknown2=unknown2,
                unknown3=unknown3,
                emblem_index=emblem_index,
                name=name,
                layer_count=layer_count,
                unknown4=unknown4,
                unknown5=unknown5,
                unknown6=unknown6,
                timestamp=timestamp,
                raw_header=header
            )
        except Exception:
            return None
    
    @classmethod
    def parse_layer(cls, data: bytes, index: int, offset: int = 0) -> Optional[EmblemLayer]:
        """Parse a single 44-byte layer record with detailed error reporting."""
        if len(data) < cls.LAYER_SIZE:
            raise ParseError(
                f"Layer data too short: {len(data)} bytes, expected {cls.LAYER_SIZE}",
                offset=offset, layer=index
            )
        
        try:
            # Unpack: uint16 shape_id, 2 padding, 9 floats, 2 bytes (outlined, flipped), 2 padding
            unpacked = struct.unpack(cls.LAYER_FORMAT, data[:cls.LAYER_SIZE])
        except struct.error as e:
            raise ParseError(
                f"Struct unpack failed: {e}",
                offset=offset, layer=index
            )
        
        shape_id = unpacked[0]
        if shape_id == cls.EMPTY_SHAPE:
            return None
        
        # Validate shape_id is reasonable - if invalid, treat as empty layer
        if shape_id > 260:  # Max known shape ID
            # Treat as empty layer instead of raising error for robustness
            return None
        
        # 9 floats: R, G, B, A, posX, posY, scaleX, scaleY, rotation
        try:
            r, g, b, a = unpacked[1:5]
            pos_x, pos_y = unpacked[5:7]
            scale_x, scale_y = unpacked[7:9]
            rotation = unpacked[9]
            outlined = bool(unpacked[10])
            flipped = bool(unpacked[11])
        except (IndexError, ValueError) as e:
            raise ParseError(
                f"Failed to extract layer fields: {e}",
                offset=offset, layer=index
            )
        
        # Validate ranges
        def check_range(name: str, value: float, min_val: float, max_val: float):
            if not (min_val <= value <= max_val):
                raise ParseError(
                    f"{name} out of range [{min_val}, {max_val}]: {value}",
                    offset=offset, layer=index, field=name, value=value
                )
        
        check_range("r", r, 0.0, 1.0)
        check_range("g", g, 0.0, 1.0)
        check_range("b", b, 0.0, 1.0)
        check_range("a", a, 0.0, 1.0)
        check_range("pos_x", pos_x, -10.0, 10.0)
        check_range("pos_y", pos_y, -10.0, 10.0)
        check_range("scale_x", scale_x, -10.0, 10.0)
        check_range("scale_y", scale_y, -10.0, 10.0)
        # BO2 allows negative rotations (equivalent to positive in opposite direction)
        # Accept -360 to 360 range, don't normalize - preserve original value
        check_range("rotation", rotation, -360.0, 360.0)
        
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
        """Parse emblem from raw bytes (handles HTTP headers and Plutonium headers)."""
        # First strip HTTP headers
        body = cls.strip_http(data)
        
        # Then detect and strip Plutonium header
        body, plutonium_header = cls.detect_plutonium_header(body)
        
        layers = []
        for i in range(cls.NUM_LAYERS):
            offset = i * cls.LAYER_SIZE
            if offset + cls.LAYER_SIZE > len(body):
                break
            
            layer_data = body[offset:offset + cls.LAYER_SIZE]
            try:
                layer = cls.parse_layer(layer_data, i, offset)
                if layer:
                    layers.append(layer)
            except ParseError as e:
                # Re-raise with full context
                raise ParseError(
                    f"Failed to parse layer {i}: {e}",
                    offset=e.offset, layer=e.layer, field=e.field, value=e.value
                ) from e
        
        return layers
    
    @classmethod
    def parse_file(cls, filepath: str) -> Tuple[List[EmblemLayer], Optional[PlutoniumHeader]]:
        """Parse emblem from file, returns (layers, plutonium_header)."""
        with open(filepath, "rb") as f:
            data = f.read()
        
        # Strip HTTP headers
        body = cls.strip_http(data)
        
        # Detect and parse Plutonium header
        body, plutonium_header = cls.detect_plutonium_header(body)
        
        layers = cls.parse_bytes(body)
        return layers, plutonium_header
    
    @classmethod
    def validate_file(cls, filepath: str) -> dict:
        """Validate emblem file and return detailed info."""
        with open(filepath, "rb") as f:
            data = f.read()
        
        body = cls.strip_http(data)
        body, plutonium_header = cls.detect_plutonium_header(body)
        
        info = {
            "file_size": len(data),
            "body_size": len(body),
            "expected_size": cls.FILE_SIZE,
            "is_valid": len(body) >= cls.FILE_SIZE,
            "layer_count": 0,
            "empty_layers": 0,
            "plutonium_header": plutonium_header is not None,
            "header_info": None,
            "errors": []
        }
        
        if plutonium_header:
            info["header_info"] = {
                "magic": plutonium_header.magic,
                "version": f"{plutonium_header.version_major}.{plutonium_header.version_minor}",
                "emblem_index": plutonium_header.emblem_index,
                "name": plutonium_header.name,
                "layer_count": plutonium_header.layer_count,
                "timestamp": plutonium_header.timestamp,
            }
        
        if len(body) < cls.FILE_SIZE:
            info["errors"].append(f"File too small: {len(body)} bytes, expected {cls.FILE_SIZE}")
            return info
        
        try:
            layers = cls.parse_bytes(body)
            info["layer_count"] = len(layers)
            info["empty_layers"] = cls.NUM_LAYERS - len(layers)
        except ParseError as e:
            info["errors"].append(str(e))
        
        return info


# Convenience functions
def load_emblem(filepath: str) -> Tuple[List[EmblemLayer], Optional[PlutoniumHeader]]:
    """Load and parse an emblem file, returns (layers, plutonium_header)."""
    return EmblemParser.parse_file(filepath)


def load_emblem_bytes(data: bytes) -> List[EmblemLayer]:
    """Parse emblem from raw bytes."""
    return EmblemParser.parse_bytes(data)