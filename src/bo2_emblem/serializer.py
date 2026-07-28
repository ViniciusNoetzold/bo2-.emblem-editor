"""
BO2 Emblem Serializer
=====================
Converts EmblemLayer objects back to .emblem/.bin binary format (1408 bytes).
"""

import struct
from typing import List, BinaryIO
from pathlib import Path

from .parser import EmblemLayer


class EmblemSerializer:
    """Serializes emblem layers to BO2 binary format."""
    
    NUM_LAYERS = 32
    LAYER_SIZE = 44
    FILE_SIZE = NUM_LAYERS * LAYER_SIZE  # 1408 bytes
    EMPTY_SHAPE = 0xFFFF
    
    # Struct format matching parser: <H 2x 9f BB 2x
    LAYER_FORMAT = "<Hxx9fBBxx"
    
    @classmethod
    def serialize_layer(cls, layer: EmblemLayer) -> bytes:
        """Serialize a single layer to 44 bytes."""
        if layer.is_empty:
            # Empty layer: shape_id = 0xFFFF, rest zeros
            return struct.pack(cls.LAYER_FORMAT, 
                cls.EMPTY_SHAPE,  # shape_id
                0.0, 0.0, 0.0, 0.0,  # r, g, b, a
                0.0, 0.0,  # pos_x, pos_y
                0.0, 0.0,  # scale_x, scale_y
                0.0,       # rotation
                0, 0       # outlined, flipped
            )
        
        return struct.pack(cls.LAYER_FORMAT,
            layer.shape_id,
            layer.r, layer.g, layer.b, layer.a,
            layer.pos_x, layer.pos_y,
            layer.scale_x, layer.scale_y,
            layer.rotation,
            1 if layer.outlined else 0,
            1 if layer.flipped else 0
        )
    
    @classmethod
    def serialize_layers(cls, layers: List[EmblemLayer]) -> bytes:
        """Serialize list of layers to 1408 bytes."""
        # Create a dict for quick lookup by index
        layer_dict = {layer.index: layer for layer in layers}
        
        result = bytearray(cls.FILE_SIZE)
        
        for i in range(cls.NUM_LAYERS):
            if i in layer_dict:
                layer_bytes = cls.serialize_layer(layer_dict[i])
            else:
                # Empty layer
                layer_bytes = cls.serialize_layer(EmblemLayer(index=i, shape_id=cls.EMPTY_SHAPE))
            
            offset = i * cls.LAYER_SIZE
            result[offset:offset + cls.LAYER_SIZE] = layer_bytes
            
        return bytes(result)
    
    @classmethod
    def write_file(cls, filepath: str, layers: List[EmblemLayer]) -> None:
        """Write layers to emblem file."""
        data = cls.serialize_layers(layers)
        with open(filepath, "wb") as f:
            f.write(data)
    
    @classmethod
    def write_file_with_http_headers(cls, filepath: str, layers: List[EmblemLayer]) -> None:
        """Write emblem file with HTTP response headers (as game would send)."""
        data = cls.serialize_layers(layers)
        headers = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/octet-stream\r\n"
            b"Content-Length: 1408\r\n"
            b"Connection: close\r\n"
            b"\r\n"
        )
        with open(filepath, "wb") as f:
            f.write(headers + data)
    
    @classmethod
    def verify_roundtrip(cls, original_layers: List[EmblemLayer]) -> bool:
        """Verify that serialize -> parse produces identical layers."""
        from .parser import EmblemParser
        
        data = cls.serialize_layers(original_layers)
        parsed_layers = EmblemParser.parse_bytes(data)
        
        # Compare
        orig_dict = {l.index: l for l in original_layers}
        parsed_dict = {l.index: l for l in parsed_layers}
        
        if set(orig_dict.keys()) != set(parsed_dict.keys()):
            return False
            
        for idx in orig_dict:
            o = orig_dict[idx]
            p = parsed_dict[idx]
            
            if (o.shape_id != p.shape_id or
                abs(o.r - p.r) > 1e-6 or abs(o.g - p.g) > 1e-6 or
                abs(o.b - p.b) > 1e-6 or abs(o.a - p.a) > 1e-6 or
                abs(o.pos_x - p.pos_x) > 1e-6 or abs(o.pos_y - p.pos_y) > 1e-6 or
                abs(o.scale_x - p.scale_x) > 1e-6 or abs(o.scale_y - p.scale_y) > 1e-6 or
                abs(o.rotation - p.rotation) > 1e-6 or
                o.outlined != p.outlined or o.flipped != p.flipped):
                return False
                
        return True


def save_emblem(filepath: str, layers: List[EmblemLayer]) -> None:
    """Convenience function to save emblem."""
    EmblemSerializer.write_file(filepath, layers)


def save_emblem_with_http(filepath: str, layers: List[EmblemLayer]) -> None:
    """Convenience function to save emblem with HTTP headers."""
    EmblemSerializer.write_file_with_http_headers(filepath, layers)


def layers_to_bytes(layers: List[EmblemLayer]) -> bytes:
    """Convenience function to serialize layers to bytes."""
    return EmblemSerializer.serialize_layers(layers)