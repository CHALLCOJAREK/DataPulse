# src/bridge/updater.py
# ==========================================================
# DataPulse v4.0 – MultiExcel Updater
# Sincroniza todos los Excels definidos en el entorno hacia la base SQLite.
# ==========================================================
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import sqlite3
import pandas as pd
from core.config import DB_PATH
from core.logger import log
from core.db_utils import sanitize_table_name
from bridge.reader import leer_excel_completo

# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================
def sync_excel_to_db():
    """
    Sincroniza todas las hojas de todos los Excels definidos en .env hacia la base de datos.
    Cada hoja se convierte en una tabla (1:1 con su estructura).
    """
    log("📂 Iniciando sincronización completa de Excels hacia la base de datos...")

    # Leer todas las hojas (multi-excel)
    hojas = leer_excel_completo()
    if not hojas:
        log("⚠️ No se encontraron hojas válidas para sincronizar.")
        return

    total = len(hojas)
    actualizadas = 0

    try:
        conn = sqlite3.connect(DB_PATH)

        for hoja, df in hojas.items():
            try:
                table_name = sanitize_table_name(hoja)
                log(f"🧩 Guardando hoja '{hoja}' → tabla '{table_name}'...")

                if df.empty:
                    log(f"⚠️ Hoja '{hoja}' vacía, se omite.")
                    continue

                df.to_sql(table_name, conn, if_exists="replace", index=False)
                log(f"✅ '{hoja}' sincronizada correctamente ({len(df)} filas, {len(df.columns)} columnas).")
                actualizadas += 1

            except Exception as e:
                log(f"❌ Error procesando hoja '{hoja}': {e}")

    except Exception as e:
        log(f"💥 Error crítico durante la sincronización: {e}")

    finally:
        if 'conn' in locals():
            conn.close()

    log(f"\n🚀 Sincronización finalizada.")
    log(f"📊 Resultado: {actualizadas}/{total} hojas sincronizadas correctamente.")
    log(f"🗃️ Base de datos actualizada en: {DB_PATH}\n")

# ==========================================================
# MODO DIRECTO (EJECUCIÓN INDEPENDIENTE)
# ==========================================================
if __name__ == "__main__":
    sync_excel_to_db()
