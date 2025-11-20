# src/bridge/scheduler.py
import sys
from pathlib import Path

# === FIX DE RUTA GLOBAL ===
# Agrega la carpeta raíz del proyecto (C:\Proyectos\DataPulse\src)
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app_test import main as run_datapulse
from core.config import SCHEDULE_INTERVAL_MINUTES
from core.logger import log
import time
from datetime import datetime


def start_scheduler():
    """Ejecuta DataPulse de manera periódica según el intervalo definido."""
    log(f"⏱️ Scheduler iniciado. Intervalo: {SCHEDULE_INTERVAL_MINUTES} minutos.")

    while True:
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log(f"🚀 Ejecución programada iniciada a las {start_time}")

        try:
            run_datapulse()
        except Exception as e:
            log(f"❌ Error en ejecución programada: {e}")

        log(f"🕓 Próxima ejecución en {SCHEDULE_INTERVAL_MINUTES} minutos...\n")
        time.sleep(SCHEDULE_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    start_scheduler()
