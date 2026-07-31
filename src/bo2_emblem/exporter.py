"""
BO2 Emblem Exporter
===================
Exports emblems to Plutonium T6 format and game directory.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

from .parser import EmblemLayer
from .serializer import EmblemSerializer


@dataclass
class ExportConfig:
    """Configuration for emblem export."""
    slot: int = 1  # 1-20
    create_backup: bool = True
    verify_write: bool = True
    plutonium_path: Optional[str] = None


class EmblemExporter:
    """Exports emblems to Plutonium T6 game directory."""
    
    # Default Plutonium storage path
    DEFAULT_PLUTONIUM_PATH = os.path.expandvars(
        r"%localappdata%\Plutonium\storage\t6\players"
    )
    
    def __init__(self, config: Optional[ExportConfig] = None):
        self.config = config or ExportConfig()
        self.plutonium_path = self._resolve_plutonium_path()
    
    def _resolve_plutonium_path(self) -> Path:
        """Resolve Plutonium storage path."""
        if self.config.plutonium_path:
            path = Path(self.config.plutonium_path).expanduser()
        else:
            path = Path(self.DEFAULT_PLUTONIUM_PATH)
        
        return path
    
    def get_players_dir(self) -> Path:
        """Get the players directory."""
        return self.plutonium_path
    
    def get_emblem_filename(self, slot: int = None) -> str:
        """Get emblem filename for slot."""
        slot = slot or self.config.slot
        return f"{slot}#emblem.emblem"
    
    def get_emblem_path(self, slot: int = None) -> Path:
        """Get full path to emblem file."""
        return self.get_players_dir() / self.get_emblem_filename(slot)
    
    def list_existing_emblems(self) -> Dict[int, Path]:
        """List all existing emblem files in Plutonium directory."""
        emblems = {}
        players_dir = self.get_players_dir()
        
        if not players_dir.exists():
            return emblems
        
        for i in range(1, 21):
            path = players_dir / f"{i}#emblem.emblem"
            if path.exists():
                emblems[i] = path
        
        return emblems
    
    def backup_emblem(self, slot: int) -> Optional[Path]:
        """Create backup of existing emblem."""
        path = self.get_emblem_path(slot)
        if not path.exists():
            return None
        
        backup_dir = path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Create timestamped backup
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{slot}#emblem.emblem.backup_{timestamp}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(path, backup_path)
        return backup_path
    
    def export_layers(self, layers: List[EmblemLayer], 
                     slot: int = None,
                     custom_path: Optional[str] = None) -> Path:
        """Export emblem layers to file."""
        slot = slot or self.config.slot
        
        if custom_path:
            output_path = Path(custom_path)
        else:
            output_path = self.get_emblem_path(slot)
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup existing
        if self.config.create_backup and output_path.exists():
            self.backup_emblem(slot)
        
        # Serialize and write
        EmblemSerializer.write_file_with_http_headers(str(output_path), layers)
        
        # Verify
        if self.config.verify_write:
            if not self._verify_export(layers, output_path):
                raise IOError(f"Export verification failed for {output_path}")
        
        return output_path
    
    def _verify_export(self, original_layers: List[EmblemLayer], 
                      path: Path) -> bool:
        """Verify exported file matches original layers."""
        try:
            # Parse back
            from .parser import EmblemParser
            parsed_layers, _ = EmblemParser.parse_file(str(path))
            
            # Compare layer count
            if len(parsed_layers) != len([l for l in original_layers if not l.is_empty]):
                return False
            
            # Compare each layer
            orig_dict = {l.index: l for l in original_layers if not l.is_empty}
            parsed_dict = {l.index: l for l in parsed_layers}
            
            if set(orig_dict.keys()) != set(parsed_dict.keys()):
                return False
            
            for idx in orig_dict:
                o = orig_dict[idx]
                p = parsed_dict[idx]
                
                if (o.shape_id != p.shape_id or
                    abs(o.r - p.r) > 1e-5 or abs(o.g - p.g) > 1e-5 or
                    abs(o.b - p.b) > 1e-5 or abs(o.a - p.a) > 1e-5 or
                    abs(o.pos_x - p.pos_x) > 1e-5 or abs(o.pos_y - p.pos_y) > 1e-5 or
                    abs(o.scale_x - p.scale_x) > 1e-5 or abs(o.scale_y - p.scale_y) > 1e-5 or
                    abs(o.rotation - p.rotation) > 1e-5 or
                    o.outlined != p.outlined or o.flipped != p.flipped):
                    return False
            
            return True
        except Exception:
            return False
    
    def export_multiple(self, emblems: Dict[int, List[EmblemLayer]]) -> Dict[int, Path]:
        """Export multiple emblems at once."""
        results = {}
        for slot, layers in emblems.items():
            results[slot] = self.export_layers(layers, slot=slot)
        return results
    
    def import_emblem(self, slot: int) -> Optional[List[EmblemLayer]]:
        """Import emblem from Plutonium directory."""
        path = self.get_emblem_path(slot)
        if not path.exists():
            return None
        
        from .parser import EmblemParser
        layers, header = EmblemParser.parse_file(str(path))
        return layers
    
    def delete_emblem(self, slot: int) -> bool:
        """Delete emblem from Plutonium directory."""
        path = self.get_emblem_path(slot)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def get_emblem_info(self, slot: int) -> Optional[Dict]:
        """Get info about an emblem."""
        path = self.get_emblem_path(slot)
        if not path.exists():
            return None
        
        from .parser import EmblemParser
        layers, header = EmblemParser.parse_file(str(path))
        
        return {
            "slot": slot,
            "path": str(path),
            "size": path.stat().st_size,
            "layer_count": len(layers),
            "layers": [l.to_dict() for l in layers],
        }


def export_to_plutonium(layers: List[EmblemLayer], 
                       slot: int = 1,
                       plutonium_path: str = None,
                       create_backup: bool = True) -> Path:
    """Convenience function to export to Plutonium."""
    config = ExportConfig(
        slot=slot,
        plutonium_path=plutonium_path,
        create_backup=create_backup
    )
    exporter = EmblemExporter(config)
    return exporter.export_layers(layers)


def list_plutonium_emblems(plutonium_path: str = None) -> Dict[int, Path]:
    """List all emblems in Plutonium directory."""
    config = ExportConfig(plutonium_path=plutonium_path)
    exporter = EmblemExporter(config)
    return exporter.list_existing_emblems()