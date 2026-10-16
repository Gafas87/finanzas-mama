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
                    data["ingresos"] = [
                        {
                            "concepto": i["concepto"],
                            "monto": i["monto"],
                            "activo": True
                        }
                        for i in data["ingresos_otros"]
                    ]
                data.setdefault(
                    "config_visual",
                    {
                        "tamano_letra": "Grande (Recomendado)",
                        "tema": "Violeta Elegante"
                    }
                )
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
                "activo": "USD Ahorro",
                "simbolo": "USD",
                "cantidad": 1200,
                "plataforma": "Caja de seguridad",
                "activo_inv": True,
                "precio_manual": 0.0
            },
            {
                "tipo": "Acciones / CEDEARs",
                "activo": "Apple (AAPL)",
                "simbolo": "AAPL",
                "cantidad": 20,
                "plataforma": "Balanz",
                "activo_inv": True,
                "precio_manual": 0.0
            },
            {
                "tipo": "Criptomonedas",
                "activo": "Bitcoin",
                "simbolo": "BTC",
                "cantidad": 0.015,
                "plataforma": "Binance",
                "activo_inv": True,
                "precio_manual": 0.0
            },
            {
                "tipo": "Efectivo / Banco",
                "activo": "Caja de Ahorro Pesos",
                "simbolo": "ARS",
                "cantidad": 350000,
                "plataforma": "Banco",
                "activo_inv": True,
                "precio_manual": 0.0
            }
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


# ----------------- AUTENTICACIÓN -----------------
USUARIO_CORRECTO = "mama"
PASSWORD_CORRECTO = "terapias123"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown(
        "<h1 style='text-align: center; color: #4b367c;'>"
        "💜 Ingreso a Mi Panel Financiero</h1>",
        unsafe_allow_html=True
    )
    c1, c2, c3 = st.columns([1, 1.6, 1])
    with c2:
        with st.form("login_form"):
            user = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button(
                "Ingresar al Panel",
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

# ----------------- CARGA DE DATOS Y ESTILOS -----------------
datos = cargar_datos()

tickers_acc = [
    inv.get("simbolo", "AAPL")
    for inv in datos.get("inversiones", [])
    if inv.get("tipo") == "Acciones / CEDEARs"
]
tickers_cri = [
    inv.get("simbolo", "BTC")
    for inv in datos.get("inversiones", [])
    if inv.get("tipo") == "Criptomonedas"
]

cotizaciones = obtener_cotizaciones(tuple(tickers_acc), tuple(tickers_cri))
dolar_b = cotizaciones["dolar_blue"]

cfg_vis = datos.get("config_visual", {})
mapa_fuente = {
    "Normal": "16px",
    "Grande (Recomendado)": "19px",
    "Extra Grande (Máxima Lectura)": "22px"
}
tam_sel = cfg_vis.get("tamano_letra", "Grande (Recomendado)")
font_px = mapa_fuente.get(tam_sel, "19px")

mapa_tema = {
    "Violeta Elegante": ("#2e1e5b", "#4b367c", "#9b59b6"),
    "Azul Real": ("#0f2b48", "#1f4e78", "#3498db"),
    "Verde Esmeralda": ("#11382a", "#1e6b52", "#2ecc71")
}
tema_sel = cfg_vis.get("tema", "Violeta Elegante")
colores_tema = mapa_tema.get(tema_sel, ("#2e1e5b", "#4b367c", "#9b59b6"))
color_osc = colores_tema[0]
color_med = colores_tema[1]
color_borde = colores_tema[2]

st.markdown(f"""
<style>
    html, body, [class*="css"], p, span, label, div {{
        font-size: {font_px};
    }}
    .metric-card {{
        padding: 1.35rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        color: white;
        box-shadow: 0 5px 12px rgba(0,0,0,0.14);
    }}
    .metric-card-costo {{
        background: linear-gradient(135deg, #7b1113, #b33939);
        border-left: 7px solid #ff5252;
    }}
    .metric-card-ingreso {{
        background: linear-gradient(135deg, #1b4d3e, #27ae60);
        border-left: 7px solid #2ecc71;
    }}
    .metric-card-superavit {{
        background: linear-gradient(135deg, {color_osc}, {color_med});
        border-left: 7px solid {color_borde};
    }}
    .metric-card-alerta {{
        background: linear-gradient(135deg, #8a6d1c, #d35400);
        border-left: 7px solid #f39c12;
    }}
    .metric-card-deficit {{
        background: linear-gradient(135deg, #5b1414, #8b0000);
        border-left: 7px solid #ff4757;
    }}
    .kpi-title {{
        font-size: 1.15rem;
        font-weight: 600;
        opacity: 0.95;
        margin-bottom: 0.25rem;
    }}
    .kpi-value {{
        font-size: 2.35rem;
        font-weight: 800;
        line-height: 1.15;
    }}
    .kpi-usd {{
        font-size: 1.15rem;
        font-weight: 600;
        color: #f1f2f6;
        margin-top: 0.3rem;
        background: rgba(0,0,0,0.22);
        display: inline-block;
        padding: 3px 10px;
        border-radius: 8px;
    }}
    .kpi-sub {{
        font-size: 0.95rem;
        opacity: 0.9;
        margin-top: 0.45rem;
    }}
    .badge-activo {{
        background-color: #e8f5e9;
        color: #1b5e20;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }}
    .badge-pausado {{
        background-color: #dcdde1;
        color: #57606f;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }}
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {{
        font-size: 1.35rem;
        font-weight: 800;
        color: {color_med};
    }}
</style>
""", unsafe_allow_html=True)

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
        f"<h2 style='color: {color_med};'>🌿 Mi Panel</h2>",
        unsafe_allow_html=True
    )
    st.markdown(f"🗓️ **{fecha_hora_texto}**")
    st.markdown("---")
    st.markdown(f"💵 **Dólar Blue:** `${dolar_b:,.0f}`")
    st.markdown(f"🪙 **Bitcoin:** `USD {cotizaciones['BTC']:,.0f}`")
    if st.button("🔄 Actualizar Cotizaciones", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    with st.expander("🎨 Personalizar Letra y Colores"):
        opciones_tam = [
            "Normal",
            "Grande (Recomendado)",
            "Extra Grande (Máxima Lectura)"
        ]
        idx_tam = opciones_tam.index(tam_sel) if tam_sel in opciones_tam else 1
        nuevo_tam = st.selectbox("Tamaño de Letra", opciones_tam, index=idx_tam)

        opciones_tema = ["Violeta Elegante", "Azul Real", "Verde Esmeralda"]
        idx_tem = opciones_tema.index(tema_sel) if tema_sel in opciones_tema else 0
        nuevo_tema = st.selectbox("Color Principal", opciones_tema, index=idx_tem)

        if nuevo_tam != tam_sel or nuevo_tema != tema_sel:
            datos["config_visual"] = {
                "tamano_letra": nuevo_tam,
                "tema": nuevo_tema
            }
            guardar_datos(datos)
            st.rerun()

    with st.expander("💾 Copia de Seguridad"):
        st.download_button(
            "⬇️ Descargar Mis Datos",
            data=json.dumps(datos, ensure_ascii=False, indent=4),
            file_name="respaldo_finanzas_mama.json",
            mime="application/json",
            use_container_width=True
        )
        archivo_subido = st.file_uploader("⬆️ Restaurar copia", type=["json"])
        if archivo_subido is not None:
            try:
                datos_restaurados = json.load(archivo_subido)
                guardar_datos(datos_restaurados)
                st.success("¡Datos restaurados!")
                st.rerun()
            except Exception:
                st.error("Archivo inválido.")

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
    costos_pausados = [c for c in datos["costos"] if not c.get("activo", True)]
    total_costos = sum(c["monto"] for c in costos_activos)

    ingresos_activos = [i for i in datos["ingresos"] if i.get("activo", True)]
    ingresos_pausados = [i for i in datos["ingresos"] if not i.get("activo", True)]
    total_ingresos = sum(i["monto"] for i in ingresos_activos)

    saldo_neto = total_ingresos - total_costos

    costos_usd = total_costos / dolar_b if dolar_b > 0 else 0
    ingresos_usd = total_ingresos / dolar_b if dolar_b > 0 else 0
    saldo_usd = saldo_neto / dolar_b if dolar_b > 0 else 0

    ratio_ahorro = (saldo_neto / total_ingresos) if total_ingresos > 0 else -1.0
    if saldo_neto > 0 and ratio_ahorro >= 0.15:
        clase_saldo = "metric-card-superavit"
        estado_saldo = "🟢 Superávit Saludable"
        sub_saldo = f"Capacidad de ahorro: {ratio_ahorro*100:.1f}% de tus ingresos"
    elif saldo_neto >= 0:
        clase_saldo = "metric-card-alerta"
        estado_saldo = "🟡 Balance Ajustado"
        sub_saldo = f"Ahorro moderado: {ratio_ahorro*100:.1f}%. Atenta a imprevistos."
    else:
        clase_saldo = "metric-card-deficit"
        estado_saldo = "🔴 Déficit / En Pérdida"
        sub_saldo = "Los costos activos superan a los ingresos activos."

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.markdown(f"""
        <div class="metric-card metric-card-costo">
            <div class="kpi-title">📉 Costos Totales Mensuales</div>
            <div class="kpi-value">${total_costos:,.0f}</div>
            <div class="kpi-usd">≈ USD {costos_usd:,.2f}</div>
            <div class="kpi-sub">✅ {len(costos_activos)} activos | ⏸️ {len(costos_pausados)} pausados</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
        <div class="metric-card metric-card-ingreso">
            <div class="kpi-title">📈 Ingresos Totales Mensuales</div>
            <div class="kpi-value">${total_ingresos:,.0f}</div>
            <div class="kpi-usd">≈ USD {ingresos_usd:,.2f}</div>
            <div class="kpi-sub">✅ {len(ingresos_activos)} activos | ⏸️ {len(ingresos_pausados)} pausados</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi3:
        st.markdown(f"""
        <div class="metric-card {clase_saldo}">
            <div class="kpi-title">⚖️ Saldo Neto ({estado_saldo})</div>
            <div class="kpi-value">${saldo_neto:,.0f}</div>
            <div class="kpi-usd">≈ USD {saldo_usd:,.2f}</div>
            <div class="kpi-sub">{sub_saldo}</div>
        </div>
        """, unsafe_allow_html=True)

    # CALCULADORA UNIFICADA DE TERAPIAS
    titulo_exp = "🧘‍♀️ **Calculadora de Terapias: ¿Cuántas sesiones necesito según lo que está activo abajo?**"
    with st.expander(titulo_exp, expanded=True):
        col_c1, col_c2 = st.columns([1.1, 2.6])
        with col_c1:
            precio_sesion = st.number_input(
                "Valor por sesión de terapia ($):",
                value=int(datos.get("precio_terapia", 30000)),
                step=2000,
                format="%d"
            )
            if precio_sesion != datos.get("precio_terapia"):
                datos["precio_terapia"] = precio_sesion
                guardar_datos(datos)
            st.caption(f"Equivale a **USD {precio_sesion/dolar_b:,.2f}** por sesión.")
            st.caption("💡 *Destildá abajo el Sueldo Farmacia o el SAC para ver cuántas terapias necesitás sin esos ingresos.*")

        faltante = total_costos - total_ingresos
        sesiones_mes = max(0.0, faltante / precio_sesion) if precio_sesion > 0 else 0.0
        sesiones_sem = sesiones_mes / 4.33
        sesiones_anio = sesiones_mes * 12

        with col_c2:
            if faltante <= 0:
                st.markdown(f"""
                <div style="background-color: #e8f5e9; border: 2px solid #2e7d32; padding: 20px; border-radius: 14px;">
                    <b style="color: #1b5e20; font-size: 1.3rem;">✨ ¡Tus costos activos están 100% cubiertos!</b><br>
                    Con los ingresos que tenés tildados hoy, cubrís todos tus gastos y te queda un ahorro a favor de <b>${abs(saldo_neto):,.0f}</b> (USD {abs(saldo_usd):,.2f}) por mes.<br>
                    <small style="color: #2e7d32;">👉 Para simular cuántas sesiones necesitarías al cerrar la farmacia, destildá esos ingresos en la lista de abajo.</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #f3e5f5; border: 2px solid #8e24aa; padding: 20px; border-radius: 14px;">
                    <b style="color: #4a148c; font-size: 1.25rem;">🎯 Sesiones requeridas para cubrir tus costos activos:</b><br>
                    Para cubrir la diferencia actual de <b>${faltante:,.0f}/mes</b> (USD {faltante/dolar_b:,.2f}), necesitás realizar:
                    <div style="font-size: 2.3rem; font-weight: 800; color: #6a1b9a; margin: 6px 0;">
                        {sesiones_mes:.1f} sesiones por mes
                    </div>
                    <span style="font-size: 1.1rem; color: #4a148c;">
                        📅 <b>{sesiones_sem:.1f} sesiones por semana</b> &nbsp;|&nbsp; 🗓️ <b>{sesiones_anio:.0f} sesiones al año</b>
                    </span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # COLUMNAS INTERACTIVAS: COSTOS E INGRESOS
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("<h3 style='color: #b33939;'>📉 Mis Costos Mensuales</h3>", unsafe_allow_html=True)
        with st.expander("➕ Agregar un Nuevo Costo"):
            with st.form("form_nuevo_costo", clear_on_submit=True):
                cat_c = st.text_input("Nombre del costo (ej. Supermercado, Luz)")
                monto_c = st.number_input("Monto Mensual ($)", min_value=0, step=5000)
                btn_c = st.form_submit_button("Guardar Costo", use_container_width=True)
                if btn_c and cat_c:
                    datos["costos"].append({"categoria": cat_c, "monto": monto_c, "activo": True})
                    guardar_datos(datos)
                    st.rerun()

        st.caption("Tildá o destildá la casilla izquierda para activar o pausar cada costo:")
        costos_modificados = False
        for idx, item in enumerate(datos["costos"]):
            estado_check = item.get("activo", True)
            c_box, c_nombre, c_monto, c_del = st.columns([0.45, 2.1, 1.55, 0.5])
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
                if estado_check:
                    usd_item = item['monto'] / dolar_b
                    st.markdown(
                        f"<span class='badge-activo'>✅ Activo</span> "
                        f"<small>≈ USD {usd_item:,.1f}</small>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        "<span class='badge-pausado'>⏸️ PAUSADO (No suma)</span>",
                        unsafe_allow_html=True
                    )
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
                if st.button("🗑️", key=f"costo_del_{idx}"):
                    datos["costos"].pop(idx)
                    guardar_datos(datos)
                    st.rerun()

        if costos_modificados:
            guardar_datos(datos)
            st.rerun()

    with col_der:
        st.markdown("<h3 style='color: #27ae60;'>📈 Mis Ingresos Mensuales</h3>", unsafe_allow_html=True)
        with st.expander("➕ Agregar un Nuevo Ingreso"):
            with st.form("form_nuevo_ingreso", clear_on_submit=True):
                nom_i = st.text_input("Concepto (ej. Sueldo Farmacia, Jubilación)")
                monto_i = st.number_input("Monto Mensual ($)", min_value=0, step=5000)
                btn_i = st.form_submit_button("Guardar Ingreso", use_container_width=True)
                if btn_i and nom_i:
                    datos["ingresos"].append({"concepto": nom_i, "monto": monto_i, "activo": True})
                    guardar_datos(datos)
                    st.rerun()

        st.caption("Tildá o destildá la casilla izquierda para activar o pausar cada ingreso:")
        ingresos_modificados = False
        for idx, item in enumerate(datos["ingresos"]):
            estado_check = item.get("activo", True)
            c_box, c_nombre, c_monto, c_del = st.columns([0.45, 2.1, 1.55, 0.5])
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
                if estado_check:
                    usd_ing = item['monto'] / dolar_b
                    st.markdown(
                        f"<span class='badge-activo'>✅ Activo</span> "
                        f"<small>≈ USD {usd_ing:,.1f}</small>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        "<span class='badge-pausado'>⏸️ PAUSADO (No suma)</span>",
                        unsafe_allow_html=True
                    )
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
                if st.button("🗑️", key=f"ing_del_{idx}"):
                    datos["ingresos"].pop(idx)
                    guardar_datos(datos)
                    st.rerun()

        if ingresos_modificados:
            guardar_datos(datos)
            st.rerun()

    st.markdown("---")

    # GRÁFICOS PIE CHART GRANDES CON TABLA DEBAJO
    st.markdown(
        f"<h3 style='color: {color_med};'>📊 Gráficos y Porcentajes Discriminados</h3>",
        unsafe_allow_html=True
    )
    col_chart_c, col_chart_i = st.columns(2)

    with col_chart_c:
        st.markdown(
            "<h4 style='color: #b33939; text-align: center;'>Distribución de Costos Activos</h4>",
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
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_c.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=16
            )
            fig_c.update_layout(
                height=460,
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False
            )
            st.plotly_chart(fig_c, use_container_width=True)

            tabla_c = df_pie_c[["categoria", "monto", "USD", "Porcentaje"]].copy()
            tabla_c.columns = ["Costo", "Valor ($)", "En USD", "% del Total"]
            tabla_c["Valor ($)"] = tabla_c["Valor ($)"].apply(lambda x: f"${x:,.0f}")
            tabla_c["En USD"] = tabla_c["En USD"].apply(lambda x: f"USD {x:,.1f}")
            tabla_c["% del Total"] = tabla_c["% del Total"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_c, use_container_width=True, hide_index=True)
        else:
            st.info("No hay costos activos para graficar.")

    with col_chart_i:
        st.markdown(
            "<h4 style='color: #27ae60; text-align: center;'>Distribución de Ingresos Activos</h4>",
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
                color_discrete_sequence=px.colors.sequential.Tealgrn_r
            )
            fig_i.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=16
            )
            fig_i.update_layout(
                height=460,
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False
            )
            st.plotly_chart(fig_i, use_container_width=True)

            tabla_i = df_pie_i[["concepto", "monto", "USD", "Porcentaje"]].copy()
            tabla_i.columns = ["Ingreso", "Valor ($)", "En USD", "% del Total"]
            tabla_i["Valor ($)"] = tabla_i["Valor ($)"].apply(lambda x: f"${x:,.0f}")
            tabla_i["En USD"] = tabla_i["En USD"].apply(lambda x: f"USD {x:,.1f}")
            tabla_i["% del Total"] = tabla_i["% del Total"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_i, use_container_width=True, hide_index=True)
        else:
            st.info("No hay ingresos activos para graficar.")


# =========================================================================
# =========================== PESTAÑA 2 ===================================
# =========================================================================
with pestana2:
    st.markdown(
        f"<h2 style='color: {color_med};'>💎 Mi Cartera de Inversiones y Ahorros</h2>",
        unsafe_allow_html=True
    )

    inversiones = datos.get("inversiones", [])
    filas = []

    for inv in inversiones:
        cant = float(inv.get("cantidad", 0))
        tipo = inv.get("tipo", "Efectivo / Banco")
        simbolo = inv.get("simbolo", "").upper()
        esta_activo = inv.get("activo_inv", True)
        precio_man = float(inv.get("precio_manual", 0.0))

        if tipo == "Dólar Billete":
            val_usd = cant
            val_ars = cant * dolar_b
            precio_ref = f"1 USD = ${dolar_b:,.0f}"
        elif tipo == "Criptomonedas":
            precio_u = precio_man if precio_man > 0 else cotizaciones.get(simbolo, 1.0)
            val_usd = cant * precio_u
            val_ars = val_usd * dolar_b
            precio_ref = f"USD {precio_u:,.2f}"
        elif tipo == "Acciones / CEDEARs":
            precio_u = precio_man if precio_man > 0 else cotizaciones.get(simbolo, 100.0)
            val_usd = cant * precio_u
            val_ars = val_usd * dolar_b
            precio_ref = f"USD {precio_u:,.2f}"
        else:
            val_ars = cant
            val_usd = cant / dolar_b if dolar_b > 0 else 0
            precio_ref = "$1 ARS"

        filas.append({
            "Tipo": tipo,
            "Activo": inv.get("activo", ""),
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

    col_pat1, col_pat2 = st.columns(2)
    with col_pat1:
        st.markdown(f"""
        <div class="metric-card metric-card-superavit">
            <div class="kpi-title">💵 Patrimonio Total en Pesos (ARS)</div>
            <div class="kpi-value">${total_patrimonio_ars:,.0f}</div>
            <div class="kpi-usd">≈ USD {total_patrimonio_usd:,.2f}</div>
            <div class="kpi-sub">Calculado automáticamente con cotizaciones en vivo</div>
        </div>
        """, unsafe_allow_html=True)
    with col_pat2:
        st.markdown(f"""
        <div class="metric-card metric-card-ingreso">
            <div class="kpi-title">🌎 Patrimonio Total en Dólares (USD)</div>
            <div class="kpi-value">USD {total_patrimonio_usd:,.2f}</div>
            <div class="kpi-usd">≈ ${total_patrimonio_ars:,.0f} ARS</div>
            <div class="kpi-sub">Dólar Blue de referencia: ${dolar_b:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    if not df_inv_activos.empty:
        tipos_unicos = [
            "Dólar Billete",
            "Efectivo / Banco",
            "Acciones / CEDEARs",
            "Criptomonedas"
        ]
        cols_sub = st.columns(4)
        for i_t, t_nom in enumerate(tipos_unicos):
            sub_df = df_inv_activos[df_inv_activos["Tipo"] == t_nom]
            suma_u = sub_df["Valor en USD"].sum() if not sub_df.empty else 0
            suma_a = sub_df["Valor en ARS"].sum() if not sub_df.empty else 0
            cols_sub[i_t].metric(
                label=f"📌 {t_nom}",
                value=f"USD {suma_u:,.2f}",
                delta=f"${suma_a:,.0f} ARS",
                delta_color="off"
            )

    st.markdown("---")

    col_inv_izq, col_inv_der = st.columns([1.05, 1.95])

    with col_inv_izq:
        st.markdown(
            f"<h3 style='color: {color_med};'>➕ Agregar Nuevo Activo</h3>",
            unsafe_allow_html=True
        )
        tipo_sel = st.selectbox(
            "1. Tipo de Activo",
            ["Dólar Billete", "Efectivo / Banco", "Acciones / CEDEARs", "Criptomonedas"]
        )

        with st.form("form_nuevo_activo", clear_on_submit=True):
            nombre_act = st.text_input("Nombre descriptivo (ej. Dólares Caja, Apple)")
            simbolo_sugerido = "USD"

            if tipo_sel == "Criptomonedas":
                simbolo_sugerido = st.selectbox(
                    "Seleccioná Criptomoneda (Binance)",
                    ["BTC", "ETH", "USDT", "SOL", "BNB"]
                )
            elif tipo_sel == "Acciones / CEDEARs":
                opciones_acc = [
                    "AAPL (Apple)", "KO (Coca-Cola)", "MELI (MercadoLibre)",
                    "SPY (S&P 500)", "MSFT (Microsoft)", "GOOGL (Google)",
                    "NVDA (Nvidia)", "TSLA (Tesla)", "AMZN (Amazon)",
                    "YPFD (YPF)", "Otra acción..."
                ]
                ticker_lista = st.selectbox("Seleccioná la Acción", opciones_acc)
                if ticker_lista == "Otra acción...":
                    simbolo_sugerido = st.text_input(
                        "Símbolo/Ticker en EE.UU. (ej. DIS, V)",
                        value="DIS"
                    ).upper()
                else:
                    simbolo_sugerido = ticker_lista.split(" ")[0]
            elif tipo_sel == "Efectivo / Banco":
                simbolo_sugerido = "ARS"

            plat_act = st.text_input("Plataforma / Dónde está (ej. Balanz, Banco, Casa)")
            cant_act = st.number_input(
                "Cantidad que tenés",
                min_value=0.0,
                step=1.0,
                format="%.4f"
            )

            btn_guardar_act = st.form_submit_button(
                "Guardar en Mi Cartera",
                use_container_width=True
            )
            if btn_guardar_act and nombre_act:
                datos["inversiones"].append({
                    "tipo": tipo_sel,
                    "activo": nombre_act,
                    "simbolo": simbolo_sugerido,
                    "cantidad": cant_act,
                    "plataforma": plat_act,
                    "activo_inv": True,
                    "precio_manual": 0.0
                })
                guardar_datos(datos)
                st.cache_data.clear()
                st.rerun()

    with col_inv_der:
        st.markdown(
            f"<h3 style='color: {color_med};'>📋 Mis Activos (Activar / Pausar / Editar)</h3>",
            unsafe_allow_html=True
        )
        st.caption("Tildá o destildá la casilla izquierda para incluir o pausar un activo:")
        if inversiones:
            inv_cambios = False
            for idx, inv in enumerate(inversiones):
                st_act = inv.get("activo_inv", True)
                fila_calc = filas[idx]
                c_chk, c_nom, c_cant, c_plat, c_del = st.columns([0.4, 1.6, 1.1, 1.2, 0.45])

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
                    if st_act:
                        v_u = fila_calc['Valor en USD']
                        v_a = fila_calc['Valor en ARS']
                        st.markdown(
                            f"<span class='badge-activo'>✅ USD {v_u:,.2f}</span> "
                            f"<small>(${v_a:,.0f})</small>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            "<span class='badge-pausado'>⏸️ PAUSADO (No suma)</span>",
                            unsafe_allow_html=True
                        )

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
                    st.caption(f"Cant. ({fila_calc['Precio Unitario']})")

                with c_plat:
                    nueva_p = st.text_input(
                        "Plataforma",
                        value=inv.get("plataforma", ""),
                        key=f"inv_p_{idx}",
                        label_visibility="collapsed",
                        disabled=not st_act
                    )
                    if nueva_p != inv.get("plataforma", ""):
                        inv["plataforma"] = nueva_p
                        inv_cambios = True
                    st.caption(f"📍 {inv.get('tipo')}")

                with c_del:
                    if st.button("🗑️", key=f"inv_del_{idx}"):
                        datos["inversiones"].pop(idx)
                        guardar_datos(datos)
                        st.rerun()

            if inv_cambios:
                guardar_datos(datos)
                st.rerun()
        else:
            st.info("No hay activos cargados aún.")

    st.markdown("---")

    # GRÁFICOS PIE CHART GRANDES DE INVERSIONES CON TABLAS DEBAJO
    st.markdown(
        f"<h3 style='color: {color_med};'>📊 Distribución Detallada de Mi Cartera</h3>",
        unsafe_allow_html=True
    )
    if not df_inv_activos.empty and total_patrimonio_ars > 0:
        col_g_inv1, col_g_inv2 = st.columns(2)

        with col_g_inv1:
            st.markdown(
                f"<h4 style='color: {color_med}; text-align: center;'>Por Tipo de Inversión</h4>",
                unsafe_allow_html=True
            )
            resumen_tipo = df_inv_activos.groupby("Tipo", as_index=False).agg({
                "Valor en ARS": "sum",
                "Valor en USD": "sum"
            }).sort_values(by="Valor en ARS", ascending=False)
            resumen_tipo["% Cartera"] = (resumen_tipo["Valor en ARS"] / total_patrimonio_ars) * 100

            fig_inv_tipo = px.pie(
                resumen_tipo,
                values="Valor en ARS",
                names="Tipo",
                hole=0.42,
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig_inv_tipo.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=16
            )
            fig_inv_tipo.update_layout(
                height=460,
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False
            )
            st.plotly_chart(fig_inv_tipo, use_container_width=True)

            tabla_t = resumen_tipo.copy()
            tabla_t["Valor en ARS"] = tabla_t["Valor en ARS"].apply(lambda x: f"${x:,.0f}")
            tabla_t["Valor en USD"] = tabla_t["Valor en USD"].apply(lambda x: f"USD {x:,.2f}")
            tabla_t["% Cartera"] = tabla_t["% Cartera"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_t, use_container_width=True, hide_index=True)

        with col_g_inv2:
            st.markdown(
                f"<h4 style='color: {color_med}; text-align: center;'>Por Activo y Plataforma</h4>",
                unsafe_allow_html=True
            )
            df_det = df_inv_activos.sort_values(by="Valor en ARS", ascending=False).copy()
            df_det["Etiqueta"] = df_det["Activo"] + " (" + df_det["Plataforma"] + ")"
            df_det["% Cartera"] = (df_det["Valor en ARS"] / total_patrimonio_ars) * 100

            fig_inv_det = px.pie(
                df_det,
                values="Valor en ARS",
                names="Etiqueta",
                hole=0.42,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_inv_det.update_traces(
                textposition='inside',
                textinfo='percent+label',
                textfont_size=16
            )
            fig_inv_det.update_layout(
                height=460,
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False
            )
            st.plotly_chart(fig_inv_det, use_container_width=True)

            cols_d = [
                "Activo", "Plataforma", "Cantidad",
                "Precio Unitario", "Valor en USD", "Valor en ARS", "% Cartera"
            ]
            tabla_d = df_det[cols_d].copy()
            tabla_d["Valor en USD"] = tabla_d["Valor en USD"].apply(lambda x: f"USD {x:,.2f}")
            tabla_d["Valor en ARS"] = tabla_d["Valor en ARS"].apply(lambda x: f"${x:,.0f}")
            tabla_d["% Cartera"] = tabla_d["% Cartera"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_d, use_container_width=True, hide_index=True)
    else:
        st.info("No hay inversiones activas para mostrar en los gráficos.")
