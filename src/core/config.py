# src/core/config.py
# ==========================================================
# DataPulse v4.0 – Configuración Dinámica Multiexcel
# Lee variables EXCEL_1 ... EXCEL_10 del .env y valida el entorno.
# ==========================================================
import os
from pathlib import Path
from dotenv import load_dotenv

# === BASE DIR ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# === CARGAR VARIABLES DE ENTORNO ===
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

# === VARIABLES GENERALES ===
PROJECT_NAME = os.getenv("PROJECT_NAME", "DataPulse")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

# === GEMINI CONFIG (opcional, placeholder de seguridad) ===
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "AIzaSyC6k7eQRqKzfSk7vIEZn07f4BhzFIyuvoM"
)

# === RUTAS PRINCIPALES ===
DATA_PATH = BASE_DIR / "data"
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "db" / "datapulse.sqlite"))
LOG_PATH = Path(os.getenv("LOG_PATH", DATA_PATH / "logs"))
BACKUP_PATH = Path(os.getenv("BACKUP_PATH", DATA_PATH / "backup"))
PROCESSED_PATH = Path(os.getenv("PROCESSED_PATH", DATA_PATH / "processed"))

# === DETECCIÓN AUTOMÁTICA DE EXCELS ===
EXCELS = {}
print("\n📊 Buscando archivos Excel configurados en el entorno...\n")

for i in range(1, 11):
    key = f"EXCEL_{i}"
    path_str = os.getenv(key, "").strip()

    if not path_str:
        print(f"⚙️  {key}: vacío o no definido.")
        continue

    path = Path(path_str)
    if path.exists():
        EXCELS[f"excel_{i}"] = path
        print(f"✅  {key}: encontrado en {path}")
    else:
        print(f"⚠️  {key}: no se encontró el archivo → {path}")

if not EXCELS:
    print("🚨 No se detectó ningún archivo Excel válido en el entorno.\n")
else:
    print(f"\n📁 Total de Excels válidos detectados: {len(EXCELS)}\n")

# === CONFIGURACIONES GENERALES ===
SCHEDULE_INTERVAL_MINUTES = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", 5))

# ==========================================================
# FUNCIÓN DE VALIDACIÓN DE ENTORNO
# ==========================================================
def validate_environment():
    """Valida y prepara el entorno de ejecución (carpetas, DB y Excels)."""
    print(f"\n🧩 Validando entorno de {PROJECT_NAME}...\n")

    # Crear carpetas base si no existen
    for folder in [DATA_PATH, LOG_PATH, BACKUP_PATH, PROCESSED_PATH]:
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            print(f"📂 Carpeta creada: {folder}")
        else:
            print(f"✅ Carpeta detectada: {folder}")

    # Validar base de datos
    db_dir = DB_PATH.parent
    if not db_dir.exists():
        db_dir.mkdir(parents=True, exist_ok=True)
        print(f"📦 Carpeta DB creada: {db_dir}")
    else:
        print(f"✅ Carpeta DB detectada: {db_dir}")

    # Validar Excels detectados
    print("\n📊 Verificando archivos Excel cargados:")
    if not EXCELS:
        print("⚠️  No se encontraron archivos Excel activos en el entorno.")
    else:
        for key, path in EXCELS.items():
            print(f"   • {key}: {path}")

    print("\n🚀 Entorno validado correctamente.\n")


if __name__ == "__main__":
    validate_environment()
