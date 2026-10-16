import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os
from datetime import datetime, timezone, timedelta

# Configuración de página
st.set_page_config(page_title="Panel Financiero", layout="wide", page_icon="💜")

DATA_FILE = "datos_finanzas.json"

# ----------------- GESTIÓN DE DATOS -----------------
def cargar_datos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for c in data.get("costos", []):
                    c.setdefault("activo", True)
                for ing in data.get("ingresos", []):
                    ing.setdefault("activo", True)
                for inv in data.get("inversiones", []):
                    inv.setdefault("activo_inv", True)
                    inv.setdefault("precio_manual", 0.0)
                if "ingresos" not in data and "ingresos_otros" in data:
                    data["ingresos"] = [{"concepto": i["concepto"], "monto": i["monto"], "activo": True} for i in data["ingresos_otros"]]
                data.setdefault("config_visual", {"tamano_letra": "Grande (Recomendado)", "tema": "Violeta Elegante"})
                return data
        except Exception:
            pass
    return {
        "config_visual": {
            "tamano_letra": "Grande (Recomendado)",
            "tema": "Violeta Elegante"
        },
        "costos": [
            {"categoria": "Alquiler / Expensas", "monto": 250000, "activo": True},
            {"categoria": "Supermercado y Comida", "monto": 280000, "activo": True},
            {"categoria": "Obra Social / Salud", "monto": 90000, "activo": True},
            {"categoria": "Servicios (Luz, Gas, Agua, Internet)", "monto": 75000, "activo": True},
            {"categoria": "Insumos Gabinete", "monto": 45000, "activo": True}
        ],
        "ingresos": [
            {"concepto": "Sueldo Farmacia", "monto": 650000, "activo": True},
            {"concepto": "Sueldo Anual Complementario (SAC mes)", "monto": 54000, "activo": True},
            {"concepto": "Jubilación", "monto": 320000, "activo": True}
        ],
        "precio_terapia": 30000,
        "inversiones": [
            {"tipo": "Dólar Billete", "activo": "USD Ahorro", "simbolo": "USD", "cantidad": 1200, "plataforma": "Caja de seguridad", "activo_inv": True, "precio_manual": 0.0},
            {"tipo": "Acciones / CEDEARs", "activo": "Apple (AAPL)", "simbolo": "AAPL", "cantidad": 20, "plataforma": "Balanz", "activo_inv": True, "precio_manual": 0.0},
            {"tipo": "Criptomonedas", "activo": "Bitcoin", "simbolo": "BTC", "cantidad": 0.015, "plataforma": "Binance", "activo_inv": True, "precio_manual": 0.0},
            {"tipo": "Efectivo / Banco", "activo": "Caja de Ahorro Pesos", "simbolo": "ARS", "cantidad": 350000, "plataforma": "Banco", "activo_inv": True, "precio_manual": 0.0}
        ]
    }

def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

# ----------------- COTIZACIONES EN TIEMPO REAL -----------------
@st.cache_data(ttl=300)
def obtener_cotizaciones(simbolos_acciones, simbolos_cripto):
    cotiz = {
        "dolar_blue": 1545.0,
        "BTC": 82000.0,
        "ETH": 2600.0,
        "USDT": 1.0,
        "SOL": 150.0,
        "BNB": 580.0,
        "AAPL": 230.0,
        "KO": 68.0,
        "MELI": 2050.0,
        "SPY": 580.0,
        "MSFT": 420.0,
        "GOOGL": 175.0,
        "AMZN": 200.0,
        "TSLA": 250.0,
        "NVDA": 135.0,
        "YPFD": 28.0
    }
    
    # 1. Dólar Blue en vivo (DolarApi)
    try:
        r_dolar = requests.get("https://dolarapi.com/v1/dolares/blue", timeout=4)
        if r_dolar.status_code == 200:
            cotiz["dolar_blue"] = float(r_dolar.json().get("venta", cotiz["dolar_blue"]))
    except Exception:
        pass

    # 2. Criptomonedas en vivo (Binance API pública + respaldo CoinGecko)
    for cripto in set(["BTC", "ETH", "SOL", "BNB"] + list(simbolos_cripto)):
        if cripto == "USDT":
            cotiz["USDT"] = 1.0
            continue
        try:
            r_bin = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={cripto.upper()}USDT", timeout=3)
            if r_bin.status_code == 200:
                cotiz[cripto.upper()] = float(r_bin.json()["price"])
        except Exception:
            pass

    # 3. Acciones en vivo (Yahoo Finance API pública)
    headers = {"User-Agent": "Mozilla/5.0"}
    for ticker in set(simbolos_acciones):
        t_clean = ticker.upper().strip()
        if not t_clean or t_clean in ["USD", "ARS"]:
            continue
        try:
            url_yf = f"https://query1.finance.yahoo.com/v8/finance/chart/{t_clean}?interval=1d&range=1d"
            r_yf = requests.get(url_yf, headers=headers, timeout=3)
            if r_yf.status_code == 200:
                meta = r_yf.json()["chart"]["result"][0]["meta"]
                precio_vivo = float(meta.get("regularMarketPrice", 0))
                if precio_vivo > 0:
                    cotiz[t_clean] = precio_vivo
        except Exception:
            pass

    return cotiz

# ----------------- AUTENTICACIÓN -----------------
USUARIO_CORRECTO = "mama"
PASSWORD_CORRECTO = "terapias123"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center; color: #4b367c;'>💜 Ingreso a Mi Panel Financiero</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.6, 1])
    with c2:
        with st.form("login_form"):
            user = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar al Panel", use_container_width=True)
            if submit:
                if user.strip().lower() == USUARIO_CORRECTO and password == PASSWORD_CORRECTO:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
    st.stop()

# ----------------- CARGA DE DATOS Y ESTILOS DINÁMICOS -----------------
datos = cargar_datos()

# Extraer símbolos para actualizar cotizaciones en vivo
tickers_acciones = [inv.get("simbolo", "AAPL") for inv in datos.get("inversiones", []) if inv.get("tipo") == "Acciones / CEDEARs"]
tickers_cripto = [inv.get("simbolo", "BTC") for inv in datos.get("inversiones", []) if inv.get("tipo") == "Criptomonedas"]

cotizaciones = obtener_cotizaciones(tuple(tickers_acciones), tuple(tickers_cripto))
dolar_b = cotizaciones["dolar_blue"]

# Configuración visual elegida por la usuaria
cfg_vis = datos.get("config_visual", {})
mapa_fuente = {
    "Normal": "16px",
    "Grande (Recomendado)": "19px",
    "Extra Grande (Máxima Lectura)": "22px"
}
font_px = mapa_fuente.get(cfg_vis.get("tamano_letra", "Grande (Recomendado)"), "19px")

mapa_tema = {
    "Violeta Elegante": ("#2e1e5b", "#4b367c", "#9b59b6"),
    "Azul Real": ("#0f2b48", "#1f4e78", "#3498db"),
    "Verde Esmeralda": ("#11382a", "#1e6b52", "#2ecc71")
}
color_osc, color_med, color_borde = mapa_tema.get(cfg_vis.get("tema", "Violeta Elegante"), ("#2e1e5b",
