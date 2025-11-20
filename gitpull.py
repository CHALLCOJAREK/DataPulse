import subprocess
import os
import sys

# ============================
# Estilos elegantes
# ============================

def banner(msg):
    print("\n" + "="*60)
    print(msg)
    print("="*60 + "\n")

def step(msg): print(f"[•] {msg}")
def ok(msg): print(f"[✓] {msg}")
def warn(msg): print(f"[!] {msg}")
def error(msg): print(f"[✗] {msg}")

def run(cmd):
    return subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# ============================
#  GIT PULL – Fénix Engine
# ============================

if __name__ == "__main__":
    banner("🔥  GIT PULL PRO – Fénix Engine v1.1 (Pull primero) 🔥")

    # Detectamos dónde está el script
    REPO_PATH = os.path.dirname(os.path.abspath(__file__))
    os.chdir(REPO_PATH)

    step(f"Proyecto detectado en:\n     {REPO_PATH}")

    # ============================
    # PRIMERO: PULL
    # ============================
    step("Buscando cambios en el remoto…")
    r = run("git pull")

    if r.returncode == 0:
        output = r.stdout.strip()

        if "Already up to date" in output:
            warn("Estás al día. No hay cambios que bajar.")
        else:
            ok("Cambios descargados con éxito ✔")
            print("\n" + output)
    else:
        error("Error al ejecutar git pull:")
        print(r.stderr)

    banner("🔥 PROCESO FINALIZADO — Pull completo 🔥")
