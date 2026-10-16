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

# Estilos CSS de alta legibilidad
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-size: 17px;
    }
    .metric-card {
        padding: 1.2rem;
        border-radius: 14px;
        margin-bottom: 1rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card-costo {
        background: linear-gradient(135deg, #7b1113, #b33939);
        border-left: 6px solid #e74c3c;
    }
    .metric-card-ingreso {
        background: linear-gradient(135deg, #1b4d3e, #27ae60);
        border-left: 6px solid #2ecc71;
    }
    .metric-card-superavit {
        background: linear-gradient(135deg, #2e1e5b, #4b367c);
        border-left: 6px solid #9b59b6;
    }
    .metric-card-alerta {
        background: linear-gradient(135deg, #8a6d1c, #d35400);
        border-left: 6px solid #f39c12;
    }
    .metric-card-deficit {
        background: linear-gradient(135deg, #5b1414, #8b0000);
        border-left: 6px solid #ff4757;
    }
    .kpi-title {
        font-size: 1.15rem;
        font-weight: 600;
        opacity: 0.95;
        margin-bottom: 0.2rem;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .kpi-usd {
        font-size: 1.05rem;
        font-weight: 500;
        opacity: 0.9;
        margin-top: 0.2rem;
    }
    .kpi-sub {
        font-size: 0.95rem;
        opacity: 0.85;
        margin-top: 0.3rem;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.3rem;
        font-weight: 700;
        color: #4b367c;
    }
</style>
""", unsafe_allow_html=True)

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
                if "ingresos" not in data and "ingresos_otros" in data:
                    data["ingresos"] = [{"concepto": i["concepto"], "monto": i["monto"], "activo": True} for i in data["ingresos_otros"]]
                return data
        except Exception:
            pass
    return {
        "costos": [
            {"categoria": "Alquiler / Expensas", "monto": 250000, "activo": True},
            {"categoria": "Servicios (Luz, Gas, Agua, Internet)", "monto": 75000, "activo": True},
            {"categoria": "Supermercado y Comida", "monto": 280000, "activo": True},
            {"categoria": "Insumos Gabinete", "monto": 45000, "activo": True},
            {"categoria": "Obra Social / Salud", "monto": 90000, "activo": True}
        ],
        "ingresos": [
            {"concepto": "Sueldo Farmacia", "monto": 650000, "activo": True},
            {"concepto": "Sueldo Anual Complementario (SAC mes)", "monto": 54000, "activo": True},
            {"concepto": "Jubilación", "monto": 320000, "activo": True}
        ],
        "precio_terapia": 30000,
        "inversiones": [
            {"tipo": "Dólar Billete", "activo": "USD Ahorro", "simbolo": "USD", "cantidad": 1200, "plataforma": "Caja de seguridad", "activo_inv": True},
            {"tipo": "Acciones / CEDEARs", "activo": "Apple (AAPL)", "simbolo": "AAPL", "cantidad": 20, "plataforma": "Balanz", "activo_inv": True},
            {"tipo": "Criptomonedas", "activo": "Bitcoin", "simbolo": "BTC", "cantidad": 0.015, "plataforma": "Binance", "activo_inv": True},
            {"tipo": "Efectivo / Banco", "activo": "Caja de Ahorro Pesos", "simbolo": "ARS", "cantidad": 350000, "plataforma": "Banco", "activo_inv": True}
        ]
    }

def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

# ----------------- COTIZACIONES EXTERNAS -----------------
@st.cache_data(ttl=600)
def obtener_cotizaciones():
    cotiz = {"dolar_blue": 1545.0, "BTC": 82000.0, "ETH": 2600.0, "AAPL": 230.0}
    try:
        r_dolar = requests.get("https://dolarapi.com/v1/dolares", timeout=4)
        if r_dolar.status_code == 200:
            for item in r_dolar.json():
                if item["casa"] == "blue":
                    cotiz["dolar_blue"] = float(item["venta"])
    except Exception:
        pass
    
    try:
        r_crypto = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", timeout=4)
        if r_crypto.status_code == 200:
            datos_c = r_crypto.json()
            cotiz["BTC"] = float(datos_c.get("bitcoin", {}).get("usd", cotiz["BTC"]))
            cotiz["ETH"] = float(datos_c.get("ethereum", {}).get("usd", cotiz["ETH"]))
    except Exception:
        pass

    return cotiz

# ----------------- AUTENTICACIÓN -----------------
USUARIO_CORRECTO = "mama"
PASSWORD_CORRECTO = "terapias123"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center; color: #4b367c;'>🌿 Ingreso al Panel Financiero</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            user = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar", use_container_width=True)
            if submit:
                if user == USUARIO_CORRECTO and password == PASSWORD_CORRECTO:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
    st.stop()

# ----------------- APP PRINCIPAL -----------------
datos = cargar_datos()
cotizaciones = obtener_cotizaciones()
dolar_b = cotizaciones["dolar_blue"]

# Formateo de fecha y hora local de Argentina (UTC-3 sin librerías externas)
tz_ar = timezone(timedelta(hours=-3))
ahora = datetime.now(tz_ar)
dias = {0: "lunes", 1: "martes", 2: "miércoles", 3: "jueves", 4: "viernes", 5: "sábado", 6: "domingo"}
meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
         7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
nombre_dia = dias[ahora.weekday()]
nombre_mes = meses[ahora.month]
fecha_hora_texto = f"Hoy es {nombre_dia} {ahora.day} de {nombre_mes} - {ahora.strftime('%H:%M')} hs"

# Barra lateral
with st.sidebar:
    st.markdown("<h2 style='color: #4b367c;'>🌿 Mi Panel</h2>", unsafe_allow_html=True)
    st.markdown(f"🗓️ **{fecha_hora_texto}**")
    st.write(f"💵 **Dólar Blue:** ${dolar_b:,.0f}")
    st.write(f"🪙 **Bitcoin:** USD {cotizaciones['BTC']:,.0f}")
    st.divider()
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

pestana1, pestana2 = st.tabs(["📊 Costos e Ingresos", "💎 Cartera de Inversiones"])

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
    
    # Conversiones a USD Blue
    costos_usd = total_costos / dolar_b if dolar_b > 0 else 0
    ingresos_usd = total_ingresos / dolar_b if dolar_b > 0 else 0
    saldo_usd = saldo_neto / dolar_b if dolar_b > 0 else 0

    # Estado y Semáforo
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
        sub_saldo = "Los costos superan los ingresos activos del mes."

    # Fila de Tarjetas KPI Superiores con USD
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.markdown(f"""
        <div class="metric-card metric-card-costo">
            <div class="kpi-title">📉 Costos Totales Mensuales</div>
            <div class="kpi-value">${total_costos:,.0f}</div>
            <div class="kpi-usd">≈ USD {costos_usd:,.2f}</div>
            <div class="kpi-sub">{len(costos_activos)} activos ({len(costos_pausados)} pausados)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
        <div class="metric-card metric-card-ingreso">
            <div class="kpi-title">📈 Ingresos Totales Mensuales</div>
            <div class="kpi-value">${total_ingresos:,.0f}</div>
            <div class="kpi-usd">≈ USD {ingresos_usd:,.2f}</div>
            <div class="kpi-sub">{len(ingresos_activos)} activos ({len(ingresos_pausados)} pausados)</div>
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

    st.markdown("---")

    # ---------------- CALCULADORA UNIFICADA DE TERAPIAS ----------------
    with st.expander("🧘‍♀️ **Calculadora de Terapias: Sesiones necesarias según tus números activos**", expanded=True):
        col_c1, col_c2 = st.columns([1.2, 2.5])
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

        faltante = total_costos - total_ingresos
        sesiones_necesarias = max(0.0, faltante / precio_sesion) if precio_sesion > 0 else 0.0

        with col_c2:
            if faltante <= 0:
                st.markdown(f"""
                <div style="background-color: #e8f5e9; border: 2px solid #2e7d32; padding: 18px; border-radius: 12px;">
                    <b style="color: #1b5e20; font-size: 1.25rem;">✨ ¡Tus costos están 100% cubiertos!</b><br>
                    Con tus ingresos activos actuales no necesitás hacer terapias para cubrir los gastos de vida del mes.
                    <br><span style="color: #2e7d32; font-size: 1.1rem; font-weight: 600;">Tenés un margen a favor de ${abs(saldo_neto):,.0f} (USD {abs(saldo_usd):,.2f}).</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #f3e5f5; border: 2px solid #8e24aa; padding: 18px; border-radius: 12px;">
                    <b style="color: #4a148c; font-size: 1.2rem;">🎯 Sesiones requeridas para cubrir la brecha del mes:</b><br>
                    Para cubrir el faltante actual de <b>${faltante:,.0f}</b> (USD {faltante/dolar_b:,.2f}), necesitás hacer:
                    <div style="font-size: 2.3rem; font-weight: 800; color: #6a1b9a; margin-top: 5px;">
                        {sesiones_necesarias:.1f} sesiones al mes
                    </div>
                    <span style="font-size: 1.05rem; color: #4a148c;">≈ <b>{sesiones_necesarias/4.3:.1f} sesiones por semana</b> (a ${precio_sesion:,.0f} por sesión).</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- LISTADO Y GESTIÓN EN COLUMNAS ----------------
    col_izq, col_der = st.columns(2)

    # COLUMNA IZQUIERDA: COSTOS
    with col_izq:
        st.markdown("<h3 style='color: #b33939;'>📉 Mis Costos</h3>", unsafe_allow_html=True)
        with st.expander("➕ Agregar Nuevo Costo"):
            with st.form("form_nuevo_costo"):
                cat_c = st.text_input("Nombre del costo (ej. Supermercado, Luz, Seguro)")
                monto_c = st.number_input("Monto Mensual ($)", min_value=0, step=5000)
                btn_c = st.form_submit_button("Guardar Costo", use_container_width=True)
                if btn_c and cat_c:
                    datos["costos"].append({"categoria": cat_c, "monto": monto_c, "activo": True})
                    guardar_datos(datos)
                    st.rerun()

        costos_modificados = False
        for idx, item in enumerate(datos["costos"]):
            estado_check = item.get("activo", True)
            c_box, c_nombre, c_monto, c_del = st.columns([0.6, 2.2, 1.5, 0.6])
            with c_box:
                nuevo_estado = st.checkbox("Activo", value=estado_check, key=f"costo_check_{idx}", label_visibility="collapsed")
                if nuevo_estado != estado_check:
                    item["activo"] = nuevo_estado
                    costos_modificados = True
            with c_nombre:
                nuevo_nom = st.text_input("Nombre", value=item["categoria"], key=f"costo_nom_{idx}", label_visibility="collapsed")
                if nuevo_nom != item["categoria"]:
                    item["categoria"] = nuevo_nom
                    costos_modificados = True
            with c_monto:
                nuevo_val = st.number_input("Monto", value=int(item["monto"]), step=2000, key=f"costo_val_{idx}", label_visibility="collapsed")
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

    # COLUMNA DERECHA: INGRESOS
    with col_der:
        st.markdown("<h3 style='color: #27ae60;'>📈 Mis Ingresos</h3>", unsafe_allow_html=True)
        with st.expander("➕ Agregar Nuevo Ingreso"):
            with st.form("form_nuevo_ingreso"):
                nom_i = st.text_input("Concepto de ingreso (ej. Sueldo, Jubilación, Renta)")
                monto_i = st.number_input("Monto Mensual ($)", min_value=0, step=5000)
                btn_i = st.form_submit_button("Guardar Ingreso", use_container_width=True)
                if btn_i and nom_i:
                    datos["ingresos"].append({"concepto": nom_i, "monto": monto_i, "activo": True})
                    guardar_datos(datos)
                    st.rerun()

        ingresos_modificados = False
        for idx, item in enumerate(datos["ingresos"]):
            estado_check = item.get("activo", True)
            c_box, c_nombre, c_monto, c_del = st.columns([0.6, 2.2, 1.5, 0.6])
            with c_box:
                nuevo_estado = st.checkbox("Activo", value=estado_check, key=f"ing_check_{idx}", label_visibility="collapsed")
                if nuevo_estado != estado_check:
                    item["activo"] = nuevo_estado
                    ingresos_modificados = True
            with c_nombre:
                nuevo_nom = st.text_input("Concepto", value=item["concepto"], key=f"ing_nom_{idx}", label_visibility="collapsed")
                if nuevo_nom != item["concepto"]:
                    item["concepto"] = nuevo_nom
                    ingresos_modificados = True
            with c_monto:
                nuevo_val = st.number_input("Monto", value=int(item["monto"]), step=5000, key=f"ing_val_{idx}", label_visibility="collapsed")
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

    # ---------------- GRÁFICOS PIE CHARTS Y TABLAS DISCRIMINADAS ----------------
    st.markdown("<h3 style='color: #4b367c;'>📊 Distribución Detallada</h3>", unsafe_allow_html=True)
    col_chart_c, col_chart_i = st.columns(2)

    with col_chart_c:
        st.markdown("<h4 style='color: #b33939; text-align: center;'>Distribución de Costos Activos</h4>", unsafe_allow_html=True)
        if costos_activos:
            df_pie_c = pd.DataFrame(costos_activos).sort_values(by="monto", ascending=False)
            df_pie_c["Porcentaje"] = (df_pie_c["monto"] / total_costos) * 100
            
            fig_c = px.pie(
                df_pie_c, values="monto", names="categoria", hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_c.update_traces(textposition='inside', textinfo='percent+label', textfont_size=15)
            fig_c.update_layout(height=430, margin=dict(t=20, b=20, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_c, use_container_width=True)

            tabla_c = df_pie_c[["categoria", "monto", "Porcentaje"]].copy()
            tabla_c.columns = ["Categoría", "Monto Mensual", "% Total"]
            tabla_c["Monto Mensual"] = tabla_c["Monto Mensual"].apply(lambda x: f"${x:,.0f}")
            tabla_c["% Total"] = tabla_c["% Total"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_c, use_container_width=True, hide_index=True)
        else:
            st.info("No hay costos activos para graficar.")

    with col_chart_i:
        st.markdown("<h4 style='color: #27ae60; text-align: center;'>Distribución de Ingresos Activos</h4>", unsafe_allow_html=True)
        if ingresos_activos:
            df_pie_i = pd.DataFrame(ingresos_activos).sort_values(by="monto", ascending=False)
            df_pie_i["Porcentaje"] = (df_pie_i["monto"] / total_ingresos) * 100
            
            fig_i = px.pie(
                df_pie_i, values="monto", names="concepto", hole=0.45,
                color_discrete_sequence=px.colors.sequential.Tealgrn_r
            )
            fig_i.update_traces(textposition='inside', textinfo='percent+label', textfont_size=15)
            fig_i.update_layout(height=430, margin=dict(t=20, b=20, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_i, use_container_width=True)

            tabla_i = df_pie_i[["concepto", "monto", "Porcentaje"]].copy()
            tabla_i.columns = ["Concepto", "Monto Mensual", "% Total"]
            tabla_i["Monto Mensual"] = tabla_i["Monto Mensual"].apply(lambda x: f"${x:,.0f}")
            tabla_i["% Total"] = tabla_i["% Total"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(tabla_i, use_container_width=True, hide_index=True)
        else:
            st.info("No hay ingresos activos para graficar.")


# =========================================================================
# =========================== PESTAÑA 2 ===================================
# =========================================================================
with pestana2:
    st.markdown("<h2 style='color: #4b367c;'>💎 Cartera de Inversiones y Activos</h2>", unsafe_allow_html=True)
    
    inversiones = datos.get("inversiones", [])
    filas = []

    for inv in inversiones:
        cant = float(inv.get("cantidad", 0))
        tipo = inv.get("tipo", "Efectivo / Banco")
        simbolo = inv.get("simbolo", "")
        esta_activo = inv.get("activo_inv", True)

        if tipo == "Dólar Billete":
            val_usd = cant
            val_ars = cant * dolar_b
            precio_ref = f"${dolar_b:,.0f}"
        elif tipo == "Criptomonedas":
            precio_u = cotizaciones.get(simbolo, 1.0)
            val_usd = cant * precio_u
            val_ars = val_usd * dolar_b
            precio_ref = f"USD {precio_u:,.0f}"
        elif tipo == "Acciones / CEDEARs":
            precio_u = cotizaciones.get(simbolo, 230.0)
            val_usd = cant * precio_u
            val_ars = val_usd * dolar_b
            precio_ref = f"USD {precio_u:,.2f}"
        else:
            val_ars = cant
            val_usd = cant / dolar_b if dolar_b > 0 else 0
            precio_ref = "$1"

        filas.append({
            "activo_obj": inv,
            "Tipo": tipo,
            "Activo": inv.get("activo", ""),
            "Plataforma": inv.get("plataforma", ""),
            "Cantidad": cant,
            "Precio Unitario": precio_ref,
            "Valor en ARS": val_ars,
            "Valor en USD": val_usd,
            "Activo_Flag": esta_activo
        })

    df_inv_todos = pd.DataFrame(filas)
    df_inv_activos = df_inv_todos[df_inv_todos["Activo_Flag"] == True] if not df_inv_todos.empty else pd.DataFrame()

    total_patrimonio_ars = df_inv_activos["Valor en ARS"].sum() if not df_inv_activos.empty else 0
    total_patrimonio_usd = df_inv_activos["Valor en USD"].sum() if not df_inv_activos.empty else 0

    col_pat1, col_pat2 = st.columns(2)
    with col_pat1:
        st.markdown(f"""
        <div class="metric-card metric-card-superavit">
            <div class="kpi-title">💵 Patrimonio Total Estimado (Pesos)</div>
            <div class="kpi-value">${total_patrimonio_ars:,.0f}</div>
            <div class="kpi-usd">Sumando solo activos habilitados</div>
        </div>
        """, unsafe_allow_html=True)
    with col_pat2:
        st.markdown(f"""
        <div class="metric-card metric-card-superavit">
            <div class="kpi-title">🌎 Equivalente Total en Dólares (Blue)</div>
            <div class="kpi-value">USD {total_patrimonio_usd:,.2f}</div>
            <div class="kpi-usd">Cotización Dólar Blue: ${dolar_b:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    if not df_inv_activos.empty:
        col_pie_inv, col_tbl_inv = st.columns([1.2, 1.8])
        with col_pie_inv:
            st.markdown("<h4 style='color: #4b367c; text-align: center;'>Distribución por Clase de Activo</h4>", unsafe_allow_html=True)
            fig_inv = px.pie(
                df_inv_activos, values="Valor en ARS", names="Tipo",
                hole=0.45, color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig_inv.update_traces(textposition='inside', textinfo='percent+label', textfont_size=15)
            fig_inv.update_layout(height=400, margin=dict(t=20, b=20, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_inv, use_container_width=True)

        with col_tbl_inv:
            st.markdown("<h4 style='color: #4b367c; text-align: center;'>Resumen por Tipo de Tenencia</h4>", unsafe_allow_html=True)
            resumen_tipo = df_inv_activos.groupby("Tipo").agg({"Valor en ARS": "sum", "Valor en USD": "sum"}).reset_index()
            resumen_tipo["% Cartera"] = (resumen_tipo["Valor en ARS"] / total_patrimonio_ars) * 100
            resumen_tipo["Valor en ARS"] = resumen_tipo["Valor en ARS"].apply(lambda x: f"${x:,.0f}")
            resumen_tipo["Valor en USD"] = resumen_tipo["Valor en USD"].apply(lambda x: f"USD {x:,.2f}")
            resumen_tipo["% Cartera"] = resumen_tipo["% Cartera"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(resumen_tipo, use_container_width=True, hide_index=True)

    st.markdown("---")

    col_inv_izq, col_inv_der = st.columns([1.1, 1.9])

    with col_inv_izq:
        st.markdown("<h3 style='color: #4b367c;'>➕ Agregar Activo</h3>", unsafe_allow_html=True)
        with st.form("form_nuevo_activo"):
            tipo_sel = st.selectbox("Tipo de Inversión", ["Dólar Billete", "Efectivo / Banco", "Acciones / CEDEARs", "Criptomonedas"])
            nombre_act = st.text_input("Nombre (ej. USD Ahorro, Plazo Fijo, Apple)")
            
            simbolo_sugerido = "USD"
            if tipo_sel == "Criptomonedas":
                simbolo_sugerido = st.selectbox("Cripto", ["BTC", "ETH"])
            elif tipo_sel == "Acciones / CEDEARs":
                simbolo_sugerido = st.selectbox("Ticker", ["AAPL"])
            elif tipo_sel == "Efectivo / Banco":
                simbolo_sugerido = "ARS"

            plat_act = st.text_input("Plataforma / Dónde está (ej. Balanz, Caja, Banco)")
            cant_act = st.number_input("Cantidad que posee", min_value=0.0, step=1.0, format="%.4f")
            
            btn_guardar_act = st.form_submit_button("Guardar Activo", use_container_width=True)
            if btn_guardar_act and nombre_act:
                datos["inversiones"].append({
                    "tipo": tipo_sel,
                    "activo": nombre_act,
                    "simbolo": simbolo_sugerido,
                    "cantidad": cant_act,
                    "plataforma": plat_act,
                    "activo_inv": True
                })
                guardar_datos(datos)
                st.rerun()

    with col_inv_der:
        st.markdown("<h3 style='color: #4b367c;'>📋 Administrar Tenencias (Pausar / Editar / Quitar)</h3>", unsafe_allow_html=True)
        if inversiones:
            inv_cambios = False
            for idx, inv in enumerate(inversiones):
                st_act = inv.get("activo_inv", True)
                c_chk, c_info, c_cant, c_plat, c_del = st.columns([0.5, 1.8, 1.1, 1.2, 0.5])
                
                with c_chk:
                    nuevo_chk = st.checkbox("Activo", value=st_act, key=f"inv_chk_{idx}", label_visibility="collapsed")
                    if nuevo_chk != st_act:
                        inv["activo_inv"] = nuevo_chk
                        inv_cambios = True

                with c_info:
                    st.write(f"**{inv.get('activo')}**\n<small>{inv.get('tipo')}</small>", unsafe_allow_html=True)

                with c_cant:
                    nueva_c = st.number_input("Cant.", value=float(inv.get("cantidad", 0)), step=1.0, key=f"inv_cant_{idx}", label_visibility="collapsed")
                    if nueva_c != inv.get("cantidad"):
                        inv["cantidad"] = nueva_c
                        inv_cambios = True

                with c_plat:
                    nueva_p = st.text_input("Plat.", value=inv.get("plataforma", ""), key=f"inv_p_{idx}", label_visibility="collapsed")
                    if nueva_p != inv.get("plataforma"):
                        inv["plataforma"] = nueva_p
                        inv_cambios = True

                with c_del:
                    if st.button("🗑️", key=f"inv_del_{idx}"):
                        datos["inversiones"].pop(idx)
                        guardar_datos(datos)
                        st.rerun()

            if inv_cambios:
                guardar_datos(datos)
                st.rerun()
        else:
            st.info("No hay activos guardados aún.")
