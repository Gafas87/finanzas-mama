"""Formato y lectura de montos (estilo argentino: 1.234,56)."""

import re


class MontoInvalido(ValueError):
    pass


def normalizar(valor):
    v = round(float(valor), 8)
    return int(v) if v == int(v) else v


def _miles(entero: str) -> str:
    return f"{int(entero):,}".replace(",", ".")


def fmt_num(valor, decimales=2):
    if valor is None:
        return "—"
    texto = f"{abs(float(valor)):,.{decimales}f}"
    texto = texto.replace(",", "#").replace(".", ",").replace("#", ".")
    return ("-" if float(valor) < 0 and float(texto.replace(".", "").replace(",", ".")) != 0 else "") + texto


def fmt_ars(valor):
    if valor is None:
        return "—"
    return f"$ {fmt_num(valor, 0)}"


def fmt_usd(valor, decimales=2):
    if valor is None:
        return "—"
    return f"US$ {fmt_num(valor, decimales)}"


def fmt_editable(valor):
    """Texto para las casillas: 1500 -> '1.500', 0.25 -> '0,25'."""
    v = normalizar(valor or 0)
    if isinstance(v, int):
        return fmt_num(v, 0)
    texto = f"{v:.8f}".rstrip("0")
    entero, dec = texto.split(".")
    return f"{_miles(entero)},{dec}"


_MILES = re.compile(r"^\d{1,3}(\.\d{3})+$")


def parse_monto(texto, permitir_cero=True):
    s = str(texto or "").replace("$", "").replace(" ", "").strip()
    if not s:
        raise MontoInvalido("Escribí un monto.")
    if s.startswith("-"):
        raise MontoInvalido("El monto no puede ser negativo.")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "." in s and _MILES.match(s):
        s = s.replace(".", "")
    try:
        valor = float(s)
    except ValueError:
        raise MontoInvalido("Ese monto no se entiende. Usá solo números, por ejemplo 25.000 o 0,25.")
    if valor != valor or valor in (float("inf"), float("-inf")):
        raise MontoInvalido("Ese monto no es válido.")
    if valor == 0 and not permitir_cero:
        raise MontoInvalido("El monto debe ser mayor que cero.")
    return valor
