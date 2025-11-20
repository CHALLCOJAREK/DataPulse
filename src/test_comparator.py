# src/test_comparator.py
from bridge.reader import leer_excel_completo
from bridge.comparator import detect_changes

data = leer_excel_completo()
resumen = detect_changes(data)
print("\n📊 RESULTADO DE COMPARACIÓN:")
for hoja, cambios in resumen.items():
    print(f" - {hoja}: {cambios}")
