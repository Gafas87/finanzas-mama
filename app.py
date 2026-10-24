"""Jardín Financiero, versión 2.

Presupuesto mensual, calculadora de terapias y cartera de inversiones.
Ejecutar:  streamlit run app.py
Configuración (usuario, contraseña y guardado permanente): ver README.md
"""

import hashlib
import hmac
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import calculos
import cotizaciones as cot
import datos as D
from numeros import MontoInvalido, fmt_ars, fmt_editable, fmt_num, fmt_usd, normalizar, parse_monto

st.set_page_config(page_title="Jardín Financiero", layout="wide", page_icon="🌿",
                   initial_sidebar_state="auto")

CARPETA_APP = Path(__file__).resolve().parent
CARPETA_DATOS = Path(os.environ.get("JARDIN_DATOS_DIR", CARPETA_APP))
ss = st.session_state

PALETA = ["#9B89B3", "#F6A682", "#76C893", "#72B0E8", "#F4D06F", "#E58F9E",
          "#64C2C7", "#C3A6A0", "#A3C9A8", "#D99B66", "#8E9AAF", "#E2AFCF"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

# ------------------------------------------------------------------ estilos
st.markdown("""
<style>
[data-testid="stMainBlockContainer"] { max-width: 1250px; }
.jardin-login-box { background: linear-gradient(145deg, #EAF6EE 0%, #F5F0FF 100%);
  border: 2px solid #95D5B2; border-radius: 22px; padding: 28px 24px 18px; text-align: center;
  box-shadow: 0 8px 20px rgba(45,106,79,0.08); margin: 20px 0 16px; }
.jardin-login-title { color: #1B4332; font-weight: 800; font-size: 1.7rem; margin: 8px 0 4px; }
.jardin-login-sub { color: #2D6A4F; font-size: 1.05rem; }
.metric-card { padding: 1.1rem 1.3rem; border-radius: 16px; margin-bottom: 0.8rem;
  box-shadow: 0 2px 6px rgba(0,0,0,0.04); }
.metric-card-costo { background: #FDEBD0; border: 1px solid #F5CBA7; border-left: 8px solid #E59866; color: #6E2C00; }
.metric-card-ingreso { background: #E8F8F5; border: 1px solid #A3E4D7; border-left: 8px solid #48C9B0; color: #0E6251; }
.metric-card-lila { background: #F3E8FF; border: 1px solid #D8B4FE; border-left: 8px solid #A78BFA; color: #3B1F4A; }
.metric-card-rojo { background: #FADBD8; border: 1px solid #F5B7B1; border-left: 8px solid #E74C3C; color: #78281F; }
.metric-card-neutro { background: #F3F4F6; border: 1px solid #D1D5DB; border-left: 8px solid #9CA3AF; color: #1F2937; }
.kpi-title { font-size: 1.05rem; font-weight: 700; margin-bottom: 0.2rem; }
.kpi-value { font-size: 2rem; font-weight: 800; line-height: 1.2; }
.kpi-usd { font-size: 1rem; font-weight: 600; margin-top: 0.3rem; padding: 2px 10px; border-radius: 8px;
  background: rgba(255,255,255,0.75); display: inline-block; }
.kpi-sub { font-size: 0.9rem; margin-top: 0.4rem; }
.col-header { font-size: 0.9rem; font-weight: 700; color: #374151; border-bottom: 2px solid #D1D5DB;
  padding-bottom: 3px; margin-bottom: 4px; }
.caja-ok { background: #E8F8F5; border: 1px solid #A3E4D7; padding: 16px 18px; border-radius: 14px; color: #0E6251; }
.caja-falta { background: #F3E8FF; border: 1px solid #D8B4FE; padding: 16px 18px; border-radius: 14px; color: #3B1F4A; }
.cifra-grande { font-size: 1.9rem; font-weight: 800; margin: 4px 0; }
.valor-fila { font-weight: 700; color: #1F2937; line-height: 1.25; }
.estado-fila { font-size: 0.8rem; color: #4B5563; }
.estado-alerta { font-size: 0.8rem; color: #9A3412; font-weight: 600; }
[data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button,
[data-testid="stDownloadButton"] button { min-height: 2.6rem; }
button[data-baseweb="tab"] p { font-size: 1.2rem; font-weight: 700; }
[class*="st-key-c_del_"] button, [class*="st-key-i_del_"] button, [class*="st-key-v_del_"] button {
  padding: 0.3rem 0.35rem; min-width: 2.6rem; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ utilidades
def secretos() -> dict:
    try:
        return {k: (dict(v) if hasattr(v, "keys") else v) for k, v in st.secrets.items()}
    except Exception:  # no hay archivo de secretos
        return {}


def ahora_ar():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=-3)))


def fecha_corta(iso):
    """'2026-10-20T15:00:00+00:00' -> '20/10 12:00' (hora argentina)."""
    try:
        d = datetime.fromisoformat(iso).astimezone(timezone(timedelta(hours=-3)))
        return d.strftime("%d/%m %H:%M")
    except (TypeError, ValueError):
        return "?"


def clave(texto):
    """Clave corta y estable para usar en nombres de widgets."""
    return hashlib.md5(texto.encode("utf-8")).hexdigest()[:8]


PREFIJOS_WIDGETS = ("c_", "i_", "v_", "conf_", "f_", "precio_terapia_txt")


def limpiar_widgets():
    """Borra el estado de las casillas para que muestren los datos recién cargados."""
    for k in list(ss.keys()):
        if isinstance(k, str) and k.startswith(PREFIJOS_WIDGETS):
            del ss[k]
    ss.errores = {}
    ss.confirmar = None


def m(texto):
    """Escapa el signo $ en textos con formato Markdown (si no, Streamlit lo toma como fórmula)."""
    return str(texto).replace("$", "\\$")


def h(texto):
    """Escapa el signo $ dentro de bloques HTML."""
    return str(texto).replace("$", "&#36;")


def avisar(tipo, mensaje):
    ss.aviso = (tipo, mensaje)


# ------------------------------------------------------------------ guardado
def almacen():
    if "almacen" not in ss:
        ss.almacen = D.crear_almacen(secretos(), CARPETA_DATOS)
    return ss.almacen


def cargar_en_sesion():
    texto, token = almacen().leer()
    if texto is None:
        data = D.datos_vacios()
    else:
        data, _ = D.desde_texto(texto)
    ss.datos, ss.token, ss.archivo_nuevo = data, token, texto is None
    ss.sin_guardar = False
    limpiar_widgets()


def guardar(mensaje="Cambios guardados", silencioso=False):
    try:
        ss.token = almacen().guardar(D.a_texto(ss.datos), ss.token)
        ss.sin_guardar = False
        ss.archivo_nuevo = False
        if not silencioso:
            avisar("ok", mensaje)
        return True
    except D.ConflictoDeVersion:
        try:
            cargar_en_sesion()
        except Exception:
            pass
        avisar("error", "Tus datos se habían cambiado en otra ventana o dispositivo. Cargué la versión "
                        "más reciente: revisá la pantalla y volvé a hacer el último cambio.")
    except D.ErrorAlmacen as e:
        ss.sin_guardar = True
        avisar("error", f"No se pudo guardar el cambio. {e} Probá de nuevo con el botón «Reintentar guardar».")
    return False


# ------------------------------------------------------------------ acciones (callbacks)
LISTAS = {"costos": ("c", "categoria"), "ingresos": ("i", "concepto"), "inversiones": ("v", "activo")}


def buscar(lista, iid):
    for pos, item in enumerate(ss.datos[lista]):
        if item["id"] == iid:
            return pos, item
    return None, None


def cb_incluir(lista, iid, k):
    _, item = buscar(lista, iid)
    if item is None:
        return
    campo = "activo_inv" if lista == "inversiones" else "activo"
    item[campo] = bool(ss[k])
    guardar("Incluido en el total" if ss[k] else "Quitado del total (no se borró)")


def cb_texto(lista, iid, campo, k, obligatorio=True):
    _, item = buscar(lista, iid)
    if item is None:
        return
    nuevo = (ss[k] or "").strip()
    if obligatorio and not nuevo:
        ss[k] = item.get(campo, "")
        ss.errores[k] = "El nombre no puede quedar vacío. Se dejó el anterior."
        return
    ss.errores.pop(k, None)
    if nuevo != item.get(campo, ""):
        item[campo] = nuevo
        guardar("Nombre guardado" if obligatorio else "Guardado")


def cb_numero(lista, iid, campo, k, permitir_cero=True):
    _, item = buscar(lista, iid)
    if item is None:
        return
    try:
        valor = parse_monto(ss[k], permitir_cero=permitir_cero)
    except MontoInvalido as e:
        extra = " Si ya no lo tenés, borralo con 🗑️." if not permitir_cero else ""
        ss.errores[k] = f"No se guardó: {e}{extra}"
        return
    ss.errores.pop(k, None)
    ss[k] = fmt_editable(valor)
    if normalizar(valor) != item.get(campo):
        item[campo] = normalizar(valor)
        nombre = item.get(LISTAS[lista][1], "")
        guardar(f"Guardado: {nombre} → {fmt_ars(valor) if lista != 'inversiones' else fmt_editable(valor)}")


def cb_pedir_borrar(iid):
    ss.confirmar = iid


def cb_cancelar_borrar():
    ss.confirmar = None


def cb_borrar(lista, iid):
    pos, item = buscar(lista, iid)
    ss.confirmar = None
    if item is None:
        return
    del ss.datos[lista][pos]
    for k in list(ss.keys()):
        if isinstance(k, str) and k.startswith(("c_", "i_", "v_")) and k.endswith(iid):
            del ss[k]
    nombre = item.get(LISTAS[lista][1], "")
    ss.deshacer = {"lista": lista, "item": item, "pos": pos, "nombre": nombre}
    guardar(f"Se borró «{nombre}». Podés deshacerlo.")


def cb_deshacer():
    d = ss.pop("deshacer", None)
    if not d:
        return
    lista = ss.datos[d["lista"]]
    lista.insert(min(d["pos"], len(lista)), d["item"])
    guardar(f"Se recuperó «{d['nombre']}».")


def cb_agregar(lista, grupo, k_nom, k_mon, k_err):
    nombre = (ss.get(k_nom) or "").strip()
    texto = ss.get(k_mon) or ""
    if not nombre:
        ss.errores[k_err] = "Escribí un nombre para el nuevo ítem."
        return
    try:
        monto = parse_monto(texto)
    except MontoInvalido as e:
        ss.errores[k_err] = f"No se agregó: {e}"
        return
    ss.errores.pop(k_err, None)
    campo = LISTAS[lista][1]
    ss.datos[lista].append({"id": D.nuevo_id(), "grupo": grupo, campo: nombre,
                            "monto": normalizar(monto), "activo": True})
    ss[k_nom], ss[k_mon] = "", ""
    guardar(f"Agregado: {nombre} ({fmt_ars(monto)})")


def cb_nueva_categoria(cats, k, k_err):
    nombre = (ss.get(k) or "").strip()
    if not nombre:
        ss.errores[k_err] = "Escribí el nombre de la categoría."
        return
    if nombre.lower() in [c.lower() for c in ss.datos[cats]]:
        ss.errores[k_err] = f"Ya existe una categoría llamada «{nombre}»."
        return
    ss.errores.pop(k_err, None)
    ss.datos[cats].append(nombre)
    ss[k] = ""
    guardar(f"Categoría «{nombre}» creada")


def cb_borrar_categoria(cats, nombre):
    if nombre in ss.datos[cats]:
        ss.datos[cats].remove(nombre)
        guardar(f"Categoría «{nombre}» eliminada")


def cb_precio_terapia():
    k = "precio_terapia_txt"
    try:
        valor = parse_monto(ss[k])
    except MontoInvalido as e:
        ss.errores[k] = f"No se guardó: {e}"
        return
    ss.errores.pop(k, None)
    ss[k] = fmt_editable(valor)
    ss.datos["precio_terapia"] = normalizar(valor)
    guardar(f"Precio de la sesión: {fmt_ars(valor)}")


SIMBOLO_OK = re.compile(r"^[A-Z0-9.\-]{1,15}$")


def cb_agregar_inversion():
    tipo = ss.get("f_inv_tipo", "")
    letra = tipo[:1]
    try:
        cant = parse_monto(ss.get("f_inv_cant", ""), permitir_cero=False)
    except MontoInvalido as e:
        ss.errores["f_inv"] = f"No se guardó: {e}"
        return
    manual = (ss.get(f"f_inv_manual_{letra}") or "").strip().upper()
    plataforma = (ss.get("f_inv_plat") or "").strip() or "Sin especificar"
    if letra == "A":
        tipo_g, nombre, simbolo = "Dólar Billete", "Dólar Billete", "USD"
    elif letra == "B":
        tipo_g, nombre, simbolo = "Pesos ARS", "Pesos ARS", "ARS"
    elif letra in ("C", "D"):
        tipo_g = "Acciones" if letra == "C" else "Criptomonedas"
        lista = "acciones_guardadas" if letra == "C" else "criptos_guardadas"
        elegido = manual or (ss.get(f"f_inv_sel_{letra}") or "")
        simbolo = elegido.split(" ")[0].upper()
        if not SIMBOLO_OK.match(simbolo):
            ss.errores["f_inv"] = ("Escribí la sigla con letras y números, sin espacios "
                                   "(por ejemplo DIS o ADA).")
            return
        nombre = elegido if not manual else manual
        if manual and manual not in ss.datos[lista] and simbolo not in [x.split(" ")[0] for x in ss.datos[lista]]:
            ss.datos[lista].append(manual)
    else:
        tipo_g, simbolo = "Otros", "ARS"
        nombre = (ss.get("f_inv_manual_E") or "").strip() or "Otros"
    ss.errores.pop("f_inv", None)
    ss.datos["inversiones"].append({"id": D.nuevo_id(), "tipo": tipo_g, "activo": nombre, "simbolo": simbolo,
                                    "cantidad": normalizar(cant), "plataforma": plataforma, "activo_inv": True})
    for k in ("f_inv_cant", "f_inv_plat", "f_inv_manual_C", "f_inv_manual_D", "f_inv_manual_E"):
        ss[k] = ""
    cotizaciones_en_vivo.clear()
    guardar(f"Guardado: {nombre} ({fmt_editable(cant)})")


def cb_restaurar(data, mensaje):
    ss.datos = data
    limpiar_widgets()
    ss.n_subida = ss.get("n_subida", 0) + 1
    guardar(mensaje)


def cb_reintentar():
    guardar("Cambios guardados")


def cb_actualizar_cotizaciones():
    cotizaciones_en_vivo.clear()


def cb_salir():
    for k in list(ss.keys()):
        del ss[k]


# ------------------------------------------------------------------ cotizaciones
@st.cache_data(ttl=300, show_spinner="Buscando cotizaciones…")
def cotizaciones_en_vivo(criptos: tuple, acciones: tuple):
    return cot.obtener(criptos, acciones)


def dato_cotizacion(inv):
    """Cotización que se usa para valuar una inversión (o None si no tiene)."""
    if inv["tipo"] == "Dólar Billete":
        return cotiz["dolar"]
    if inv["tipo"] == "Criptomonedas":
        return cotiz["cripto"].get(inv["simbolo"])
    if inv["tipo"] == "Acciones":
        return cotiz["acciones"].get(inv["simbolo"])
    return {"estado": "pesos"}


def estado_cotizacion(dato, corto=False):
    e = (dato or {}).get("estado")
    if e == "en_vivo":
        return "en vivo" if corto else f"actualizada {fecha_corta(dato['fecha'])[-5:]} hs"
    if e == "guardada":
        fecha = fecha_corta(dato["fecha"])
        return f"⚠️ precio del {fecha[:5]}" if corto else f"⚠️ última conocida, del {fecha}"
    if e == "pesos":
        return "en pesos" if corto else "cargado en pesos"
    return "⚠️ sin cotización"


# ------------------------------------------------------------------ pantallas
def pantalla_configuracion():
    st.title("🌿 Jardín Financiero")
    st.error("Falta configurar el usuario y la contraseña de la app.")
    st.markdown(
        "Para la persona que administra la app: agregá estos datos en los **secretos** "
        "(en Streamlit Cloud: *Settings → Secrets*; en la computadora: el archivo "
        "`.streamlit/secrets.toml`). Hay un ejemplo en `.streamlit/secrets.toml.example` y "
        "los pasos están en `README.md`."
    )
    st.code('[login]\nusuario = "mama"\npassword = "elegí-una-contraseña"', language="toml")


def pantalla_login(cred):
    _, centro, _ = st.columns([1, 1.3, 1])
    with centro:
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
        </div>""", unsafe_allow_html=True)
        espera = ss.get("bloqueo_hasta", 0) - time.time()
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            entrar = st.form_submit_button("Ingresar", type="primary", width="stretch", key="login_btn")
        if entrar:
            if espera > 0:
                st.error(f"Demasiados intentos. Esperá {int(espera) + 1} segundos y probá de nuevo.")
            elif (hmac.compare_digest(usuario.strip().lower().encode("utf-8"),
                                      str(cred.get("usuario", "")).strip().lower().encode("utf-8"))
                  and hmac.compare_digest(password.encode("utf-8"),
                                          str(cred.get("password", "")).encode("utf-8"))):
                ss.autenticado = True
                ss.intentos = 0
                st.rerun()
            else:
                ss.intentos = ss.get("intentos", 0) + 1
                if ss.intentos >= 5:
                    ss.bloqueo_hasta = time.time() + 30
                    ss.intentos = 0
                st.error("Usuario o contraseña incorrectos. Revisá las mayúsculas de la contraseña.")


def pantalla_error_datos(mensaje):
    st.title("🌿 Jardín Financiero")
    st.error("**No pude leer tus datos guardados.** No se cambió ni se borró nada.")
    with st.expander("Detalle para quien administra la app"):
        st.text(mensaje)
    a = almacen()
    if isinstance(a, D.AlmacenLocal) and a.copias():
        st.subheader("Recuperar la última copia automática")
        for ruta in a.copias()[:5]:
            try:
                data, _ = D.desde_texto(ruta.read_text(encoding="utf-8"))
            except D.DatosInvalidos:
                continue
            sello = datetime.strptime(ruta.stem.split("_", 1)[1][:15], "%Y%m%d-%H%M%S")
            st.write(f"Copia del **{sello:%d/%m/%Y a las %H:%M}**: {len(data['costos'])} gastos, "
                     f"{len(data['ingresos'])} ingresos, {len(data['inversiones'])} inversiones.")
            st.button("Usar esta copia", key="usar_copia", type="primary",
                      on_click=_recuperar, args=(data,))
            break
    elif isinstance(a, D.AlmacenGitHub):
        st.info("Los datos están en GitHub: se puede volver a una versión anterior desde el historial "
                "del archivo (ver README, «Recuperar una versión anterior»).")
    seccion_restaurar(en_error=True)


def _recuperar(data):
    texto, token = almacen().leer()
    ss.token = token
    ss.datos = data
    limpiar_widgets()
    if guardar("Se recuperó la copia"):
        ss.error_datos = None


def pantalla_error_conexion(mensaje):
    st.title("🌿 Jardín Financiero")
    st.error(f"**No pude abrir tus datos.** {mensaje}")
    st.write("Revisá la conexión a internet y probá de nuevo. Tus datos no se modificaron.")
    if st.button("Probar de nuevo", type="primary"):
        st.rerun()


# ------------------------------------------------------------------ componentes
def tarjeta(clase, titulo, valor, usd, sub, estilo=""):
    usd_html = f'<div class="kpi-usd">≈ {h(usd)}</div>' if usd else ""
    st.markdown(f"""<div class="metric-card {clase}" style="{estilo}">
        <div class="kpi-title">{titulo}</div><div class="kpi-value">{h(valor)}</div>
        {usd_html}<div class="kpi-sub">{h(sub)}</div></div>""", unsafe_allow_html=True)


def items_incluidos(n):
    return "1 ítem incluido" if n == 1 else f"{n} ítems incluidos"


def mostrar_error(k):
    if ss.errores.get(k):
        st.error(ss.errores[k], icon="⚠️")


def torta(etiquetas, valores):
    total = sum(valores) or 1.0
    textos = [f"{e}<br>{fmt_num(v / total * 100, 1)}%" for e, v in zip(etiquetas, valores)]
    fig = go.Figure(go.Pie(
        labels=etiquetas, values=valores, hole=0.36, sort=False, direction="clockwise",
        text=textos, textinfo="text", customdata=[fmt_ars(v) for v in valores],
        hovertemplate="%{label}: %{customdata}<extra></extra>",
        textposition=["outside" if v / total < 0.09 else "inside" for v in valores],
        insidetextorientation="horizontal", automargin=True,
        textfont=dict(size=15, color="#1F2937", family="Arial, sans-serif"),
        marker=dict(colors=[PALETA[i % len(PALETA)] for i in range(len(valores))],
                    line=dict(color="#FFFFFF", width=2)),
        showlegend=False,
    ))
    fig.update_layout(height=420, margin=dict(t=30, b=30, l=30, r=30),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


COLS_FILA = [0.42, 2.1, 1.3, 0.72]


def fila_item(lista, item, dolar):
    pref, campo = LISTAS[lista]
    iid = item["id"]
    k_chk, k_nom, k_mon = f"{pref}_chk_{iid}", f"{pref}_nom_{iid}", f"{pref}_mon_{iid}"
    if ss.get("confirmar") == iid:
        st.warning(m(f"¿Borrar **{item[campo]}** ({fmt_ars(item['monto'])})?"))
        b1, b2, _ = st.columns([1, 1, 1.2])
        b1.button("Sí, borrar", key=f"conf_si_{iid}", type="primary", on_click=cb_borrar,
                  args=(lista, iid), width="stretch")
        b2.button("No, dejarlo", key=f"conf_no_{iid}", on_click=cb_cancelar_borrar, width="stretch")
        return
    ss.setdefault(k_chk, item.get("activo", True))
    ss.setdefault(k_nom, item.get(campo, ""))
    ss.setdefault(k_mon, fmt_editable(item.get("monto", 0)))
    c1, c2, c3, c4 = st.columns(COLS_FILA, vertical_alignment="center")
    c1.checkbox("Incluir en el total", key=k_chk, label_visibility="collapsed",
                on_change=cb_incluir, args=(lista, iid, k_chk),
                help="Tildado: se suma al total. Destildado: queda guardado pero no se suma.")
    c2.text_input("Nombre", key=k_nom, label_visibility="collapsed",
                  on_change=cb_texto, args=(lista, iid, campo, k_nom))
    c3.text_input("Monto en pesos", key=k_mon, label_visibility="collapsed",
                  on_change=cb_numero, args=(lista, iid, "monto", k_mon))
    c4.button("🗑️", key=f"{pref}_del_{iid}", help=f"Borrar «{item.get(campo, '')}»",
              on_click=cb_pedir_borrar, args=(iid,), width="stretch")
    mostrar_error(k_nom)
    mostrar_error(k_mon)


def seccion_lista(lista, cats, titulo, color, nuevo_txt, dolar):
    pref, campo = LISTAS[lista]
    st.markdown(f"<h3 style='color:{color};margin-bottom:0'>{titulo}</h3>", unsafe_allow_html=True)
    st.caption("Para cambiar un monto, escribilo y apretá **Enter**. Destildá la casilla para dejar un "
               "ítem fuera del total sin borrarlo.")
    for cat in list(ss.datos[cats]):
        kc = clave(cat)
        items = [i for i in ss.datos[lista] if i.get("grupo") == cat]
        sub = calculos.subtotal_grupo(ss.datos[lista], cat)
        usd = calculos.en_usd(sub, dolar)
        etiqueta = m(f"**{cat}** — {fmt_ars(sub)}" + (f"  ({fmt_usd(usd, 0)})" if usd is not None else ""))
        with st.expander(etiqueta, expanded=True):
            d = ss.get("deshacer")
            if d and d["lista"] == lista and d["item"].get("grupo") == cat:
                u1, u2 = st.columns([1.7, 1.2], vertical_alignment="center")
                u1.info(f"Se borró «{d['nombre']}».")
                u2.button("↩️ Deshacer", key=f"{pref}_undo_{kc}", on_click=cb_deshacer, width="stretch")
            if items:
                h1, h2, h3, _ = st.columns(COLS_FILA)
                h1.markdown("<div class='col-header'>✓</div>", unsafe_allow_html=True)
                h2.markdown("<div class='col-header'>Nombre</div>", unsafe_allow_html=True)
                h3.markdown("<div class='col-header'>Monto ($)</div>", unsafe_allow_html=True)
            for item in items:
                fila_item(lista, item, dolar)
            k_nom, k_mon, k_err = f"f_{pref}_nom_{kc}", f"f_{pref}_mon_{kc}", f"f_{pref}_err_{kc}"
            with st.form(f"f_{pref}_form_{kc}", border=False):
                a1, a2, a3 = st.columns([2.1, 1.3, 1.2], vertical_alignment="bottom")
                a1.text_input(nuevo_txt, key=k_nom, placeholder="Nombre")
                a2.text_input("Monto ($)", key=k_mon, placeholder="Ej. 25.000")
                a3.form_submit_button("Agregar", on_click=cb_agregar, args=(lista, cat, k_nom, k_mon, k_err),
                                      width="stretch", key=f"f_{pref}_btn_{kc}")
            mostrar_error(k_err)
            if not items:
                st.button(f"Eliminar la categoría «{cat}»", key=f"{pref}_delcat_{kc}",
                          on_click=cb_borrar_categoria, args=(cats, cat), type="tertiary")
    with st.expander("➕ Crear una categoría nueva"):
        k, k_err = f"f_{pref}_nuevacat", f"f_{pref}_nuevacat_err"
        with st.form(f"f_{pref}_nuevacat_form", border=False):
            n1, n2 = st.columns([2.5, 1], vertical_alignment="bottom")
            n1.text_input("Nombre de la categoría", key=k, placeholder="Ej. Salud, Educación")
            n2.form_submit_button("Crear", on_click=cb_nueva_categoria, args=(cats, k, k_err), width="stretch",
                                  key=f"f_{pref}_nuevacat_btn")
        mostrar_error(k_err)


def seccion_restaurar(en_error=False):
    titulo = "Restaurar desde un archivo de copia" if en_error else "Restaurar una copia"
    with st.expander(titulo, expanded=en_error):
        st.caption("Elegí un archivo descargado antes con «Descargar copia de seguridad». "
                   "Reemplaza los datos actuales; la versión actual queda en el historial de copias.")
        archivo = st.file_uploader("Archivo de copia (.json)", type=["json"],
                                   key=f"subida_{ss.get('n_subida', 0)}")
        if archivo is not None:
            try:
                data, _ = D.desde_texto(archivo.getvalue().decode("utf-8"))
            except (D.DatosInvalidos, UnicodeDecodeError) as e:
                st.error(f"Ese archivo no es una copia válida. {e}")
                return
            st.write(f"La copia tiene **{len(data['costos'])} gastos**, **{len(data['ingresos'])} ingresos** "
                     f"y **{len(data['inversiones'])} inversiones**.")
            if en_error:
                st.button("Usar esta copia", type="primary", on_click=_recuperar, args=(data,))
            else:
                st.button("Reemplazar mis datos por esta copia", type="primary",
                          on_click=cb_restaurar, args=(data, "Copia restaurada"))


# ================================================================== inicio
if "errores" not in ss:
    ss.errores = {}

cred = secretos().get("login")
if not cred or not cred.get("usuario") or not cred.get("password"):
    pantalla_configuracion()
    st.stop()

if not ss.get("autenticado"):
    pantalla_login(cred)
    st.stop()

if "datos" not in ss or ss.get("error_datos"):
    try:
        cargar_en_sesion()
        ss.error_datos = None
    except D.DatosInvalidos as e:
        ss.error_datos = str(e)
    except D.ErrorAlmacen as e:
        pantalla_error_conexion(str(e))
        st.stop()
if ss.get("error_datos"):
    pantalla_error_datos(ss.error_datos)
    st.stop()

datos = ss.datos

# ------------------------------------------------------------------ cotizaciones
inv_todas = datos["inversiones"]
sim_cri = tuple(sorted({i["simbolo"] for i in inv_todas if i["tipo"] == "Criptomonedas" and i["simbolo"]}))
sim_acc = tuple(sorted({i["simbolo"] for i in inv_todas if i["tipo"] == "Acciones" and i["simbolo"]}))
vivas = cotizaciones_en_vivo(sim_cri, sim_acc)
cotiz = cot.combinar(vivas, datos.get("cotizaciones_guardadas"))
nuevas, hubo_cambio = cot.actualizar_guardadas(datos.get("cotizaciones_guardadas"), vivas)
if hubo_cambio and not ss.get("sin_guardar"):
    datos["cotizaciones_guardadas"] = nuevas
    guardar(silencioso=True)
dolar = cotiz["dolar"]["valor"]

# ------------------------------------------------------------------ avisos
aviso = ss.pop("aviso", None)
if aviso and aviso[0] == "ok":
    st.toast(m(aviso[1]), icon="✅")
elif aviso:
    st.error(m(aviso[1]), icon="⚠️")
if ss.get("sin_guardar"):
    w1, w2 = st.columns([3, 1], vertical_alignment="center")
    w1.warning("Hay cambios que todavía **no se guardaron**.")
    w2.button("Reintentar guardar", on_click=cb_reintentar, type="primary", width="stretch")
if isinstance(almacen(), D.AlmacenLocal) and D.en_streamlit_cloud():
    st.error("**Atención:** en este servidor los datos pueden borrarse cuando la app se reinicia. "
             "Descargá una copia de seguridad (panel de la izquierda) después de hacer cambios. "
             "Para quien administra la app: activá el guardado en GitHub (ver README).", icon="⚠️")

# ------------------------------------------------------------------ panel lateral
with st.sidebar:
    st.markdown("<h2 style='color:#2D6A4F;margin-top:0'>🌿 Mi Panel</h2>", unsafe_allow_html=True)
    hoy = ahora_ar()
    st.markdown(f"📅 Hoy es **{DIAS[hoy.weekday()]} {hoy.day} de {MESES[hoy.month - 1]}**")
    st.divider()
    if dolar:
        st.markdown(m(f"💵 **Dólar blue (venta):** {fmt_ars(dolar)}"))
        st.caption(estado_cotizacion(cotiz["dolar"]))
    else:
        st.markdown("💵 **Dólar blue:** sin dato")
        st.caption("No se pudo obtener la cotización. Los valores en dólares no se muestran.")
    if "BTC" in cotiz["cripto"] and cotiz["cripto"]["BTC"]["valor"]:
        st.markdown(m(f"🪙 **Bitcoin:** {fmt_usd(cotiz['cripto']['BTC']['valor'], 0)}"))
    st.button("🔄 Actualizar cotizaciones", on_click=cb_actualizar_cotizaciones, width="stretch")
    st.divider()
    st.markdown("**💾 Copia de seguridad**")
    st.download_button("Descargar copia de seguridad", data=D.a_texto(datos).encode("utf-8"),
                       file_name=f"jardin_financiero_copia_{hoy:%Y-%m-%d}.json", mime="application/json",
                       width="stretch", on_click="ignore")
    seccion_restaurar()
    lugar = "GitHub (repositorio privado)" if isinstance(almacen(), D.AlmacenGitHub) else "archivo en este equipo"
    st.caption(f"Tus datos se guardan en: {lugar}.")
    st.divider()
    st.button("🚪 Cerrar sesión", on_click=cb_salir, width="stretch")

# ------------------------------------------------------------------ bienvenida
if ss.get("archivo_nuevo") and not (datos["costos"] or datos["ingresos"] or datos["inversiones"]):
    st.info("**¡Bienvenida!** Todavía no hay datos cargados. Agregá tus gastos e ingresos en cada "
            "categoría con el botón **➕ Agregar**. Si tenés una copia de seguridad, podés "
            "restaurarla desde el panel de la izquierda.")
    viejo = CARPETA_APP / "datos_finanzas.json"
    if isinstance(almacen(), D.AlmacenGitHub) and viejo.exists():
        try:
            data_vieja, _ = D.desde_texto(viejo.read_text(encoding="utf-8"))
            st.write(f"Encontré datos de la versión anterior en este servidor: {len(data_vieja['costos'])} "
                     f"gastos, {len(data_vieja['ingresos'])} ingresos y {len(data_vieja['inversiones'])} inversiones.")
            st.button("Importar los datos de la versión anterior", type="primary",
                      on_click=cb_restaurar, args=(data_vieja, "Datos de la versión anterior importados"))
        except D.DatosInvalidos:
            pass

pestana1, pestana2 = st.tabs(["📊 Costos e Ingresos", "💎 Cartera de Inversiones"])

# ================================================================== PESTAÑA 1
with pestana1:
    r = calculos.resumen_mensual(datos["costos"], datos["ingresos"])
    usd = lambda v: fmt_usd(calculos.en_usd(v, dolar)) if dolar else None  # noqa: E731
    k1, k2, k3 = st.columns(3)
    with k1:
        tarjeta("metric-card-costo", "Costos del mes", fmt_ars(r["costos"]), usd(r["costos"]),
                items_incluidos(r["n_costos"]))
    with k2:
        tarjeta("metric-card-ingreso", "Ingresos del mes", fmt_ars(r["ingresos"]), usd(r["ingresos"]),
                items_incluidos(r["n_ingresos"]))
    with k3:
        if r["saldo"] > 0:
            tarjeta("metric-card-lila", "Te queda por mes 😊", fmt_ars(r["saldo"]), usd(r["saldo"]),
                    "Los ingresos cubren los costos")
        elif r["saldo"] == 0:
            tarjeta("metric-card-neutro", "Te queda por mes", fmt_ars(0), None, "Ingresos y costos son iguales")
        else:
            tarjeta("metric-card-rojo", "Te falta por mes", fmt_ars(-r["saldo"]), usd(-r["saldo"]),
                    "Los costos superan a los ingresos")

    with st.expander("🧘 **Calculadora de terapias:** ¿cuántas sesiones necesito para cubrir mis costos?",
                     expanded=True):
        p1, p2 = st.columns([1.1, 2.5])
        with p1:
            ss.setdefault("precio_terapia_txt", fmt_editable(datos.get("precio_terapia", 0)))
            st.text_input("Valor de una sesión ($)", key="precio_terapia_txt", on_change=cb_precio_terapia,
                          help="Escribí el valor y apretá Enter. Ej. 30.000")
            mostrar_error("precio_terapia_txt")
            precio = float(datos.get("precio_terapia") or 0)
            if precio and dolar:
                st.caption(m(f"Equivale a {fmt_usd(precio / dolar)} por sesión."))
        s = calculos.sesiones_necesarias(r["costos"], r["ingresos"], precio)
        with p2:
            if s["faltante"] <= 0:
                st.markdown(f"""<div class="caja-ok"><b>✨ Tus ingresos cubren todos tus costos incluidos.</b><br>
                    Te quedan <b>{h(fmt_ars(r['saldo']))}</b> por mes, sin necesidad de sesiones extra.</div>""",
                            unsafe_allow_html=True)
            elif not precio:
                st.markdown(f"""<div class="caja-falta">Te faltan <b>{h(fmt_ars(s['faltante']))}</b> por mes.<br>
                    Escribí el valor de una sesión a la izquierda para saber cuántas sesiones necesitás.</div>""",
                            unsafe_allow_html=True)
            else:
                palabra = "sesión" if s["por_mes"] == 1 else "sesiones"
                st.markdown(f"""<div class="caja-falta">Te faltan <b>{h(fmt_ars(s['faltante']))}</b> por mes.
                    Con sesiones de {h(fmt_ars(precio))}, necesitás:
                    <div class="cifra-grande">{s['por_mes']} {palabra} por mes</div>
                    Aproximadamente {fmt_num(s['por_semana'], 1)} por semana · {s['por_anio']} al año</div>""",
                            unsafe_allow_html=True)

    st.write("")
    izq, _, der = st.columns([1, 0.05, 1])
    with izq:
        seccion_lista("costos", "categorias_costos", "📉 Mis costos mensuales", "#A04000", "Nuevo gasto", dolar)
    with der:
        seccion_lista("ingresos", "categorias_ingresos", "📈 Mis ingresos mensuales", "#0E6251",
                      "Nuevo ingreso", dolar)

    st.divider()
    st.markdown("<h3 style='color:#5B4B8A'>📊 Gráficos</h3>", unsafe_allow_html=True)
    modo = st.radio("Ver los gráficos:", ["Por categoría", "Por cada ítem"], horizontal=True)
    g1, _, g2 = st.columns([1, 0.06, 1])
    for col, lista, campo, titulo, color in (
        (g1, "costos", "categoria", "Costos incluidos", "#A04000"),
        (g2, "ingresos", "concepto", "Ingresos incluidos", "#0E6251"),
    ):
        with col:
            st.markdown(f"<h4 style='color:{color};text-align:center'>{titulo}</h4>", unsafe_allow_html=True)
            filas = [i for i in calculos.incluidos(datos[lista]) if float(i["monto"]) > 0]
            if not filas:
                st.info("No hay montos incluidos para graficar.")
                continue
            df = pd.DataFrame(filas)
            if modo == "Por categoría":
                df = df.groupby("grupo", as_index=False)["monto"].sum().rename(columns={"grupo": "Nombre"})
            else:
                df = df.rename(columns={campo: "Nombre"})[["Nombre", "monto"]]
            df = df.sort_values("monto", ascending=False)
            tot = df["monto"].sum()
            st.plotly_chart(torta(df["Nombre"].tolist(), df["monto"].tolist()), config={"displayModeBar": False})
            tabla = pd.DataFrame({
                "Categoría" if modo == "Por categoría" else "Ítem": df["Nombre"],
                "Pesos": df["monto"].map(fmt_ars),
                "Dólares": df["monto"].map(lambda v: fmt_usd(v / dolar) if dolar else "—"),
                "% del total": (df["monto"] / tot * 100).map(lambda v: f"{fmt_num(v, 1)}%"),
            })
            st.dataframe(tabla, hide_index=True)

# ================================================================== PESTAÑA 2
with pestana2:
    p = calculos.patrimonio(inv_todas, cotiz)
    notas = []
    if p["sin_valor"]:
        nombres = ", ".join(i.get("activo", "") for i in p["sin_valor"])
        notas.append(f"⚠️ Sin cotización, no incluido en el total: {nombres}")
    usadas_guardadas = [sim for g in ("cripto", "acciones") for sim, v in cotiz[g].items()
                        if v["estado"] == "guardada"]
    if cotiz["dolar"]["estado"] == "guardada":
        usadas_guardadas.insert(0, "dólar")
    if usadas_guardadas:
        notas.append("⚠️ Con la última cotización conocida (no en vivo): " + ", ".join(usadas_guardadas))
    nota_total = "<br>".join(notas) if notas else "Calculado con cotizaciones en vivo"
    tarjeta("metric-card-lila", "Patrimonio total", fmt_ars(p["ars"]),
            fmt_usd(p["usd"]) if p["usd"] is not None else None, nota_total, estilo="text-align:center")

    st.write("")
    c_izq, _, c_der = st.columns([0.85, 0.05, 2.15])
    with c_izq:
        st.markdown("<h3 style='color:#5B4B8A'>➕ Agregar una inversión</h3>", unsafe_allow_html=True)
        tipo = st.selectbox("1. ¿Qué tipo es?", ["A - Dólar Billete", "B - Pesos ARS", "C - Acciones (EE. UU.)",
                                                 "D - Criptomonedas", "E - Otros"], key="f_inv_tipo")
        letra = tipo[:1]
        with st.form("f_inv_form", border=True):
            if letra == "C":
                st.selectbox("2. Elegí la acción", datos["acciones_guardadas"], key="f_inv_sel_C")
                st.text_input("¿No está en la lista? Escribí la sigla (ej. DIS, V)", key="f_inv_manual_C")
            elif letra == "D":
                st.selectbox("2. Elegí la criptomoneda", datos["criptos_guardadas"], key="f_inv_sel_D")
                st.text_input("¿No está en la lista? Escribí la sigla (ej. LTC)", key="f_inv_manual_D")
            elif letra == "E":
                st.text_input("2. ¿Qué es? (ej. Plazo fijo, FCI)", key="f_inv_manual_E")
            st.text_input("¿Dónde está? (banco, app, en casa)", key="f_inv_plat")
            etiqueta_cant = {"A": "Cantidad de dólares", "B": "Cantidad de pesos", "C": "Cantidad de acciones",
                             "D": "Cantidad de monedas", "E": "Valor en pesos"}[letra]
            st.text_input(etiqueta_cant, key="f_inv_cant", placeholder="Ej. 1.500 o 0,25")
            st.form_submit_button("Guardar inversión", type="primary", on_click=cb_agregar_inversion,
                                  width="stretch", key="f_inv_btn")
        mostrar_error("f_inv")

    with c_der:
        st.markdown("<h3 style='color:#5B4B8A'>📋 Mis inversiones</h3>", unsafe_allow_html=True)
        if not inv_todas:
            st.info("Todavía no cargaste inversiones. Usá el formulario de la izquierda.")
        for tipo_inv in calculos.TIPOS_INVERSION:
            items = [i for i in inv_todas if i["tipo"] == tipo_inv]
            if not items:
                continue
            valores = {i["id"]: calculos.valuar_inversion(i, cotiz) for i in items}
            sub_ars = sum(v["valor_ars"] or 0 for i, v in zip(items, valores.values()) if i.get("activo_inv", True))
            with st.expander(m(f"**{tipo_inv}** — {fmt_ars(sub_ars)}"), expanded=True):
                d = ss.get("deshacer")
                if d and d["lista"] == "inversiones" and d["item"].get("tipo") == tipo_inv:
                    u1, u2 = st.columns([1.7, 1.2], vertical_alignment="center")
                    u1.info(f"Se borró «{d['nombre']}».")
                    u2.button("↩️ Deshacer", key=f"v_undo_{clave(tipo_inv)}", on_click=cb_deshacer, width="stretch")
                cols = [0.35, 1.55, 1.0, 1.1, 1.3, 0.65]
                hs = st.columns(cols)
                for hcol, txt in zip(hs, ["✓", "Detalle", "Cantidad", "Dónde está", "Valor", ""]):
                    hcol.markdown(f"<div class='col-header'>{txt}</div>", unsafe_allow_html=True)
                for inv in items:
                    iid = inv["id"]
                    if ss.get("confirmar") == iid:
                        st.warning(f"¿Borrar **{inv['activo']}** ({fmt_editable(inv['cantidad'])})?")
                        b1, b2, _ = st.columns([1, 1, 1.2])
                        b1.button("Sí, borrar", key=f"conf_si_{iid}", type="primary", on_click=cb_borrar,
                                  args=("inversiones", iid), width="stretch")
                        b2.button("No, dejarlo", key=f"conf_no_{iid}", on_click=cb_cancelar_borrar, width="stretch")
                        continue
                    ks = {n: f"v_{n}_{iid}" for n in ("chk", "nom", "cant", "plat")}
                    ss.setdefault(ks["chk"], inv.get("activo_inv", True))
                    ss.setdefault(ks["nom"], inv.get("activo", ""))
                    ss.setdefault(ks["cant"], fmt_editable(inv.get("cantidad", 0)))
                    ss.setdefault(ks["plat"], inv.get("plataforma", ""))
                    f = st.columns(cols, vertical_alignment="center")
                    f[0].checkbox("Incluir en el total", key=ks["chk"], label_visibility="collapsed",
                                  on_change=cb_incluir, args=("inversiones", iid, ks["chk"]))
                    f[1].text_input("Detalle", key=ks["nom"], label_visibility="collapsed",
                                    on_change=cb_texto, args=("inversiones", iid, "activo", ks["nom"]))
                    f[2].text_input("Cantidad", key=ks["cant"], label_visibility="collapsed",
                                    on_change=cb_numero, args=("inversiones", iid, "cantidad", ks["cant"], False))
                    f[3].text_input("Dónde está", key=ks["plat"], label_visibility="collapsed",
                                    on_change=cb_texto, args=("inversiones", iid, "plataforma", ks["plat"], False))
                    v = valores[iid]
                    estado = estado_cotizacion(dato_cotizacion(inv), corto=True)
                    clase_estado = "estado-alerta" if "⚠️" in estado else "estado-fila"
                    valor_txt = h(fmt_ars(v["valor_ars"])) if v["valor_ars"] is not None else "—"
                    f[4].markdown(f"<div class='valor-fila'>{valor_txt}</div>"
                                  f"<div class='{clase_estado}'>{estado}</div>", unsafe_allow_html=True)
                    f[5].button("🗑️", key=f"v_del_{iid}", help=f"Borrar «{inv.get('activo', '')}»",
                                on_click=cb_pedir_borrar, args=(iid,), width="stretch")
                    for k in ks.values():
                        mostrar_error(k)

    st.divider()
    st.markdown("<h3 style='color:#5B4B8A'>📊 Distribución y cotizaciones</h3>", unsafe_allow_html=True)
    filas = []
    for inv in inv_todas:
        if not inv.get("activo_inv", True):
            continue
        v = calculos.valuar_inversion(inv, cotiz)
        tipo_inv = inv["tipo"]
        dato = dato_cotizacion(inv)
        if tipo_inv in ("Criptomonedas", "Acciones"):
            precio_txt = f"1 {inv['simbolo']} = {fmt_usd(v['precio_usd'])}" if v["precio_usd"] else "—"
        elif tipo_inv == "Dólar Billete":
            precio_txt = f"1 US$ = {fmt_ars(dolar)}" if dolar else "—"
        else:
            precio_txt = "—"
        filas.append({"Categoría": tipo_inv, "Activo": inv.get("activo", ""), "Dónde está": inv.get("plataforma", ""),
                      "Cantidad": fmt_editable(inv.get("cantidad", 0)), "Cotización usada": precio_txt,
                      "Estado": estado_cotizacion(dato), "_ars": v["valor_ars"]})
    con_valor = [fila for fila in filas if fila["_ars"] is not None and fila["_ars"] > 0]
    if not con_valor:
        st.info("No hay inversiones incluidas con valor para mostrar.")
    else:
        d1, _, d2 = st.columns([1, 0.06, 1])
        df = pd.DataFrame(con_valor)
        total_inv = df["_ars"].sum()
        with d1:
            st.markdown("<h4 style='color:#5B4B8A;text-align:center'>Por categoría</h4>", unsafe_allow_html=True)
            rt = df.groupby("Categoría", as_index=False)["_ars"].sum().sort_values("_ars", ascending=False)
            st.plotly_chart(torta(rt["Categoría"].tolist(), rt["_ars"].tolist()), config={"displayModeBar": False})
            st.dataframe(pd.DataFrame({
                "Categoría": rt["Categoría"], "Pesos": rt["_ars"].map(fmt_ars),
                "Dólares": rt["_ars"].map(lambda x: fmt_usd(x / dolar) if dolar else "—"),
                "%": (rt["_ars"] / total_inv * 100).map(lambda x: f"{fmt_num(x, 1)}%"),
            }), hide_index=True)
        with d2:
            st.markdown("<h4 style='color:#5B4B8A;text-align:center'>Por inversión</h4>", unsafe_allow_html=True)
            dd = df.sort_values("_ars", ascending=False)
            etiquetas = (dd["Activo"] + " (" + dd["Dónde está"] + ")").tolist()
            st.plotly_chart(torta(etiquetas, dd["_ars"].tolist()), config={"displayModeBar": False})
        tabla = pd.DataFrame(filas).sort_values("_ars", ascending=False, na_position="last")
        tabla["Valor en pesos"] = tabla["_ars"].map(lambda x: fmt_ars(x) if x is not None and x == x else "—")
        tabla["Valor en dólares"] = tabla["_ars"].map(
            lambda x: fmt_usd(x / dolar) if dolar and x is not None and x == x else "—")
        st.dataframe(tabla.drop(columns=["_ars"]), hide_index=True)
