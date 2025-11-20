# ==========================================================
# DataPulse Tool – Inspect Database Structure (robusto)
# Carga automática de la ruta raíz del proyecto
# ==========================================================
import sys
from pathlib import Path
import sqlite3

# === 🔧 FIX GLOBAL DE RUTA (para evitar "No module named src") ===
BASE_DIR = Path(__file__).resolve().parents[1]  # apunta a /src
ROOT_DIR = BASE_DIR.parent                      # apunta a /DataPulse
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# === Imports del proyecto ===
from core.config import DB_PATH
from core.logger import log


def inspect_database():
    """Muestra todas las tablas y sus columnas."""
    try:
        db_path = Path(DB_PATH)
        if not db_path.exists():
            log(f"❌ No se encontró la base de datos: {db_path}")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"\n📂 Base de datos: {db_path}\n")

        print("📋 Tablas disponibles:")
        tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")]
        for t in tables:
            print(f" - {t}")

        print("\n🔍 Estructura detallada:")
        for t in tables:
            print(f"\n🧱 {t}")
            for col in cursor.execute(f"PRAGMA table_info('{t}');"):
                col_id, col_name, col_type = col[:3]
                print(f"   {col_name} ({col_type})")

        conn.close()
        log("✅ Inspección completada correctamente.")

    except Exception as e:
        log(f"💥 Error inspeccionando la base: {e}")


if __name__ == "__main__":
    inspect_database()
