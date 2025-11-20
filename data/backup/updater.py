# src/bridge/updater.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import sqlite3
from datetime import datetime
from src.core.config import DB_PATH, BACKUP_PATH
from src.core.logger import log
from src.core.db_utils import sanitize_table_name

# === FUNCIONES BASE ===

def backup_table(table_name: str):
    """Genera un respaldo CSV de la tabla antes de actualizarla."""
    table = sanitize_table_name(table_name)
    backup_file = BACKUP_PATH / f"{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        df.to_csv(backup_file, index=False, encoding="utf-8-sig")
        log(f"🗂️ Backup generado: {backup_file.name} ({len(df)} filas)")
        conn.close()
        return True
    except Exception as e:
        log(f"⚠️ No se pudo generar backup para '{table}': {e}")
        return False


def update_table_safe(table_name: str, nuevos: pd.DataFrame, modificados: pd.DataFrame):
    """Actualiza la tabla solo agregando nuevos y modificados."""
    table = sanitize_table_name(table_name)
    conn = sqlite3.connect(DB_PATH)

    try:
        # Backup antes de tocar nada
        backup_table(table)

        # Insertar nuevos registros
        if not nuevos.empty:
            nuevos.to_sql(table, conn, if_exists="append", index=False)
            log(f"➕ {len(nuevos)} registros nuevos insertados en '{table}'.")

        # Actualizar registros modificados (reemplazo simple por claves coincidentes)
        if not modificados.empty:
            claves = ["fecha", "descripcion__actividad", "monto_", "responsable"]
            for _, row in modificados.iterrows():
                cond = " AND ".join([f"{c}='{row[c]}'" for c in claves if c in row.index])
                conn.execute(f"DELETE FROM {table} WHERE {cond}")
            modificados.to_sql(table, conn, if_exists="append", index=False)
            log(f"✏️ {len(modificados)} registros actualizados en '{table}'.")

        conn.commit()
    except Exception as e:
        log(f"❌ Error al actualizar tabla '{table}': {e}")
    finally:
        conn.close()


def apply_updates(change_summary: dict, dataframes: dict):
    """Aplica los cambios detectados a la base de datos."""
    for hoja, resumen in change_summary.items():
        nuevos = resumen.get("nuevos_df", pd.DataFrame())
        modificados = resumen.get("modificados_df", pd.DataFrame())

        if nuevos.empty and modificados.empty:
            log(f"⚙️ Sin cambios para '{hoja}'.")
            continue

        update_table_safe(hoja, nuevos, modificados)
    log("🚀 Actualización segura completada.")
