import subprocess
import datetime
import sys
import os
import shutil

# ============================
# Estilos para imprimir bonito
# ============================

def banner(msg):
    print("\n" + "="*62)
    print(msg)
    print("="*62 + "\n")

def step(msg):
    print(f"[•] {msg}")

def ok(msg):
    print(f"[✓] {msg}")

def warn(msg):
    print(f"[!] {msg}")

def error(msg):
    print(f"[✗] {msg}")

def run(cmd):
    return subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# ============================
# CONFIG: Solo defines Backup
# ============================

RUTA_BACKUP = r"C:\Users\chall\iBit\Gytres - ETL Cashflow - General\Backup"

# ============================
# AUTO-DETECT DEL PROYECTO
# ============================

RUTA_PROYECTO = os.path.dirname(os.path.abspath(__file__))


# ============================
# GIT PUSH + BACKUP PRO
# ============================

if __name__ == "__main__":
    banner("🔥  GIT PUSH PRO – Fénix Engine v3.0 (Auto-Detect) 🔥")

    step(f"Proyecto detectado en:\n    {RUTA_PROYECTO}")
    os.chdir(RUTA_PROYECTO)

    fecha = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    carpeta_backup = os.path.join(RUTA_BACKUP, f"Backup_{fecha}")

    mensaje = f"Auto-commit {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # ADD
    step("Añadiendo cambios al stage…")
    run("git add .")

    # STATUS
    status = run("git status --porcelain")

    if status.stdout.strip() == "":
        warn("Repo limpio. No hay nada nuevo para subir.")
    else:
        # COMMIT
        step("Creando commit elegante…")
        r_commit = run(f'git commit -m "{mensaje}"')

        if r_commit.returncode != 0:
            error("Falló el commit.")
            print(r_commit.stderr)
            sys.exit(1)

        ok("Commit generado ✔")

        # PUSH
        step("Haciendo push al remoto…")
        r_push = run("git push")

        if r_push.returncode != 0:
            error("Error subiendo al remoto")
            print(r_push.stderr)
            sys.exit(1)

        ok("Push completado ✔")

    # BACKUP
    step("Creando backup full del proyecto…")
    os.makedirs(carpeta_backup, exist_ok=True)

    try:
        shutil.copytree(
            RUTA_PROYECTO,
            os.path.join(carpeta_backup, "Proyecto"),
            dirs_exist_ok=True
        )
        ok(f"Backup guardado en:\n    {carpeta_backup}")
    except Exception as e:
        error("Error creando backup:")
        print(e)

    banner("🔥 PROCESO COMPLETADO — Git + Backup OK 🔥")
