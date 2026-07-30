import pytest
from bo2_emblem.parser import EmblemParser, EmblemLayer

def test_parser_empty():
    layer = EmblemLayer(index=0, shape_id=65535)
    assert layer.is_empty == True
    
    layer = EmblemLayer(index=1, shape_id=192)
    assert layer.is_empty == False

def test_parser_bounds():
    # Verify bounds checking
    pass
