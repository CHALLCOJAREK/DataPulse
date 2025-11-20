# src/tools/verify_data.py
import sys
from pathlib import Path

# === FIX GLOBAL DE RUTA ===
# Agrega la carpeta raíz del proyecto (C:\Proyectos\DataPulse)
CURRENT_DIR = Path(__file__).resolve()
ROOT_DIR = CURRENT_DIR.parents[3]
sys.path.append(str(ROOT_DIR))

import pandas as pd
import sqlite3
from src.core.config import EXCELS, DB_PATH, DATA_PATH
from src.core.logger import log

# ==========================================================
# CONFIGURACIÓN
# ==========================================================
EXCEL_PATH = EXCELS.get("movimientos")
OUTPUT_PATH = DATA_PATH / "Comparativo_Resultados.xlsx"

OMITIR_HOJAS = {"Reporte_Bancos", "FE", "Clientes_Proveedores"}

# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================
def verificar_excel_vs_db():
    """Compara cada hoja del Excel con su tabla equivalente en SQLite."""
    if not EXCEL_PATH or not EXCEL_PATH.exists():
        log(f"❌ No se encontró el archivo Excel: {EXCEL_PATH}")
        return

    if not DB_PATH.exists():
        log(f"❌ No se encontró la base de datos: {DB_PATH}")
        return

    log("📘 Iniciando comparación hoja ↔ tabla...")

    conn = sqlite3.connect(DB_PATH)
    xls = pd.ExcelFile(EXCEL_PATH, engine="openpyxl")

    resumen, diferencias = [], []

    for hoja in xls.sheet_names:
        if hoja in OMITIR_HOJAS:
            continue

        log(f"🔍 Comparando '{hoja}'...")

        try:
            # --- Leer desde Excel y BD ---
            df_excel = pd.read_excel(EXCEL_PATH, sheet_name=hoja, dtype=str).fillna("")
            df_sql = pd.read_sql_query(f"SELECT * FROM '{hoja}'", conn).fillna("")

            # --- Igualar dimensiones y columnas ---
            max_rows = max(len(df_excel), len(df_sql))
            df_excel = df_excel.reindex(range(max_rows)).reindex(columns=df_sql.columns, fill_value="")
            df_sql = df_sql.reindex(range(max_rows)).reindex(columns=df_sql.columns, fill_value="")

            # --- Comparar celda a celda ---
            diff_matrix = (df_excel != df_sql)
            total_dif = diff_matrix.sum().sum()

            if total_dif == 0:
                resumen.append([hoja, "✅ 100% Correcto", len(df_excel), len(df_excel.columns), 0])
            else:
                resumen.append([hoja, "⚠️ Diferencias", len(df_excel), len(df_excel.columns), total_dif])
                for r in range(max_rows):
                    for c, col in enumerate(df_sql.columns):
                        if diff_matrix.iloc[r, c]:
                            diferencias.append([
                                hoja,
                                r + 2,  # fila (considerando encabezado)
                                col,
                                df_excel.iloc[r, c],
                                df_sql.iloc[r, c]
                            ])

        except Exception as e:
            resumen.append([hoja, "❌ Error", 0, 0, str(e)])
            log(f"❌ Error al comparar '{hoja}': {e}")

    conn.close()

    # --- Exportar resultados ---
    df_resumen = pd.DataFrame(
        resumen,
        columns=["Hoja / Tabla", "Estado", "Filas", "Columnas", "Celdas Diferentes"]
    )

    log("📊 Resultados del comparativo:")
    print(df_resumen.to_string(index=False))

    if diferencias:
        df_diferencias = pd.DataFrame(
            diferencias,
            columns=["Hoja", "Fila", "Columna", "Valor Excel", "Valor BD"]
        )
        with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
            df_resumen.to_excel(writer, sheet_name="Resumen", index=False)
            df_diferencias.to_excel(writer, sheet_name="Diferencias", index=False)
        log(f"📁 Archivo de diferencias generado: {OUTPUT_PATH}")
    else:
        log("✅ Todas las hojas coinciden 100 % con las tablas. No se generó archivo de diferencias.")

# ==========================================================
# EJECUCIÓN DIRECTA
# ==========================================================
if __name__ == "__main__":
    verificar_excel_vs_db()
