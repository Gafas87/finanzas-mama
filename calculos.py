"""Cálculos de presupuesto y patrimonio."""

import math

TIPOS_INVERSION = ["Dólar Billete", "Pesos ARS", "Acciones", "Criptomonedas", "Otros"]


def incluidos(items):
    return [i for i in items if i.get("activo", True)]


def _total(items):
    return sum(float(i.get("monto", 0) or 0) for i in incluidos(items))


def subtotal_grupo(items, grupo):
    return _total([i for i in items if i.get("grupo") == grupo])


def en_usd(valor, dolar):
    return valor / dolar if dolar else None


def resumen_mensual(costos, ingresos):
    c, i = _total(costos), _total(ingresos)
    return {"costos": c, "ingresos": i, "saldo": i - c,
            "n_costos": len(incluidos(costos)), "n_ingresos": len(incluidos(ingresos))}


def sesiones_necesarias(costos, ingresos, precio):
    faltante = max(costos - ingresos, 0.0)
    por_mes = math.ceil(faltante / precio - 1e-9) if (faltante > 0 and precio) else 0
    return {"faltante": faltante, "por_mes": por_mes,
            "por_semana": por_mes * 12 / 52, "por_anio": por_mes * 12}


def valuar_inversion(inv, cotiz):
    cant = float(inv.get("cantidad", 0) or 0)
    tipo = inv.get("tipo")
    dolar = (cotiz.get("dolar") or {}).get("valor")
    precio_usd = None
    if tipo == "Dólar Billete":
        ars = cant * dolar if dolar else None
        precio_usd = 1.0
    elif tipo in ("Criptomonedas", "Acciones"):
        grupo = cotiz["cripto"] if tipo == "Criptomonedas" else cotiz["acciones"]
        precio_usd = (grupo.get(inv.get("simbolo")) or {}).get("valor")
        ars = cant * precio_usd * dolar if (precio_usd and dolar) else None
    else:
        ars = cant
    return {"valor_ars": ars, "precio_usd": precio_usd}


def patrimonio(inversiones, cotiz):
    ars, sin_valor = 0.0, []
    for inv in inversiones:
        if not inv.get("activo_inv", True):
            continue
        v = valuar_inversion(inv, cotiz)["valor_ars"]
        if v is None:
            sin_valor.append(inv)
        else:
            ars += v
    dolar = (cotiz.get("dolar") or {}).get("valor")
    return {"ars": ars, "usd": en_usd(ars, dolar), "sin_valor": sin_valor}
