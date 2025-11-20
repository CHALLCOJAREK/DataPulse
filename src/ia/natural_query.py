# ==========================================================
# NATURAL QUERY – DataPulse + Gemini (Híbrido)
# Conversor de lenguaje natural a SQL con respuesta IA
# ==========================================================
import sys
from pathlib import Path

# === FIX DE RUTA GLOBAL ===
sys.path.append(str(Path(__file__).resolve().parents[2]))

import google.generativeai as genai
from datetime import datetime
from src.core.logger import log
from src.core.config import DB_PATH, GEMINI_API_KEY
from src.ia.guardrails import sanitize_sql_query, safe_execute_sql  # 🔒 Protección

# ==========================================================
# CONFIGURACIÓN GEMINI
# ==========================================================
genai.configure(api_key=GEMINI_API_KEY or "")

FALLBACK_MODELS = [
    "models/gemini-1.5-pro",
    "models/gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "models/gemini-pro",
]


def pick_gemini_model() -> str:
    """Detecta el modelo Gemini disponible (como en el anticaptcha)."""
    try:
        models = list(genai.list_models())
        for m in models:
            name = getattr(m, "name", "")
            methods = getattr(m, "supported_generation_methods", [])
            if "generateContent" in methods and any(k in name.lower() for k in ["1.5", "pro", "flash"]):
                return name
    except Exception:
        pass
    return FALLBACK_MODELS[1]  # por defecto flash


# ==========================================================
# TABLA → ALIAS AUTOMÁTICO
# ==========================================================
ALIASES = {
    "bcp": "b_bcp_soles",
    "interbank": "b_interbank_soles",
    "bbva": "b_bbva_soles",
    "nacion": "b_banco_nacion",
    "finanzas": "c_finanzas_soles",
    "arequipa": "c_arequipa_soles",
    "operativa": "caja_operativa",
    "ruben": "ruben_bustamante",
    "walter": "walter_a",
    "juber": "juber_monteza",
    "willian": "willian_leon",
    "juan": "juan_tarifa",
    "miguel": "miguel_solis",
    "anthony": "anthony_huamani",
    "nelson": "nelson_quispe",
    "ronald": "ronald_guizado",
}


# ==========================================================
# GENERADOR DE CONSULTA SQL
# ==========================================================
def generate_sql(question: str) -> str | None:
    """Convierte texto natural en una consulta SQL básica y segura."""
    q = question.lower().strip()
    table = None
    for alias, real in ALIASES.items():
        if alias in q:
            table = real
            break

    if not table:
        log("⚠️ No se detectó una tabla válida en la consulta.")
        return None

    # Detectar filtro de mes
    month_map = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "setiembre": "09", "septiembre": "09", "octubre": "10",
        "noviembre": "11", "diciembre": "12"
    }

    month_filter = ""
    for m_name, m_num in month_map.items():
        if m_name in q:
            month_filter = f" WHERE strftime('%m', fecha) = '{m_num}'"
            break

    sql = f"SELECT SUM(monto) AS resultado FROM '{table}'{month_filter};"
    try:
        sql = sanitize_sql_query(sql)  # 🔒 Valida estructura y comando
    except Exception as e:
        log(f"⚠️ SQL no segura detectada: {e}")
        return None

    log(f"🧠 SQL generado: {sql}")
    return sql


# ==========================================================
# EJECUCIÓN DE CONSULTA (MODO SEGURO)
# ==========================================================
def run_sql(sql: str) -> float | None:
    """Ejecuta una consulta validada en modo lectura."""
    try:
        rows = safe_execute_sql(sql)
        if not rows or not rows[0][0]:
            return None
        return float(rows[0][0])
    except Exception as e:
        log(f"⚠️ Error ejecutando SQL: {e}")
        return None


# ==========================================================
# INTERPRETACIÓN NATURAL (GEMINI + fallback)
# ==========================================================
def natural_answer(question: str, sql: str, result: float) -> str:
    """Genera respuesta natural con Gemini, o fallback manual si falla."""
    model_name = pick_gemini_model()
    try:
        model = genai.GenerativeModel(model_name)
        prompt = (
            f"Eres un analista financiero. "
            f"La consulta fue: '{question}'. "
            f"El SQL ejecutado fue: {sql}. "
            f"El resultado numérico fue: {result:.2f}. "
            f"Responde con una frase clara y profesional en español, "
            f"indicando el total o resumen correspondiente. No inventes valores."
        )
        resp = model.generate_content(prompt)
        if resp and resp.text:
            return resp.text.strip()

        raise ValueError("Sin texto devuelto por Gemini")

    except Exception as e:
        log(f"⚠️ Gemini no disponible o falló ({e}). Generando respuesta local.")
        # === fallback manual ===
        base = question.lower()
        resumen = ""
        if "bcp" in base:
            resumen = "Banco de Crédito del Perú (BCP)"
        elif "interbank" in base:
            resumen = "Interbank"
        elif "bbva" in base:
            resumen = "BBVA"
        elif "nacion" in base:
            resumen = "Banco de la Nación"
        elif "finanzas" in base:
            resumen = "cuenta de finanzas"
        else:
            resumen = "la cuenta consultada"

        return f"El total registrado en {resumen} es de S/. {result:,.2f} según los movimientos analizados."


# ==========================================================
# MODO INTERACTIVO
# ==========================================================
def main():
    log("🗣️ Modo interactivo de Natural Query (Gemini – Híbrido) activo.\n")

    while True:
        q = input("🤖 Pregunta (natural o técnica) > ").strip()
        if not q:
            continue
        if q.lower() in ["salir", "exit", "quit"]:
            break

        log(f"🧠 Pregunta (normalizada): {q}")
        sql = generate_sql(q)
        if not sql:
            print("⚠️ No se pudo generar consulta válida.")
            continue

        result = run_sql(sql)
        if result is None:
            print("⚠️ No se encontró ningún resultado.")
            continue

        log(f"✅ Consulta ejecutada correctamente: 1 filas obtenidas.")
        answer = natural_answer(q, sql, result)

        print("\n---")
        print(f"SQL: {sql}")
        print(f"Respuesta IA:\n{answer}\n")


if __name__ == "__main__":
    main()
