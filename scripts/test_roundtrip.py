import os
import sys
from pathlib import Path
import io

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bo2_emblem.parser import EmblemParser
from bo2_emblem.serializer import EmblemSerializer

def test_roundtrip():
    emblems_dir = Path(__file__).parent.parent / "Exemplos de .emblem"
    
    emblem_files = list(emblems_dir.glob("*.emblem"))
    
    success = 0
    fail = 0
    
    for file in emblem_files:
        try:
            # 1. Read Original
            with open(file, "rb") as f:
                original_bytes = f.read()
                
            layers, header = EmblemParser.parse_file(str(file))
            
            # 2. Serialize
            new_bytes = EmblemSerializer.serialize_layers(layers)
            
            # 3. Parse again
            layers2 = EmblemParser.parse_bytes(new_bytes)
            
            if len(layers) == len(layers2):
                success += 1
                print(f"[SUCCESS] Roundtrip {file.name}")
            else:
                fail += 1
                print(f"[FAIL] Roundtrip {file.name}: layer count changed!")
        except Exception as e:
            fail += 1
            print(f"[ERROR] {file.name}: {e}")
            
    print(f"\nTotal: {len(emblem_files)}, Sucesso: {success}, Falhas: {fail}")
    if fail > 0:
        sys.exit(1)

if __name__ == "__main__":
    test_roundtrip()
