# src/core/db_utils.py
# ==========================================================
# DataPulse v4.0 – DB Utilities Multiexcel
# Guarda todas las hojas leídas de múltiples Excels en la base SQLite.
# ==========================================================
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import sqlite3
import pandas as pd
import unicodedata
from core.config import DB_PATH
from core.logger import log

# ==========================================================
# 🔗 CONEXIÓN A LA BASE DE DATOS
# ==========================================================
def create_connection():
    """Crea o abre una conexión a la base de datos SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        log(f"🧩 Conexión establecida con la base de datos: {DB_PATH}")
        return conn
    except Exception as e:
        log(f"❌ Error al conectar con la base de datos: {e}")
        return None

# ==========================================================
# 🧱 NORMALIZACIÓN DE NOMBRES
# ==========================================================
def sanitize_table_name(name: str) -> str:
    """
    Normaliza el nombre de una hoja o tabla:
    - Convierte a minúsculas
    - Reemplaza espacios y símbolos
    - Elimina tildes y caracteres no ASCII
    - Conserva solo letras, números y guiones bajos
    """
    try:
        original = name
        name = (
            name.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace(".", "_")
            .replace("/", "_")
        )

        name = ''.join(
            c for c in unicodedata.normalize('NFD', name)
            if unicodedata.category(c) != 'Mn'
        )

        name = ''.join(ch for ch in name if ch.isalnum() or ch == '_')

        if not name:
            name = "tabla_sin_nombre"

        # Limita a 50 caracteres para evitar conflictos SQLite
        name = name[:50]

        return name
    except Exception as e:
        log(f"⚠️ Error al sanitizar nombre '{name}': {e}")
        return "tabla_invalida"

# ==========================================================
# 💾 GUARDADO DE DATAFRAMES
# ==========================================================
def save_dataframe_to_db(df: pd.DataFrame, table_name: str):
    """
    Guarda un DataFrame en la base de datos:
    - Crea o reemplaza la tabla según corresponda.
    - Mantiene nombres seguros para múltiples Excels.
    """
    conn = create_connection()
    if conn is None:
        return

    table = sanitize_table_name(table_name)

    try:
        if df.empty:
            log(f"⚠️ '{table_name}' está vacía. No se guardará en la base.")
            return

        df.to_sql(table, conn, if_exists="replace", index=False)
        log(f"✅ Tabla '{table}' guardada correctamente ({len(df)} filas).")

    except Exception as e:
        log(f"💥 Error al guardar '{table_name}' → {e}")

    finally:
        conn.close()

# ==========================================================
# 🧠 INICIALIZACIÓN GLOBAL MULTIEXCEL
# ==========================================================
def init_database_from_reader(dataframes: dict):
    """
    Recibe el dict de `reader.py` con todas las hojas
    (de varios Excels) y las guarda en la base SQLite.
    """
    if not dataframes:
        log("⚠️ No se recibieron DataFrames para guardar.")
        return

    total = len(dataframes)
    log(f"📦 Iniciando volcado de {total} hojas hacia la base de datos...")

    guardadas = 0
    for hoja, df in dataframes.items():
        save_dataframe_to_db(df, hoja)
        guardadas += 1

    log(f"🚀 Volcado completado: {guardadas}/{total} tablas guardadas correctamente.")
    log(f"🗃️ Base actualizada en: {DB_PATH}")

# ==========================================================
# 🧭 EJECUCIÓN DIRECTA
# ==========================================================
if __name__ == "__main__":
    log("ℹ️ db_utils.py ejecutado directamente. No hay DataFrames que procesar.")
