import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import requests
import json
import os
from datetime import datetime, timezone, timedelta

st.set_page_config(
    page_title="Jardín Financiero",
    layout="wide",
    page_icon="🌿"
)

DATA_FILE = "datos_finanzas.json"

# Paleta de colores pasteles mate bien diferenciados para que cada porción contraste
PALETA_PASTEL = [
    "#9B89B3",  # Lila ciruela pastel
    "#F6A682",  # Coral durazno pastel
    "#76C893",  # Verde menta vivo pastel
    "#72B0E8",  # Azul cielo pastel
    "#F4D06F",  # Amarillo cálido pastel
    "#E58F9E",  # Rosa antiguo pastel
    "#64C2C7",  # Turquesa pastel
    "#C3A6A0",  # Visón / Taupe suave
    "#A3C9A8",  # Verde salvia pastel
    "#D99B66",  # Terracota suave
    "#8E9AAF",  # Azul pizarra pastel
    "#E2AFCF"   # Orquídea pastel
]


# ----------------- NAVEGACIÓN CON FLECHAS DEL TECLADO -----------------
def activar_navegacion_flechas():
    js_code = """
    <script>
    const doc = window.parent.document;
    if (!doc.flechasNavegacionActivas) {
        doc.addEventListener('keydown', function(e) {
            const active = doc.activeElement;
            if (!active || active.tagName !== 'INPUT') return;

            if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                const inputs = Array.from(
                    doc.querySelectorAll(
                        'input:not([disabled]):not([type="hidden"]):not([type="checkbox"])'
                    )
                ).filter(el => el.offsetParent !== null);

                const idx = inputs.indexOf(active);
                if (idx !== -1) {
                    e.preventDefault();
                    e.stopPropagation();
                    const nextIdx = e.key === 'ArrowDown' ? idx + 1 : idx - 1;
                    if (nextIdx >= 0 && nextIdx < inputs.length) {
                        inputs[nextIdx].focus();
                        if (inputs[nextIdx].select) {
                            inputs[nextIdx].select();
                        }
                    }
                }
            }
        }, true);
        doc.flechasNavegacionActivas = true;
    }
    </script>
    """
    components.html(js_code, height=0, width=0)


# ----------------- FUNCIÓN GRÁFICO DE TORTA 2D CON FLECHAS EXTERNAS -----------------
def crear_torta_2d(df, col_valores, col_nombres):
    valores = df[col_valores].tolist()
    nombres = df[col_nombres].tolist()
    total = sum(valores) if sum(valores) > 0 else 1.0
    n = len(valores)

    colores = [PALETA_PASTEL[i % len(PALETA_PASTEL)] for i in range(n)]

    # Si la porción es menor al 9%, saca el texto afuera con línea guía para que no se achique
    posiciones = [
        "outside" if (v / total) < 0.09 else "inside"
        for v in valores
    ]

    fig = go.Figure(data=[go.Pie(
        labels=nombres,
        values=valores,
        hole=0.38,
        sort=True,
        direction="clockwise",
        textposition=posiciones,
        textinfo="label+percent",
        insidetextorientation="horizontal",
        pull=[0.015] * n,
        automargin=True,
        textfont=dict(
            size=15,
            color="#1F2937",
            family="Arial, sans-serif"
        ),
        insidetextfont=dict(
            size=15,
            color="#1F2937",
            family="Arial, sans-serif"
        ),
        outsidetextfont=dict(
            size=15,
            color="#1F2937",
            family="Arial, sans-serif"
        ),
        marker=dict(
            colors=colores,
            line=dict(color="#FFFFFF", width=2.5)
        ),
        showlegend=False
    )])

    # uniformtext con mode='show' garantiza que TODAS las letras tengan exactamente el mismo tamaño
    fig.update_layout(
        uniformtext=dict(minsize=15, mode="show"),
        height=450,
        margin=dict(t=45, b=45, l=45, r=45),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def formatear_cant(valor):
    try:
        num = float(valor)
        if num.is_integer():
            return str(int(num))
        return f"{num:.6f}".rstrip("0").rstrip(".")
    except Exception:
        return str(valor)


def clasificar_costo_existente(nombre):
    n = nombre.upper().strip()
    if any(k in n for k in ["INMOBILIARIO", "CISI", "COSI", "AUTOMOTOR", "IMPUESTO", "MONOTRIBUTO"]):
        return "Impuestos"
    if any(k in n for k in ["SAT", "EDET", "GAS", "CLARO", "LUZ", "AGUA", "INTERNET", "SERVICIO"]):
        return "Servicios"
    if any(k in n for k in ["NETFLIX", "DISNEY", "SPOTIFY", "FLOW", "YOUTUBE"]):
        return "Suscripciones"
    if any(k in n for k in ["NAFTA", "SEGURO", "AUTO", "PATENTE", "COCHERA"]):
        return "Vehículo y Movilidad"
    if any(k in n for k in ["GABINETE", "INSUMO", "CONSULTORIO"]):
        return "Gabinete"
    return "Hogar y Otros"


# ----------------- GESTIÓN Y MIGRACIÓN DE DATOS -----------------
def cargar_datos():
    criptos_base = ["BTC", "ETH", "USDT", "SOL", "BNB", "ADA", "XRP", "DOT", "DOGE"]
    acciones_base = [
        "AAPL (Apple)", "KO (Coca-Cola)", "MELI (MercadoLibre)",
        "SPY (S&P 500)", "MSFT (Microsoft)", "GOOGL (Google)",
        "NVDA (Nvidia)", "TSLA (Tesla)", "AMZN (Amazon)", "YPFD (YPF)"
    ]

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

                for c in data.get("costos", []):
                    c.setdefault("activo", True)
                    if "grupo" not in c or not c["grupo"]:
                        c["grupo"] = clasificar_costo_existente(c.get("categoria", ""))

                for ing in data.get("ingresos", []):
                    ing.setdefault("activo", True)
                    if "grupo" not in ing or not ing["grupo"]:
                        nom_low = ing.get("concepto", "").lower()
                        if "farmacia" in nom_low or "sac" in nom_low:
                            ing["grupo"] = "Farmacia"
                        elif "jubil" in nom_low:
                            ing["grupo"] = "Jubilación"
                        else:
                            ing["grupo"] = "Otros Ingresos"

                cats_base_c = ["Impuestos", "Servicios", "Suscripciones", "Vehículo y Movilidad", "Hogar y Otros", "Gabinete"]
                cats_c = list(dict.fromkeys(
                    data.get("categorias_costos", cats_base_c)
                    + [c["grupo"] for c in data.get("costos", [])]
                ))
                data["categorias_costos"] = cats_c

                cats_base_i = ["Farmacia", "Jubilación", "Terapias"]
                cats_i = list(dict.fromkeys(
                    data.get("categorias_ingresos", cats_base_i)
                    + [i["grupo"] for i in data.get("ingresos", [])]
                ))
                data["categorias_ingresos"] = cats_i

                for inv in data.get("inversiones", []):
                    inv.setdefault("activo_inv", True)
                    if inv.get("tipo") == "Acciones / CEDEARs":
                        inv["tipo"] = "Acciones"
                    elif inv.get("tipo") == "Efectivo / Banco":
                        inv["tipo"] = "Pesos ARS"

                criptos_actuales = data.get("criptos_guardadas", criptos_base)
                for inv in data.get("inversiones", []):
                    if inv.get("tipo") == "Criptomonedas":
                        sim = inv.get("simbolo", "").upper().strip()
                        if sim and sim not in criptos_actuales:
                            criptos_actuales.append(sim)
                data["criptos_guardadas"] = criptos_actuales

                acciones_actuales = data.get("acciones_guardadas", acciones_base)
                data["acciones_guardadas"] = acciones_actuales
                return data
        except Exception:
            pass

    return {
        "categorias_costos": [
            "Impuestos",
            "Servicios",
            "Suscripciones",
            "Vehículo y Movilidad",
            "Hogar y Otros"
        ],
        "costos": [
            {"grupo": "Impuestos", "categoria": "INMOBILIARIO", "monto": 2462, "activo": True},
            {"grupo": "Impuestos", "categoria": "CISI", "monto": 2659, "activo": True},
            {"grupo": "Impuestos", "categoria": "AUTOMOTOR", "monto": 2667, "activo": True},
            {"grupo": "Servicios", "categoria": "SAT", "monto": 36000, "activo": True},
            {"grupo": "Servicios", "categoria": "EDET", "monto": 60000, "activo": True},
            {"grupo": "Servicios", "categoria": "GAS", "monto": 16000, "activo": True},
            {"grupo": "Servicios", "categoria": "CLARO + RECARGA", "monto": 29000, "activo": True},
            {"grupo": "Suscripciones", "categoria": "NETFLIX", "monto": 15000, "activo": True},
            {"grupo": "Suscripciones", "categoria": "DISNEY", "monto": 9000, "activo": True},
            {"grupo": "Vehículo y Movilidad", "categoria": "NAFTA", "monto": 86000, "activo": True},
            {"grupo": "Vehículo y Movilidad", "categoria": "SEGURO", "monto": 28000, "activo": True}
        ],
        "categorias_ingresos": [
            "Farmacia",
            "Jubilación",
            "Terapias"
        ],
        "ingresos": [
            {"grupo": "Farmacia", "concepto": "Sueldo Farmacia", "monto": 650000, "activo": True},
            {"grupo": "Farmacia", "concepto": "SAC (Aguinaldo proporcional)", "monto": 54000, "activo": True},
            {"grupo": "Jubilación", "concepto": "Jubilación", "monto": 320000, "activo": True}
        ],
        "precio_terapia": 30000,
        "criptos_guardadas": criptos_base,
        "acciones_guardadas": acciones_base,
        "inversiones": [
            {
                "tipo": "Criptomonedas",
                "activo": "BTC",
                "simbolo": "BTC",
                "cantidad": 0.5,
                "plataforma": "BINANCE",
                "activo_inv": True
            },
            {
                "tipo": "Otros",
                "activo": "FRASCO NX",
                "simbolo": "ARS",
                "cantidad": 100000,
                "plataforma": "NX APP",
                "activo_inv": True
            }
        ]
    }


def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)


# ----------------- COTIZACIONES AUTOMÁTICAS EN VIVO -----------------
@st.cache_data(ttl=180)
def obtener_cotizaciones(simbolos_acciones, simbolos_cripto):
    cotiz = {
        "dolar_blue": 1555.0,
        "BTC": 82000.0,
        "ETH": 2600.0,
        "USDT": 1.0,
        "SOL": 150.0,
        "BNB": 580.0,
        "ADA": 0.75,
        "XRP": 1.10,
        "DOT": 6.50,
        "DOGE": 0.22,
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

    try:
        url_dolar = "https://dolarapi.com/v1/dolares/blue"
        r_dolar = requests.get(url_dolar, timeout=4)
        if r_dolar.status_code == 200:
            venta = r_dolar.json().get("venta", cotiz["dolar_blue"])
            cotiz["dolar_blue"] = float(venta)
    except Exception:
        pass

    lista_c = set(["BTC", "ETH", "SOL", "BNB"] + list(simbolos_cripto))
    for cripto in lista_c:
        c_up = cripto.upper().strip()
        if not c_up:
            continue
        if c_up in ["USDT", "USDC", "DAI"]:
            cotiz[c_up] = 1.0
            continue
        try:
            par = f"{c_up}USDT"
            url_bin = f"https://api.binance.com/api/v3/ticker/price?symbol={par}"
            r_bin = requests.get(url_bin, timeout=3)
            if r_bin.status_code == 200:
                cotiz[c_up] = float(r_bin.json()["price"])
        except Exception:
            pass

    headers = {"User-Agent": "Mozilla/5.0"}
    for ticker in set(simbolos_acciones):
        t_clean = ticker.upper().strip().split(" ")[0]
        if not t_clean or t_clean in ["USD", "ARS"]:
            continue
        try:
            url_yf = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/"
                f"{t_clean}?interval=1d&range=1d"
            )
            r_yf = requests.get(url_yf, headers=headers, timeout=3)
            if r_yf.status_code == 200:
                res = r_yf.json()["chart"]["result"][0]["meta"]
                precio_vivo = float(res.get("regularMarketPrice", 0))
                if precio_vivo > 0:
                    cotiz[t_clean] = precio_vivo
        except Exception:
            pass

    return cotiz


# ----------------- ESTILOS CSS PASTEL MATE -----------------
st.markdown("""
<style>
    html, body, [class*="css"], p, span, label, div {
        font-size: 16px;
        color: #374151;
    }

    /* Portada Jardín Financiero (Limpia, estética y fija) */
    .jardin-login-box {
        background: linear-gradient(145deg, #EAF6EE 0%, #F5F0FF 100%);
        border: 2px solid #95D5B2;
        border-radius: 22px;
        padding: 30px 26px 20px 26px;
        box-shadow: 0 8px 20px rgba(45, 106, 79, 0.08);
        text-align: center;
        margin-top: 25px;
        margin-bottom: 16px;
    }
    .jardin-login-title {
        color: #1B4332;
        font-weight: 800;
        font-size: 1.9rem;
        margin: 10px 0 6px 0;
    }
    .jardin-login-sub {
        color: #40916C;
        font-size: 1.05rem;
        font-weight: 500;
        margin-bottom: 4px;
    }

    /* Solapas principales grandes y visibles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 18px;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px !important;
        padding: 12px 30px !important;
        background-color: #F3F4F6 !important;
        border-radius: 14px 14px 0px 0px !important;
        border: 1px solid #E5E7EB !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #F3E8FF !important;
        border: 2px solid #C084FC !important;
        border-bottom: 4px solid #7E22CE !important;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.45rem !important;
        font-weight: 800 !important;
        color: #4A235A !important;
    }

    /* Tarjetas KPI en gama pastel mate */
    .metric-card {
        padding: 1.35rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .metric-card-costo {
        background-color: #FDEBD0;
        border: 1px solid #F5CBA7;
        border-left: 7px solid #E59866;
        color: #6E2C00;
    }
    .metric-card-ingreso {
        background-color: #E8F8F5;
        border: 1px solid #A3E4D7;
        border-left: 7px solid #76D7C4;
        color: #117864;
    }
    .metric-card-lila {
        background-color: #F3E8FF;
        border: 1px solid #D8B4FE;
        border-left: 7px solid #B794F4;
        color: #4A235A;
    }
    .metric-card-rojo-pastel {
        background-color: #FADBD8;
        border: 1px solid #F5B7B1;
        border-left: 7px solid #EC7063;
        color: #78281F;
    }
    .metric-card-neutro {
        background-color: #F3F4F6;
        border: 1px solid #D1D5DB;
        border-left: 7px solid #9CA3AF;
        color: #374151;
    }
    .kpi-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .kpi-value {
        font-size: 2.1rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .kpi-usd {
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 0.35rem;
        padding: 3px 10px;
        border-radius: 8px;
        background-color: rgba(255, 255, 255, 0.7);
        display: inline-block;
    }
    .kpi-sub {
        font-size: 0.9rem;
        opacity: 0.85;
        margin-top: 0.45rem;
    }

    /* Encabezados de columnas en tablas editables */
    .col-header {
        font-size: 0.85rem;
        font-weight: 700;
        color: #4B5563;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        padding-bottom: 4px;
        border-bottom: 2px solid #D1D5DB;
        margin-bottom: 8px;
    }

    /* Tildes 100% VERDES cuando están activos */
    div[data-testid="stCheckbox"] {
        filter: hue-rotate(125deg) saturate(0.85) brightness(0.95) !important;
        padding-top: 0.35rem;
    }

    /* Renglones desactivados en GRIS */
    div[data-testid="stTextInput"]:has(input:disabled) > div,
    div[data-testid="stNumberInput"]:has(input:disabled) > div {
        background-color: #E5E7EB !important;
        border-color: #D1D5DB !important;
        opacity: 0.65 !important;
    }
    input:disabled {
        background-color: #E5E7EB !important;
        color: #9CA3AF !important;
        -webkit-text-fill-color: #9CA3AF !important;
    }

    /* Botón del basurerito completo y centrado */
    div[data-testid="stButton"] button {
        border-radius: 10px !important;
        border: 1px solid #D1D5DB !important;
        background-color: #FFFFFF !important;
        padding: 0.35rem 0.55rem !important;
        min-width: 46px !important;
        min-height: 40px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stButton"] button p {
        font-size: 1.15rem !important;
        line-height: 1 !important;
        margin: 0 !important;
        overflow: visible !important;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #FEE2E2 !important;
        border-color: #FCA5A5 !important;
    }
</style>
""", unsafe_allow_html=True)

# Activar navegación con flechas Arriba / Abajo del teclado
activar_navegacion_flechas()

# ----------------- AUTENTICACIÓN: ENTRÁ A TU JARDÍN FINANCIERO -----------------
USUARIO_CORRECTO = "mama"
PASSWORD_CORRECTO = "terapias123"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([1, 1.35, 1])
    with c2:
        st.markdown("""
        <div class="jardin-login-box">
            <svg width="80" height="54" viewBox="0 0 80 54" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M40 50V18" stroke="#2D6A4F" stroke-width="3" stroke-linecap="round"/>
                <path d="M40 36C26 36 16 26 16 12C30 12 40 22 40 36Z" fill="#74C69D" stroke="#2D6A4F" stroke-width="2.2"/>
                <path d="M40 28C54 28 64 18 64 4C50 4 40 14 40 28Z" fill="#95D5B2" stroke="#2D6A4F" stroke-width="2.2"/>
                <circle cx="40" cy="12" r="4" fill="#D8B4FE" stroke="#5B4B8A" stroke-width="1.5"/>
            </svg>
            <div class="jardin-login-title">Entrá a tu Jardín Financiero</div>
            <div class="jardin-login-sub">Tu espacio personal de claridad y organización</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            user = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button(
                "Ingresar",
                use_container_width=True
            )
            if submit:
                u_ok = user.strip().lower() == USUARIO_CORRECTO
                p_ok = password == PASSWORD_CORRECTO
                if u_ok and p_ok:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
    st.stop()

# ----------------- CARGA DE DATOS -----------------
datos = cargar_datos()

tickers_acc = [
    inv.get("simbolo", "AAPL")
    for inv in datos.get("inversiones", [])
    if inv.get("tipo") == "Acciones"
] + [a.split(" ")[0] for a in datos.get("acciones_guardadas", [])]

tickers_cri = [
    inv.get("simbolo", "BTC")
    for inv in datos.get("inversiones", [])
    if inv.get("tipo") == "Criptomonedas"
] + datos.get("criptos_guardadas", [])

cotizaciones = obtener_cotizaciones(tuple(tickers_acc), tuple(tickers_cri))
dolar_b = cotizaciones["dolar_blue"]

# ----------------- FECHA Y BARRA LATERAL -----------------
tz_ar = timezone(timedelta(hours=-3))
ahora = datetime.now(tz_ar)
dias = {
    0: "lunes", 1: "martes", 2: "miércoles", 3: "jueves",
    4: "viernes", 5: "sábado", 6: "domingo"
}
meses = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}
dia_str = dias[ahora.weekday()]
mes_str = meses[ahora.month]
hora_str = ahora.strftime('%H:%M')
fecha_hora_texto = f"Hoy es {dia_str} {ahora.day} de {mes_str} - {hora_str} hs"

with st.sidebar:
    st.markdown(
        "<h2 style='color: #2D6A4F;'>🌿 Mi Panel</h2>",
        unsafe_allow_html=True
    )
    st.markdown(f"🗓️ **{fecha_hora_texto}**")
    st.markdown("---")
    st.markdown(f"💵 **Dólar Blue:** `{dolar_b:,.0f} ARS`")
    st.markdown(f"🪙 **Bitcoin:** `{cotizaciones['BTC']:,.0f} USD`")
    st.markdown("---")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# ----------------- PESTAÑAS PRINCIPALES -----------------
pestana1, pestana2 = st.tabs([
    "📊 Costos e Ingresos",
    "💎 Cartera de Inversiones"
])

# =========================================================================
# =========================== PESTAÑA 1 ===================================
# =========================================================================
with pestana1:
    costos_activos = [c for c in datos["costos"] if c.get("activo", True)]
    total_costos = sum(c["monto"] for c in costos_activos)

    ingresos_activos = [i for i in datos["ingresos"] if i.get("activo", True)]
    total_ingresos = sum(i["monto"] for i in ingresos_activos)

    saldo_neto = total_ingresos - total_costos

    costos_usd = total_costos / dolar_b if dolar_b > 0 else 0
    ingresos_usd = total_ingresos / dolar_b if dolar_b > 0 else 0
    saldo_usd = saldo_neto / dolar_b if dolar_b > 0 else 0

    if saldo_neto > 0:
        clase_saldo = "metric-card-lila"
        carita = "😊"
        sub_saldo = "Resultado positivo (Ganancia / Ahorro)"
    elif saldo_neto == 0:
        clase_saldo = "metric-card-neutro"
        carita = "😐"
        sub_saldo = "Resultado neutro (Sin ganancia ni pérdida)"
    else:
        clase_saldo = "metric-card-rojo-pastel"
        carita = "😟"
        sub_saldo = "Resultado negativo (Pérdida del mes)"

    # 1. TARJETAS KPI SUPERIORES
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.markdown(f"""
        <div class="metric-card metric-card-costo">
            <div class="kpi-title">Costo Mensual</div>
            <div class="kpi-value">{total_costos:,.0f} ARS</div>
            <div class="kpi-usd">≈ {costos_usd:,.2f} USD</div>
            <div class="kpi-sub">{len(costos_activos)} ítems activos</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
        <div class="metric-card metric-card-ingreso">
            <div class="kpi-title">Ingreso Mensual</div>
            <div class="kpi-value">{total_ingresos:,.0f} ARS</div>
            <div class="kpi-usd">≈ {ingresos_usd:,.2f} USD</div>
            <div class="kpi-sub">{len(ingresos_activos)} ítems activos</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi3:
        st.markdown(f"""
        <div class="metric-card {clase_saldo}">
            <div class="kpi-title">Ahorro Mensual {carita}</div>
            <div class="kpi-value">{saldo_neto:,.0f} ARS</div>
            <div class="kpi-usd">≈ {saldo_usd:,.2f} USD</div>
            <div class="kpi-sub">{sub_saldo}</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. CALCULADORA UNIFICADA DE TERAPIAS
    titulo_exp = "🧘‍♀️ **Calculadora de Terapias: Sesiones necesarias según tus números activos**"
    with st.expander(titulo_exp, expanded=True):
        col_c1, col_c2 = st.columns([1.1, 2.5])
        with col_c1:
            precio_sesion = st.number_input(
                "Valor por sesión de terapia (ARS):",
                value=int(datos.get("precio_terapia", 30000)),
                step=2000,
                format="%d"
            )
            if precio_sesion != datos.get("precio_terapia"):
                datos["precio_terapia"] = precio_sesion
                guardar_datos(datos)
            st.caption(f"Equivale a **{precio_sesion/dolar_b:,.2f} USD** por sesión.")

        faltante = total_costos - total_ingresos
        sesiones_mes = max(0.0, faltante / precio_sesion) if precio_sesion > 0 else 0.0
        sesiones_sem = sesiones_mes / 4.33
        sesiones_anio = sesiones_mes * 12

        with col_c2:
            if faltante <= 0:
                st.markdown(f"""
                <div style="background-color: #E8F8F5; border: 1px solid #A3E4D7; padding: 18px; border-radius: 14px; color: #117864;">
                    <b style="font-size: 1.2rem;">✨ ¡Tus costos activos están 100% cubiertos!</b><br>
                    Con los ingresos que tenés tildados hoy, cubrís todos tus gastos y te queda un ahorro a favor de <b>{abs(saldo_neto):,.0f} ARS</b> ({abs(saldo_usd):,.2f} USD) por mes.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #F3E8FF; border: 1px solid #D8B4FE; padding: 18px; border-radius: 14px; color: #4A235A;">
                    <b style="font-size: 1.15rem;">🎯 Sesiones requeridas para cubrir tus costos activos:</b><br>
                    Para cubrir la diferencia actual de <b>{faltante:,.0f} ARS</b> ({faltante/dolar_b:,.2f} USD), necesitás realizar:
                    <div style="font-size: 2.0rem; font-weight: 800; margin: 6px 0;">
                        {sesiones_mes:.1f} sesiones por mes
                    </div>
                    <span>
                        📅 <b>{sesiones_sem:.1f} sesiones por semana</b> &nbsp;|&nbsp; 🗓️ <b>{sesiones_anio:.0f} sesiones al año</b>
                    </span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # 3. COLUMNAS DE COSTOS E INGRESOS POR CATEGORÍAS COLAPSABLES
    col_izq, col_espacio, col_der = st.columns([1, 0.12, 1])

    # ---------------- COLUMNA IZQUIERDA: COSTOS POR CATEGORÍA ----------------
    with col_izq:
        st.markdown("<h3 style='color: #A04000;'>📉 Mis Costos Mensuales</h3>", unsafe_allow_html=True)

        with st.expander("📁 ➕ Agregar Nueva Categoría de Costos"):
            with st.form("form_nueva_cat_costo", clear_on_submit=True):
                nueva_cat_c = st.text_input("Nombre de la Categoría (ej. Impuestos, Servicios, Educación)")
                btn_cat_c = st.form_submit_button("Crear Categoría", use_container_width=True)
                if btn_cat_c and nueva_cat_c.strip():
                    nom_limpio = nueva_cat_c.strip()
                    if nom_limpio not in datos["categorias_costos"]:
                        datos["categorias_costos"].append(nom_limpio)
                        guardar_datos(datos)
                        st.rerun()

        costos_modificados = False
        for cat_idx, cat_nombre in enumerate(list(datos["categorias_costos"])):
            items_cat = [
                (idx, item) for idx, item in enumerate(datos["costos"])
                if item.get("grupo", "Hogar y Otros") == cat_nombre
            ]
            sub_ars = sum(i["monto"] for _, i in items_cat if i.get("activo", True))
            sub_usd = sub_ars / dolar_b if dolar_b > 0 else 0

            titulo_cat = f"📂 **{cat_nombre}** — Subtotal: **{sub_ars:,.0f} ARS** ({sub_usd:,.1f} USD)"
            with st.expander(titulo_cat, expanded=True):
                if items_cat:
                    h1, h2, h3, h4 = st.columns([0.4, 2.0, 1.5, 0.7])
                    h1.markdown("<div class='col-header'>Act.</div>", unsafe_allow_html=True)
                    h2.markdown("<div class='col-header'>Subcategoría</div>", unsafe_allow_html=True)
                    h3.markdown("<div class='col-header'>Monto (ARS)</div>", unsafe_allow_html=True)
                    h4.markdown("<div class='col-header'>Borrar</div>", unsafe_allow_html=True)

                for idx, item in items_cat:
                    estado_check = item.get("activo", True)
                    c_box, c_nombre, c_monto, c_del = st.columns([0.4, 2.0, 1.5, 0.7])
                    with c_box:
                        nuevo_estado = st.checkbox(
                            "Activo",
                            value=estado_check,
                            key=f"costo_check_{idx}",
                            label_visibility="collapsed"
                        )
                        if nuevo_estado != estado_check:
                            item["activo"] = nuevo_estado
                            costos_modificados = True
                    with c_nombre:
                        nuevo_nom = st.text_input(
                            "Subcategoría",
                            value=item["categoria"],
                            key=f"costo_nom_{idx}",
                            label_visibility="collapsed",
                            disabled=not estado_check
                        )
                        if nuevo_nom != item["categoria"]:
                            item["categoria"] = nuevo_nom
                            costos_modificados = True
                    with c_monto:
                        monto_str = formatear_cant(item["monto"])
                        nuevo_val_str = st.text_input(
                            "Monto",
                            value=monto_str,
                            key=f"costo_val_{idx}",
                            label_visibility="collapsed",
                            disabled=not estado_check
                        )
                        try:
                            nuevo_val = float(nuevo_val_str.replace(",", "."))
                            if nuevo_val != float(item["monto"]):
                                item["monto"] = int(nuevo_val) if nuevo_val.is_integer() else nuevo_val
                                costos_modificados = True
                        except ValueError:
                            pass
                    with c_del:
                        if st.button("🗑️", key=f"costo_del_{idx}", help="Eliminar este ítem"):
                            datos["costos"].pop(idx)
                            guardar_datos(datos)
                            st.rerun()

                with st.form(f"form_sub_costo_{cat_idx}", clear_on_submit=True):
                    sc1, sc2, sc3 = st.columns([2.0, 1.4, 1.2])
                    with sc1:
                        sub_nom_c = st.text_input(
                            "Nueva subcategoría",
                            placeholder=f"Nuevo en {cat_nombre}...",
                            label_visibility="collapsed"
                        )
                    with sc2:
                        sub_val_c = st.text_input(
                            "Monto ARS",
                            placeholder="Monto ARS",
                            label_visibility="collapsed"
                        )
                    with sc3:
                        btn_sub_c = st.form_submit_button("➕ Agregar", use_container_width=True)
                        if btn_sub_c and sub_nom_c.strip():
                            try:
                                m_num = float(sub_val_c.strip().replace(",", ".")) if sub_val_c.strip() else 0
                            except ValueError:
                                m_num = 0
                            datos["costos"].append({
                                "grupo": cat_nombre,
                                "categoria": sub_nom_c.strip(),
                                "monto": int(m_num) if float(m_num).is_integer() else m_num,
                                "activo": True
                            })
                            guardar_datos(datos)
                            st.rerun()

                if not items_cat:
                    if st.button(f"🗑️ Eliminar categoría vacía '{cat_nombre}'", key=f"del_cat_c_{cat_idx}"):
                        datos["categorias_costos"].remove(cat_nombre)
                        guardar_datos(datos)
                        st.rerun()

        if costos_modificados:
            guardar_datos(datos)
            st.rerun()

    # ---------------- COLUMNA DERECHA: INGRESOS POR CATEGORÍA ----------------
    with col_der:
        st.markdown("<h3 style='color: #117864;'>📈 Mis Ingresos Mensuales</h3>", unsafe_allow_html=True)

        with st.expander("📁 ➕ Agregar Nueva Categoría de Ingresos"):
            with st.form("form_nueva_cat_ing", clear_on_submit=True):
                nueva_cat_i = st.text_input("Nombre de la Categoría (ej. Farmacia, Consultorio, Otros)")
                btn_cat_i = st.form_submit_button("Crear Categoría", use_container_width=True)
                if btn_cat_i and nueva_cat_i.strip():
                    nom_limpio_i = nueva_cat_i.strip()
                    if nom_limpio_i not in datos["categorias_ingresos"]:
                        datos["categorias_ingresos"].append(nom_limpio_i)
                        guardar_datos(datos)
                        st.rerun()

        ingresos_modificados = False
        for cat_idx_i, cat_nombre_i in enumerate(list(datos["categorias_ingresos"])):
            items_cat_i = [
                (idx, item) for idx, item in enumerate(datos["ingresos"])
                if item.get("grupo", "Otros Ingresos") == cat_nombre_i
            ]
            sub_ars_i = sum(i["monto"] for _, i in items_cat_i if i.get("activo", True))
            sub_usd_i = sub_ars_i / dolar_b if dolar_b > 0 else 0

            titulo_cat_i = f"📂 **{cat_nombre_i}** — Subtotal: **{sub_ars_i:,.0f} ARS** ({sub_usd_i:,.1f} USD)"
            with st.expander(titulo_cat_i, expanded=True):
                if items_cat_i:
                    hi1, hi2, hi3, hi4 = st.columns([0.4, 2.0, 1.5, 0.7])
                    hi1.markdown("<div class='col-header'>Act.</div>", unsafe_allow_html=True)
                    hi2.markdown("<div class='col-header'>Subcategoría</div>", unsafe_allow_html=True)
                    hi3.markdown("<div class='col-header'>Monto (ARS)</div>", unsafe_allow_html=True)
                    hi4.markdown("<div class='col-header'>Borrar</div>", unsafe_allow_html=True)

                for idx, item in items_cat_i:
                    estado_check = item.get("activo", True)
                    c_box, c_nombre, c_monto, c_del = st.columns([0.4, 2.0, 1.5, 0.7])
                    with c_box:
                        nuevo_estado = st.checkbox(
                            "Activo",
                            value=estado_check,
                            key=f"ing_check_{idx}",
                            label_visibility="collapsed"
                        )
                        if nuevo_estado != estado_check:
                            item["activo"] = nuevo_estado
                            ingresos_modificados = True
                    with c_nombre:
                        nuevo_nom = st.text_input(
                            "Concepto",
                            value=item["concepto"],
                            key=f"ing_nom_{idx}",
                            label_visibility="collapsed",
                            disabled=not estado_check
                        )
                        if nuevo_nom != item["concepto"]:
                            item["concepto"] = nuevo_nom
                            ingresos_modificados = True
                    with c_monto:
                        monto_i_str = formatear_cant(item["monto"])
                        nuevo_val_i_str = st.text_input(
                            "Monto",
                            value=monto_i_str,
                            key=f"ing_val_{idx}",
                            label_visibility="collapsed",
                            disabled=not estado_check
                        )
                        try:
                            nuevo_val_i = float(nuevo_val_i_str.replace(",", "."))
                            if nuevo_val_i != float(item["monto"]):
                                item["monto"] = int(nuevo_val_i) if nuevo_val_i.is_integer() else nuevo_val_i
                                ingresos_modificados = True
                        except ValueError:
                            pass
                    with c_del:
                        if st.button("🗑️", key=f"ing_del_{idx}", help="Eliminar este ingreso"):
                            datos["ingresos"].pop(idx)
                            guardar_datos(datos)
                            st.rerun()

                with st.form(f"form_sub_ing_{cat_idx_i}", clear_on_submit=True):
                    si1, si2, si3 = st.columns([2.0, 1.4, 1.2])
                    with si1:
                        sub_nom_i = st.text_input(
                            "Nuevo ingreso",
                            placeholder=f"Nuevo en {cat_nombre_i}...",
                            label_visibility="collapsed"
                        )
                    with si2:
                        sub_val_i = st.text_input(
                            "Monto ARS",
                            placeholder="Monto ARS",
                            label_visibility="collapsed"
                        )
                    with si3:
                        btn_sub_i = st.form_submit_button("➕ Agregar", use_container_width=True)
                        if btn_sub_i and sub_nom_i.strip():
                            try:
                                mi_num = float(sub_val_i.strip().replace(",", ".")) if sub_val_i.strip() else 0
                            except ValueError:
                                mi_num = 0
                            datos["ingresos"].append({
                                "grupo": cat_nombre_i,
                                "concepto": sub_nom_i.strip(),
                                "monto": int(mi_num) if float(mi_num).is_integer() else mi_num,
                                "activo": True
                            })
                            guardar_datos(datos)
                            st.rerun()

                if not items_cat_i:
                    if st.button(f"🗑️ Eliminar categoría vacía '{cat_nombre_i}'", key=f"del_cat_i_{cat_idx_i}"):
                        datos["categorias_ingresos"].remove(cat_nombre_i)
                        guardar_datos(datos)
                        st.rerun()

        if ingresos_modificados:
            guardar_datos(datos)
            st.rerun()

    st.markdown("---")

    # 4. GRÁFICOS DE TORTA 2D CON FLECHAS EXTERNAS Y SUBTOTALES
    st.markdown(
        "<h3 style='color: #5B4B8A;'>📊 Gráficos de Torta y Subtotales</h3>",
        unsafe_allow_html=True
    )
    modo_grafico = st.radio(
        "Ver gráficos de torta según:",
        ["Por Categoría (Subtotales)", "Detallado por cada Subcategoría"],
        horizontal=True
    )

    col_chart_c, col_esp_g, col_chart_i = st.columns([1, 0.08, 1])

    with col_chart_c:
        st.markdown(
            "<h4 style='color: #A04000; text-align: center;'>Distribución de Costos Activos</h4>",
            unsafe_allow_html=True
        )
        if costos_activos and total_costos > 0:
            df_c_raw = pd.DataFrame(costos_activos)
            if modo_grafico.startswith("Por Categoría"):
                df_pie_c = df_c_raw.groupby("grupo", as_index=False)["monto"].sum().sort_values(by="monto", ascending=False)
                col_label_c = "grupo"
                titulo_col_c = "Categoría"
            else:
                df_pie_c = df_c_raw.sort_values(by="monto", ascending=False).copy()
                df_pie_c["etiqueta"] = df_pie_c["categoria"]
                col_label_c = "etiqueta"
                titulo_col_c = "Subcategoría"

            df_pie_c["USD"] = df_pie_c["monto"] / dolar_b
            df_pie_c["Porcentaje"] = (df_pie_c["monto"] / total_costos) * 100

            fig_c = crear_torta_2d(df_pie_c, "monto", col_label_c)
            st.plotly_chart(fig_c, use_container_width=True)

            tabla_c = df_pie_c[[col_label_c, "monto", "USD", "Porcentaje"]].copy()
            tabla_c.columns = [titulo_col_c, "Subtotal en ARS", "Subtotal en USD", "% del Total"]
            tabla_c["Subtotal en ARS"] = tabla_c["Subtotal en ARS"].apply(lambda x: f"{x:,.0f} ARS")
            tabla_c["Subtotal en USD"] = tabla_c["Subtotal en USD"].apply(lambda x: f"{x:,.2f} USD")
            tabla_c["% del Total"] = tabla_c["% del Total"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_c, use_container_width=True, hide_index=True)
        else:
            st.info("No hay costos activos para graficar.")

    with col_chart_i:
        st.markdown(
            "<h4 style='color: #117864; text-align: center;'>Distribución de Ingresos Activos</h4>",
            unsafe_allow_html=True
        )
        if ingresos_activos and total_ingresos > 0:
            df_i_raw = pd.DataFrame(ingresos_activos)
            if modo_grafico.startswith("Por Categoría"):
                df_pie_i = df_i_raw.groupby("grupo", as_index=False)["monto"].sum().sort_values(by="monto", ascending=False)
                col_label_i = "grupo"
                titulo_col_i = "Categoría"
            else:
                df_pie_i = df_i_raw.sort_values(by="monto", ascending=False).copy()
                df_pie_i["etiqueta"] = df_pie_i["concepto"]
                col_label_i = "etiqueta"
                titulo_col_i = "Subcategoría"

            df_pie_i["USD"] = df_pie_i["monto"] / dolar_b
            df_pie_i["Porcentaje"] = (df_pie_i["monto"] / total_ingresos) * 100

            fig_i = crear_torta_2d(df_pie_i, "monto", col_label_i)
            st.plotly_chart(fig_i, use_container_width=True)

            tabla_i = df_pie_i[[col_label_i, "monto", "USD", "Porcentaje"]].copy()
            tabla_i.columns = [titulo_col_i, "Subtotal en ARS", "Subtotal en USD", "% del Total"]
            tabla_i["Subtotal en ARS"] = tabla_i["Subtotal en ARS"].apply(lambda x: f"{x:,.0f} ARS")
            tabla_i["Subtotal en USD"] = tabla_i["Subtotal en USD"].apply(lambda x: f"{x:,.2f} USD")
            tabla_i["% del Total"] = tabla_i["% del Total"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_i, use_container_width=True, hide_index=True)
        else:
            st.info("No hay ingresos activos para graficar.")


# =========================================================================
# =========================== PESTAÑA 2 ===================================
# =========================================================================
with pestana2:
    inversiones = datos.get("inversiones", [])
    filas = []

    for inv in inversiones:
        cant = float(inv.get("cantidad", 0))
        tipo = inv.get("tipo", "Pesos ARS")
        simbolo = inv.get("simbolo", "").upper().strip()
        esta_activo = inv.get("activo_inv", True)

        if tipo == "Dólar Billete":
            val_usd = cant
            val_ars = cant * dolar_b
            cotiz_actual_str = f"1 USD = {dolar_b:,.0f} ARS"
        elif tipo == "Criptomonedas":
            precio_u = cotizaciones.get(simbolo, 1.0)
            val_usd = cant * precio_u
            val_ars = val_usd * dolar_b
            cotiz_actual_str = f"1 {simbolo} = {precio_u:,.2f} USD ({precio_u*dolar_b:,.0f} ARS)"
        elif tipo == "Acciones":
            precio_u = cotizaciones.get(simbolo, 100.0)
            val_usd = cant * precio_u
            val_ars = val_usd * dolar_b
            cotiz_actual_str = f"1 {simbolo} = {precio_u:,.2f} USD ({precio_u*dolar_b:,.0f} ARS)"
        else:
            val_ars = cant
            val_usd = cant / dolar_b if dolar_b > 0 else 0
            cotiz_actual_str = f"1 USD = {dolar_b:,.0f} ARS"

        filas.append({
            "Tipo": tipo,
            "Activo": inv.get("activo", tipo),
            "Simbolo": simbolo,
            "Plataforma": inv.get("plataforma", ""),
            "Cantidad_Num": cant,
            "Cantidad": formatear_cant(cant),
            "Cotización Actual": cotiz_actual_str,
            "Valor en ARS": val_ars,
            "Valor en USD": val_usd,
            "Activo_Flag": esta_activo
        })

    df_inv_todos = pd.DataFrame(filas)
    if not df_inv_todos.empty:
        df_inv_activos = df_inv_todos[df_inv_todos["Activo_Flag"] == True]
    else:
        df_inv_activos = pd.DataFrame()

    total_patrimonio_ars = df_inv_activos["Valor en ARS"].sum() if not df_inv_activos.empty else 0
    total_patrimonio_usd = df_inv_activos["Valor en USD"].sum() if not df_inv_activos.empty else 0

    # TARJETA ÚNICA DE PATRIMONIO TOTAL
    st.markdown(f"""
    <div class="metric-card metric-card-lila" style="text-align: center;">
        <div class="kpi-title" style="font-size: 1.25rem;">Patrimonio Total</div>
        <div class="kpi-value" style="font-size: 2.35rem;">{total_patrimonio_ars:,.0f} ARS</div>
        <div class="kpi-usd" style="font-size: 1.2rem;">{total_patrimonio_usd:,.2f} USD</div>
        <div class="kpi-sub">Calculado automáticamente con cotizaciones en vivo</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # COLUMNAS DE INVERSIONES
    col_inv_izq, col_inv_esp, col_inv_der = st.columns([1.05, 0.12, 1.85])

    # ---------------- COLUMNA IZQUIERDA: AGREGAR ACTIVO ----------------
    with col_inv_izq:
        st.markdown(
            "<h3 style='color: #5B4B8A;'>➕ Agregar Activo</h3>",
            unsafe_allow_html=True
        )
        opciones_tipo = [
            "A - Dólar Billete",
            "B - Pesos ARS",
            "C - Acciones",
            "D - Criptomonedas",
            "E - Otros"
        ]
        tipo_elegido = st.selectbox("1. Tipo de Activo", opciones_tipo)

        # Formulario unificado para que al apretar ENTER en cualquier campo se guarde el activo y sin ,0000
        with st.form("form_guardar_activo_inv", clear_on_submit=True):
            simbolo_elegido = "USD"
            detalle_manual = ""

            if tipo_elegido.startswith("C"):
                lista_acc_actual = datos.get("acciones_guardadas", [])
                simbolo_elegido = st.selectbox("Seleccioná la Acción de la lista", lista_acc_actual)
                detalle_manual = st.text_input(
                    "¿No está en la lista? Escribila a mano acá y quedará grabada (ej. DIS, V):"
                )
            elif tipo_elegido.startswith("D"):
                lista_cri_actual = datos.get("criptos_guardadas", [])
                simbolo_elegido = st.selectbox("Seleccioná la Criptomoneda de la lista", lista_cri_actual)
                detalle_manual = st.text_input(
                    "¿No está en la lista? Escribí la sigla a mano acá y quedará grabada (ej. DFT, ADA):"
                )
            elif tipo_elegido.startswith("E"):
                detalle_manual = st.text_input(
                    "Detalle qué es (ej. FRASCO NX, FCI, PF UVA)"
                )

            plat_act = st.text_input("2. Ubicación, ¿dónde está?")
            cant_texto = st.text_input(
                "3. Cantidad que tenés (apretá Enter para guardar)",
                placeholder="Ej: 40000 o 0.5"
            )
            btn_guardar_inv = st.form_submit_button(
                "Guardar Activo",
                use_container_width=True
            )

            if btn_guardar_inv:
                texto_limpio = cant_texto.strip().replace(",", ".")
                try:
                    cant_num = float(texto_limpio) if texto_limpio else 0.0
                except ValueError:
                    cant_num = -1.0

                if cant_num > 0:
                    if tipo_elegido.startswith("A"):
                        tipo_guardar = "Dólar Billete"
                        nombre_act = "Dólar Billete"
                        simbolo_final = "USD"
                    elif tipo_elegido.startswith("B"):
                        tipo_guardar = "Pesos ARS"
                        nombre_act = "Pesos ARS"
                        simbolo_final = "ARS"
                    elif tipo_elegido.startswith("C"):
                        tipo_guardar = "Acciones"
                        if detalle_manual.strip():
                            nuevo_acc = detalle_manual.strip().upper()
                            if nuevo_acc not in datos["acciones_guardadas"]:
                                datos["acciones_guardadas"].append(nuevo_acc)
                            nombre_act = nuevo_acc
                            simbolo_final = nuevo_acc.split(" ")[0]
                        else:
                            nombre_act = simbolo_elegido
                            simbolo_final = simbolo_elegido.split(" ")[0].upper()
                    elif tipo_elegido.startswith("D"):
                        tipo_guardar = "Criptomonedas"
                        if detalle_manual.strip():
                            nueva_cri = detalle_manual.strip().upper().split(" ")[0]
                            if nueva_cri not in datos["criptos_guardadas"]:
                                datos["criptos_guardadas"].append(nueva_cri)
                            nombre_act = nueva_cri
                            simbolo_final = nueva_cri
                        else:
                            nombre_act = simbolo_elegido.strip().upper()
                            simbolo_final = nombre_act
                    else:
                        tipo_guardar = "Otros"
                        nombre_act = detalle_manual.strip() if detalle_manual.strip() else "Otros"
                        simbolo_final = "ARS"

                    datos["inversiones"].append({
                        "tipo": tipo_guardar,
                        "activo": nombre_act,
                        "simbolo": simbolo_final,
                        "cantidad": int(cant_num) if cant_num.is_integer() else cant_num,
                        "plataforma": plat_act.strip() if plat_act.strip() else "Sin especificar",
                        "activo_inv": True
                    })
                    guardar_datos(datos)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Ingresá una cantidad válida mayor a 0.")

    # ---------------- COLUMNA DERECHA: MIS ACTIVOS POR CATEGORÍA CON ENCABEZADOS ----------------
    with col_inv_der:
        st.markdown(
            "<h3 style='color: #5B4B8A;'>📋 Mis Activos por Categoría</h3>",
            unsafe_allow_html=True
        )
        orden_categorias_inv = [
            "Dólar Billete",
            "Pesos ARS",
            "Acciones",
            "Criptomonedas",
            "Otros"
        ]

        if inversiones:
            inv_cambios = False
            for cat_inv in orden_categorias_inv:
                items_cat_inv = [
                    (idx, inv) for idx, inv in enumerate(inversiones)
                    if inv.get("tipo", "Otros") == cat_inv
                ]
                if not items_cat_inv:
                    continue

                sub_inv_ars = sum(
                    filas[idx]["Valor en ARS"]
                    for idx, inv in items_cat_inv
                    if inv.get("activo_inv", True)
                )
                sub_inv_usd = sum(
                    filas[idx]["Valor en USD"]
                    for idx, inv in items_cat_inv
                    if inv.get("activo_inv", True)
                )

                titulo_exp_inv = (
                    f"📂 **{cat_inv}** — Subtotal: "
                    f"**{sub_inv_ars:,.0f} ARS** ({sub_inv_usd:,.2f} USD)"
                )
                with st.expander(titulo_exp_inv, expanded=True):
                    hc1, hc2, hc3, hc4, hc5 = st.columns([0.4, 1.45, 1.25, 1.35, 0.65])
                    hc1.markdown("<div class='col-header'>Act.</div>", unsafe_allow_html=True)
                    hc2.markdown("<div class='col-header'>Detalle</div>", unsafe_allow_html=True)
                    hc3.markdown("<div class='col-header'>Cantidad</div>", unsafe_allow_html=True)
                    hc4.markdown("<div class='col-header'>Ubicación</div>", unsafe_allow_html=True)
                    hc5.markdown("<div class='col-header'>Borrar</div>", unsafe_allow_html=True)

                    for idx, inv in items_cat_inv:
                        st_act = inv.get("activo_inv", True)
                        c_chk, c_nom, c_cant, c_plat, c_del = st.columns([0.4, 1.45, 1.25, 1.35, 0.65])

                        with c_chk:
                            nuevo_chk = st.checkbox(
                                "Activo",
                                value=st_act,
                                key=f"inv_chk_{idx}",
                                label_visibility="collapsed"
                            )
                            if nuevo_chk != st_act:
                                inv["activo_inv"] = nuevo_chk
                                inv_cambios = True

                        with c_nom:
                            nuevo_nom_inv = st.text_input(
                                "Detalle",
                                value=inv.get("activo", ""),
                                key=f"inv_nom_{idx}",
                                label_visibility="collapsed",
                                disabled=not st_act
                            )
                            if nuevo_nom_inv != inv.get("activo", ""):
                                inv["activo"] = nuevo_nom_inv
                                inv_cambios = True

                        with c_cant:
                            cant_str_actual = formatear_cant(inv.get("cantidad", 0))
                            nueva_c_str = st.text_input(
                                "Cantidad",
                                value=cant_str_actual,
                                key=f"inv_cant_{idx}",
                                label_visibility="collapsed",
                                disabled=not st_act
                            )
                            try:
                                nueva_c_num = float(nueva_c_str.replace(",", "."))
                                if nueva_c_num != float(inv.get("cantidad", 0)):
                                    inv["cantidad"] = int(nueva_c_num) if nueva_c_num.is_integer() else nueva_c_num
                                    inv_cambios = True
                            except ValueError:
                                pass

                        with c_plat:
                            nueva_p = st.text_input(
                                "Ubicación",
                                value=inv.get("plataforma", ""),
                                key=f"inv_p_{idx}",
                                label_visibility="collapsed",
                                disabled=not st_act
                            )
                            if nueva_p != inv.get("plataforma", ""):
                                inv["plataforma"] = nueva_p
                                inv_cambios = True

                        with c_del:
                            if st.button("🗑️", key=f"inv_del_{idx}", help="Eliminar este activo"):
                                datos["inversiones"].pop(idx)
                                guardar_datos(datos)
                                st.rerun()

            if inv_cambios:
                guardar_datos(datos)
                st.rerun()
        else:
            st.info("No hay activos cargados aún.")

    st.markdown("---")

    # GRÁFICOS DE TORTA 2D CON FLECHAS EXTERNAS Y TABLAS CON COTIZACIÓN ACTUAL
    st.markdown(
        "<h3 style='color: #5B4B8A;'>📊 Distribución de Mi Cartera y Cotizaciones en Vivo</h3>",
        unsafe_allow_html=True
    )
    if not df_inv_activos.empty and total_patrimonio_ars > 0:
        col_g_inv1, col_g_esp, col_g_inv2 = st.columns([1, 0.08, 1])

        with col_g_inv1:
            st.markdown(
                "<h4 style='color: #5B4B8A; text-align: center;'>Por Categoría de Activo</h4>",
                unsafe_allow_html=True
            )
            resumen_tipo = df_inv_activos.groupby("Tipo", as_index=False).agg({
                "Valor en ARS": "sum",
                "Valor en USD": "sum"
            }).sort_values(by="Valor en ARS", ascending=False)
            resumen_tipo["%"] = (resumen_tipo["Valor en ARS"] / total_patrimonio_ars) * 100

            fig_inv_tipo = crear_torta_2d(resumen_tipo, "Valor en ARS", "Tipo")
            st.plotly_chart(fig_inv_tipo, use_container_width=True)

            tabla_t = resumen_tipo.copy()
            tabla_t.columns = ["Categoría", "Subtotal en ARS", "Subtotal en USD", "%"]
            tabla_t["Subtotal en ARS"] = tabla_t["Subtotal en ARS"].apply(lambda x: f"{x:,.0f} ARS")
            tabla_t["Subtotal en USD"] = tabla_t["Subtotal en USD"].apply(lambda x: f"{x:,.2f} USD")
            tabla_t["%"] = tabla_t["%"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_t, use_container_width=True, hide_index=True)

        with col_g_inv2:
            st.markdown(
                "<h4 style='color: #5B4B8A; text-align: center;'>Por Activo Individual y Ubicación</h4>",
                unsafe_allow_html=True
            )
            df_det = df_inv_activos.sort_values(by="Valor en ARS", ascending=False).copy()
            df_det["Etiqueta"] = df_det["Activo"] + " (" + df_det["Plataforma"] + ")"
            df_det["%"] = (df_det["Valor en ARS"] / total_patrimonio_ars) * 100

            fig_inv_det = crear_torta_2d(df_det, "Valor en ARS", "Etiqueta")
            st.plotly_chart(fig_inv_det, use_container_width=True)

            cols_d = [
                "Tipo", "Activo", "Plataforma", "Cantidad",
                "Cotización Actual", "Valor en ARS", "Valor en USD", "%"
            ]
            tabla_d = df_det[cols_d].copy()
            tabla_d.columns = [
                "Categoría", "Activo", "Ubicación", "Cantidad",
                "Cotización Actual Tomada", "Valor en ARS", "Valor en USD", "%"
            ]
            tabla_d["Valor en ARS"] = tabla_d["Valor en ARS"].apply(lambda x: f"{x:,.0f} ARS")
            tabla_d["Valor en USD"] = tabla_d["Valor en USD"].apply(lambda x: f"{x:,.2f} USD")
            tabla_d["%"] = tabla_d["%"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_d, use_container_width=True, hide_index=True)
    else:
        st.info("No hay inversiones activas para mostrar en los gráficos.")
