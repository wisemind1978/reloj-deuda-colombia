#!/usr/bin/env python3
"""Actualiza la deuda del Gobierno Nacional Central en data.json.

Descarga el Excel oficial "Perfil de Deuda Bruta GNC" que publica mensualmente
el IRC (Investors Relations Colombia, del Ministerio de Hacienda) y extrae el
saldo de deuda total/interna/externa y su % del PIB. Lo ejecuta la GitHub Action.

Requiere: xlrd (se instala en el workflow).
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import xlrd

DATA = Path(__file__).resolve().parent.parent / "data.json"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
URL_BASE = "https://www.irc.gov.co/documents/d/guest/perfil-deuda-bruta-gnc-{mes}-{anio}"
OLE_MAGIC = b"\xd0\xcf\x11\xe0"  # los .xls (formato Excel 97-2003) empiezan así


def mes_calendario_atras(anio, mes, n):
    """Retrocede n meses desde (anio, mes)."""
    idx = (anio * 12 + (mes - 1)) - n
    return idx // 12, idx % 12 + 1


def descargar_excel_reciente():
    """Prueba el mes actual y hasta 4 atrás; devuelve (bytes, anio, mes) del más reciente."""
    hoy = datetime.now()
    for atras in range(5):
        anio, mes = mes_calendario_atras(hoy.year, hoy.month, atras)
        url = URL_BASE.format(mes=MESES[mes - 1], anio=anio)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "reloj-deuda-colombia"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                contenido = resp.read()
            if contenido[:4] == OLE_MAGIC:
                return contenido, anio, mes
        except Exception:
            continue
    return None, None, None


def main():
    contenido, anio, mes = descargar_excel_reciente()
    if contenido is None:
        print("ERROR: no se encontró el Excel del IRC en los últimos 5 meses", file=sys.stderr)
        sys.exit(1)

    wb = xlrd.open_workbook(file_contents=contenido)
    sh = wb.sheet_by_name("Resumen-Total")

    # Celdas fijas de la hoja Resumen-Total (formato estable del IRC):
    #   fila 14: saldos en COP millones  -> col 2 interna, col 4 externa, col 6 total
    #   fila 16: % del PIB               -> col 6 total
    #   fila 8 : fecha de corte (serial Excel) en col 2
    interna_m = sh.cell_value(14, 2)
    externa_m = sh.cell_value(14, 4)
    total_m = sh.cell_value(14, 6)
    pib_total = sh.cell_value(16, 6)
    fecha_serial = sh.cell_value(8, 2)

    # Validación de plausibilidad (evita escribir basura si cambia el formato)
    if not (500_000_000 < total_m < 5_000_000_000):
        print(f"ERROR: total de deuda fuera de rango ({total_m} M COP) — ¿cambió el formato?", file=sys.stderr)
        sys.exit(1)
    if not (0.3 < pib_total < 1.2):
        print(f"ERROR: % PIB fuera de rango ({pib_total}) — ¿cambió el formato?", file=sys.stderr)
        sys.exit(1)

    total_cop = round(total_m * 1e6)
    interna_cop = round(interna_m * 1e6)
    externa_cop = round(externa_m * 1e6)
    pib_pct = round(pib_total * 100, 1)
    fecha = datetime(1899, 12, 30) + timedelta(days=int(fecha_serial))
    fecha_iso = fecha.strftime("%Y-%m-%d")

    # Cargar y actualizar data.json
    data = json.loads(DATA.read_text(encoding="utf-8"))
    anterior = data["deuda"]["total_cop"]

    data["deuda"]["total_cop"] = total_cop
    data["deuda"]["interna_cop"] = interna_cop
    data["deuda"]["externa_cop"] = externa_cop
    data["deuda"]["fecha_corte"] = fecha_iso
    data["deuda"]["fuente"] = f"IRC/Minhacienda · Perfil Deuda Bruta GNC {MESES[mes - 1]} {anio}"

    data["macro"]["deuda_pib_pct"] = pib_pct
    data["meta"]["ultima_actualizacion_oficial"] = fecha_iso
    data["meta"]["fuente_deuda"] = f"IRC · Perfil Deuda Bruta GNC, corte {fecha_iso}"
    data["meta"]["ultima_corrida_script"] = datetime.now().astimezone().isoformat(timespec="seconds")

    # Contexto: incremento bajo el gobierno actual (desde ago-2022)
    ago2022 = data["contexto_gobierno"]["deuda_ago_2022_cop"]
    data["contexto_gobierno"]["deuda_actual_cop"] = total_cop
    data["contexto_gobierno"]["incremento_cop"] = total_cop - ago2022
    data["contexto_gobierno"]["incremento_pct"] = round((total_cop - ago2022) / ago2022 * 100)

    # Serie deuda/PIB: actualizar el punto del año de corte con el dato oficial
    serie = data["serie_deuda_pib"]["datos"]
    for par in serie:
        if par[0] == fecha.year:
            par[1] = pib_pct
            break
    else:
        serie.append([fecha.year, pib_pct])

    # Guardar manteniendo las series compactas (una línea por par)
    texto = json.dumps(data, ensure_ascii=False, indent=2)
    texto = re.sub(r"\[\s*\n\s*(\d+),\s*\n\s*([\d.]+)\s*\n\s*\]", r"[\1, \2]", texto)
    DATA.write_text(texto + "\n", encoding="utf-8")

    print(f"Deuda actualizada ({MESES[mes - 1]} {anio}, corte {fecha_iso}):")
    print(f"  total: {anterior} -> {total_cop} COP  ({pib_pct}% PIB)")
    print(f"  interna: {interna_cop} · externa: {externa_cop}")


if __name__ == "__main__":
    main()
