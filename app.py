import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os

# Configuración de página con título amigable
st.set_page_config(page_title="Panel Financiero", layout="wide", page_icon="💜")

DATA_FILE = "datos_finanzas.json"

# Estilos CSS pensados para alta legibilidad (fuente ampliada, colores violeta/azul y semáforos)
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-size: 17px;
    }
    .metric-card {
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        color: white;
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
        font-size: 1.1rem;
        font-weight: 600;
        opacity: 0.9;
        margin-bottom: 0.2rem;
    }
    .kpi-value {
        font-size: 2.1rem;
        font-weight: 700;
    }
    .kpi-sub {
        font-size: 0.95rem;
        opacity: 0.85;
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
                # Migración / compatibilidad: asegurar campo 'activo' (para mutear)
                for c in data.get("costos", []):
                    c.setdefault("activo", True)
                for ing in data.get("ingresos", []):
                    ing.setdefault("activo", True)
                # Si venía del formato viejo con ingresos_otros
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
            {"tipo": "Dólar Billete", "activo": "USD Ahorro", "simbolo": "USD", "cantidad": 1200, "plataforma": "Caja / Seguridad"},
            {"tipo": "Acciones / CEDEARs", "activo": "Apple (AAPL)", "simbolo": "AAPL", "cantidad": 20, "plataforma": "Balanz"},
            {"tipo": "Criptomonedas", "activo": "Bitcoin", "simbolo": "BTC", "cantidad": 0.015, "plataforma": "Lemon / Binance"},
            {"tipo": "Efectivo / Banco", "activo": "Caja de Ahorro Pesos", "simbolo": "ARS", "cantidad": 350000, "plataforma": "Banco"}
        ]
    }

def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

# ----------------- COTIZACIONES EXTERNAS -----------------
@st.cache_data(ttl=600)
def obtener_cotizaciones():
    cotiz = {"dolar_blue": 1350.0, "dolar_mep": 1310.0, "dolar_oficial": 1050.0, "BTC": 67000.0, "ETH": 2600.0, "AAPL": 230.0}
    try:
        r_dolar = requests.get("https://dolarapi.com/v1/dolares", timeout=4)
        if r_dolar.status_code == 200:
            for item in r_dolar.json():
                if item["casa"] == "blue":
                    cotiz["dolar_blue"] = float(item["venta"])
                elif item["casa"] == "bolsa":
                    cotiz["dolar_mep"] = float(item["venta"])
                elif item["casa"] == "oficial":
                    cotiz["dolar_oficial"] = float(item["venta"])
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

# ----------------- CARGA DE DATOS -----------------
datos = cargar_datos()
cotizaciones = obtener_cotizaciones()

# Barra lateral
with st.sidebar:
    st.markdown("<h2 style='color: #4b367c;'>🌿 Mi Panel</h2>", unsafe_allow_html=True)
    st.write(f"💵 **Dólar Blue:** ${cotizaciones['dolar_blue']:,.0f}")
    st.write(f"📈 **Dólar MEP:** ${cotizaciones['dolar_mep']:,.0f}")
    st.write(f"🪙 **Bitcoin:** USD {cotizaciones['BTC']:,.0f}")
    st.divider()
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# Pestañas principales
pestana1, pestana2 = st.tabs(["📊 Costos e Ingresos", "💎 Cartera de Inversiones"])

# =========================================================================
# =========================== PESTAÑA 1 ===================================
# =========================================================================
with pestana1:
    # Cálculo dinámico de totales activos vs inactivos
    costos_activos = [c for c in datos["costos"] if c.get("activo", True)]
    costos_pausados = [c for c in datos["costos"] if not c.get("activo", True)]
    total_costos = sum(c["monto"] for c in costos_activos)

    ingresos_activos = [i for i in datos["ingresos"] if i.get("activo", True)]
    ingresos_pausados = [i for i in datos["ingresos"] if not i.get("activo", True)]
    total_ingresos = sum(i["monto"] for i in ingresos_activos)

    saldo_neto = total_ingresos - total_costos
    
    # Determinación del semáforo para el saldo neto
    if total_ingresos > 0:
        ratio_ahorro = (saldo_neto / total_ingresos)
    else:
        ratio_ahorro = -1.0

    if saldo_neto > 0 and ratio_ahorro >= 0.15:
        clase_saldo = "metric-card-superavit"
        estado_saldo = "🟢 Superávit Saludable"
        sub_saldo = f"Capacidad de ahorro: {ratio_ahorro*100:.1f}% de tus ingresos"
    elif saldo_neto >= 0:
        clase_saldo = "metric-card-alerta"
        estado_saldo = "🟡 Balance Ajustado"
        sub_saldo = f"Ahorro moderado: {ratio_ahorro*100:.1f}%. Atenta a gastos imprevistos."
    else:
        clase_saldo = "metric-card-deficit"
        estado_saldo = "🔴 Déficit / En Pérdida"
        sub_saldo = "Los costos superan los ingresos activos del mes."

    # Fila superior de Tarjetas KPI
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.markdown(f"""
        <div class="metric-card metric-card-costo">
            <div class="kpi-title">📉 Costos Totales Mensuales</div>
            <div class="kpi-value">${total_costos:,.0f}</div>
            <div class="kpi-sub">{len(costos_activos)} costos activos ({len(costos_pausados)} pausados)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
        <div class="metric-card metric-card-ingreso">
            <div class="kpi-title">📈 Ingresos Totales Mensuales</div>
            <div class="kpi-value">${total_ingresos:,.0f}</div>
            <div class="kpi-sub">{len(ingresos_activos)} ingresos activos ({len(ingresos_pausados)} pausados)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi3:
        st.markdown(f"""
        <div class="metric-card {clase_saldo}">
            <div class="kpi-title">⚖️ Saldo Neto Mensual ({estado_saldo})</div>
            <div class="kpi-value">${saldo_neto:,.0f}</div>
            <div class="kpi-sub">{sub_saldo}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- CALCULADORA DE TERAPIAS (BREAK-EVEN) ----------------
    with st.expander("🧘‍♀️ **Calculadora de Terapias: ¿Cuántas sesiones cubren tus costos?**", expanded=True):
        col_calc1, col_calc2, col_calc3 = st.columns([1.2, 1.4, 1.4])
        with col_calc1:
            precio_sesion = st.number_input(
                "Valor por sesión de terapia ($):",
                value=int(datos.get("precio_terapia", 30000)),
                step=2000,
                format="%d"
            )
            if precio_sesion != datos.get("precio_terapia"):
                datos["precio_terapia"] = precio_sesion
                guardar_datos(datos)

        # Cálculos de cobertura
        sesiones_para_costo_total = total_costos / precio_sesion if precio_sesion > 0 else 0
        faltante = max(0, total_costos - total_ingresos)
        sesiones_para_faltante = faltante / precio_sesion if precio_sesion > 0 else 0

        with col_calc2:
            st.markdown(f"""
            <div style="background-color: #f3e5f5; border: 2px solid #9c27b0; padding: 15px; border-radius: 10px;">
                <b style="color: #4a148c; font-size: 1.1rem;">Escenario Independiente (Solo Terapias):</b><br>
                Si cerrás la farmacia y no tuvieras ningún otro ingreso activo, necesitás:<br>
                <span style="font-size: 1.8rem; font-weight: bold; color: #6a1b9a;">{sesiones_para_costo_total:.1f} sesiones/mes</span><br>
                <small>≈ {sesiones_para_costo_total/4.3:.1f} sesiones por semana</small>
            </div>
            """, unsafe_allow_html=True)

        with col_calc3:
            st.markdown(f"""
            <div style="background-color: #e8f5e9; border: 2px solid #2e7d32; padding: 15px; border-radius: 10px;">
                <b style="color: #1b5e20; font-size: 1.1rem;">Escenario Mixto (Con Ingresos Activos):</b><br>
                Considerando los ingresos que tenés tildados hoy, necesitás:<br>
                <span style="font-size: 1.8rem; font-weight: bold; color: #2e7d32;">{sesiones_para_faltante:.1f} sesiones/mes</span><br>
                <small>{"¡Tus ingresos activos ya cubren todos tus costos!" if faltante == 0 else f"Para cubrir la diferencia de ${faltante:,.0f}"}</small>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- LISTADO Y GESTIÓN EN COLUMNAS ----------------
    col_izq, col_der = st.columns(2)

    # COLUMNA IZQUIERDA: COSTOS
    with col_izq:
        st.markdown("<h3 style='color: #b33939;'>📉 Mis Costos</h3>", unsafe_allow_html=True)
        
        # Formulario para agregar costo
        with st.expander("➕ Agregar Nuevo Costo"):
            with st.form("form_nuevo_costo"):
                cat_c = st.text_input("Nombre del costo (ej. Supermercado, Luz, Seguro)")
                monto_c = st.number_input("Monto Mensual ($)", min_value=0, step=5000)
                btn_c = st.form_submit_button("Guardar Costo", use_container_width=True)
                if btn_c and cat_c:
                    datos["costos"].append({"categoria": cat_c, "monto": monto_c, "activo": True})
                    guardar_datos(datos)
                    st.rerun()

        # Lista de costos existentes
        costos_modificados = False
        for idx, item in enumerate(datos["costos"]):
            estado_check = item.get("activo", True)
            fondo = "#ffffff" if estado_check else "#eeeeee"
            borde = "#b33939" if estado_check else "#cccccc"
            texto_color = "#111111" if estado_check else "#888888"

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
        
        # Formulario para agregar ingreso
        with st.expander("➕ Agregar Nuevo Ingreso"):
            with st.form("form_nuevo_ingreso"):
                nom_i = st.text_input("Concepto de ingreso (ej. Sueldo, Jubilación, Renta)")
                monto_i = st.number_input("Monto Mensual ($)", min_value=0, step=5000)
                btn_i = st.form_submit_button("Guardar Ingreso", use_container_width=True)
                if btn_i and nom_i:
                    datos["ingresos"].append({"concepto": nom_i, "monto": monto_i, "activo": True})
                    guardar_datos(datos)
                    st.rerun()

        # Lista de ingresos existentes
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

    # ---------------- GRÁFICOS DE DISTRIBUCIÓN ----------------
    st.subheader("📊 Análisis Visual de Costos Activos")
    if costos_activos:
        df_c = pd.DataFrame(costos_activos).sort_values(by="monto", ascending=False)
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_pie = px.pie(
                df_c, values="monto", names="categoria",
                title="Proporción de Gastos", hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_g2:
            fig_bar = px.bar(
                df_c, x="monto", y="categoria", orientation="h",
                title="Mayores a Menores Gastos ($)",
                labels={"monto": "Monto Mensual ($)", "categoria": "Categoría"},
                text_auto='.2s', color="monto",
                color_continuous_scale="Reds"
            )
            fig_bar.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No hay costos activos para graficar.")


# =========================================================================
# =========================== PESTAÑA 2 ===================================
# =========================================================================
with pestana2:
    st.markdown("<h2 style='color: #4b367c;'>💎 Mi Cartera de Inversiones</h2>", unsafe_allow_html=True)
    
    inversiones = datos.get("inversiones", [])
    filas = []

    for inv in inversiones:
        cant = float(inv.get("cantidad", 0))
        tipo = inv.get("tipo", "Efectivo / Banco")
        simbolo = inv.get("simbolo", "")

        # Cálculo de valor en USD y ARS dinámicamente
        if tipo == "Dólar Billete":
            val_usd = cant
            val_ars = cant * cotizaciones["dolar_blue"]
            precio_unit_ref = f"1 USD = ${cotizaciones['dolar_blue']:,.0f} ARS"
        elif tipo == "Criptomonedas":
            precio_usd = cotizaciones.get(simbolo, 1.0)
            val_usd = cant * precio_usd
            val_ars = val_usd * cotizaciones["dolar_blue"]
            precio_unit_ref = f"USD {precio_usd:,.0f}"
        elif tipo == "Acciones / CEDEARs":
            precio_usd = cotizaciones.get(simbolo, 230.0)
            val_usd = cant * precio_usd
            val_ars = val_usd * cotizaciones["dolar_mep"]
            precio_unit_ref = f"USD {precio_usd:,.2f}"
        else: # Pesos / Banco / Plazo Fijo
            val_ars = cant
            val_usd = cant / cotizaciones["dolar_blue"] if cotizaciones["dolar_blue"] > 0 else 0
            precio_unit_ref = "$1 ARS"

        filas.append({
            "Tipo": tipo,
            "Activo": inv.get("activo", ""),
            "Plataforma / Custodia": inv.get("plataforma", ""),
            "Cantidad": cant,
            "Precio Referencia": precio_unit_ref,
            "Valor en ARS": val_ars,
            "Valor en USD": val_usd
        })

    df_inv = pd.DataFrame(filas)

    if not df_inv.empty:
        total_patrimonio_ars = df_inv["Valor en ARS"].sum()
        total_patrimonio_usd = df_inv["Valor en USD"].sum()

        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.markdown(f"""
            <div class="metric-card metric-card-superavit">
                <div class="kpi-title">💵 Patrimonio Total Estimado (Pesos)</div>
                <div class="kpi-value">${total_patrimonio_ars:,.0f}</div>
                <div class="kpi-sub">Calculado al tipo de cambio libre y de mercado</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
            <div class="metric-card metric-card-superavit">
                <div class="kpi-title">🌎 Equivalente Total en Dólares</div>
                <div class="kpi-value">USD {total_patrimonio_usd:,.2f}</div>
                <div class="kpi-sub">Total acumulado en moneda dura</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        col_pi, col_tb = st.columns([1.1, 1.9])
        with col_pi:
            st.subheader("Distribución de Activos")
            fig_activos = px.pie(
                df_inv, values="Valor en ARS", names="Tipo",
                hole=0.45, color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig_activos.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_activos, use_container_width=True)

        with col_tb:
            st.subheader("Detalle de Tenencias")
            df_mostrar = df_inv.copy()
            df_mostrar["Valor en ARS"] = df_mostrar["Valor en ARS"].apply(lambda x: f"${x:,.0f}")
            df_mostrar["Valor en USD"] = df_mostrar["Valor en USD"].apply(lambda x: f"USD {x:,.2f}")
            st.dataframe(df_mostrar, use_container_width=True)

    else:
        st.info("No hay activos cargados en la cartera.")

    st.markdown("---")

    # ---------------- AGREGAR Y ADMINISTRAR INVERSIONES ----------------
    col_ag1, col_ag2 = st.columns([1.2, 1.8])
    with col_ag1:
        st.subheader("➕ Agregar Activo")
        with st.form("form_nuevo_activo"):
            tipo_sel = st.selectbox("Tipo de Inversión", ["Dólar Billete", "Efectivo / Banco", "Acciones / CEDEARs", "Criptomonedas"])
            nombre_act = st.text_input("Nombre (ej. Dólares billete, Galicia Plazo Fijo, Apple)")
            
            simbolo_sugerido = ""
            if tipo_sel == "Criptomonedas":
                simbolo_sugerido = st.selectbox("Criptomoneda", ["BTC", "ETH"])
            elif tipo_sel == "Acciones / CEDEARs":
                simbolo_sugerido = st.selectbox("Ticker", ["AAPL"])
            elif tipo_sel == "Dólar Billete":
                simbolo_sugerido = "USD"
            else:
                simbolo_sugerido = "ARS"

            plat_act = st.text_input("Plataforma / Ubicación (ej. Balanz, Banco, Caja fuerte)")
            cant_act = st.number_input("Cantidad que posee", min_value=0.0, step=1.0, format="%.4f")
            
            btn_guardar_act = st.form_submit_button("Guardar Activo", use_container_width=True)
            if btn_guardar_act and nombre_act:
                datos["inversiones"].append({
                    "tipo": tipo_sel,
                    "activo": nombre_act,
                    "simbolo": simbolo_sugerido,
                    "cantidad": cant_act,
                    "plataforma": plat_act
                })
                guardar_datos(datos)
                st.rerun()

    with col_ag2:
        st.subheader("⚙️ Modificar o Quitar Activos")
        if inversiones:
            inv_modificadas = False
            for idx, inv in enumerate(inversiones):
                c_nom, c_cant, c_plat, c_borrar = st.columns([2, 1.2, 1.5, 0.6])
                with c_nom:
                    st.write(f"**{inv.get('activo')}** ({inv.get('tipo')})")
                with c_cant:
                    nueva_cant = st.number_input("Cant.", value=float(inv.get("cantidad", 0)), step=1.0, key=f"inv_cant_{idx}", label_visibility="collapsed")
                    if nueva_cant != inv.get("cantidad"):
                        inv["cantidad"] = nueva_cant
                        inv_modificadas = True
                with c_plat:
                    nueva_plat = st.text_input("Plat.", value=inv.get("plataforma", ""), key=f"inv_plat_{idx}", label_visibility="collapsed")
                    if nueva_plat != inv.get("plataforma"):
                        inv["plataforma"] = nueva_plat
                        inv_modificadas = True
                with c_borrar:
                    if st.button("🗑️", key=f"inv_del_{idx}"):
                        datos["inversiones"].pop(idx)
                        guardar_datos(datos)
                        st.rerun()
            if inv_modificadas:
                guardar_datos(datos)
                st.rerun()
        else:
            st.write("No hay activos para editar.")
