# src/bridge/comparator.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import sqlite3
from src.core.config import DB_PATH
from src.core.logger import log

def load_table_from_db(table_name: str) -> pd.DataFrame:
    """Carga una tabla existente desde SQLite como DataFrame."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
        conn.close()
        log(f"📦 Tabla '{table_name}' cargada desde la base ({len(df)} filas).")
        return df
    except Exception as e:
        log(f"⚠️ No se pudo cargar '{table_name}': {e}")
        return pd.DataFrame()

def compare_dataframes(df_old: pd.DataFrame, df_new: pd.DataFrame, keys=None):
    """
    Compara dos DataFrames y devuelve tres DataFrames:
    - nuevos registros
    - eliminados
    - modificados
    """
    # Clave por defecto más robusta
    if keys is None:
        keys = [col for col in ["fecha", "descripcion__actividad", "monto_", "responsable"] if col in df_new.columns]

    if not keys:
        log("⚠️ No se encontraron columnas clave válidas.")
        return None, None, None

    # --- Normalización de datos ---
    for df in [df_old, df_new]:
        for col in df.columns:
            if "fecha" in col.lower():
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
            df[col] = df[col].astype(str).str.strip().fillna("")

    # --- Normalizar clave a minúsculas para evitar falsos negativos ---
    df_old.columns = [c.lower().strip() for c in df_old.columns]
    df_new.columns = [c.lower().strip() for c in df_new.columns]

    # === NUEVOS REGISTROS ===
    nuevos = df_new.merge(df_old, on=keys, how="left", indicator=True)
    nuevos = nuevos[nuevos["_merge"] == "left_only"].drop(columns=["_merge"])

    # === ELIMINADOS ===
    eliminados = df_old.merge(df_new, on=keys, how="left", indicator=True)
    eliminados = eliminados[eliminados["_merge"] == "left_only"].drop(columns=["_merge"])

    # === MODIFICADOS ===
    comunes = df_new.merge(df_old, on=keys, suffixes=("_new", "_old"))
    modificados = []
    for _, row in comunes.iterrows():
        for col in df_new.columns:
            if col in keys:
                continue
            col_new = f"{col}_new"
            col_old = f"{col}_old"
            if col_new in comunes.columns and col_old in comunes.columns:
                if row[col_new] != row[col_old]:
                    modificados.append(row)
                    break
    modificados = pd.DataFrame(modificados)

    return nuevos, eliminados, modificados

def detect_changes(new_data: dict):
    """
    Recorre todos los DataFrames del reader y compara con las tablas SQLite.
    Retorna un resumen general con totales por hoja.
    """
    summary = {}

    for hoja, df_new in new_data.items():
        table_name = hoja.lower().replace(" ", "_")

        df_old = load_table_from_db(table_name)
        if df_old.empty:
            log(f"🆕 Tabla '{table_name}' no existía. Se considerará todo como nuevo.")
            summary[hoja] = {"nuevos": len(df_new), "eliminados": 0, "modificados": 0}
            continue

        nuevos, eliminados, modificados = compare_dataframes(df_old, df_new)
        summary[hoja] = {
            "nuevos": len(nuevos) if nuevos is not None else 0,
            "eliminados": len(eliminados) if eliminados is not None else 0,
            "modificados": len(modificados) if modificados is not None else 0,
        }

        log(f"🔍 Hoja '{hoja}' → +{summary[hoja]['nuevos']} nuevos, "
            f"-{summary[hoja]['eliminados']} eliminados, "
            f"✏️ {summary[hoja]['modificados']} modificados.")

    return summary


if __name__ == "__main__":
    log("⚙️ Ejecutando comparación de prueba (sin datos nuevos).")
