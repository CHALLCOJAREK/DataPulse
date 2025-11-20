# src/ia/summarizer.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import sqlite3
from datetime import datetime
from src.core.config import DB_PATH
from src.core.logger import log


def get_all_tables():
    """Obtiene todas las tablas disponibles en la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    try:
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table';", conn
        )["name"].tolist()
        return tables
    finally:
        conn.close()


def summarize_table(table: str):
    """Analiza una tabla bancaria y devuelve un resumen numérico."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(f"SELECT * FROM '{table}'", conn)
        if df.empty:
            return None

        # Detectar columnas financieras comunes
        cols = [c.lower() for c in df.columns]
        monto_cols = [c for c in cols if "monto" in c or "importe" in c or "total" in c]

        if not monto_cols:
            return None

        monto_col = monto_cols[0]
        df[monto_col] = pd.to_numeric(df[monto_col], errors="coerce").fillna(0)

        total = df[monto_col].sum()
        promedio = df[monto_col].mean()
        conteo = len(df)

        # Detectar fechas
        fecha_cols = [c for c in cols if "fecha" in c]
        fecha_min, fecha_max = None, None
        if fecha_cols:
            fecha_col = fecha_cols[0]
            try:
                df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
                fecha_min = df[fecha_col].min()
                fecha_max = df[fecha_col].max()
            except Exception:
                pass

        return {
            "tabla": table,
            "transacciones": conteo,
            "total_monto": round(total, 2),
            "promedio_monto": round(promedio, 2),
            "fecha_min": str(fecha_min) if fecha_min else None,
            "fecha_max": str(fecha_max) if fecha_max else None,
        }

    except Exception as e:
        log(f"⚠️ Error analizando tabla '{table}': {e}")
        return None
    finally:
        conn.close()


def generate_summary_report():
    """Genera el resumen global (numérico + narrativo)."""
    log("🧠 Generando resumen analítico de DataPulse...")

    tablas = get_all_tables()
    if not tablas:
        log("⚠️ No se encontraron tablas en la base.")
        return None

    resumenes = []
    for t in tablas:
        res = summarize_table(t)
        if res:
            resumenes.append(res)

    if not resumenes:
        log("⚠️ No se pudieron generar resúmenes válidos.")
        return None

    total_general = sum(r["total_monto"] for r in resumenes)
    transacciones_total = sum(r["transacciones"] for r in resumenes)

    texto = (
        f"📊 **RESUMEN GENERAL DE DATAPULSE — {datetime.now().strftime('%Y-%m-%d')}**\n\n"
        f"Se analizaron {len(resumenes)} cuentas registradas con un total de "
        f"{transacciones_total:,} movimientos. El monto total procesado alcanza "
        f"S/. {total_general:,.2f}.\n\n"
    )

    # Top 3 cuentas con mayor movimiento
    top = sorted(resumenes, key=lambda x: x["total_monto"], reverse=True)[:3]
    texto += "🏦 **Cuentas con mayor flujo:**\n"
    for r in top:
        texto += f" - {r['tabla']}: S/. {r['total_monto']:,.2f}\n"

    texto += "\n🧾 **Detalle completo por tabla:**\n"
    for r in resumenes:
        texto += (
            f" • {r['tabla']} → {r['transacciones']} movs | "
            f"Total: S/. {r['total_monto']:,.2f} | Prom: S/. {r['promedio_monto']:,.2f}\n"
        )

    return {"resumen": resumenes, "texto": texto}


if __name__ == "__main__":
    resultado = generate_summary_report()
    if resultado:
        print(resultado["texto"])
