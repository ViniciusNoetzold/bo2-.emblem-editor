import os
import sys
import subprocess
import shutil
from pathlib import Path

def build():
    print("Iniciando build do BO2 Emblem Studio...")
    
    project_dir = Path(__file__).parent.parent
    src_dir = project_dir / "src"
    gui_main = src_dir / "bo2_emblem" / "gui" / "__main__.py"
    
    if not gui_main.exists():
        print(f"Erro: Entry point não encontrado: {gui_main}")
        sys.exit(1)
        
    print("Limpando builds anteriores...")
    for p in ["build", "dist"]:
        path = project_dir / p
        if path.exists():
            shutil.rmtree(path)
            
    # As we have reference_shapes, we should bundle them!
    # Let's include the research/bo2-emblem-toolkit/reference_shapes directory
    shapes_src = project_dir / "research" / "bo2-emblem-toolkit" / "reference_shapes"
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "BO2_Emblem_Studio",
        "--hidden-import", "aiohttp",
        "--hidden-import", "requests",
        "--hidden-import", "bo2_emblem.parser",
        "--hidden-import", "bo2_emblem.serializer",
        "--hidden-import", "bo2_emblem.renderer",
        "--hidden-import", "bo2_emblem.importer",
        "--hidden-import", "bo2_emblem.exporter",
        "--hidden-import", "bo2_emblem.optimizer",
        "--hidden-import", "bo2_emblem.ai_hermes",
        "--hidden-import", "bo2_emblem.gui.editor",
        f"--add-data={shapes_src}{os.pathsep}bo2_emblem/reference_shapes", # Copy shapes into the bundle
        str(gui_main)
    ]
    
    print(f"Executando PyInstaller:\n{' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=project_dir)
    
    if result.returncode == 0:
        print("\nBuild completado com sucesso! Verifique a pasta 'dist/BO2_Emblem_Studio'")
    else:
        print(f"\nBuild falhou com código {result.returncode}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    build()
