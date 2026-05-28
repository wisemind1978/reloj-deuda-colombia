#!/usr/bin/env python3
"""Actualiza la TRM (tasa de cambio del dólar) en data.json.

Lee la TRM oficial certificada por la Superintendencia Financiera desde la API
de datos.gov.co y la escribe en data.json. Lo ejecuta la GitHub Action a diario.
Solo usa la librería estándar de Python: no requiere instalar nada.
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

# data.json vive una carpeta arriba de este script (scripts/ -> raíz del proyecto)
DATA = Path(__file__).resolve().parent.parent / "data.json"
URL = "https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciahasta%20DESC"


def main():
    # 1. Consultar la API oficial
    req = urllib.request.Request(URL, headers={"User-Agent": "reloj-deuda-colombia"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            registros = json.load(resp)
    except Exception as e:
        print(f"ERROR consultando la API de TRM: {e}", file=sys.stderr)
        sys.exit(1)

    if not registros:
        print("ERROR: la API no devolvió ningún registro de TRM", file=sys.stderr)
        sys.exit(1)

    reg = registros[0]
    trm = round(float(reg["valor"]), 2)
    y, m, d = reg["vigenciahasta"][:10].split("-")  # 'YYYY-MM-DD'
    fecha_legible = f"{d}/{m}/{y}"

    # 2. Cargar data.json
    data = json.loads(DATA.read_text(encoding="utf-8"))

    # 3. Actualizar solo los campos de la TRM + marca de tiempo de la corrida
    anterior = data["macro"].get("trm_fallback")
    data["macro"]["trm_fallback"] = trm
    data["macro"]["trm_fecha_fallback"] = fecha_legible
    hora_col = timezone(timedelta(hours=-5))
    data["meta"]["ultima_corrida_script"] = datetime.now(hora_col).isoformat(timespec="seconds")

    # 4. Guardar (ensure_ascii=False conserva acentos y ñ).
    #    Recompactamos los pares [año, valor] de las series a una sola línea
    #    para mantener data.json legible tras cada corrida del robot.
    texto = json.dumps(data, ensure_ascii=False, indent=2)
    texto = re.sub(r"\[\s*\n\s*(\d+),\s*\n\s*([\d.]+)\s*\n\s*\]", r"[\1, \2]", texto)
    DATA.write_text(texto + "\n", encoding="utf-8")

    print(f"TRM actualizada: {anterior} -> {trm}  (vigencia {fecha_legible})")


if __name__ == "__main__":
    main()
