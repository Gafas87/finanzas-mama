import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import requests
import json
import os
import io
import zipfile
import random
import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from xml.sax.saxutils import escape as xml_escape

st.set_page_config(
    page_title="Jardín Financiero",
    layout="wide",
    page_icon="🌿",
    initial_sidebar_state="expanded"
)

DATA_FILE = "datos_finanzas.json"

PALETA_PASTEL = [
    "#9B89B3",  # Lila ciruela pastel
    "#F6A682",  # Coral durazno pastel
    "#76C893",  # Verde menta pastel
    "#72B0E8",  # Celeste cielo pastel
    "#F4D06F",  # Amarillo cálido pastel
    "#E58F9E",  # Rosa viejo pastel
    "#64C2C7",  # Turquesa pastel
    "#C3A6A0",  # Visón pastel
    "#A3C9A8",  # Verde salvia pastel
    "#D99B66",  # Terracota suave
    "#8E9AAF",  # Azul pizarra pastel
    "#E2AFCF"   # Orquídea pastel
]

ICONOS_DISPONIBLES = [
    "🧾", "💡", "🚗", "👗", "🏠", "🛒", "🩺", "🏊‍♀️", "🧘‍♀️", "✈️",
    "📺", "🐾", "📚", "🎁", "💳", "💼", "💵", "👵", "📈", "📁",
    "🌿", "💎", "🛠️", "🧹", "🍽️", "📱", "⛽", "📌"
]


# ----------------- PREDICCIÓN INTELIGENTE DE ÍCONOS -----------------
def predecir_icono_categoria(nombre, tipo="costo"):
    n = (nombre or "").upper().strip()
    reglas = [
        (["IMPUESTO", "MONOTRIBUTO", "AFIP", "ARBA", "RENTAS", "INMOBILIARIO", "CISI", "TASA"], "🧾"),
        (["SERVICIO", "LUZ", "AGUA", "GAS", "INTERNET", "EDET", "SAT", "CLARO", "WIFI", "TELEFONO", "CELULAR"], "💡"),
        (["AUTO", "VEHICULO", "NAFTA", "COCHE", "PATENTE", "MECANICO", "SEGURO", "COCHERA", "UBER", "REMIS", "MOVILIDAD"], "🚗"),
        (["BELLEZA", "ESTETICA", "PELUQUERIA", "ROPA", "INDUMENTARIA", "CREMA", "COSMETICA", "UÑAS", "MODA"], "👗"),
        (["SALUD", "MEDICO", "OBRA SOCIAL", "FARMACIA", "REMEDIO", "ODONTOLOGO", "PSICOLOGO", "CLINICA", "ESTUDIO"], "🩺"),
        (["DEPORTE", "GIMNASIO", "NATACION", "YOGA", "PILATES", "CLUB", "ENTRENAMIENTO", "PADDLE", "TENIS"], "🏊‍♀️"),
        (["SUPERMERCADO", "COMIDA", "VERDURA", "CARNICERIA", "ALIMENTO", "DIETETICA", "FERIA", "MERCADO", "PANADERIA"], "🛒"),
        (["CASA", "HOGAR", "ALQUILER", "EXPENSA", "LIMPIEZA", "ARREGLO", "MANTENIMIENTO", "JARDIN", "MUEBLE"], "🏠"),
        (["GABINETE", "TERAPIA", "CONSULTORIO", "INSUMO", "PACIENTE", "SESION", "MASAJE", "REIKI"], "🧘‍♀️"),
        (["VACACION", "VIAJE", "PASEO", "TURISMO", "HOTEL", "VUELO", "ESCAPADA"], "✈️"),
        (["SUSCRIPCION", "NETFLIX", "SPOTIFY", "DISNEY", "YOUTUBE", "CABLE", "FLOW", "AMAZON", "HBO"], "📺"),
        (["MASCOTA", "PERRO", "GATO", "VETERINARIA", "ALIMENTO PERRO"], "🐾"),
        (["EDUCACION", "CURSO", "LIBRO", "TALLER", "FACULTAD", "COLEGIO"], "📚"),
        (["REGALO", "CUMPLEAÑOS", "SALIDA", "RESTAURANTE", "CAFE", "OCIO", "CINE"], "🎁"),
        (["TARJETA", "CREDITO", "BANCO", "PRESTAMO", "CUOTA", "DEUDA"], "💳"),
        (["TRABAJO", "SUELDO", "SALARIO", "HONORARIO", "AGUINALDO", "SAC", "EMPLEO"], "💼"),
        (["JUBILACION", "PENSION", "ANSES"], "👵"),
        (["RENTA", "INVERSION", "DIVIDENDO", "INTERES", "ALQUILER COBRADO"], "📈"),
        (["OTRO", "VARIOS", "EXTRA"], "💵" if tipo == "ingreso" else "📌"),
    ]
    for palabras, icono in reglas:
        if any(p in n for p in palabras):
            return icono
    return "💵" if tipo == "ingreso" else "📌"


# ----------------- NAVEGACIÓN CON FLECHAS + DRAG & DROP INTERACTIVO -----------------
def activar_interactividad_avanzada():
    js_code = """
    <script>
    const doc = window.parent.document;

    // 1. Navegación con flechas Arriba/Abajo entre casilleros numéricos y de texto
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

    // 2. Drag & Drop directo sobre los bloques de categorías (Mouse, Trackpad y Táctil Android)
    function enviarNuevoOrdenAStreamlit(placeholderText, nuevoOrdenArray) {
        const inputs = Array.from(doc.querySelectorAll('input[type="text"]'));
        const targetInput = inputs.find(el => el.placeholder === placeholderText);
        if (!targetInput) return;

        const valorJson = JSON.stringify(nuevoOrdenArray);
        if (targetInput.value === valorJson) return;

        const nativeSetter = Object.getOwnPropertyDescriptor(
            window.parent.HTMLInputElement.prototype,
            'value'
        ).set;
        nativeSetter.call(targetInput, valorJson);
        targetInput.dispatchEvent(new Event('input', { bubbles: true }));
        targetInput.dispatchEvent(new Event('change', { bubbles: true }));
        targetInput.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
        }));
        targetInput.blur();
    }

    function inicializarDragCategorias() {
        const expanders = Array.from(doc.querySelectorAll('details'));
        const grupos = { costo: [], ingreso: [] };

        expanders.forEach(det => {
            const summary = det.querySelector('summary');
            if (!summary) return;
            const texto = summary.innerText || '';
            if (!texto.includes('Subtotal:')) return;

            const wrapper = det.closest('[data-testid="stExpander"]') || det;
            if (texto.includes('⠿')) {
                // Determinar a qué columna pertenece buscando el encabezado superior
                const col = wrapper.closest('[data-testid="column"]');
                if (!col) return;
                const colText = col.innerText || '';
                const tipo = colText.includes('Mis Costos Mensuales') ? 'costo' :
                             (colText.includes('Mis Ingresos Mensuales') ? 'ingreso' : null);
                if (!tipo) return;

                // Extraer el nombre limpio de la categoría
                let parteCat = texto.split('— Subtotal:')[0].replace('⠿', '').trim();
                // Quitar primer token (ícono)
                const tokens = parteCat.split(' ');
                if (tokens.length > 1) {
                    tokens.shift();
                }
                const catNombre = tokens.join(' ').trim();
                wrapper.setAttribute('data-cat-nombre', catNombre);
                wrapper.setAttribute('data-cat-tipo', tipo);
                wrapper.style.transition = 'transform 0.15s ease, box-shadow 0.15s ease';
                summary.style.cursor = 'grab';
                summary.title = 'Arrastrá con el mouse o el dedo para cambiar el orden de esta categoría';
                grupos[tipo].push(wrapper);
            }
        });

        ['costo', 'ingreso'].forEach(tipo => {
            const items = grupos[tipo];
            if (items.length < 2) return;
            const parentContainer = items[0].parentElement;
            if (!parentContainer || parentContainer.getAttribute('data-dnd-ready') === 'true') return;
            parentContainer.setAttribute('data-dnd-ready', 'true');

            let draggedEl = null;

            items.forEach(item => {
                item.setAttribute('draggable', 'true');

                item.addEventListener('dragstart', function(e) {
                    // Evitar iniciar drag si el usuario está escribiendo en un input dentro del expander
                    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT')) {
                        e.preventDefault();
                        return;
                    }
                    draggedEl = item;
                    item.style.opacity = '0.55';
                    item.style.boxShadow = '0 8px 20px rgba(126, 34, 206, 0.22)';
                    if (e.dataTransfer) {
                        e.dataTransfer.effectAllowed = 'move';
                        e.dataTransfer.setData('text/plain', item.getAttribute('data-cat-nombre'));
                    }
                });

                item.addEventListener('dragover', function(e) {
                    e.preventDefault();
                    if (!draggedEl || draggedEl === item) return;
                    if (draggedEl.getAttribute('data-cat-tipo') !== item.getAttribute('data-cat-tipo')) return;
                    const rect = item.getBoundingClientRect();
                    const mitad = rect.top + rect.height / 2;
                    if (e.clientY < mitad) {
                        parentContainer.insertBefore(draggedEl, item);
                    } else {
                        parentContainer.insertBefore(draggedEl, item.nextSibling);
                    }
                });

                item.addEventListener('dragend', function() {
                    if (!draggedEl) return;
                    draggedEl.style.opacity = '1';
                    draggedEl.style.boxShadow = 'none';
                    const tipoActual = draggedEl.getAttribute('data-cat-tipo');
                    const actuales = Array.from(
                        parentContainer.querySelectorAll('[data-cat-tipo="' + tipoActual + '"]')
                    ).map(el => el.getAttribute('data-cat-nombre')).filter(Boolean);

                    const placeholderKey = tipoActual === 'costo' ? 'SYNC_ORDEN_COSTOS' : 'SYNC_ORDEN_INGRESOS';
                    enviarNuevoOrdenAStreamlit(placeholderKey, actuales);
                    draggedEl = null;
                });

                // Soporte táctil para celulares Android (arrastrar desde el encabezado)
                const summaryEl = item.querySelector('summary');
                if (summaryEl) {
                    let touchActive = false;
                    let startY = 0;

                    summaryEl.addEventListener('touchstart', function(e) {
                        if (e.touches.length !== 1) return;
                        startY = e.touches[0].clientY;
                        touchActive = false;
                    }, { passive: true });

                    summaryEl.addEventListener('touchmove', function(e) {
                        if (e.touches.length !== 1) return;
                        const currentY = e.touches[0].clientY;
                        if (Math.abs(currentY - startY) > 14) {
                            touchActive = true;
                            draggedEl = item;
                            item.style.opacity = '0.65';
                            item.style.boxShadow = '0 8px 20px rgba(126, 34, 206, 0.22)';
                            const siblings = Array.from(
                                parentContainer.querySelectorAll('[data-cat-tipo="' + tipo + '"]')
                            );
                            siblings.forEach(sib => {
                                if (sib === item) return;
                                const rect = sib.getBoundingClientRect();
                                if (currentY > rect.top && currentY < rect.bottom) {
                                    const mitad = rect.top + rect.height / 2;
                                    if (currentY < mitad) {
                                        parentContainer.insertBefore(item, sib);
                                    } else {
                                        parentContainer.insertBefore(item, sib.nextSibling);
                                    }
                                }
                            });
                        }
                    }, { passive: true });

                    summaryEl.addEventListener('touchend', function() {
                        if (!touchActive || !draggedEl) return;
                        draggedEl.style.opacity = '1';
                        draggedEl.style.boxShadow = 'none';
                        const actuales = Array.from(
                            parentContainer.querySelectorAll('[data-cat-tipo="' + tipo + '"]')
                        ).map(el => el.getAttribute('data-cat-nombre')).filter(Boolean);
                        const placeholderKey = tipo === 'costo' ? 'SYNC_ORDEN_COSTOS' : 'SYNC_ORDEN_INGRESOS';
                        enviarNuevoOrdenAStreamlit(placeholderKey, actuales);
                        draggedEl = null;
                        touchActive = false;
                    });
                }
            });
        });
    }

    setTimeout(inicializarDragCategorias, 350);
    setTimeout(inicializarDragCategorias, 1000);
    </script>
    """
    components.html(js_code, height=0, width=0)


# ----------------- GRÁFICO DE TORTA 2D CON LÍNEAS EXTERNAS -----------------
def crear_torta_2d(df, col_valores, col_nombres):
    valores = df[col_valores].tolist()
    nombres = df[col_nombres].tolist()
    total = sum(valores) if sum(valores) > 0 else 1.0
    n = len(valores)

    colores = [PALETA_PASTEL[i % len(PALETA_PASTEL)] for i in range(n)]

    posiciones = [
        "outside" if (v / total) < 0.09 else "inside"
        for v in valores
    ]

    fig = go.Figure(data=[go.Pie(
        labels=nombres,
        values=valores,
        hole=0.36,
        sort=True,
        direction="clockwise",
        textposition=posiciones,
        textinfo="label+percent",
        insidetextorientation="horizontal",
        pull=[0.012] * n,
        automargin=True,
        textfont=dict(
            size=15,
            color="#1F2937",
            family="Arial, sans-serif"
        ),
        marker=dict(
            colors=colores,
            line=dict(color="#FFFFFF", width=2)
        ),
        showlegend=False
    )])

    fig.update_layout(
        uniformtext=dict(minsize=14, mode="show"),
        height=430,
        margin=dict(t=35, b=35, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode=False
    )
    return fig


# ----------------- GRÁFICO DE BARRAS HORIZONTALES LIMPIO (REQ 7 y 8) -----------------
def crear_barras_horizontales(df, col_valores, col_nombres):
    df_ord = df.sort_values(by=col_valores, ascending=True).copy()
    valores = df_ord[col_valores].tolist()
    nombres = df_ord[col_nombres].tolist()
    total = sum(valores) if sum(valores) > 0 else 1.0
    max_val = max(valores) if valores else 1.0
    n = len(valores)

    # Colores pastel por nivel (de menor a mayor porque está ordenado ascendente para Plotly horizontal)
    colores = []
    for idx_b, v in enumerate(valores):
        ratio = (idx_b + 1) / max(n, 1)
        if ratio > 0.66:
            colores.append("#F5B7B1")  # Rojo pastel suave
        elif ratio > 0.33:
            colores.append("#F9E79F")  # Amarillo pastel suave
        else:
            colores.append("#ABEBC6")  # Verde pastel suave

    # Únicamente el monto en ARS y el % (sin ejes ni grillas grises ni 0.5M / 1M / 100k)
    textos = [f"  {v:,.0f} ARS ({(v / total) * 100:.1f}%)" for v in valores]

    fig = go.Figure(data=[go.Bar(
        x=valores,
        y=nombres,
        orientation="h",
        text=textos,
        textposition="outside",
        cliponaxis=False,
        textfont=dict(
            size=14,
            color="#1F2937",
            family="Arial, sans-serif"
        ),
        marker=dict(
            color=colores,
            line=dict(color="#6B7280", width=1.2)
        ),
        hoverinfo="skip"
    )])

    altura_dinamica = max(300, n * 48 + 40)

    fig.update_layout(
        height=altura_dinamica,
        margin=dict(t=15, b=15, l=10, r=140),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode=False,
        xaxis=dict(
            visible=False,
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            showline=False,
            title="",
            range=[0, max_val * 1.48]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            title="",
            automargin=True,
            tickfont=dict(
                size=13,
                color="#1F2937",
                family="Arial, sans-serif"
            )
        )
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
    n = (nombre or "").upper().strip()
    if any(k in n for k in ["INMOBILIARIO", "CISI", "COSI", "AUTOMOTOR", "IMPUESTO", "MONOTRIBUTO"]):
        return "IMPUESTOS"
    if any(k in n for k in ["SAT", "EDET", "GAS", "CLARO", "LUZ", "AGUA", "INTERNET", "SERVICIO"]):
        return "SERVICIOS"
    if any(k in n for k in ["NETFLIX", "DISNEY", "SPOTIFY", "FLOW", "YOUTUBE"]):
        return "SUSCRIPCIONES"
    if any(k in n for k in ["NAFTA", "SEGURO", "AUTO", "PATENTE", "COCHERA"]):
        return "AUTO"
    if any(k in n for k in ["GABINETE", "INSUMO", "CONSULTORIO"]):
        return "GABINETE"
    return "HOGAR Y OTROS"


# ----------------- GESTIÓN Y PERSISTENCIA DE DATOS -----------------
def cargar_datos():
    criptos_base = ["BTC", "ETH", "USDT", "SOL", "BNB", "ADA", "XRP", "DOT", "DOGE"]
    acciones_base = [
        "AAPL (Apple)", "KO (Coca-Cola)", "MELI (MercadoLibre)",
        "SPY (S&P 500)", "MSFT (Microsoft)", "GOOGL (Google)",
        "NVDA (Nvidia)", "TSLA (Tesla)", "AMZN (Amazon)", "YPFD (YPF)"
    ]

    datos_por_defecto = {
        "seguridad": {
            "usuario": "mama",
            "password_actual": "Finanzasmama123",
            "passwords_validas": ["Finanzasmama123", "terapias123"],
            "email_recuperacion": "",
            "telefono_recuperacion": ""
        },
        "categorias_costos": [
            "IMPUESTOS",
            "SERVICIOS",
            "AUTO",
            "BELLEZA",
            "HOGAR Y OTROS",
            "GABINETE"
        ],
        "iconos_costos": {
            "IMPUESTOS": "🧾",
            "SERVICIOS": "💡",
            "AUTO": "🚗",
            "BELLEZA": "👗",
            "HOGAR Y OTROS": "🏠",
            "GABINETE": "🧘‍♀️"
        },
        "costos": [
            {"grupo": "IMPUESTOS", "categoria": "INMOBILIARIO", "monto": 2462, "activo": True},
            {"grupo": "IMPUESTOS", "categoria": "CISI", "monto": 2659, "activo": True},
            {"grupo": "IMPUESTOS", "categoria": "AUTOMOTOR", "monto": 2667, "activo": True},
            {"grupo": "SERVICIOS", "categoria": "SAT", "monto": 36000, "activo": True},
            {"grupo": "SERVICIOS", "categoria": "EDET", "monto": 60000, "activo": True},
            {"grupo": "SERVICIOS", "categoria": "GAS", "monto": 16000, "activo": True},
            {"grupo": "SERVICIOS", "categoria": "CLARO + RECARGA", "monto": 29000, "activo": True},
            {"grupo": "AUTO", "categoria": "NAFTA", "monto": 86000, "activo": True},
            {"grupo": "AUTO", "categoria": "SEGURO", "monto": 40083, "activo": True},
            {"grupo": "BELLEZA", "categoria": "ESTETICA", "monto": 85000, "activo": True},
            {"grupo": "HOGAR Y OTROS", "categoria": "CASA ARREGLOS", "monto": 150000, "activo": True},
            {"grupo": "HOGAR Y OTROS", "categoria": "VERDURAS", "monto": 80000, "activo": True},
            {"grupo": "HOGAR Y OTROS", "categoria": "ADRIAN LIMP", "monto": 64000, "activo": True},
            {"grupo": "HOGAR Y OTROS", "categoria": "NATACION", "monto": 95000, "activo": True},
            {"grupo": "HOGAR Y OTROS", "categoria": "VACACIONES", "monto": 200000, "activo": True},
            {"grupo": "GABINETE", "categoria": "GABINETE", "monto": 80000, "activo": True}
        ],
        "categorias_ingresos": [
            "Trabajo",
            "Otros ingresos"
        ],
        "iconos_ingresos": {
            "Trabajo": "📁",
            "Otros ingresos": "💵"
        },
        "ingresos": [
            {"grupo": "Trabajo", "concepto": "SUELDO", "monto": 1400000, "activo": True},
            {"grupo": "Trabajo", "concepto": "SAC", "monto": 116667, "activo": True},
            {"grupo": "Otros ingresos", "concepto": "JUBILACION", "monto": 647000, "activo": True}
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
        ],
        "historial_cierres": []
    }

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Asegurar bloque de seguridad
            seg = data.get("seguridad", {})
            seg.setdefault("usuario", "mama")
            seg.setdefault("password_actual", "Finanzasmama123")
            pw_val = seg.get("passwords_validas", ["Finanzasmama123", "terapias123"])
            if seg["password_actual"] not in pw_val:
                pw_val.append(seg["password_actual"])
            seg["passwords_validas"] = pw_val
            seg.setdefault("email_recuperacion", "")
            seg.setdefault("telefono_recuperacion", "")
            data["seguridad"] = seg

            for c in data.get("costos", []):
                c.setdefault("activo", True)
                if "grupo" not in c or not c["grupo"]:
                    c["grupo"] = clasificar_costo_existente(c.get("categoria", ""))

            for ing in data.get("ingresos", []):
                ing.setdefault("activo", True)
                if "grupo" not in ing or not ing["grupo"]:
                    nom_low = ing.get("concepto", "").lower()
                    if "farmacia" in nom_low or "sac" in nom_low or "sueldo" in nom_low:
                        ing["grupo"] = "Trabajo"
                    else:
                        ing["grupo"] = "Otros ingresos"

            cats_c = list(dict.fromkeys(
                data.get("categorias_costos", datos_por_defecto["categorias_costos"])
                + [c["grupo"] for c in data.get("costos", [])]
            ))
            data["categorias_costos"] = cats_c

            cats_i = list(dict.fromkeys(
                data.get("categorias_ingresos", datos_por_defecto["categorias_ingresos"])
                + [i["grupo"] for i in data.get("ingresos", [])]
            ))
            data["categorias_ingresos"] = cats_i

            # Asignar íconos automáticamente si alguna categoría no lo tiene
            iconos_c = data.get("iconos_costos", {})
            for cat in cats_c:
                if cat not in iconos_c or not iconos_c[cat]:
                    iconos_c[cat] = predecir_icono_categoria(cat, "costo")
            data["iconos_costos"] = iconos_c

            iconos_i = data.get("iconos_ingresos", {})
            for cat in cats_i:
                if cat not in iconos_i or not iconos_i[cat]:
                    iconos_i[cat] = predecir_icono_categoria(cat, "ingreso")
            data["iconos_ingresos"] = iconos_i

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
            data.setdefault("acciones_guardadas", acciones_base)
            data.setdefault("historial_cierres", [])
            return data
        except Exception:
            pass

    return datos_por_defecto


def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)


# ----------------- EXPORTACIÓN A EXCEL (.XLSX), CSV (.CSV) Y PDF (.PDF) -----------------
def armar_dataframes_exportacion(datos, dolar_b, cotizaciones):
    tz_ar = timezone(timedelta(hours=-3))
    fecha_actual = datetime.now(tz_ar).strftime("%Y-%m-%d %H:%M")

    filas_mov = []
    for c in datos.get("costos", []):
        monto_ars = float(c.get("monto", 0))
        filas_mov.append({
            "Fecha Registro": fecha_actual,
            "Tipo": "Costo",
            "Categoría": c.get("grupo", ""),
            "Subcategoría / Concepto": c.get("categoria", ""),
            "Activo": "Sí" if c.get("activo", True) else "No",
            "Monto (ARS)": monto_ars,
            "Monto (USD Blue)": round(monto_ars / dolar_b, 2) if dolar_b > 0 else 0.0
        })

    for i in datos.get("ingresos", []):
        monto_ars = float(i.get("monto", 0))
        filas_mov.append({
            "Fecha Registro": fecha_actual,
            "Tipo": "Ingreso",
            "Categoría": i.get("grupo", ""),
            "Subcategoría / Concepto": i.get("concepto", ""),
            "Activo": "Sí" if i.get("activo", True) else "No",
            "Monto (ARS)": monto_ars,
            "Monto (USD Blue)": round(monto_ars / dolar_b, 2) if dolar_b > 0 else 0.0
        })

    df_mov = pd.DataFrame(filas_mov) if filas_mov else pd.DataFrame(
        columns=["Fecha Registro", "Tipo", "Categoría", "Subcategoría / Concepto", "Activo", "Monto (ARS)", "Monto (USD Blue)"]
    )

    filas_inv = []
    for inv in datos.get("inversiones", []):
        cant = float(inv.get("cantidad", 0))
        tipo = inv.get("tipo", "Pesos ARS")
        simbolo = inv.get("simbolo", "").upper().strip()
        if tipo == "Dólar Billete":
            val_usd = cant
            val_ars = cant * dolar_b
        elif tipo in ["Criptomonedas", "Acciones"]:
            precio_u = cotizaciones.get(simbolo, 1.0)
            val_usd = cant * precio_u
            val_ars = val_usd * dolar_b
        else:
            val_ars = cant
            val_usd = cant / dolar_b if dolar_b > 0 else 0.0

        filas_inv.append({
            "Fecha Registro": fecha_actual,
            "Categoría Activo": tipo,
            "Activo": inv.get("activo", ""),
            "Ubicación / Plataforma": inv.get("plataforma", ""),
            "Cantidad": cant,
            "Activo en Cartera": "Sí" if inv.get("activo_inv", True) else "No",
            "Valor Estimado (ARS)": round(val_ars, 2),
            "Valor Estimado (USD)": round(val_usd, 2)
        })

    df_inv = pd.DataFrame(filas_inv) if filas_inv else pd.DataFrame(
        columns=["Fecha Registro", "Categoría Activo", "Activo", "Ubicación / Plataforma", "Cantidad", "Activo en Cartera", "Valor Estimado (ARS)", "Valor Estimado (USD)"]
    )

    df_hist = pd.DataFrame(datos.get("historial_cierres", []))
    return df_mov, df_inv, df_hist


def generar_csv_bytes(datos, dolar_b, cotizaciones):
    df_mov, df_inv, df_hist = armar_dataframes_exportacion(datos, dolar_b, cotizaciones)
    buf = io.StringIO()
    buf.write("--- COSTOS E INGRESOS MENSUALES ---\n")
    df_mov.to_csv(buf, index=False)
    buf.write("\n--- CARTERA DE INVERSIONES ---\n")
    df_inv.to_csv(buf, index=False)
    if not df_hist.empty:
        buf.write("\n--- HISTORIAL ACUMULADO DE CIERRES ---\n")
        df_hist.to_csv(buf, index=False)
    return ("\ufeff" + buf.getvalue()).encode("utf-8")


def _generar_xlsx_fallback_zip(hojas_dict):
    """Generador nativo de .xlsx sin dependencias externas si openpyxl no está instalado."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""")
        zf.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""")
        zf.writestr("xl/workbook.xml", """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Costos e Ingresos" sheetId="1" r:id="rId1"/>
    <sheet name="Inversiones" sheetId="2" r:id="rId2"/>
    <sheet name="Historial Acumulado" sheetId="3" r:id="rId3"/>
  </sheets>
</workbook>""")
        zf.writestr("xl/_rels/workbook.xml.rels", """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>
</Relationships>""")

        for idx_s, (_, df_s) in enumerate(hojas_dict.items(), start=1):
            rows_xml = []
            if not df_s.empty:
                headers = list(df_s.columns)
                cells_h = "".join(
                    f'<c t="inlineStr"><is><t>{xml_escape(str(h))}</t></is></c>' for h in headers
                )
                rows_xml.append(f'<row r="1">{cells_h}</row>')
                for r_idx, row in enumerate(df_s.itertuples(index=False), start=2):
                    cells_r = []
                    for val in row:
                        if isinstance(val, (int, float)) and not isinstance(val, bool):
                            cells_r.append(f"<c><v>{val}</v></c>")
                        else:
                            cells_r.append(f'<c t="inlineStr"><is><t>{xml_escape(str(val))}</t></is></c>')
                    rows_xml.append(f'<row r="{r_idx}">{"" .join(cells_r)}</row>')
            else:
                rows_xml.append('<row r="1"><c t="inlineStr"><is><t>Sin registros</t></is></c></row>')
            sheet_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<sheetData>{"".join(rows_xml)}</sheetData></worksheet>'
            )
            zf.writestr(f"xl/worksheets/sheet{idx_s}.xml", sheet_xml)
    return buf.getvalue()


def generar_excel_bytes(datos, dolar_b, cotizaciones):
    df_mov, df_inv, df_hist = armar_dataframes_exportacion(datos, dolar_b, cotizaciones)
    try:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df_mov.to_excel(writer, sheet_name="Costos e Ingresos", index=False)
            df_inv.to_excel(writer, sheet_name="Inversiones", index=False)
            if not df_hist.empty:
                df_hist.to_excel(writer, sheet_name="Historial Acumulado", index=False)
        return buf.getvalue()
    except Exception:
        return _generar_xlsx_fallback_zip({
            "Costos e Ingresos": df_mov,
            "Inversiones": df_inv,
            "Historial Acumulado": df_hist
        })


def generar_pdf_bytes(datos, dolar_b, cotizaciones):
    df_mov, df_inv, df_hist = armar_dataframes_exportacion(datos, dolar_b, cotizaciones)
    tz_ar = timezone(timedelta(hours=-3))
    fecha_str = datetime.now(tz_ar).strftime("%d/%m/%Y %H:%M")

    costos_act = sum(c["monto"] for c in datos.get("costos", []) if c.get("activo", True))
    ingresos_act = sum(i["monto"] for i in datos.get("ingresos", []) if i.get("activo", True))
    ahorro_act = ingresos_act - costos_act

    lineas = [
        f"JARDIN FINANCIERO - RESUMEN Y RESPALDO ({fecha_str})",
        f"Dolar Blue de referencia: {dolar_b:,.0f} ARS",
        "-" * 68,
        f"Total Ingresos Activos: {ingresos_act:,.0f} ARS ({ingresos_act/dolar_b:,.2f} USD)",
        f"Total Costos Activos:   {costos_act:,.0f} ARS ({costos_act/dolar_b:,.2f} USD)",
        f"Ahorro Mensual Neto:    {ahorro_act:,.0f} ARS ({ahorro_act/dolar_b:,.2f} USD)",
        "-" * 68,
        "DETALLE DE COSTOS E INGRESOS:",
    ]
    for _, r in df_mov.iterrows():
        lineas.append(
            f" [{r['Tipo']}] {r['Categoría']} > {r['Subcategoría / Concepto']}: "
            f"{r['Monto (ARS)']:,.0f} ARS ({r['Monto (USD Blue)']:,.2f} USD) - Activo: {r['Activo']}"
        )

    lineas.append("-" * 68)
    lineas.append("CARTERA DE INVERSIONES:")
    for _, r in df_inv.iterrows():
        lineas.append(
            f" [{r['Categoría Activo']}] {r['Activo']} ({r['Ubicación / Plataforma']}): "
            f"Cant {r['Cantidad']} -> {r['Valor Estimado (ARS)']:,.0f} ARS ({r['Valor Estimado (USD)']:,.2f} USD)"
        )

    if not df_hist.empty:
        lineas.append("-" * 68)
        lineas.append("HISTORIAL ACUMULADO DE CIERRES:")
        for _, r in df_hist.tail(15).iterrows():
            lineas.append(
                f" {r.get('Fecha', '')} | Ingresos: {r.get('Ingresos ARS', 0):,.0f} | "
                f"Costos: {r.get('Costos ARS', 0):,.0f} | Ahorro: {r.get('Ahorro ARS', 0):,.0f}"
            )

    # Construcción de PDF 1.4 estándar sin requerir librerías externas
    def _esc_pdf(s):
        s_ascii = s.encode("latin-1", "replace").decode("latin-1")
        return s_ascii.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    paginas = [lineas[i:i + 46] for i in range(0, max(1, len(lineas)), 46)]
    objs = []
    objs.append("1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj")
    kids_refs = " ".join(f"{3 + i * 2} 0 R" for i in range(len(paginas)))
    objs.append(f"2 0 obj << /Type /Pages /Kids [{kids_refs}] /Count {len(paginas)} >> endobj")
    font_obj_num = 3 + len(paginas) * 2

    for idx_p, pag_lineas in enumerate(paginas):
        page_num = 3 + idx_p * 2
        content_num = page_num + 1
        ops = ["BT", "/F1 10 Tf", "40 790 Td", "15 TL"]
        for ln in pag_lineas:
            ops.append(f"({_esc_pdf(ln)}) Tj T*")
        ops.append("ET")
        stream_data = "\n".join(ops)
        objs.append(
            f"{page_num} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_obj_num} 0 R >> >> /Contents {content_num} 0 R >> endobj"
        )
        objs.append(
            f"{content_num} 0 obj << /Length {len(stream_data.encode('latin-1'))} >> stream\n"
            f"{stream_data}\nendstream endobj"
        )

    objs.append(f"{font_obj_num} 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj")

    pdf_out = "%PDF-1.4\n"
    offsets = []
    for o in objs:
        offsets.append(len(pdf_out.encode("latin-1")))
        pdf_out += o + "\n"
    xref_pos = len(pdf_out.encode("latin-1"))
    pdf_out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n"
    for off in offsets:
        pdf_out += f"{off:010d} 00000 n \n"
    pdf_out += (
        f"trailer << /Size {len(objs) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF"
    )
    return pdf_out.encode("latin-1")


def registrar_snapshot_cierre(datos, dolar_b, cotizaciones):
    tz_ar = timezone(timedelta(hours=-3))
    fecha_str = datetime.now(tz_ar).strftime("%Y-%m-%d %H:%M")
    costos_act = sum(c["monto"] for c in datos.get("costos", []) if c.get("activo", True))
    ingresos_act = sum(i["monto"] for i in datos.get("ingresos", []) if i.get("activo", True))
    ahorro_act = ingresos_act - costos_act

    hist = datos.setdefault("historial_cierres", [])
    # Evitar duplicar si ya se registró en el mismo minuto
    if not hist or hist[-1].get("Fecha") != fecha_str:
        hist.append({
            "Fecha": fecha_str,
            "Ingresos ARS": round(ingresos_act, 2),
            "Costos ARS": round(costos_act, 2),
            "Ahorro ARS": round(ahorro_act, 2),
            "Dólar Blue": round(dolar_b, 2),
            "Ahorro USD": round(ahorro_act / dolar_b, 2) if dolar_b > 0 else 0.0
        })
    guardar_datos(datos)


# ----------------- ENVÍO DE RECUPERACIÓN POR GMAIL -----------------
def intentar_enviar_gmail(destinatario, codigo, usuario_actual):
    """Intenta enviar el correo vía SMTP si hay credenciales en st.secrets; devuelve (enviado_bool, detalle)."""
    try:
        smtp_user = st.secrets.get("gmail_user", "")
        smtp_pass = st.secrets.get("gmail_app_password", "")
        if smtp_user and smtp_pass:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = destinatario
            msg["Subject"] = "🌿 Recuperación de acceso - Tu Jardín Financiero"
            cuerpo = (
                f"Hola!\n\n"
                f"Solicitaste recuperar tu acceso a Jardín Financiero.\n"
                f"• Tu Usuario es: {usuario_actual}\n"
                f"• Tu Código de verificación es: {codigo}\n\n"
                f"Ingresá este código en la pantalla para crear una nueva contraseña."
            )
            msg.attach(MIMEText(cuerpo, "plain", "utf-8"))
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=6)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            return True, "Correo enviado automáticamente a tu cuenta de Gmail."
    except Exception:
        pass
    return False, "Modo directo activado."


# ----------------- COTIZACIONES EXTERNAS -----------------
@st.cache_data(ttl=180)
def obtener_cotizaciones(simbolos_acciones, simbolos_cripto):
    cotiz = {
        "dolar_blue": 1575.0,
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


# ----------------- ESTILOS CSS OPTIMIZADOS (LAPTOP + ANDROID) -----------------
st.markdown("""
<style>
    html, body, [class*="css"], p, span, label, div {
        font-size: 16px;
        color: #374151;
    }

    /* Aprovechar al máximo el ancho de la pantalla en notebook y celular (Req 4) */
    .block-container {
        max-width: 98% !important;
        padding-left: 1.4rem !important;
        padding-right: 1.4rem !important;
        padding-top: 1.4rem !important;
        padding-bottom: 2.5rem !important;
    }

    @media (max-width: 768px) {
        .block-container {
            max-width: 100% !important;
            padding-left: 0.65rem !important;
            padding-right: 0.65rem !important;
            padding-top: 0.8rem !important;
        }
        .kpi-value {
            font-size: 1.65rem !important;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 14px !important;
            height: 52px !important;
        }
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.1rem !important;
        }
    }

    .jardin-login-box {
        background: linear-gradient(145deg, #EAF6EE 0%, #F5F0FF 100%);
        border: 2px solid #95D5B2;
        border-radius: 22px;
        padding: 28px 24px 18px 24px;
        box-shadow: 0 8px 20px rgba(45, 106, 79, 0.08);
        text-align: center;
        margin-top: 18px;
        margin-bottom: 14px;
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

    /* Botón principal de login "Ingresar a Mi Jardín" */
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(90deg, #40916C 0%, #2D6A4F 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.15rem !important;
        border-radius: 12px !important;
        border: 2px solid #1B4332 !important;
        min-height: 48px !important;
    }
    div[data-testid="stFormSubmitButton"] button p,
    div[data-testid="stFormSubmitButton"] button span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }

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

    /* Encabezado de tabla en un solo renglón sin cortarse nunca (Req 3: ACT.) */
    .col-header {
        font-size: 0.82rem;
        font-weight: 700;
        color: #4B5563;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        padding-bottom: 4px;
        border-bottom: 2px solid #D1D5DB;
        margin-bottom: 8px;
        white-space: nowrap !important;
        overflow: visible !important;
        word-break: keep-all !important;
    }

    div[data-testid="stCheckbox"] {
        filter: hue-rotate(125deg) saturate(0.85) brightness(0.95) !important;
        padding-top: 0.35rem;
    }
    div[data-testid="stCheckbox"] label p {
        white-space: nowrap !important;
    }

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

    div[data-testid="stButton"] button {
        border-radius: 10px !important;
        border: 1px solid #D1D5DB !important;
        background-color: #FFFFFF !important;
        padding: 0.35rem 0.55rem !important;
        min-width: 44px !important;
        min-height: 42px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stButton"] button p {
        font-size: 1.05rem !important;
        line-height: 1.1 !important;
        margin: 0 !important;
        overflow: visible !important;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #FEE2E2 !important;
        border-color: #FCA5A5 !important;
    }

    /* Estilo distintivo y amplio para los bloques de Agregar Nueva Categoría (Req 4) */
    details:has(summary p strong), details {
        border-radius: 12px !important;
    }
    div[data-testid="stExpander"]:has(summary:contains("AGREGAR NUEVA CATEGORÍA DE COSTOS")),
    div[data-testid="stExpander"]:first-of-type {
        border-radius: 14px !important;
    }

    /* Ocultar los inputs puente usados para sincronizar el Drag & Drop */
    div[data-testid="stTextInput"]:has(input[placeholder="SYNC_ORDEN_COSTOS"]),
    div[data-testid="stTextInput"]:has(input[placeholder="SYNC_ORDEN_INGRESOS"]) {
        position: absolute !important;
        left: -9999px !important;
        width: 1px !important;
        height: 1px !important;
        overflow: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
</style>
""", unsafe_allow_html=True)

datos = cargar_datos()

# ----------------- PANTALLA DE LOGIN Y RECUPERACIÓN (REQ 1) -----------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "login_fallido" not in st.session_state:
    st.session_state.login_fallido = False
if "mostrar_recuperacion" not in st.session_state:
    st.session_state.mostrar_recuperacion = False
if "codigo_recuperacion" not in st.session_state:
    st.session_state.codigo_recuperacion = None
if "metodo_recuperacion_activo" not in st.session_state:
    st.session_state.metodo_recuperacion_activo = None
if "destino_recuperacion" not in st.session_state:
    st.session_state.destino_recuperacion = ""

if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([0.85, 1.5, 0.85])
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
            user = st.text_input("Usuario", value="mama")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button(
                "🌿 Ingresar a Mi Jardín",
                use_container_width=True
            )
            if submit:
                seg = datos.get("seguridad", {})
                usuario_esperado = seg.get("usuario", "mama").strip().lower()
                passwords_validas = seg.get("passwords_validas", ["Finanzasmama123", "terapias123"])
                u_ok = user.strip().lower() == usuario_esperado
                p_ok = password in passwords_validas or password == seg.get("password_actual", "Finanzasmama123")
                if u_ok and p_ok:
                    st.session_state.autenticado = True
                    st.session_state.login_fallido = False
                    st.session_state.mostrar_recuperacion = False
                    st.rerun()
                else:
                    st.session_state.login_fallido = True
                    st.session_state.mostrar_recuperacion = True

        if st.session_state.login_fallido:
            st.error("Usuario o contraseña incorrectos.")

        if st.button("🔑 ¿Olvidaste tu contraseña o usuario? Recuperar acceso", use_container_width=True):
            st.session_state.mostrar_recuperacion = not st.session_state.mostrar_recuperacion

        if st.session_state.mostrar_recuperacion:
            st.markdown("""
            <div style="background-color: #F3E8FF; border: 2px solid #C084FC; border-radius: 16px; padding: 16px; margin-top: 8px;">
                <b style="color: #4A235A; font-size: 1.1rem;">🔐 Recuperación de Usuario y Contraseña</b><br>
                <span style="font-size: 0.95rem; color: #374151;">
                    Elegí cómo preferís recibir tu código de recuperación para ver tu usuario o cambiar tu contraseña:
                </span>
            </div>
            """, unsafe_allow_html=True)

            tab_mail, tab_cel = st.tabs(["📧 Por Gmail / Email", "📱 Por Código al Celular"])

            with tab_mail:
                email_guardado = datos.get("seguridad", {}).get("email_recuperacion", "")
                email_input = st.text_input(
                    "Ingresá tu dirección de Gmail / Email:",
                    value=email_guardado,
                    placeholder="ejemplo@gmail.com",
                    key="rec_email_input"
                )
                if st.button("📨 Enviar código de recuperación a mi Gmail", use_container_width=True, key="btn_send_mail"):
                    if email_input.strip() and "@" in email_input:
                        datos["seguridad"]["email_recuperacion"] = email_input.strip()
                        guardar_datos(datos)
                        codigo_gen = str(random.randint(100000, 999999))
                        st.session_state.codigo_recuperacion = codigo_gen
                        st.session_state.metodo_recuperacion_activo = "email"
                        st.session_state.destino_recuperacion = email_input.strip()
                        enviado_smtp, _ = intentar_enviar_gmail(
                            email_input.strip(),
                            codigo_gen,
                            datos["seguridad"].get("usuario", "mama")
                        )
                        st.session_state.enviado_smtp = enviado_smtp
                    else:
                        st.warning("Por favor ingresá una dirección de correo válida (con @).")

            with tab_cel:
                tel_guardado = datos.get("seguridad", {}).get("telefono_recuperacion", "")
                tel_input = st.text_input(
                    "Ingresá tu número de celular (con código de área):",
                    value=tel_guardado,
                    placeholder="Ej: +54 9 381 1234567",
                    key="rec_tel_input"
                )
                if st.button("📲 Enviar código de verificación a mi celular", use_container_width=True, key="btn_send_sms"):
                    limpio_tel = "".join(ch for ch in tel_input if ch.isdigit())
                    if len(limpio_tel) >= 7:
                        datos["seguridad"]["telefono_recuperacion"] = tel_input.strip()
                        guardar_datos(datos)
                        codigo_gen = str(random.randint(100000, 999999))
                        st.session_state.codigo_recuperacion = codigo_gen
                        st.session_state.metodo_recuperacion_activo = "celular"
                        st.session_state.destino_recuperacion = limpio_tel
                    else:
                        st.warning("Por favor ingresá un número de celular válido.")

            if st.session_state.codigo_recuperacion:
                cod_actual = st.session_state.codigo_recuperacion
                usr_actual = datos.get("seguridad", {}).get("usuario", "mama")
                st.markdown("---")
                if st.session_state.metodo_recuperacion_activo == "email":
                    dest = st.session_state.destino_recuperacion
                    asunto_url = urllib.parse.quote("Recuperación de acceso - Jardín Financiero")
                    cuerpo_url = urllib.parse.quote(
                        f"Hola! Tu usuario es: {usr_actual} y tu código de recuperación es: {cod_actual}"
                    )
                    gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to={dest}&su={asunto_url}&body={cuerpo_url}"
                    st.info(
                        f"📩 Código generado para **{dest}**: **`{cod_actual}`** "
                        f"([Abrir en Gmail]({gmail_link}))"
                    )
                else:
                    dest = st.session_state.destino_recuperacion
                    texto_wa = urllib.parse.quote(
                        f"🌿 Jardín Financiero: Tu usuario es *{usr_actual}* y tu código de recuperación es *{cod_actual}*"
                    )
                    wa_link = f"https://wa.me/{dest}?text={texto_wa}"
                    st.info(
                        f"📲 Código generado para tu celular: **`{cod_actual}`** "
                        f"([Enviar a mi WhatsApp]({wa_link}))"
                    )

                cod_ingresado = st.text_input(
                    "Ingresá el código de 6 dígitos recibido:",
                    value=cod_actual,
                    key="input_verificar_codigo"
                )
                if cod_ingresado.strip() == cod_actual:
                    st.success(f"✅ Código verificado. Tu usuario es: **{usr_actual}**")
                    nueva_pass = st.text_input(
                        "Escribí tu nueva contraseña (o dejá la sugerida):",
                        value="Finanzasmama123",
                        key="input_nueva_pass_rec"
                    )
                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        if st.button("💾 Guardar nueva contraseña y Entrar", use_container_width=True):
                            if nueva_pass.strip():
                                datos["seguridad"]["password_actual"] = nueva_pass.strip()
                                if nueva_pass.strip() not in datos["seguridad"]["passwords_validas"]:
                                    datos["seguridad"]["passwords_validas"].append(nueva_pass.strip())
                                guardar_datos(datos)
                                st.session_state.autenticado = True
                                st.session_state.login_fallido = False
                                st.session_state.mostrar_recuperacion = False
                                st.session_state.codigo_recuperacion = None
                                st.rerun()
                    with col_r2:
                        if st.button("🌿 Entrar directo ahora", use_container_width=True):
                            st.session_state.autenticado = True
                            st.session_state.login_fallido = False
                            st.session_state.mostrar_recuperacion = False
                            st.session_state.codigo_recuperacion = None
                            st.rerun()
    st.stop()


# ----------------- APP PRINCIPAL -----------------
activar_interactividad_avanzada()

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

# ----------------- SIDEBAR Y CIERRE DE SESIÓN CON RESPALDO (REQ 2) -----------------
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
stamp_archivo = ahora.strftime("%Y-%m-%d_%H-%M")

if "confirmar_cierre" not in st.session_state:
    st.session_state.confirmar_cierre = False


def finalizar_sesion():
    st.session_state.confirmar_cierre = False
    st.session_state.autenticado = False


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

    with st.expander("🔐 Mis Datos de Recuperación"):
        seg_actual = datos.get("seguridad", {})
        em_conf = st.text_input(
            "Gmail de recuperación:",
            value=seg_actual.get("email_recuperacion", ""),
            placeholder="ejemplo@gmail.com",
            key="side_email_rec"
        )
        tel_conf = st.text_input(
            "Celular de recuperación:",
            value=seg_actual.get("telefono_recuperacion", ""),
            placeholder="+54 9 381 ...",
            key="side_tel_rec"
        )
        if (
            em_conf != seg_actual.get("email_recuperacion", "")
            or tel_conf != seg_actual.get("telefono_recuperacion", "")
        ):
            datos["seguridad"]["email_recuperacion"] = em_conf.strip()
            datos["seguridad"]["telefono_recuperacion"] = tel_conf.strip()
            guardar_datos(datos)
            st.toast("✅ Datos de recuperación guardados automáticamente")

    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        # Guardado automático inmediato en la plataforma + registro en historial acumulado (Req 2)
        registrar_snapshot_cierre(datos, dolar_b, cotizaciones)
        st.session_state.confirmar_cierre = True
        st.rerun()

# Cuadro interactivo al apretar Cerrar Sesión (Req 2)
if st.session_state.confirmar_cierre:
    st.markdown("""
    <div style="background: linear-gradient(145deg, #EAF6EE 0%, #F3E8FF 100%);
                border: 2px solid #7E22CE; border-radius: 18px; padding: 20px; margin-bottom: 20px;
                box-shadow: 0 8px 24px rgba(126, 34, 206, 0.14);">
        <h3 style="color: #1B4332; margin-top: 0;">✅ ¡Tus cambios ya se guardaron automáticamente en la plataforma!</h3>
        <p style="font-size: 1.08rem; color: #374151; margin-bottom: 8px;">
            <b>¿Deseás descargar una planilla con tus cambios acumulados antes de salir?</b><br>
            Podés guardarla en tu celular o computadora en formato <b>Excel (.xlsx)</b>, <b>CSV (.csv)</b> o <b>PDF (.pdf)</b> para ir acumulando tus cierres.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_dl1, col_dl2, col_dl3, col_dl4, col_dl5 = st.columns([1.2, 1.2, 1.2, 1.3, 1.1])
    with col_dl1:
        st.download_button(
            label="📥 SÍ, bajar Excel (.xlsx)",
            data=generar_excel_bytes(datos, dolar_b, cotizaciones),
            file_name=f"Finanzas_Mama_{stamp_archivo}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            on_click=finalizar_sesion
        )
    with col_dl2:
        st.download_button(
            label="📥 SÍ, bajar CSV (.csv)",
            data=generar_csv_bytes(datos, dolar_b, cotizaciones),
            file_name=f"Finanzas_Mama_{stamp_archivo}.csv",
            mime="text/csv",
            use_container_width=True,
            on_click=finalizar_sesion
        )
    with col_dl3:
        st.download_button(
            label="📥 SÍ, bajar PDF (.pdf)",
            data=generar_pdf_bytes(datos, dolar_b, cotizaciones),
            file_name=f"Finanzas_Mama_{stamp_archivo}.pdf",
            mime="application/pdf",
            use_container_width=True,
            on_click=finalizar_sesion
        )
    with col_dl4:
        if st.button("🚪 NO descargar, solo Salir", use_container_width=True):
            finalizar_sesion()
            st.rerun()
    with col_dl5:
        if st.button("↩️ Seguir en la App", use_container_width=True):
            st.session_state.confirmar_cierre = False
            st.rerun()


# ----------------- CALLBACKS DE GUARDADO AUTOMÁTICO (REQ 3, 5, 6) -----------------
def sync_orden_costos_cb():
    raw = st.session_state.get("sync_orden_costos_input", "")
    if not raw:
        return
    try:
        nuevo_orden = json.loads(raw)
        actuales = datos["categorias_costos"]
        if isinstance(nuevo_orden, list) and len(nuevo_orden) == len(actuales) and set(nuevo_orden) == set(actuales):
            if nuevo_orden != actuales:
                datos["categorias_costos"] = nuevo_orden
                guardar_datos(datos)
    except Exception:
        pass


def sync_orden_ingresos_cb():
    raw = st.session_state.get("sync_orden_ingresos_input", "")
    if not raw:
        return
    try:
        nuevo_orden = json.loads(raw)
        actuales = datos["categorias_ingresos"]
        if isinstance(nuevo_orden, list) and len(nuevo_orden) == len(actuales) and set(nuevo_orden) == set(actuales):
            if nuevo_orden != actuales:
                datos["categorias_ingresos"] = nuevo_orden
                guardar_datos(datos)
    except Exception:
        pass


def crear_categoria_costo_auto():
    nom = st.session_state.get("input_nueva_cat_costo", "").strip()
    if nom and nom not in datos["categorias_costos"]:
        datos["categorias_costos"].append(nom)
        datos.setdefault("iconos_costos", {})[nom] = predecir_icono_categoria(nom, "costo")
        guardar_datos(datos)
        st.session_state["input_nueva_cat_costo"] = ""


def crear_categoria_ingreso_auto():
    nom = st.session_state.get("input_nueva_cat_ingreso", "").strip()
    if nom and nom not in datos["categorias_ingresos"]:
        datos["categorias_ingresos"].append(nom)
        datos.setdefault("iconos_ingresos", {})[nom] = predecir_icono_categoria(nom, "ingreso")
        guardar_datos(datos)
        st.session_state["input_nueva_cat_ingreso"] = ""


def auto_editar_cat_costo(cat_idx, nombre_viejo):
    nuevo_icono = st.session_state.get(f"edit_ico_c_{cat_idx}")
    nuevo_nombre = st.session_state.get(f"edit_nom_c_{cat_idx}", "").strip()
    modificado = False

    if nuevo_icono:
        datos.setdefault("iconos_costos", {})[nombre_viejo] = nuevo_icono
        modificado = True

    if nuevo_nombre and nuevo_nombre != nombre_viejo:
        if nuevo_nombre not in datos["categorias_costos"]:
            datos["categorias_costos"][cat_idx] = nuevo_nombre
            ico_actual = datos.get("iconos_costos", {}).pop(nombre_viejo, predecir_icono_categoria(nuevo_nombre, "costo"))
            datos["iconos_costos"][nuevo_nombre] = nuevo_icono or ico_actual
            for c in datos.get("costos", []):
                if c.get("grupo") == nombre_viejo:
                    c["grupo"] = nuevo_nombre
            modificado = True

    if modificado:
        guardar_datos(datos)


def auto_editar_cat_ingreso(cat_idx_i, nombre_viejo_i):
    nuevo_icono = st.session_state.get(f"edit_ico_i_{cat_idx_i}")
    nuevo_nombre = st.session_state.get(f"edit_nom_i_{cat_idx_i}", "").strip()
    modificado = False

    if nuevo_icono:
        datos.setdefault("iconos_ingresos", {})[nombre_viejo_i] = nuevo_icono
        modificado = True

    if nuevo_nombre and nuevo_nombre != nombre_viejo_i:
        if nuevo_nombre not in datos["categorias_ingresos"]:
            datos["categorias_ingresos"][cat_idx_i] = nuevo_nombre
            ico_actual = datos.get("iconos_ingresos", {}).pop(nombre_viejo_i, predecir_icono_categoria(nuevo_nombre, "ingreso"))
            datos["iconos_ingresos"][nuevo_nombre] = nuevo_icono or ico_actual
            for i in datos.get("ingresos", []):
                if i.get("grupo") == nombre_viejo_i:
                    i["grupo"] = nuevo_nombre
            modificado = True

    if modificado:
        guardar_datos(datos)


# Inputs puente invisibles para recibir el nuevo orden al arrastrar categorías
st.text_input(
    "sync_costos",
    key="sync_orden_costos_input",
    placeholder="SYNC_ORDEN_COSTOS",
    label_visibility="collapsed",
    on_change=sync_orden_costos_cb
)
st.text_input(
    "sync_ingresos",
    key="sync_orden_ingresos_input",
    placeholder="SYNC_ORDEN_INGRESOS",
    label_visibility="collapsed",
    on_change=sync_orden_ingresos_cb
)

# ----------------- PESTAÑAS -----------------
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

    # Tarjetas KPI
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3, gap="medium")
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

    # Calculadora de Terapias
    titulo_exp = "🧘‍♀️ **Calculadora de Terapias: Sesiones necesarias según tus números activos**"
    with st.expander(titulo_exp, expanded=True):
        col_c1, col_c2 = st.columns([1.1, 2.5], gap="medium")
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
                        📅 <b>{sesiones_sem:.1f} sesiones por semana</b>  |  🗓️ <b>{sesiones_anio:.0f} sesiones al año</b>
                    </span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # Columnas más anchas aprovechando todo el ancho disponible (Req 4)
    col_izq, col_der = st.columns(2, gap="medium")

    # ---------------- COSTOS ----------------
    with col_izq:
        st.markdown("<h3 style='color: #A04000; margin-bottom: 6px;'>📉 Mis Costos Mensuales</h3>", unsafe_allow_html=True)
        st.caption("💡 Podés arrastrar cualquier categoría hacia arriba o abajo para cambiar su orden.")

        with st.expander("➕ AGREGAR NUEVA CATEGORÍA DE COSTOS"):
            c_nc1, c_nc2 = st.columns([2.8, 1.2])
            with c_nc1:
                st.text_input(
                    "Nombre de la Categoría (ej. IMPUESTOS, AUTO, SALUD)",
                    placeholder="Escribí el nombre y apretá Enter (el ícono se asigna solo)...",
                    key="input_nueva_cat_costo",
                    on_change=crear_categoria_costo_auto
                )
            with c_nc2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("➕ Crear Categoría", key="btn_crear_cat_c", use_container_width=True):
                    crear_categoria_costo_auto()
                    st.rerun()

        costos_modificados = False
        for cat_idx, cat_nombre in enumerate(list(datos["categorias_costos"])):
            items_cat = [
                (idx, item) for idx, item in enumerate(datos["costos"])
                if item.get("grupo", "HOGAR Y OTROS") == cat_nombre
            ]
            sub_ars = sum(i["monto"] for _, i in items_cat if i.get("activo", True))
            sub_usd = sub_ars / dolar_b if dolar_b > 0 else 0
            icono_cat = datos.get("iconos_costos", {}).get(cat_nombre, predecir_icono_categoria(cat_nombre, "costo"))

            titulo_cat = f"⠿ {icono_cat} **{cat_nombre}** — Subtotal: **{sub_ars:,.0f} ARS** ({sub_usd:,.1f} USD)"
            with st.expander(titulo_cat, expanded=False):
                # Edición automática de nombre o ícono sin botón Guardar y sin flechas celestes (Req 3 y 5)
                editar_cat = st.checkbox(
                    "✏️ Editar nombre o ícono de la categoría",
                    key=f"chk_edit_c_{cat_idx}"
                )
                if editar_cat:
                    opciones_ico = list(dict.fromkeys([icono_cat] + ICONOS_DISPONIBLES))
                    ec1, ec2 = st.columns([1.0, 3.0])
                    with ec1:
                        st.selectbox(
                            "Ícono",
                            options=opciones_ico,
                            index=0,
                            key=f"edit_ico_c_{cat_idx}",
                            label_visibility="collapsed",
                            on_change=auto_editar_cat_costo,
                            args=(cat_idx, cat_nombre)
                        )
                    with ec2:
                        st.text_input(
                            "Nombre Categoría",
                            value=cat_nombre,
                            key=f"edit_nom_c_{cat_idx}",
                            label_visibility="collapsed",
                            on_change=auto_editar_cat_costo,
                            args=(cat_idx, cat_nombre)
                        )

                if items_cat:
                    # Proporción optimizada para que ACT. quede en un solo renglón (Req 3 y 4)
                    h1, h2, h3, h4 = st.columns([0.58, 2.35, 1.45, 0.55])
                    h1.markdown("<div class='col-header'>ACT.</div>", unsafe_allow_html=True)
                    h2.markdown("<div class='col-header'>SUBCATEGORÍA</div>", unsafe_allow_html=True)
                    h3.markdown("<div class='col-header'>MONTO (ARS)</div>", unsafe_allow_html=True)
                    h4.markdown("<div class='col-header'>BORRAR</div>", unsafe_allow_html=True)

                for idx, item in items_cat:
                    estado_check = item.get("activo", True)
                    c_box, c_nombre, c_monto, c_del = st.columns([0.58, 2.35, 1.45, 0.55])
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
                    sc1, sc2, sc3 = st.columns([2.2, 1.35, 1.05])
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

    # ---------------- INGRESOS ----------------
    with col_der:
        st.markdown("<h3 style='color: #117864; margin-bottom: 6px;'>📈 Mis Ingresos Mensuales</h3>", unsafe_allow_html=True)
        st.caption("💡 Podés arrastrar cualquier categoría hacia arriba o abajo para cambiar su orden.")

        with st.expander("➕ AGREGAR NUEVA CATEGORÍA DE INGRESOS"):
            c_ni1, c_ni2 = st.columns([2.8, 1.2])
            with c_ni1:
                st.text_input(
                    "Nombre de la Categoría (ej. Trabajo, Consultorio, Otros)",
                    placeholder="Escribí el nombre y apretá Enter (el ícono se asigna solo)...",
                    key="input_nueva_cat_ingreso",
                    on_change=crear_categoria_ingreso_auto
                )
            with c_ni2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("➕ Crear Categoría", key="btn_crear_cat_i", use_container_width=True):
                    crear_categoria_ingreso_auto()
                    st.rerun()

        ingresos_modificados = False
        for cat_idx_i, cat_nombre_i in enumerate(list(datos["categorias_ingresos"])):
            items_cat_i = [
                (idx, item) for idx, item in enumerate(datos["ingresos"])
                if item.get("grupo", "Otros ingresos") == cat_nombre_i
            ]
            sub_ars_i = sum(i["monto"] for _, i in items_cat_i if i.get("activo", True))
            sub_usd_i = sub_ars_i / dolar_b if dolar_b > 0 else 0
            icono_cat_i = datos.get("iconos_ingresos", {}).get(cat_nombre_i, predecir_icono_categoria(cat_nombre_i, "ingreso"))

            titulo_cat_i = f"⠿ {icono_cat_i} **{cat_nombre_i}** — Subtotal: **{sub_ars_i:,.0f} ARS** ({sub_usd_i:,.1f} USD)"
            with st.expander(titulo_cat_i, expanded=False):
                editar_cat_i = st.checkbox(
                    "✏️ Editar nombre o ícono de la categoría",
                    key=f"chk_edit_i_{cat_idx_i}"
                )
                if editar_cat_i:
                    opciones_ico_i = list(dict.fromkeys([icono_cat_i] + ICONOS_DISPONIBLES))
                    ei1, ei2 = st.columns([1.0, 3.0])
                    with ei1:
                        st.selectbox(
                            "Ícono",
                            options=opciones_ico_i,
                            index=0,
                            key=f"edit_ico_i_{cat_idx_i}",
                            label_visibility="collapsed",
                            on_change=auto_editar_cat_ingreso,
                            args=(cat_idx_i, cat_nombre_i)
                        )
                    with ei2:
                        st.text_input(
                            "Nombre Categoría",
                            value=cat_nombre_i,
                            key=f"edit_nom_i_{cat_idx_i}",
                            label_visibility="collapsed",
                            on_change=auto_editar_cat_ingreso,
                            args=(cat_idx_i, cat_nombre_i)
                        )

                if items_cat_i:
                    hi1, hi2, hi3, hi4 = st.columns([0.58, 2.35, 1.45, 0.55])
                    hi1.markdown("<div class='col-header'>ACT.</div>", unsafe_allow_html=True)
                    hi2.markdown("<div class='col-header'>SUBCATEGORÍA</div>", unsafe_allow_html=True)
                    hi3.markdown("<div class='col-header'>MONTO (ARS)</div>", unsafe_allow_html=True)
                    hi4.markdown("<div class='col-header'>BORRAR</div>", unsafe_allow_html=True)

                for idx, item in items_cat_i:
                    estado_check = item.get("activo", True)
                    c_box, c_nombre, c_monto, c_del = st.columns([0.58, 2.35, 1.45, 0.55])
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
                    si1, si2, si3 = st.columns([2.2, 1.35, 1.05])
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

    # Gráficos de Torta y Barras Horizontales Limpias (Req 7 y 8)
    st.markdown(
        "<h3 style='color: #5B4B8A;'>📊 Gráficos y Subtotales</h3>",
        unsafe_allow_html=True
    )
    modo_grafico = st.radio(
        "Ver gráficos según:",
        ["Por Categoría (Subtotales)", "Detallado por cada Subcategoría"],
        horizontal=True
    )

    col_chart_c, col_chart_i = st.columns(2, gap="medium")

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
                fig_c = crear_torta_2d(df_pie_c, "monto", col_label_c)
            else:
                df_pie_c = df_c_raw.sort_values(by="monto", ascending=False).copy()
                df_pie_c["etiqueta"] = df_pie_c["categoria"]
                col_label_c = "etiqueta"
                titulo_col_c = "Subcategoría"
                fig_c = crear_barras_horizontales(df_pie_c, "monto", col_label_c)

            df_pie_c["USD"] = df_pie_c["monto"] / dolar_b
            df_pie_c["Porcentaje"] = (df_pie_c["monto"] / total_costos) * 100

            st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar": False})

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
                fig_i = crear_torta_2d(df_pie_i, "monto", col_label_i)
            else:
                df_pie_i = df_i_raw.sort_values(by="monto", ascending=False).copy()
                df_pie_i["etiqueta"] = df_pie_i["concepto"]
                col_label_i = "etiqueta"
                titulo_col_i = "Subcategoría"
                fig_i = crear_barras_horizontales(df_pie_i, "monto", col_label_i)

            df_pie_i["USD"] = df_pie_i["monto"] / dolar_b
            df_pie_i["Porcentaje"] = (df_pie_i["monto"] / total_ingresos) * 100

            st.plotly_chart(fig_i, use_container_width=True, config={"displayModeBar": False})

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

    # Tarjeta de Patrimonio
    st.markdown(f"""
    <div class="metric-card metric-card-lila" style="text-align: center;">
        <div class="kpi-title" style="font-size: 1.25rem;">Patrimonio Total</div>
        <div class="kpi-value" style="font-size: 2.35rem;">{total_patrimonio_ars:,.0f} ARS</div>
        <div class="kpi-usd" style="font-size: 1.2rem;">{total_patrimonio_usd:,.2f} USD</div>
        <div class="kpi-sub">Calculado automáticamente con cotizaciones en vivo</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col_inv_izq, col_inv_der = st.columns([1.05, 1.85], gap="medium")

    # ---------------- AGREGAR ACTIVO ----------------
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

    # ---------------- MIS ACTIVOS ----------------
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
                    hc1, hc2, hc3, hc4, hc5 = st.columns([0.55, 1.45, 1.25, 1.35, 0.55])
                    hc1.markdown("<div class='col-header'>ACT.</div>", unsafe_allow_html=True)
                    hc2.markdown("<div class='col-header'>DETALLE</div>", unsafe_allow_html=True)
                    hc3.markdown("<div class='col-header'>CANTIDAD</div>", unsafe_allow_html=True)
                    hc4.markdown("<div class='col-header'>UBICACIÓN</div>", unsafe_allow_html=True)
                    hc5.markdown("<div class='col-header'>BORRAR</div>", unsafe_allow_html=True)

                    for idx, inv in items_cat_inv:
                        st_act = inv.get("activo_inv", True)
                        c_chk, c_nom, c_cant, c_plat, c_del = st.columns([0.55, 1.45, 1.25, 1.35, 0.55])

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
                            cant_str_actual = formatear_cant(inv.get("cantidad", 0)).replace(",", "")
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

    # Tabla discriminada con Cotizaciones en Vivo
    st.markdown(
        "<h3 style='color: #5B4B8A;'>📊 Distribución y Cotizaciones en Vivo</h3>",
        unsafe_allow_html=True
    )
    if not df_inv_activos.empty and total_patrimonio_ars > 0:
        col_g_inv1, col_g_inv2 = st.columns(2, gap="medium")

        with col_g_inv1:
            st.markdown(
                "<h4 style='color: #5B4B8A; text-align: center;'>Subtotales por Categoría de Activo</h4>",
                unsafe_allow_html=True
            )
            resumen_tipo = df_inv_activos.groupby("Tipo", as_index=False).agg({
                "Valor en ARS": "sum",
                "Valor en USD": "sum"
            }).sort_values(by="Valor en ARS", ascending=False)
            resumen_tipo["%"] = (resumen_tipo["Valor en ARS"] / total_patrimonio_ars) * 100

            fig_inv_tipo = crear_torta_2d(resumen_tipo, "Valor en ARS", "Tipo")
            st.plotly_chart(fig_inv_tipo, use_container_width=True, config={"displayModeBar": False})

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
            st.plotly_chart(fig_inv_det, use_container_width=True, config={"displayModeBar": False})

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
