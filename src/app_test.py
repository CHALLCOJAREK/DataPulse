# src/app_test.py
# ==========================================================
# DataPulse v4.0 – Ejecución Segura (Lectura 1:1 + Respaldo)
# Sin Consolidator
# ==========================================================
import sys
from pathlib import Path

# === FIX DE RUTA GLOBAL ===
sys.path.append(str(Path(__file__).resolve().parents[1]))

from bridge.reader import leer_excel_completo
from bridge.comparator import detect_changes
from bridge.updater import sync_excel_to_db
from core.db_utils import init_database_from_reader
from core.logger import log
from core.backup import create_backup, purge_old_backups


def main():
    """Ejecución controlada de DataPulse (modo TEST SEGURO)."""
    log("🚀 Iniciando ejecución completa de DataPulse (modo TEST SEGURO)")

    try:
        # === 1. LECTURA EXACTA DE EXCEL ===
        log("📘 Leyendo hojas desde el archivo Excel principal...")
        data = leer_excel_completo()
        if not data:
            log("⚠️ No se encontraron datos válidos en el Excel. Proceso detenido.")
            return

        # === 2. VALIDACIÓN E INICIALIZACIÓN DE BASE ===
        log("🧱 Verificando estructura inicial de la base de datos...")
        init_database_from_reader(data)

        # === 3. COMPARACIÓN CON LA BASE EXISTENTE ===
        log("🔍 Analizando diferencias entre Excel y base de datos...")
        change_summary = detect_changes(data)
        if not change_summary:
            log("✅ No se detectaron cambios. Base ya actualizada.")
            return

        # === 4. RESPALDO PREVIO A LA SINCRONIZACIÓN ===
        log("💾 Creando respaldo antes de aplicar cambios...")
        backup_file = create_backup()
        purge_old_backups(limit=5)

        if backup_file:
            log(f"📦 Respaldo generado correctamente: {backup_file.name}")
        else:
            log("⚠️ No se generó respaldo (posible base vacía o error menor).")

        # === 5. APLICAR SINCRONIZACIÓN EXCEL → DB ===
        log("🧩 Iniciando sincronización hoja por hoja (1:1 estructura Excel)...")
        sync_excel_to_db()
        log("✅ Sincronización completada correctamente. DataPulse está actualizado.")

    except KeyboardInterrupt:
        log("🛑 Ejecución interrumpida manualmente por el usuario.")
    except Exception as e:
        log(f"💥 Error crítico durante la ejecución de DataPulse: {e}")
    finally:
        log("🏁 Proceso DataPulse finalizado (modo TEST SEGURO).\n")


if __name__ == "__main__":
    main()
