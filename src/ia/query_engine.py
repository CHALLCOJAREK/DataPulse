# src/ia/query_engine.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import sqlite3
import pandas as pd
import re
from datetime import datetime
from src.core.config import DB_PATH
from src.core.logger import log
from src.ia.summarizer import get_all_tables
from src.ia.guardrails import safe_execute_sql  # 🔒 Protección de consultas


def execute_query(sql: str) -> pd.DataFrame | None:
    """Ejecuta una consulta SQL segura (solo lectura)."""
    if not sql.strip().lower().startswith("select"):
        log("⚠️ Solo se permiten consultas de tipo SELECT.")
        return None

    try:
        # Usa el modo seguro de guardrails
        rows = safe_execute_sql(sql)
        if not rows:
            return None

        df = pd.DataFrame(rows, columns=["resultado"])
        log(f"✅ Consulta ejecutada correctamente: {len(df)} filas obtenidas.")
        return df

    except Exception as e:
        log(f"❌ Error al ejecutar SQL: {e}")
        return None


def detect_intent_and_generate_sql(query_text: str) -> str | None:
    """
    Convierte lenguaje natural (español) en SQL.
    Ejemplo:
    - 'total de ingresos en b_bcp_soles'
    - 'promedio en c_finanzas_soles entre enero y marzo'
    """
    text = query_text.lower()
    tables = get_all_tables()

    # --- Detectar tabla probable
    table = None
    for t in tables:
        if t.lower() in text:
            table = t
            break

    if not table:
        log("⚠️ No se detectó una tabla válida en la consulta.")
        return None

    # --- Detectar tipo de análisis
    if "promedio" in text or "media" in text:
        action = "AVG"
    elif "cantidad" in text or "cuenta" in text or "número" in text:
        action = "COUNT"
    elif "max" in text or "máximo" in text:
        action = "MAX"
    elif "min" in text or "mínimo" in text:
        action = "MIN"
    else:
        action = "SUM"

    # --- Detectar columna monetaria
    monto_fields = ["monto", "importe", "total"]
    conn = sqlite3.connect(DB_PATH)
    cols = pd.read_sql_query(f"PRAGMA table_info('{table}')", conn)["name"].tolist()
    conn.close()
    monto_col = next((c for c in cols if any(m in c.lower() for m in monto_fields)), None)
    if not monto_col:
        log("⚠️ No se encontró una columna de monto en la tabla.")
        return None

    # --- Detectar rango de fechas
    rango = re.findall(
        r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)", text
    )
    fecha_col = next((c for c in cols if "fecha" in c.lower()), None)
    filtro_fecha = ""
    if rango and fecha_col:
        mes = rango[0]
        meses = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
        }
        filtro_fecha = f"WHERE strftime('%m', {fecha_col}) = '{meses[mes]:02d}'"

    sql = f"SELECT {action}({monto_col}) AS resultado FROM '{table}' {filtro_fecha};"
    log(f"🧠 SQL generado: {sql}")
    return sql


def process_query(user_input: str) -> str:
    """Procesa una consulta natural o SQL directa."""
    if user_input.strip().lower().startswith("select"):
        df = execute_query(user_input)
    else:
        sql = detect_intent_and_generate_sql(user_input)
        if not sql:
            return "⚠️ No se pudo generar una consulta válida."
        df = execute_query(sql)

    if df is None or df.empty:
        return "⚠️ No se obtuvieron resultados."

    valor = df.iloc[0, 0]
    return f"🧾 Resultado: {valor:,.2f}" if isinstance(valor, (int, float)) else f"📊 Resultado: {valor}"


if __name__ == "__main__":
    log("💬 Modo interactivo de DataPulse IA activo.")
    while True:
        pregunta = input("\n🤖 Pregunta SQL/Natural> ").strip()
        if pregunta.lower() in ("salir", "exit", "quit"):
            log("👋 Saliendo del motor IA.")
            break
        respuesta = process_query(pregunta)
        print(respuesta)
