"""Cotizaciones en vivo (dólar blue, criptomonedas y acciones) con respaldo guardado."""

from datetime import datetime, timedelta, timezone

import requests

TIMEOUT = 8
REFRESCO_GUARDADA = timedelta(hours=6)


def _ahora():
    return datetime.now(timezone.utc).isoformat()


def _get(url, **kw):
    r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0"}, **kw)
    r.raise_for_status()
    return r.json()


def _dolar():
    for url in ("https://dolarapi.com/v1/dolares/blue", "https://api.bluelytics.com.ar/v2/latest"):
        try:
            d = _get(url)
            valor = d.get("venta") or d.get("blue", {}).get("value_sell")
            if valor:
                return {"valor": float(valor), "fecha": _ahora()}
        except Exception:
            continue
    return None


def _cripto(sim):
    try:
        d = _get("https://api.binance.com/api/v3/ticker/price", params={"symbol": f"{sim}USDT"})
        return {"valor": float(d["price"]), "fecha": _ahora()}
    except Exception:
        return None


def _accion(sim):
    try:
        d = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sim}", params={"interval": "1d", "range": "1d"})
        return {"valor": float(d["chart"]["result"][0]["meta"]["regularMarketPrice"]), "fecha": _ahora()}
    except Exception:
        return None


def obtener(criptos, acciones):
    cri = {s: c for s in criptos if (c := _cripto(s))}
    acc = {s: c for s in acciones if (c := _accion(s))}
    if "BTC" not in cri and (b := _cripto("BTC")):
        cri["BTC"] = b
    return {"dolar": _dolar(), "cripto": cri, "acciones": acc}


def _mezclar(vivo, guardado):
    out = {}
    for s, v in (guardado or {}).items():
        out[s] = {**v, "estado": "guardada"}
    for s, v in (vivo or {}).items():
        out[s] = {**v, "estado": "en_vivo"}
    return out


def combinar(vivas, guardadas):
    guardadas = guardadas or {}
    if vivas.get("dolar"):
        dolar = {**vivas["dolar"], "estado": "en_vivo"}
    elif guardadas.get("dolar"):
        dolar = {**guardadas["dolar"], "estado": "guardada"}
    else:
        dolar = {"valor": None, "fecha": None, "estado": "sin_dato"}
    return {"dolar": dolar,
            "cripto": _mezclar(vivas.get("cripto"), guardadas.get("cripto")),
            "acciones": _mezclar(vivas.get("acciones"), guardadas.get("acciones"))}


def _vieja(fecha):
    try:
        return datetime.now(timezone.utc) - datetime.fromisoformat(fecha) > REFRESCO_GUARDADA
    except (TypeError, ValueError):
        return True


def actualizar_guardadas(guardadas, vivas):
    """Guarda cotizaciones nuevas o con más de 6 horas, para no escribir en cada recarga."""
    nuevas = {"dolar": (guardadas or {}).get("dolar"),
              "cripto": dict((guardadas or {}).get("cripto") or {}),
              "acciones": dict((guardadas or {}).get("acciones") or {})}
    cambio = False
    if vivas.get("dolar") and (not nuevas["dolar"] or _vieja(nuevas["dolar"].get("fecha"))):
        nuevas["dolar"], cambio = vivas["dolar"], True
    for g in ("cripto", "acciones"):
        for s, v in (vivas.get(g) or {}).items():
            if s not in nuevas[g] or _vieja(nuevas[g][s].get("fecha")):
                nuevas[g][s], cambio = v, True
    return nuevas, cambio
