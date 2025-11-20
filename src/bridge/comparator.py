# src/bridge/comparator.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import sqlite3
import unicodedata
from src.core.config import DB_PATH
from src.core.logger import log

# --- Mapa de claves por defecto (puede faltar 'responsable' en alguna hoja) ---
DEFAULT_KEYS = ["fecha", "descripcion__actividad", "monto_", "responsable"]
FALLBACK_KEYS = ["fecha", "descripcion__actividad", "monto_"]

OMITIR_HOJAS = {"reporte_bancos", "fe"}  # por si acaso

def load_table_from_db(table_name: str) -> pd.DataFrame:
    """Carga una tabla desde SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
        conn.close()
        log(f"📦 Tabla '{table_name}' cargada desde la base ({len(df)} filas).")
        return df
    except Exception as e:
        log(f"⚠️ No se pudo cargar '{table_name}': {e}")
        return pd.DataFrame()

# ---------- Normalización ----------
def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas: minúsculas, sin tildes, _ en vez de espacios/slash."""
    cols = []
    for c in df.columns:
        c2 = str(c).strip().replace("\n", " ")
        c2 = c2.replace(" / ", "_").replace("/", "_").replace(" ", "_")
        c2 = _strip_accents(c2).lower()
        cols.append(c2)
    df = df.copy()
    df.columns = cols
    return df

def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Fija tipos básicos: fechas a YYYY-MM-DD, numéricos a string estable, resto string."""
    dfx = df.copy()
    # Fecha
    for col in dfx.columns:
        if "fecha" in col:
            dfx[col] = pd.to_datetime(dfx[col], errors="coerce").dt.strftime("%Y-%m-%d")
    # Monto
        if col.startswith("monto"):
            dfx[col] = pd.to_numeric(dfx[col], errors="coerce")
    # Resto a string estable
    for col in dfx.columns:
        if dfx[col].dtype.kind in ("f", "i"):
            # numéricos: formateo consistente (evita 100 vs 100.0)
            dfx[col] = dfx[col].astype("float").round(2).astype(str)
        else:
            dfx[col] = dfx[col].astype(str).str.strip()
    return dfx.fillna("")

def get_keys_for_sheet(columns: list[str]) -> list[str]:
    """Devuelve la mejor lista de claves disponible según columnas reales."""
    keys = [k for k in DEFAULT_KEYS if k in columns]
    if len(keys) < 3:
        keys = [k for k in FALLBACK_KEYS if k in columns]
    return keys

# ---------- Comparación ----------
def compare_dataframes(df_old: pd.DataFrame, df_new: pd.DataFrame):
    """
    Devuelve (nuevos, eliminados, modificados) como DataFrames.
    """
    if df_new.empty and df_old.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Normalizar columnas y tipos en ambos lados (solo para comparar)
    df_old_n = coerce_types(normalize_columns(df_old))
    df_new_n = coerce_types(normalize_columns(df_new))

    # Calcular claves
    common_cols = sorted(set(df_old_n.columns).intersection(df_new_n.columns))
    if not common_cols:
        log("⚠️ No hay columnas en común para comparar.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    keys = get_keys_for_sheet(common_cols)
    if not keys:
        log(f"⚠️ No se encontraron claves válidas. Columnas comunes: {common_cols[:10]}…")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # NUEVOS (están en new y no en old)
    nuevos = df_new_n.merge(df_old_n[keys], on=keys, how="left", indicator=True)
    nuevos = nuevos[nuevos["_merge"] == "left_only"].drop(columns=["_merge"])

    # ELIMINADOS (están en old y no en new)
    eliminados = df_old_n.merge(df_new_n[keys], on=keys, how="left", indicator=True)
    eliminados = eliminados[eliminados["_merge"] == "left_only"].drop(columns=["_merge"])

    # MODIFICADOS (coincide clave, difiere alguna columna no-clave)
    comunes = df_new_n.merge(df_old_n, on=keys, suffixes=("_new", "_old"))
    diffs = []
    non_key_cols = [c for c in df_new_n.columns if c not in keys]
    for _, row in comunes.iterrows():
        changed = False
        for c in non_key_cols:
            cn = f"{c}_new"
            co = f"{c}_old"
            if cn in comunes.columns and co in comunes.columns:
                if str(row[cn]) != str(row[co]):
                    changed = True
                    break
        if changed:
            diffs.append(row)
    modificados = pd.DataFrame(diffs)

    return nuevos, eliminados, modificados

def detect_changes(new_data: dict):
    """
    Recorre todos los DataFrames del reader y compara con las tablas SQLite.
    Retorna resumen {hoja: {nuevos, eliminados, modificados, nuevos_df, eliminados_df, modificados_df}}
    """
    summary = {}

    for hoja, df_new in new_data.items():
        table_name = hoja.replace(" ", "_").lower()
        if table_name in OMITIR_HOJAS:
            continue

        df_old = load_table_from_db(table_name)
        if df_old.empty:
            # Consideramos todo como nuevo si no existe tabla previa
            ndf, edf, mdf = df_new.copy(), pd.DataFrame(), pd.DataFrame()
            summary[hoja] = {
                "nuevos": len(ndf), "eliminados": 0, "modificados": 0,
                "nuevos_df": ndf, "eliminados_df": edf, "modificados_df": mdf
            }
            log(f"🆕 Tabla '{table_name}' no existía. Todo se considera NUEVO: {len(ndf)} filas.")
            continue

        nuevos, eliminados, modificados = compare_dataframes(df_old, df_new)
        summary[hoja] = {
            "nuevos": len(nuevos), "eliminados": len(eliminados), "modificados": len(modificados),
            "nuevos_df": nuevos, "eliminados_df": eliminados, "modificados_df": modificados
        }
        log(f"🔍 Hoja '{hoja}' → +{len(nuevos)} nuevos, -{len(eliminados)} eliminados, ✏️ {len(modificados)} modificados.")

    return summary

if __name__ == "__main__":
    log("⚙️ comparator.py: ejecución directa solo para depuración.")
