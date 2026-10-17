import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os
from datetime import datetime, timezone, timedelta

st.set_page_config(
    page_title="Panel Financiero",
    layout="wide",
    page_icon="💜"
)

DATA_FILE = "datos_finanzas.json"

# Paleta de colores pasteles mate bien diferenciados entre sí
PALETA_PASTEL = [
    "#B8B5FF",  # Lila pastel
    "#FFD3B6",  # Durazno pastel
    "#A8E6CF",  # Verde menta pastel
    "#FFAAA5",  # Coral rosado pastel
    "#A2D2FF",  # Celeste pastel
    "#FDFD96",  # Amarillo pastel suave
    "#CDB4DB",  # Lavanda mate
    "#98DDCA",  # Turquesa pastel
    "#F6DFEB",  # Rosa pálido
    "#D4A5A5"   # Rosa viejo mate
]


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
                    if inv.get("tipo") == "Acciones / CEDEARs":
                        inv["tipo"] = "Acciones"
                    elif inv.get("tipo") == "Efectivo / Banco":
                        inv["tipo"] = "Pesos ARS"
                if "ingresos" not in data and "ingresos_otros" in data:
                    data["ingresos"] = [
                        {
                            "concepto": i["concepto"],
                            "monto": i["monto"],
                            "activo": True
                        }
                        for i in data["ingresos_otros"]
                    ]
                return data
        except Exception:
            pass

    return {
        "costos": [
            {"categoria": "Alquiler / Expensas", "monto": 250000, "activo": True},
            {"categoria": "Supermercado y Comida", "monto": 280000, "activo": True},
            {"categoria": "Obra Social / Salud", "monto": 90000, "activo": True},
            {"categoria": "Servicios (Luz, Gas, Agua)", "monto": 75000, "activo": True},
            {"categoria": "Insumos Gabinete", "monto": 45000, "activo": True}
        ],
        "ingresos": [
            {"concepto": "Sueldo Farmacia", "monto": 650000, "activo": True},
            {"concepto": "SAC (Aguinaldo proporcional)", "monto": 54000, "activo": True},
            {"concepto": "Jubilación", "monto": 320000, "activo": True}
        ],
        "precio_terapia": 30000,
        "inversiones": [
            {
                "tipo": "Dólar Billete",
                "activo": "Dólar Billete",
                "simbolo": "USD",
                "cantidad": 1200,
                "plataforma": "Caja de seguridad",
                "activo_inv": True
            },
            {
                "tipo": "Acciones",
                "activo": "AAPL (Apple)",
                "simbolo": "AAPL",
                "cantidad": 20,
                "plataforma": "Balanz",
                "activo_inv": True
            },
            {
                "tipo": "Criptomonedas",
                "activo": "BTC",
                "simbolo": "BTC",
                "cantidad": 0.015,
                "plataforma": "Binance",
                "activo_inv": True
            },
            {
                "tipo": "Pesos ARS",
                "activo": "Pesos ARS",
                "simbolo": "ARS",
                "cantidad": 350000,
                "plataforma": "Banco",
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
        if cripto == "USDT":
            cotiz["USDT"] = 1.0
            continue
        try:
            par = f"{cripto.upper()}USDT"
            url_bin = f"https://api.binance.com/api/v3/ticker/price?symbol={par}"
            r_bin = requests.get(url_bin, timeout=3)
            if r_bin.status_code == 200:
                cotiz[cripto.upper()] = float(r_bin.json()["price"])
        except Exception:
            pass

    headers = {"User-Agent": "Mozilla/5.0"}
    for ticker in set(simbolos_acciones):
        t_clean = ticker.upper().strip()
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


# ----------------- ESTILOS CSS PASTEL MATE Y ARREGLO DE ICONOS -----------------
st.markdown("""
<style>
    html, body, [class*="css"], p, span, label, div {
        font-size: 16px;
        color: #374151;
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
    .metric-card-amarillo {
        background-color: #FEF9E7;
        border: 1px solid #F9E79F;
        border-left: 7px solid #F4D03F;
        color: #7D6608;
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

    /* Cambiar el tilde de naranja/rojo a VERDE cuando está activo */
    div[data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input:checked) > span:first-of-type,
    div[data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input[aria-checked="true"]) > span:first-of-type,
    span[data-baseweb="checkbox"][aria-checked="true"] {
        background-color: #52B788 !important;
        border-color: #52B788 !important;
    }
    div[data-testid="stCheckbox"] {
        padding-top: 0.35rem;
    }

    /* Poner todo el renglón en GRIS cuando está desactivado/pausado */
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

    /* Arreglo para que el ícono del basurerito se vea entero y nunca se corte */
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

    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: 700;
        color: #5B4B8A;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- AUTENTICACIÓN -----------------
USUARIO_CORRECTO = "mama"
PASSWORD_CORRECTO = "terapias123"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown(
        "<h2 style='text-align: center; color: #5B4B8A;'>"
        "💜 Ingreso a Mi Panel Financiero</h2>",
        unsafe_allow_html=True
    )
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
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
]
tickers_cri = [
    inv.get("simbolo", "BTC")
    for inv in datos.get("inversiones", [])
    if inv.get("tipo") == "Criptomonedas"
]

cotizaciones = obtener_cotizaciones(tuple(tickers_acc), tuple(tickers_cri))
dolar_b = cotizaciones["dolar_blue"]

# ----------------- FECHA Y BARRA LATERAL LIMPIA -----------------
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
        "<h2 style='color: #5B4B8A;'>🌿 Mi Panel</h2>",
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
        clase_saldo = "metric-card-amarillo"
        carita = "😟"
        sub_saldo = "Resultado negativo (Pérdida del mes)"

    # 1. TARJETAS KPI SUPERIORES EN COLORES PASTELES MATE
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.markdown(f"""
        <div class="metric-card metric-card-costo">
            <div class="kpi-title">Costo Mensual</div>
            <div class="kpi-value">{total_costos:,.0f} ARS</div>
            <div class="kpi-usd">≈ {costos_usd:,.2f} USD</div>
            <div class="kpi-sub">{len(costos_activos)} activos</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
        <div class="metric-card metric-card-ingreso">
            <div class="kpi-title">Ingreso Mensual</div>
            <div class="kpi-value">{total_ingresos:,.0f} ARS</div>
            <div class="kpi-usd">≈ {ingresos_usd:,.2f} USD</div>
            <div class="kpi-sub">{len(ingresos_activos)} activos</div>
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

    # 2. CALCULADORA UNIFICADA DE TERAPIAS (SIN COMENTARIOS EXTRA)
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

    # 3. COLUMNAS DE COSTOS E INGRESOS CON AMPLIA SEPARACIÓN EN EL MEDIO
    col_izq, col_espacio, col_der = st.columns([1, 0.16, 1])

    with col_izq:
        st.markdown("<h3 style='color: #A04000;'>📉 Mis Costos Mensuales</h3>", unsafe_allow_html=True)
        with st.expander("➕ Agregar un Nuevo Costo"):
            with st.form("form_nuevo_costo", clear_on_submit=True):
                cat_c = st.text_input("Nombre del costo (ej. Supermercado, Luz)")
                monto_c = st.number_input("Monto Mensual (ARS)", min_value=0, step=5000)
                btn_c = st.form_submit_button("Guardar Costo", use_container_width=True)
                if btn_c and cat_c:
                    datos["costos"].append({"categoria": cat_c, "monto": monto_c, "activo": True})
                    guardar_datos(datos)
                    st.rerun()

        costos_modificados = False
        for idx, item in enumerate(datos["costos"]):
            estado_check = item.get("activo", True)
            c_box, c_nombre, c_monto, c_del = st.columns([0.4, 2.1, 1.5, 0.75])
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
                    "Nombre",
                    value=item["categoria"],
                    key=f"costo_nom_{idx}",
                    label_visibility="collapsed",
                    disabled=not estado_check
                )
                if nuevo_nom != item["categoria"]:
                    item["categoria"] = nuevo_nom
                    costos_modificados = True
            with c_monto:
                nuevo_val = st.number_input(
                    "Monto",
                    value=int(item["monto"]),
                    step=5000,
                    key=f"costo_val_{idx}",
                    label_visibility="collapsed",
                    disabled=not estado_check
                )
                if nuevo_val != item["monto"]:
                    item["monto"] = nuevo_val
                    costos_modificados = True
            with c_del:
                if st.button("🗑️", key=f"costo_del_{idx}", help="Eliminar este costo"):
                    datos["costos"].pop(idx)
                    guardar_datos(datos)
                    st.rerun()

        if costos_modificados:
            guardar_datos(datos)
            st.rerun()

    with col_der:
        st.markdown("<h3 style='color: #117864;'>📈 Mis Ingresos Mensuales</h3>", unsafe_allow_html=True)
        with st.expander("➕ Agregar un Nuevo Ingreso"):
            with st.form("form_nuevo_ingreso", clear_on_submit=True):
                nom_i = st.text_input("Concepto (ej. Sueldo Farmacia, Jubilación)")
                monto_i = st.number_input("Monto Mensual (ARS)", min_value=0, step=5000)
                btn_i = st.form_submit_button("Guardar Ingreso", use_container_width=True)
                if btn_i and nom_i:
                    datos["ingresos"].append({"concepto": nom_i, "monto": monto_i, "activo": True})
                    guardar_datos(datos)
                    st.rerun()

        ingresos_modificados = False
        for idx, item in enumerate(datos["ingresos"]):
            estado_check = item.get("activo", True)
            c_box, c_nombre, c_monto, c_del = st.columns([0.4, 2.1, 1.5, 0.75])
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
                nuevo_val = st.number_input(
                    "Monto",
                    value=int(item["monto"]),
                    step=5000,
                    key=f"ing_val_{idx}",
                    label_visibility="collapsed",
                    disabled=not estado_check
                )
                if nuevo_val != item["monto"]:
                    item["monto"] = nuevo_val
                    ingresos_modificados = True
            with c_del:
                if st.button("🗑️", key=f"ing_del_{idx}", help="Eliminar este ingreso"):
                    datos["ingresos"].pop(idx)
                    guardar_datos(datos)
                    st.rerun()

        if ingresos_modificados:
            guardar_datos(datos)
            st.rerun()

    st.markdown("---")

    # 4. GRÁFICOS DE TORTA CON PORCIONES EN DISTINTOS COLORES PASTELES
    st.markdown(
        "<h3 style='color: #5B4B8A;'>📊 Gráficos y Porcentajes Discriminados</h3>",
        unsafe_allow_html=True
    )
    col_chart_c, col_esp_g, col_chart_i = st.columns([1, 0.1, 1])

    with col_chart_c:
        st.markdown(
            "<h4 style='color: #A04000; text-align: center;'>Distribución de Costos Activos</h4>",
            unsafe_allow_html=True
        )
        if costos_activos and total_costos > 0:
            df_pie_c = pd.DataFrame(costos_activos).sort_values(by="monto", ascending=False)
            df_pie_c["USD"] = df_pie_c["monto"] / dolar_b
            df_pie_c["Porcentaje"] = (df_pie_c["monto"] / total_costos) * 100

            fig_c = px.pie(
                df_pie_c,
                values="monto",
                names="categoria",
                hole=0.42,
                color_discrete_sequence=PALETA_PASTEL
            )
            fig_c.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=15
            )
            fig_c.update_layout(
                height=440,
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False
            )
            st.plotly_chart(fig_c, use_container_width=True)

            tabla_c = df_pie_c[["categoria", "monto", "USD", "Porcentaje"]].copy()
            tabla_c.columns = ["Costo", "Valor en ARS", "Valor en USD", "% del Total"]
            tabla_c["Valor en ARS"] = tabla_c["Valor en ARS"].apply(lambda x: f"{x:,.0f} ARS")
            tabla_c["Valor en USD"] = tabla_c["Valor en USD"].apply(lambda x: f"{x:,.2f} USD")
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
            df_pie_i = pd.DataFrame(ingresos_activos).sort_values(by="monto", ascending=False)
            df_pie_i["USD"] = df_pie_i["monto"] / dolar_b
            df_pie_i["Porcentaje"] = (df_pie_i["monto"] / total_ingresos) * 100

            fig_i = px.pie(
                df_pie_i,
                values="monto",
                names="concepto",
                hole=0.42,
                color_discrete_sequence=PALETA_PASTEL
            )
            fig_i.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=15
            )
            fig_i.update_layout(
                height=440,
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False
            )
            st.plotly_chart(fig_i, use_container_width=True)

            tabla_i = df_pie_i[["concepto", "monto", "USD", "Porcentaje"]].copy()
            tabla_i.columns = ["Ingreso", "Valor en ARS", "Valor en USD", "% del Total"]
            tabla_i["Valor en ARS"] = tabla_i["Valor en ARS"].apply(lambda x: f"{x:,.0f} ARS")
            tabla_i["Valor en USD"] = tabla_i["Valor en USD"].apply(lambda x: f"{x:,.2f} USD")
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
        simbolo = inv.get("simbolo", "").upper()
        esta_activo = inv.get("activo_inv", True)

        if tipo == "Dólar Billete":
            val_usd = cant
            val_ars = cant * dolar_b
            precio_ref = f"{dolar_b:,.0f} ARS"
        elif tipo == "Criptomonedas":
            precio_u = cotizaciones.get(simbolo, 1.0)
            val_usd = cant * precio_u
            val_ars = val_usd * dolar_b
            precio_ref = f"{precio_u:,.2f} USD"
        elif tipo == "Acciones":
            precio_u = cotizaciones.get(simbolo, 100.0)
            val_usd = cant * precio_u
            val_ars = val_usd * dolar_b
            precio_ref = f"{precio_u:,.2f} USD"
        else:
            val_ars = cant
            val_usd = cant / dolar_b if dolar_b > 0 else 0
            precio_ref = "1 ARS"

        filas.append({
            "Tipo": tipo,
            "Activo": inv.get("activo", tipo),
            "Simbolo": simbolo,
            "Plataforma": inv.get("plataforma", ""),
            "Cantidad": cant,
            "Precio Unitario": precio_ref,
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

    # TARJETA ÚNICA DE PATRIMONIO TOTAL EN LILA PASTEL MATE (SIN ICONO DE BILLETE)
    st.markdown(f"""
    <div class="metric-card metric-card-lila" style="text-align: center;">
        <div class="kpi-title" style="font-size: 1.25rem;">Patrimonio Total</div>
        <div class="kpi-value" style="font-size: 2.35rem;">{total_patrimonio_ars:,.0f} ARS</div>
        <div class="kpi-usd" style="font-size: 1.2rem;">{total_patrimonio_usd:,.2f} USD</div>
        <div class="kpi-sub">Calculado automáticamente con cotizaciones en vivo</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # COLUMNAS DE INVERSIONES CON SEPARACIÓN AMPLIA
    col_inv_izq, col_inv_esp, col_inv_der = st.columns([1, 0.16, 1.7])

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

        simbolo_sugerido = "USD"
        nombre_act = "Dólar Billete"
        tipo_guardar = "Dólar Billete"

        if tipo_elegido.startswith("A"):
            tipo_guardar = "Dólar Billete"
            nombre_act = "Dólar Billete"
            simbolo_sugerido = "USD"
        elif tipo_elegido.startswith("B"):
            tipo_guardar = "Pesos ARS"
            nombre_act = "Pesos ARS"
            simbolo_sugerido = "ARS"
        elif tipo_elegido.startswith("C"):
            tipo_guardar = "Acciones"
            opciones_acc = [
                "AAPL (Apple)", "KO (Coca-Cola)", "MELI (MercadoLibre)",
                "SPY (S&P 500)", "MSFT (Microsoft)", "GOOGL (Google)",
                "NVDA (Nvidia)", "TSLA (Tesla)", "AMZN (Amazon)",
                "YPFD (YPF)", "Otra acción..."
            ]
            ticker_lista = st.selectbox("Seleccioná la Acción", opciones_acc)
            if ticker_lista == "Otra acción...":
                simbolo_sugerido = st.text_input(
                    "Símbolo de la Acción (ej. DIS, V)",
                    value="DIS"
                ).upper()
                nombre_act = simbolo_sugerido
            else:
                simbolo_sugerido = ticker_lista.split(" ")[0]
                nombre_act = ticker_lista
        elif tipo_elegido.startswith("D"):
            tipo_guardar = "Criptomonedas"
            simbolo_sugerido = st.selectbox(
                "Seleccioná la Criptomoneda",
                ["BTC", "ETH", "USDT", "SOL", "BNB"]
            )
            nombre_act = simbolo_sugerido
        elif tipo_elegido.startswith("E"):
            tipo_guardar = "Otros"
            detalle_otro = st.text_input(
                "Detalle qué es (ej. FCI, PF UVA, etc.)"
            )
            nombre_act = detalle_otro.strip() if detalle_otro.strip() else "Otros"
            simbolo_sugerido = "ARS"

        plat_act = st.text_input("2. Ubicación, ¿dónde está?")
        cant_act = st.number_input(
            "3. Cantidad que tenés",
            min_value=0.0,
            step=1.0,
            format="%.4f"
        )

        if st.button("Guardar Activo", use_container_width=True):
            if cant_act > 0:
                datos["inversiones"].append({
                    "tipo": tipo_guardar,
                    "activo": nombre_act,
                    "simbolo": simbolo_sugerido,
                    "cantidad": cant_act,
                    "plataforma": plat_act,
                    "activo_inv": True
                })
                guardar_datos(datos)
                st.cache_data.clear()
                st.rerun()

    with col_inv_der:
        st.markdown(
            "<h3 style='color: #5B4B8A;'>📋 Mis Activos</h3>",
            unsafe_allow_html=True
        )
        if inversiones:
            inv_cambios = False
            for idx, inv in enumerate(inversiones):
                st_act = inv.get("activo_inv", True)
                c_chk, c_nom, c_cant, c_plat, c_del = st.columns([0.4, 1.5, 1.3, 1.3, 0.75])

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
                        "Activo",
                        value=inv.get("activo", ""),
                        key=f"inv_nom_{idx}",
                        label_visibility="collapsed",
                        disabled=not st_act
                    )
                    if nuevo_nom_inv != inv.get("activo", ""):
                        inv["activo"] = nuevo_nom_inv
                        inv_cambios = True

                with c_cant:
                    nueva_c = st.number_input(
                        "Cantidad",
                        value=float(inv.get("cantidad", 0)),
                        step=1.0,
                        format="%.4f",
                        key=f"inv_cant_{idx}",
                        label_visibility="collapsed",
                        disabled=not st_act
                    )
                    if nueva_c != float(inv.get("cantidad", 0)):
                        inv["cantidad"] = nueva_c
                        inv_cambios = True

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

    # GRÁFICOS PIE CHART DE INVERSIONES CON TABLAS DEBAJO
    st.markdown(
        "<h3 style='color: #5B4B8A;'>📊 Distribución Detallada de Mi Cartera</h3>",
        unsafe_allow_html=True
    )
    if not df_inv_activos.empty and total_patrimonio_ars > 0:
        col_g_inv1, col_g_esp, col_g_inv2 = st.columns([1, 0.1, 1])

        with col_g_inv1:
            st.markdown(
                "<h4 style='color: #5B4B8A; text-align: center;'>Por Tipo de Activo</h4>",
                unsafe_allow_html=True
            )
            resumen_tipo = df_inv_activos.groupby("Tipo", as_index=False).agg({
                "Valor en ARS": "sum",
                "Valor en USD": "sum"
            }).sort_values(by="Valor en ARS", ascending=False)
            resumen_tipo["%"] = (resumen_tipo["Valor en ARS"] / total_patrimonio_ars) * 100

            fig_inv_tipo = px.pie(
                resumen_tipo,
                values="Valor en ARS",
                names="Tipo",
                hole=0.42,
                color_discrete_sequence=PALETA_PASTEL
            )
            fig_inv_tipo.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=15
            )
            fig_inv_tipo.update_layout(
                height=440,
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False
            )
            st.plotly_chart(fig_inv_tipo, use_container_width=True)

            tabla_t = resumen_tipo.copy()
            tabla_t["Valor en ARS"] = tabla_t["Valor en ARS"].apply(lambda x: f"{x:,.0f} ARS")
            tabla_t["Valor en USD"] = tabla_t["Valor en USD"].apply(lambda x: f"{x:,.2f} USD")
            tabla_t["%"] = tabla_t["%"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_t, use_container_width=True, hide_index=True)

        with col_g_inv2:
            st.markdown(
                "<h4 style='color: #5B4B8A; text-align: center;'>Por Activo y Ubicación</h4>",
                unsafe_allow_html=True
            )
            df_det = df_inv_activos.sort_values(by="Valor en ARS", ascending=False).copy()
            df_det["Etiqueta"] = df_det["Activo"] + " (" + df_det["Plataforma"] + ")"
            df_det["%"] = (df_det["Valor en ARS"] / total_patrimonio_ars) * 100

            fig_inv_det = px.pie(
                df_det,
                values="Valor en ARS",
                names="Etiqueta",
                hole=0.42,
                color_discrete_sequence=PALETA_PASTEL
            )
            fig_inv_det.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=15
            )
            fig_inv_det.update_layout(
                height=440,
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False
            )
            st.plotly_chart(fig_inv_det, use_container_width=True)

            cols_d = [
                "Activo", "Plataforma", "Cantidad",
                "Valor en ARS", "Valor en USD", "%"
            ]
            tabla_d = df_det[cols_d].copy()
            tabla_d.columns = [
                "Activo", "Ubicación", "Cantidad",
                "Valor en ARS", "Valor en USD", "%"
            ]
            tabla_d["Valor en ARS"] = tabla_d["Valor en ARS"].apply(lambda x: f"{x:,.0f} ARS")
            tabla_d["Valor en USD"] = tabla_d["Valor en USD"].apply(lambda x: f"{x:,.2f} USD")
            tabla_d["%"] = tabla_d["%"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_d, use_container_width=True, hide_index=True)
    else:
        st.info("No hay inversiones activas para mostrar en los gráficos.")
