# src/core/logger.py
import logging
from datetime import datetime
from pathlib import Path
from src.core.config import LOG_PATH

# === Configurar ruta del log ===
LOG_PATH.mkdir(parents=True, exist_ok=True)
log_file = LOG_PATH / f"{datetime.now().strftime('%Y%m%d')}_datapulse.log"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def log(message: str):
    """Registra un mensaje en consola y archivo."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    logging.info(message)
