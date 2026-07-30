import os
import sys
from pathlib import Path
from PIL import Image

def test_all_shapes():
    shape_dir = Path(__file__).parent.parent / "research/bo2-emblem-toolkit/reference_shapes"
    
    if not shape_dir.exists():
        print(f"Diretório de shapes não encontrado: {shape_dir}")
        sys.exit(1)
        
    print(f"Testando shapes no diretório: {shape_dir}\n")
    
    missing_count = 0
    invalid_alpha_count = 0
    total_checked = 0
    
    # BO2 shapes go from 0 to 260
    for i in range(261):
        # We need to find the file based on the ID map, but we can also just iterate files.
        # Actually, let's load the shape map to know what the names should be.
        pass
        
    # Better approach: check all PNGs in the directory
    png_files = list(shape_dir.glob("*.png"))
    for file in png_files:
        try:
            img = Image.open(str(file))
            total_checked += 1
            if img.mode != 'RGBA' and img.mode != 'LA':
                print(f"[WARNING] {file.name} não é RGBA nem LA (mode={img.mode})")
                
            # Check alpha channel
            if img.mode == 'RGBA':
                alpha = img.getchannel('A')
            elif img.mode == 'LA':
                alpha = img.getchannel('A')
            else:
                img = img.convert('RGBA')
                alpha = img.getchannel('A')
                
            extrema = alpha.getextrema()
            if extrema == (0, 0):
                print(f"[FAIL] {file.name} é TOTALMENTE TRANSPARENTE!")
                invalid_alpha_count += 1
            elif extrema == (255, 255):
                print(f"[FAIL] {file.name} é TOTALMENTE OPACO (Renderização Branca possivelmente causada aqui)")
                invalid_alpha_count += 1
                
        except Exception as e:
            print(f"[ERROR] Falha ao carregar {file.name}: {e}")
            missing_count += 1
            
    print("\n--- RELATÓRIO DE SHAPES ---")
    print(f"Shapes verificados: {total_checked}")
    print(f"Erros de carregamento: {missing_count}")
    print(f"Erros de Alpha (Transparente/Opaco total): {invalid_alpha_count}")
    
    if missing_count > 0 or invalid_alpha_count > 0:
        sys.exit(1)
    else:
        print("100% DE SHAPES VÁLIDOS!")
        sys.exit(0)

if __name__ == "__main__":
    test_all_shapes()
