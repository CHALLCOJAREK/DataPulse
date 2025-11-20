# src/ia/guardrails.py
import re
import sqlite3
from pathlib import Path
from src.core.logger import log
from src.core.config import DB_PATH

# === CONFIGURACIÓN BASE ===
SAFE_SQL_COMMANDS = {"SELECT", "WITH"}  # Solo lectura
ALLOWED_TABLE_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")
ALLOWED_SQL_PATTERN = re.compile(
    r"^(SELECT|WITH)\s+.*?(FROM|AS)\s+.+", re.IGNORECASE | re.DOTALL
)


def sanitize_sql_query(query: str) -> str:
    """
    Limpia una consulta SQL generada por IA o usuario.
    Elimina comandos peligrosos y normaliza formato.
    """
    if not query:
        return ""

    # Normaliza espacios
    q = re.sub(r"\s+", " ", query.strip())

    # Rechazar comandos no seguros
    first_token = q.split(" ")[0].upper()
    if first_token not in SAFE_SQL_COMMANDS:
        raise ValueError(f"Comando SQL no permitido: {first_token}")

    # Bloquear operaciones destructivas
    banned = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    if any(cmd in q.upper() for cmd in banned):
        raise ValueError("Consulta contiene comandos no permitidos")

    # Validar estructura SQL general
    if not ALLOWED_SQL_PATTERN.match(q):
        raise ValueError("Consulta SQL no válida o incompleta")

    return q


def validate_table_name(table: str) -> str:
    """
    Asegura que el nombre de tabla cumpla formato permitido.
    Evita inyecciones o rutas externas.
    """
    if not table or not ALLOWED_TABLE_PATTERN.match(table):
        raise ValueError(f"Nombre de tabla inválido: {table}")
    return table.lower()


def safe_execute_sql(query: str) -> list[tuple]:
    """
    Ejecuta de forma segura una consulta SQL validada.
    Usa sólo lectura sobre la base SQLite de DataPulse.
    """
    try:
        query = sanitize_sql_query(query)
        log(f"🧩 Ejecutando consulta validada: {query}")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()

        log(f"✅ Consulta ejecutada correctamente: {len(rows)} filas obtenidas.")
        return rows

    except Exception as e:
        log(f"⚠️ Error en ejecución SQL segura: {e}")
        return []


def detect_suspicious_patterns(text: str) -> bool:
    """
    Detecta patrones sospechosos (intentos de inyección, palabras clave prohibidas, etc.)
    Retorna True si se detecta algo riesgoso.
    """
    risky = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "ATTACH", "--", ";", "/*", "*/", "xp_"]
    pattern = re.compile("|".join(risky), re.IGNORECASE)
    return bool(pattern.search(text or ""))


# === TEST RÁPIDO ===
if __name__ == "__main__":
    log("🔍 Test rápido de guardrails...")

    tests = [
        "SELECT * FROM b_bcp_soles;",
        "DELETE FROM users;",
        "DROP TABLE accounts;",
        "WITH temp AS (SELECT 1) SELECT * FROM temp;",
    ]

    for t in tests:
        try:
            print(f"\n➡️ {t}")
            clean = sanitize_sql_query(t)
            print(f"   ✅ Aprobada: {clean}")
        except Exception as e:
            print(f"   ❌ Bloqueada: {e}")
