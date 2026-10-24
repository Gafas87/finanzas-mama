"""Datos de la app y almacenamiento (archivo local o repositorio privado de GitHub)."""

import base64
import hashlib
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import requests

NOMBRE_ARCHIVO = "datos_finanzas.json"


class DatosInvalidos(Exception):
    pass


class ErrorAlmacen(Exception):
    pass


class ConflictoDeVersion(Exception):
    pass


def nuevo_id():
    return uuid.uuid4().hex[:10]


def en_streamlit_cloud():
    return os.path.exists("/mount/src")


def datos_vacios():
    return {
        "version": 2,
        "costos": [], "ingresos": [], "inversiones": [],
        "categorias_costos": ["Vivienda", "Alimentación", "Transporte", "Salud", "Otros"],
        "categorias_ingresos": ["Trabajo", "Otros ingresos"],
        "acciones_guardadas": ["AAPL (Apple)", "MSFT (Microsoft)", "GOOGL (Google)", "AMZN (Amazon)",
                               "TSLA (Tesla)", "KO (Coca-Cola)"],
        "criptos_guardadas": ["BTC (Bitcoin)", "ETH (Ethereum)", "SOL (Solana)", "USDT (Tether)"],
        "precio_terapia": 0,
        "cotizaciones_guardadas": {},
    }


def desde_texto(texto):
    try:
        data = json.loads(texto)
    except (TypeError, ValueError) as e:
        raise DatosInvalidos(f"El archivo no es un JSON válido: {e}")
    if not isinstance(data, dict):
        raise DatosInvalidos("El archivo no tiene el formato esperado.")
    base = datos_vacios()
    for k, v in base.items():
        data.setdefault(k, v)
    for k in ("costos", "ingresos", "inversiones", "categorias_costos", "categorias_ingresos",
              "acciones_guardadas", "criptos_guardadas"):
        if not isinstance(data[k], list):
            raise DatosInvalidos(f"El campo «{k}» debe ser una lista.")
    for k in ("costos", "ingresos", "inversiones"):
        for item in data[k]:
            if not isinstance(item, dict):
                raise DatosInvalidos(f"Hay un elemento inválido en «{k}».")
            item.setdefault("id", nuevo_id())
    if not isinstance(data["cotizaciones_guardadas"], dict):
        data["cotizaciones_guardadas"] = {}
    return data, []


def a_texto(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


def _token(texto):
    return hashlib.sha1(texto.encode("utf-8")).hexdigest()


class AlmacenLocal:
    def __init__(self, carpeta):
        self.carpeta = Path(carpeta)
        self.archivo = self.carpeta / NOMBRE_ARCHIVO
        self.dir_copias = self.carpeta / "copias"

    def leer(self):
        if not self.archivo.exists():
            return None, None
        texto = self.archivo.read_text(encoding="utf-8")
        return texto, _token(texto)

    def guardar(self, texto, token):
        try:
            actual, tok_actual = self.leer()
            if actual is not None and token is not None and tok_actual != token:
                raise ConflictoDeVersion()
            if actual is not None:
                self.dir_copias.mkdir(parents=True, exist_ok=True)
                sello = datetime.now().strftime("%Y%m%d-%H%M%S")
                (self.dir_copias / f"copia_{sello}.json").write_text(actual, encoding="utf-8")
                for vieja in self.copias()[30:]:
                    vieja.unlink(missing_ok=True)
            tmp = self.archivo.with_suffix(".tmp")
            tmp.write_text(texto, encoding="utf-8")
            tmp.replace(self.archivo)
            return _token(texto)
        except OSError as e:
            raise ErrorAlmacen(f"No se pudo escribir el archivo ({e}).")

    def copias(self):
        if not self.dir_copias.exists():
            return []
        return sorted(self.dir_copias.glob("copia_*.json"), reverse=True)


class AlmacenGitHub:
    def __init__(self, cfg):
        self.url = f"https://api.github.com/repos/{cfg['repo']}/contents/{cfg.get('path', NOMBRE_ARCHIVO)}"
        self.rama = cfg.get("branch", "main")
        self.headers = {"Authorization": f"Bearer {cfg['token']}", "Accept": "application/vnd.github+json"}

    def leer(self):
        try:
            r = requests.get(self.url, headers=self.headers, params={"ref": self.rama}, timeout=15)
        except requests.RequestException as e:
            raise ErrorAlmacen(f"No hay conexión con GitHub ({e}).")
        if r.status_code == 404:
            return None, None
        if r.status_code != 200:
            raise ErrorAlmacen(f"GitHub respondió {r.status_code}. Revisá el token y el repositorio.")
        j = r.json()
        return base64.b64decode(j["content"]).decode("utf-8"), j["sha"]

    def guardar(self, texto, token):
        body = {"message": "Actualización de datos", "branch": self.rama,
                "content": base64.b64encode(texto.encode("utf-8")).decode("ascii")}
        if token:
            body["sha"] = token
        try:
            r = requests.put(self.url, headers=self.headers, json=body, timeout=20)
        except requests.RequestException as e:
            raise ErrorAlmacen(f"No hay conexión con GitHub ({e}).")
        if r.status_code in (409, 422):
            raise ConflictoDeVersion()
        if r.status_code not in (200, 201):
            raise ErrorAlmacen(f"GitHub respondió {r.status_code} al guardar.")
        return r.json()["content"]["sha"]


def crear_almacen(secretos, carpeta):
    g = secretos.get("github")
    if g and g.get("token") and g.get("repo"):
        return AlmacenGitHub(g)
    return AlmacenLocal(carpeta)
