import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os

st.set_page_config(page_title="Finanzas y Gabinete", layout="wide", page_icon="🌿")

DATA_FILE = "datos_finanzas.json"

def cargar_datos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "costos": [
            {"categoria": "Servicios (Luz/Gas/Agua)", "monto": 35000},
            {"categoria": "Insumos Gabinete", "monto": 25000},
            {"categoria": "Alquiler / Expensas", "monto": 120000},
            {"categoria": "Comida y Supermercado", "monto": 150000}
        ],
        "ingresos_otros": [
            {"concepto": "Jubilación / Otros", "monto": 250000}
        ],
        "precio_terapia": 15000,
        "inversiones": [
            {"tipo": "Dólar Billete", "activo": "USD Físico", "cantidad": 500, "plataforma": "Caja de seguridad", "costo_compra": 1000},
            {"tipo": "Plazo Fijo UVA", "activo": "PF Banco", "cantidad": 250000, "plataforma": "Banco", "costo_compra": 200000}
        ]
    }

def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

@st.cache_data(ttl=600)
def obtener_cotizaciones():
    cotizaciones = {"dolar_blue": 1300.0, "dolar_mep": 1280.0, "dolar_oficial": 1000.0}
    try:
        r = requests.get("https://dolarapi.com/v1/dolares", timeout=5)
        if r.status_code == 200:
            for item in r.json():
                if item["casa"] == "blue":
                    cotizaciones["dolar_blue"] = float(item["venta"])
                elif item["casa"] == "bolsa":
                    cotizaciones["dolar_mep"] = float(item["venta"])
                elif item["casa"] == "oficial":
                    cotizaciones["dolar_oficial"] = float(item["venta"])
    except Exception:
        pass
    return cotizaciones

# ----------------- AUTENTICACIÓN SIMPLE -----------------
USUARIO_CORRECTO = "mama"
PASSWORD_CORRECTO = "terapias123"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center;'>🌿 Ingreso al Panel Financiero</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
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

# Barra lateral
with st.sidebar:
    st.title("🌿 Menú Principal")
    st.write(f"**Dólar Blue hoy:** ${cotizaciones['dolar_blue']:,.0f}")
    st.write(f"**Dólar MEP hoy:** ${cotizaciones['dolar_mep']:,.0f}")
    st.divider()
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

pestana1, pestana2 = st.tabs(["📊 Presupuesto y Terapias", "📈 Cartera de Inversiones"])

# ================= PESTAÑA 1 =================
with pestana1:
    st.header("Control Mensual y Gabinete")
    
    total_costos = sum(item["monto"] for item in datos["costos"])
    total_otros_ingresos = sum(item["monto"] for item in datos["ingresos_otros"])
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.subheader("💡 Calculador de Terapias")
        precio_terapia = st.number_input("Precio por sesión de terapia ($):", value=int(datos.get("precio_terapia", 15000)), step=1000)
        if precio_terapia != datos.get("precio_terapia"):
            datos["precio_terapia"] = precio_terapia
            guardar_datos(datos)
            
        terapias_cubrir_total = total_costos / precio_terapia if precio_terapia > 0 else 0
        faltante_con_otros_ingresos = max(0, total_costos - total_otros_ingresos)
        terapias_cubrir_restante = faltante_con_otros_ingresos / precio_terapia if precio_terapia > 0 else 0

        st.metric(label="Terapias para cubrir TODOS los costos", value=f"{terapias_cubrir_total:.1f} sesiones")
        st.metric(label="Terapias necesarias (restando otros ingresos)", value=f"{terapias_cubrir_restante:.1f} sesiones")

    with col_t2:
        st.subheader("Resumen General")
        st.metric(label="Costos Totales Mensuales", value=f"${total_costos:,.0f}")
        st.metric(label="Otros Ingresos Fijos", value=f"${total_otros_ingresos:,.0f}")
        ahorro_base = total_otros_ingresos - total_costos
        st.metric(label="Balance sin Terapias", value=f"${ahorro_base:,.0f}", delta=f"${ahorro_base:,.0f}")

    st.divider()
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Distribución de Costos")
        if datos["costos"]:
            df_costos = pd.DataFrame(datos["costos"])
            fig_torta = px.pie(df_costos, values="monto", names="categoria", hole=0.4)
            st.plotly_chart(fig_torta, use_container_width=True)
        else:
            st.info("No hay costos registrados.")
            
    with col_g2:
        st.subheader("Administrar Costos")
        with st.form("nuevo_costo"):
            nueva_cat = st.text_input("Categoría de costo (ej: Luz, Alquiler, Insumos)")
            nuevo_monto = st.number_input("Monto mensual ($)", min_value=0, step=1000)
            agregar_costo = st.form_submit_button("Agregar Costo")
            if agregar_costo and nueva_cat:
                datos["costos"].append({"categoria": nueva_cat, "monto": nuevo_monto})
                guardar_datos(datos)
                st.rerun()

# ================= PESTAÑA 2 =================
with pestana2:
    st.header("Seguimiento de Inversiones y Activos")
    
    inversiones = datos.get("inversiones", [])
    filas_inv = []
    
    for inv in inversiones:
        cant = inv["cantidad"]
        tipo = inv["tipo"]
        if tipo == "Dólar Billete":
            val_actual = cant * cotizaciones["dolar_blue"]
        elif tipo in ["Acciones/CEDEARs", "Cripto", "Plazo Fijo UVA", "FCI"]:
            val_actual = cant
        else:
            val_actual = cant
            
        filas_inv.append({
            "Tipo": tipo,
            "Activo": inv["activo"],
            "Plataforma": inv["plataforma"],
            "Cantidad": cant,
            "Valor Estimado (ARS)": val_actual
        })
        
    df_inv = pd.DataFrame(filas_inv)
    
    if not df_inv.empty:
        total_patrimonio = df_inv["Valor Estimado (ARS)"].sum()
        total_usd = total_patrimonio / cotizaciones["dolar_blue"]
        
        m1, m2 = st.columns(2)
        m1.metric("Patrimonio Total Estimado (Pesos)", f"${total_patrimonio:,.0f}")
        m2.metric("Equivalente en Dólares (Blue)", f"USD {total_usd:,.2f}")
        
        st.subheader("Composición de la Cartera")
        fig_inv = px.pie(df_inv, values="Valor Estimado (ARS)", names="Tipo", hole=0.4)
        st.plotly_chart(fig_inv, use_container_width=True)
        
        st.dataframe(df_inv, use_container_width=True)
    else:
        st.info("No hay activos cargados todavía.")
        
    st.divider()
    st.subheader("Agregar Nuevo Activo")
    with st.form("form_nuevo_activo"):
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            tipo_sel = st.selectbox("Tipo de Inversión", ["Dólar Billete", "Plazo Fijo UVA", "FCI", "Acciones/CEDEARs", "Cripto"])
            activo_nombre = st.text_input("Nombre o Detalle (ej: USD Físico, PF Banco Galicia)")
        with col_a2:
            plat = st.text_input("Plataforma / Ubicación (ej: Balanz, Banco, Efectivo)")
            cant_input = st.number_input("Cantidad o Monto Actual ($ o USD)", min_value=0.0, step=100.0)
            
        guardar_activo = st.form_submit_button("Guardar Activo")
        if guardar_activo and activo_nombre:
            datos["inversiones"].append({
                "tipo": tipo_sel,
                "activo": activo_nombre,
                "plataforma": plat,
                "cantidad": cant_input,
                "costo_compra": cant_input
            })
            guardar_datos(datos)
            st.rerun()
