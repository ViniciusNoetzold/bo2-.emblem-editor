import os
import sys
import traceback
from pathlib import Path

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bo2_emblem.parser import EmblemParser

def test_all_emblems():
    emblems_dir = Path(__file__).parent.parent / "Exemplos de .emblem"
    
    if not emblems_dir.exists():
        print(f"Diretório não encontrado: {emblems_dir}")
        sys.exit(1)
    
    emblem_files = list(emblems_dir.glob("*.emblem")) + list(emblems_dir.glob("*.bin"))
    print(f"Encontrados {len(emblem_files)} arquivos para teste.\n")
    
    if not emblem_files:
        print("Nenhum arquivo .emblem ou .bin encontrado!")
        sys.exit(1)
        
    success_count = 0
    fail_count = 0
    
    for file in emblem_files:
        try:
            layers, header = EmblemParser.parse_file(str(file))
            print(f"[SUCCESS] {file.name} - {len(layers)} layers carregados.")
            success_count += 1
        except Exception as e:
            print(f"[FAIL] {file.name}")
            print(f"  Error: {e}")
            traceback.print_exc()
            fail_count += 1
            
    print("\n--- RELATÓRIO FINAL ---")
    print(f"Total: {len(emblem_files)}")
    print(f"Sucessos: {success_count}")
    print(f"Falhas: {fail_count}")
    
    if fail_count > 0:
        sys.exit(1)
    else:
        print("100% DE SUCESSO!")
        sys.exit(0)

if __name__ == "__main__":
    test_all_emblems()
