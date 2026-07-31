import os
import sys
import traceback
from pathlib import Path
import io

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bo2_emblem.parser import EmblemParser
from bo2_emblem.serializer import EmblemSerializer

def test_roundtrip():
    emblems_dir = Path(__file__).parent.parent / "Exemplos de .emblem"
    
    emblem_files = list(emblems_dir.glob("*.emblem")) + list(emblems_dir.glob("*.bin"))
    
    if not emblem_files:
        print("Nenhum arquivo .emblem ou .bin encontrado!")
        sys.exit(1)
        
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
            traceback.print_exc()
            
    print(f"\nTotal: {len(emblem_files)}, Sucessos: {success}, Falhas: {fail}")
    if fail > 0:
        sys.exit(1)
    else:
        print("100% DE SUCESSO!")
        sys.exit(0)

if __name__ == "__main__":
    test_roundtrip()
