# src/bridge/consolidator.py
# ==========================================================
# DataPulse v3.9 – Consolidator Engine (Estable)
# Crea vistas resumen por cada tabla + vista global consolidada.
# ==========================================================
import sys
import sqlite3
from pathlib import Path

# === FIX DE RUTA GLOBAL ===
sys.path.append(str(Path(__file__).resolve().parents[2]))

from core.logger import log

# ==========================================================
# CONFIGURACIÓN BASE
# ==========================================================
# Detecta ruta de la base desde .env o usa valor por defecto
try:
    from core.config import DATABASE_URL
    DB_PATH = Path(DATABASE_URL or "db/datapulse.sqlite")
except Exception:
    DB_PATH = Path("db/datapulse.sqlite")

EXCLUDE_TABLES = {
    "clientes_proveedores", "sqlite_sequence",
    "reporte_bancos", "v_reporte_bancos"
}

# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================
def get_tables(conn):
    """Obtiene todas las tablas SQLite excluyendo las auxiliares."""
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall() if t[0] not in EXCLUDE_TABLES]
    return sorted(tables)


def create_summary_view(conn, table):
    """Crea o reemplaza una vista resumen para una tabla dada."""
    view_name = f"v_{table}_resumen"

    sql = f"""
    CREATE VIEW IF NOT EXISTS {view_name} AS
    SELECT
        portafolio,
        responsable,
        MIN(fecha) AS fecha_inicio,
        MAX(fecha) AS fecha_fin,
        SUM(CASE WHEN tipo_mov='INGRESO' THEN abono ELSE 0 END) AS total_ingresos,
        SUM(CASE WHEN tipo_mov='EGRESO' THEN retiro ELSE 0 END) AS total_egresos,
        MAX(saldo) AS saldo_final,
        '{table}' AS fuente
    FROM {table}
    WHERE saldo IS NOT NULL
    GROUP BY portafolio, responsable;
    """

    conn.execute(sql)
    log(f"🧩 Vista resumen creada: {view_name}")


def create_master_view(conn, views):
    """Crea la vista consolidada global (v_reporte_bancos)."""
    if not views:
        log("⚠️ No hay vistas para consolidar. Proceso omitido.")
        return

    union_sql = "\nUNION ALL\n".join([f"SELECT * FROM {v}" for v in views])
    master_sql = f"""
    CREATE VIEW IF NOT EXISTS v_reporte_bancos AS
    {union_sql};
    """

    conn.execute(master_sql)
    log("📊 Vista global consolidada creada: v_reporte_bancos")


# ==========================================================
# EJECUCIÓN PRINCIPAL
# ==========================================================
def main():
    log("🚀 Iniciando consolidación de vistas resumen...")

    if not DB_PATH.exists():
        log(f"❌ No se encontró la base de datos: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        tables = get_tables(conn)
        if not tables:
            log("⚠️ No se encontraron tablas para consolidar.")
            return

        views = []
        for t in tables:
            create_summary_view(conn, t)
            views.append(f"v_{t}_resumen")

        create_master_view(conn, views)
        conn.commit()
        log(f"✅ Consolidación completada con {len(views)} vistas generadas.")

    except Exception as e:
        log(f"💥 Error durante la consolidación: {e}")
    finally:
        conn.close()
        log("🏁 Consolidator finalizado correctamente.\n")


# ==========================================================
# EJECUCIÓN DIRECTA
# ==========================================================
if __name__ == "__main__":
    main()
