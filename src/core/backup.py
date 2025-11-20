# src/core/backup.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import shutil
from datetime import datetime
from src.core.config import DB_PATH, BACKUP_PATH, PROJECT_NAME
from src.core.logger import log

def create_backup():
    """Crea un respaldo automático de la base SQLite."""
    try:
        BACKUP_PATH.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        src = Path(DB_PATH)
        if not src.exists():
            log("⚠️ No se encontró base de datos para respaldar.")
            return None

        backup_file = BACKUP_PATH / f"{PROJECT_NAME}_{timestamp}.sqlite"
        shutil.copy2(src, backup_file)
        log(f"🧾 Respaldo creado: {backup_file.name}")
        return backup_file

    except Exception as e:
        log(f"❌ Error creando respaldo: {e}")
        return None


def purge_old_backups(limit: int = 5):
    """
    Mantiene solo los últimos 'limit' backups.
    Elimina los más antiguos automáticamente.
    """
    try:
        files = sorted(BACKUP_PATH.glob("*.sqlite"), key=lambda f: f.stat().st_mtime, reverse=True)
        if len(files) > limit:
            for old_file in files[limit:]:
                old_file.unlink()
                log(f"🗑️ Backup antiguo eliminado: {old_file.name}")
        else:
            log("✅ No hay backups antiguos que eliminar.")
    except Exception as e:
        log(f"⚠️ Error limpiando backups antiguos: {e}")
