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
import time
import hmac
import hashlib
import base64
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
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
    # 28 existentes conservados
    "🧾", "💡", "🚗", "👗", "🏠", "🛒", "🩺", "🏊‍♀️", "🧘‍♀️", "✈️",
    "📺", "🐾", "📚", "🎁", "💳", "💼", "💵", "👵", "📈", "📁",
    "🌿", "💎", "🛠️", "🧹", "🍽️", "📱", "⛽", "📌",
    # Nuevos íconos (vivienda, transporte, comida, servicios, salud, educación, ocio, inversiones, ahorros, sueldo, impuestos, deudas, regalos, mascotas)
    "🔨", "🧰", "🖌️", "🌱", "🐜", "🚚", "🔑", "🛋️", "🛏️", "🖼️",
    "🧺", "🚨", "🚿", "❄️", "🌡️", "☀️", "🍎", "🥩", "🥖", "☕",
    "🧴", "🫧", "👕", "🧻", "🧽", "🪥", "🧼", "🌸", "🚆", "🚕",
    "🏍️", "🛡️", "📋", "🔧", "🛞", "🅿️", "🏥", "🦷", "💊", "🧪",
    "🩻", "👓", "🦵", "🧠", "🥗", "🧥", "🕶️", "⌚", "🪡", "🎒",
    "💍", "💰", "🏦", "🪙", "📊", "🎓", "🎭", "🐶", "🐱"
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


# ----------------- INTERACTIVIDAD: ESTILOS DINÁMICOS, CONECTORES TORTA Y ANTI-POPUP -----------------
def activar_interactividad_avanzada(cats_costos=None, cats_ingresos=None, ubicaciones_guardadas=None, tooltip_cantidad=None):
    ubicaciones_json = json.dumps((ubicaciones_guardadas or [])[:8], ensure_ascii=False)
    tooltip_cant_json = json.dumps(tooltip_cantidad or "", ensure_ascii=False)
    js_code = r"""
    <script>
    (function() {
        const win = window.parent;
        const doc = win.document;
        const ubicacionesRecientes = __UBICACIONES_JSON__;
        const textoTooltipCantidad = __TOOLTIP_CANT_JSON__;

        // 1. Estilizar las solapas principales con 🍀 (1.3em, opacidad 1 activa / 0.5 inactiva) y eliminar la línea roja inferior
        function estilizarTrebolesSolapas() {
            const highlights = doc.querySelectorAll('[data-baseweb="tab-highlight"], [data-baseweb="tab-border"]');
            highlights.forEach(el => {
                el.style.setProperty('display', 'none', 'important');
                el.style.setProperty('height', '0px', 'important');
                el.style.setProperty('background', 'transparent', 'important');
                el.style.setProperty('background-color', 'transparent', 'important');
                el.style.setProperty('border', 'none', 'important');
            });

            const tabLists = doc.querySelectorAll('[data-baseweb="tab-list"]');
            tabLists.forEach(tl => {
                tl.style.setProperty('height', 'auto', 'important');
                tl.style.setProperty('min-height', '72px', 'important');
                tl.style.setProperty('overflow', 'visible', 'important');
                tl.style.setProperty('padding', '8px 4px', 'important');
                tl.style.setProperty('gap', '16px', 'important');
                tl.style.setProperty('align-items', 'center', 'important');
                tl.style.setProperty('border', 'none', 'important');
            });

            const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
            tabs.forEach(tab => {
                const isSelected = tab.getAttribute('aria-selected') === 'true';
                tab.style.setProperty('border-radius', '999px', 'important');
                tab.style.setProperty('min-height', '58px', 'important');
                tab.style.setProperty('height', 'auto', 'important');
                tab.style.setProperty('padding', '12px 32px', 'important');
                tab.style.setProperty('transition', 'all 0.25s ease-in-out', 'important');
                tab.style.setProperty('overflow', 'visible', 'important');

                if (isSelected) {
                    tab.style.setProperty('background', '#E6F7EF', 'important');
                    tab.style.setProperty('background-color', '#E6F7EF', 'important');
                    tab.style.setProperty('border', '2px solid #A8DFC4', 'important');
                    tab.style.setProperty('box-shadow', '0 4px 14px rgba(45, 106, 79, 0.14)', 'important');
                } else {
                    tab.style.setProperty('background', '#F9FAFB', 'important');
                    tab.style.setProperty('background-color', '#F9FAFB', 'important');
                    tab.style.setProperty('border', '1.5px solid #D8ECE3', 'important');
                    tab.style.setProperty('box-shadow', '0 2px 6px rgba(0, 0, 0, 0.04)', 'important');
                }

                const p = tab.querySelector('[data-testid="stMarkdownContainer"] p') || tab.querySelector('p');
                if (p) {
                    p.style.setProperty('font-size', '1.22rem', 'important');
                    p.style.setProperty('font-weight', '800', 'important');
                    p.style.setProperty('color', isSelected ? '#1B4332' : '#4B5563', 'important');
                    p.style.setProperty('margin', '0px', 'important');
                    p.style.setProperty('display', 'inline-flex', 'important');
                    p.style.setProperty('align-items', 'center', 'important');
                    p.style.setProperty('gap', '8px', 'important');

                    let spanClover = p.querySelector('.trebol-tab-icon');
                    if (!spanClover && (p.textContent || '').includes('🍀')) {
                        const textoLimpio = (p.textContent || '').replace('🍀', '').trim();
                        p.innerHTML = '<span class="trebol-tab-icon">🍀</span><span>' + textoLimpio + '</span>';
                        spanClover = p.querySelector('.trebol-tab-icon');
                    }
                    if (spanClover) {
                        spanClover.style.setProperty('font-size', '1.3em', 'important');
                        spanClover.style.setProperty('line-height', '1', 'important');
                        spanClover.style.setProperty('vertical-align', 'middle', 'important');
                        spanClover.style.setProperty('display', 'inline-block', 'important');
                        spanClover.style.setProperty('transition', 'opacity 0.25s ease', 'important');
                        spanClover.style.setProperty('opacity', isSelected ? '1' : '0.5', 'important');
                    }
                }
            });
        }

        // 2. Ocultar "Press Enter to apply" y blindar inputs contra el popup de contraseñas guardadas
        function limpiarInputsYPopups() {
            const instrucciones = doc.querySelectorAll('[data-testid="InputInstructions"]');
            instrucciones.forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
            });

            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            const inputs = doc.querySelectorAll('input');
            inputs.forEach((inp, idx) => {
                const enSidebar = sidebar && sidebar.contains(inp);
                if (inp.getAttribute('data-clean-autofill') !== 'true') {
                    inp.setAttribute('data-clean-autofill', 'true');
                    inp.setAttribute('autocomplete', enSidebar ? 'one-time-code' : 'off');
                    inp.setAttribute('autocorrect', 'off');
                    inp.setAttribute('autocapitalize', 'off');
                    inp.setAttribute('spellcheck', 'false');
                    inp.setAttribute('data-ddg-inputtype', 'unknown');
                    inp.setAttribute('data-1p-ignore', 'true');
                    inp.setAttribute('data-lpignore', 'true');
                    inp.setAttribute('data-bwignore', 'true');
                    inp.setAttribute('data-form-type', 'other');
                }

                if (enSidebar && inp.type !== 'checkbox') {
                    inp.setAttribute('autocomplete', 'one-time-code');
                    inp.setAttribute('name', 'jardin_cfg_field_' + idx);
                    const ariaLbl = (inp.getAttribute('aria-label') || '');
                    if (ariaLbl.includes('Clave App') || ariaLbl.includes('API Key')) {
                        inp.style.webkitTextSecurity = 'disc';
                    }
                    if (inp.getAttribute('data-readonly-shield') !== 'true') {
                        inp.setAttribute('data-readonly-shield', 'true');
                        if (doc.activeElement !== inp) {
                            inp.readOnly = true;
                        }
                        inp.addEventListener('pointerdown', function() {
                            inp.readOnly = false;
                        });
                        inp.addEventListener('focus', function() {
                            setTimeout(() => { inp.readOnly = false; }, 15);
                        });
                        inp.addEventListener('blur', function() {
                            inp.readOnly = true;
                        });
                    }
                }
            });

            const extNodes = doc.querySelectorAll('ddg-autofill, [data-ddg-autofill], .fx-relay-icon, firefox-private-relay-addon-data');
            extNodes.forEach(n => n.remove());
        }

        // 3. Resaltar "+ AGREGAR NUEVA CATEGORÍA" y compactar únicamente los botones ▲ y ▼ de categorías
        function estilizarSolapasYBotonesOrden() {
            const todosDetails = Array.from(doc.querySelectorAll('details'));
            todosDetails.forEach(det => {
                const sum = det.querySelector('summary');
                if (!sum) return;
                const txt = (sum.innerText || sum.textContent || '').toUpperCase();

                if (txt.includes('AGREGAR NUEVA CATEGORÍA DE COSTOS')) {
                    det.setAttribute('data-add-cat', 'costo');
                    det.style.setProperty('background-color', '#FFF2EE', 'important');
                    det.style.setProperty('border', '2px solid #E07A5F', 'important');
                    det.style.setProperty('border-radius', '16px', 'important');
                    det.style.setProperty('margin-bottom', '14px', 'important');
                    det.style.setProperty('box-shadow', '0 4px 12px rgba(224, 122, 95, 0.16)', 'important');
                    sum.style.setProperty('background-color', '#FADBD8', 'important');
                    sum.style.setProperty('color', '#922B21', 'important');
                    sum.style.setProperty('font-weight', '800', 'important');
                    sum.style.setProperty('border-radius', '14px', 'important');
                    sum.style.setProperty('padding', '12px 16px', 'important');
                    sum.querySelectorAll('p, span, svg').forEach(el => {
                        el.style.setProperty('color', '#922B21', 'important');
                        el.style.setProperty('fill', '#922B21', 'important');
                        el.style.setProperty('font-weight', '800', 'important');
                    });
                } else if (txt.includes('AGREGAR NUEVA CATEGORÍA DE INGRESOS')) {
                    det.setAttribute('data-add-cat', 'ingreso');
                    det.style.setProperty('background-color', '#ECFDF5', 'important');
                    det.style.setProperty('border', '2px solid #48C9B0', 'important');
                    det.style.setProperty('border-radius', '16px', 'important');
                    det.style.setProperty('margin-bottom', '14px', 'important');
                    det.style.setProperty('box-shadow', '0 4px 12px rgba(72, 201, 176, 0.16)', 'important');
                    sum.style.setProperty('background-color', '#D1F2EB', 'important');
                    sum.style.setProperty('color', '#0E6251', 'important');
                    sum.style.setProperty('font-weight', '800', 'important');
                    sum.style.setProperty('border-radius', '14px', 'important');
                    sum.style.setProperty('padding', '12px 16px', 'important');
                    sum.querySelectorAll('p, span, svg').forEach(el => {
                        el.style.setProperty('color', '#0E6251', 'important');
                        el.style.setProperty('fill', '#0E6251', 'important');
                        el.style.setProperty('font-weight', '800', 'important');
                    });
                }
            });

            // Ajustar únicamente los botones ▲ y ▼ y estilizar el botón de eliminar categoría vacía
            const botones = Array.from(doc.querySelectorAll('button'));
            botones.forEach(btn => {
                const t = (btn.innerText || btn.textContent || '').trim();
                if (t === '▲' || t === '▼') {
                    btn.classList.add('btn-flecha-cat');
                    btn.style.setProperty('height', '21px', 'important');
                    btn.style.setProperty('min-height', '21px', 'important');
                    btn.style.setProperty('max-height', '21px', 'important');
                    btn.style.setProperty('width', '28px', 'important');
                    btn.style.setProperty('min-width', '28px', 'important');
                    btn.style.setProperty('padding', '0px', 'important');
                    btn.style.setProperty('margin', '0px', 'important');
                    btn.style.setProperty('border-radius', '6px', 'important');
                    btn.style.setProperty('line-height', '1', 'important');
                    btn.querySelectorAll('p, span, div').forEach(ch => {
                        ch.style.setProperty('font-size', '0.68rem', 'important');
                        ch.style.setProperty('line-height', '1', 'important');
                        ch.style.setProperty('margin', '0px', 'important');
                        ch.style.setProperty('padding', '0px', 'important');
                    });
                    const col = btn.closest('[data-testid="stColumn"]');
                    if (col && !col.querySelector('[data-testid="stColumn"]')) {
                        const innerVb = col.querySelector('[data-testid="stVerticalBlock"]');
                        if (innerVb) {
                            innerVb.style.setProperty('gap', '2px', 'important');
                        }
                    }
                } else if (t === '+') {
                    btn.classList.add('btn-mas-trebol');
                    btn.setAttribute('title', 'Agregar categoría');
                    btn.style.setProperty('background', '#57CC99', 'important');
                    btn.style.setProperty('background-color', '#57CC99', 'important');
                    btn.style.setProperty('border', '1.5px solid #38A3A5', 'important');
                    btn.style.setProperty('color', '#FFFFFF', 'important');
                    btn.style.setProperty('width', '38px', 'important');
                    btn.style.setProperty('min-width', '38px', 'important');
                    btn.style.setProperty('max-width', '38px', 'important');
                    btn.style.setProperty('height', '38px', 'important');
                    btn.style.setProperty('min-height', '38px', 'important');
                    btn.style.setProperty('padding', '0px', 'important');
                    btn.style.setProperty('border-radius', '10px', 'important');
                    btn.style.setProperty('display', 'inline-flex', 'important');
                    btn.style.setProperty('align-items', 'center', 'important');
                    btn.style.setProperty('justify-content', 'center', 'important');
                    btn.querySelectorAll('p, span, div').forEach(ch => {
                        ch.style.setProperty('color', '#FFFFFF', 'important');
                        ch.style.setProperty('font-size', '1.35rem', 'important');
                        ch.style.setProperty('font-weight', '800', 'important');
                        ch.style.setProperty('line-height', '1', 'important');
                        ch.style.setProperty('margin', '0px', 'important');
                        ch.style.setProperty('padding', '0px', 'important');
                    });
                } else if (t === '🗑️' && (btn.getAttribute('title') === 'Eliminar categoría' || btn.closest('.contenedor-del-cat-vacia'))) {
                    btn.classList.add('btn-eliminar-cat-vacia');
                    btn.setAttribute('title', 'Eliminar categoría');
                    btn.style.setProperty('display', 'inline-flex', 'important');
                    btn.style.setProperty('align-items', 'center', 'important');
                    btn.style.setProperty('justify-content', 'center', 'important');
                    btn.style.setProperty('width', '46px', 'important');
                    btn.style.setProperty('min-width', '46px', 'important');
                    btn.style.setProperty('max-width', '46px', 'important');
                    btn.style.setProperty('height', '44px', 'important');
                    btn.style.setProperty('min-height', '44px', 'important');
                    btn.style.setProperty('padding', '0px', 'important');
                    btn.style.setProperty('border-radius', '10px', 'important');
                    btn.style.setProperty('background-color', '#FFF5F5', 'important');
                    btn.style.setProperty('border', '1.5px solid #F5B7B1', 'important');
                    btn.querySelectorAll('p, span, div').forEach(ch => {
                        ch.style.setProperty('font-size', '1.5rem', 'important');
                        ch.style.setProperty('line-height', '1', 'important');
                        ch.style.setProperty('margin', '0px', 'important');
                        ch.style.setProperty('padding', '0px', 'important');
                    });
                }
            });
        }

        // 4. Asegurar líneas conectoras en todas las etiquetas externas del gráfico de torta
        function asegurarLineasConectorasTortas() {
            const pieLayers = doc.querySelectorAll('g.pielayer');
            pieLayers.forEach(layer => {
                const traces = layer.querySelectorAll('g.trace');
                traces.forEach(trace => {
                    const slices = Array.from(trace.querySelectorAll('g.slice'));
                    if (slices.length === 0) return;

                    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                    slices.forEach(sl => {
                        const surf = sl.querySelector('path.surface');
                        if (!surf || !surf.getBBox) return;
                        try {
                            const b = surf.getBBox();
                            if (b.width > 0 && b.height > 0) {
                                minX = Math.min(minX, b.x);
                                minY = Math.min(minY, b.y);
                                maxX = Math.max(maxX, b.x + b.width);
                                maxY = Math.max(maxY, b.y + b.height);
                            }
                        } catch (e) {}
                    });

                    if (!isFinite(minX) || !isFinite(maxX)) return;
                    const cx = (minX + maxX) / 2;
                    const cy = (minY + maxY) / 2;
                    const R = Math.max(maxX - minX, maxY - minY) / 2;
                    if (R <= 10) return;

                    slices.forEach(sl => {
                        const existingLine = sl.querySelector('path.textline:not(.jardin-leader-line)');
                        if (existingLine && (existingLine.getAttribute('d') || '').trim().length > 0) {
                            existingLine.style.stroke = '#1F2937';
                            existingLine.style.strokeWidth = '1.5px';
                            const oldCustom = sl.querySelector('path.jardin-leader-line');
                            if (oldCustom) oldCustom.remove();
                            return;
                        }

                        const stext = sl.querySelector('g.slicetext');
                        if (!stext || !stext.getBBox) return;
                        try {
                            const tb = stext.getBBox();
                            if (tb.width === 0 && tb.height === 0) return;
                            const tx = tb.x + tb.width / 2;
                            const ty = tb.y + tb.height / 2;
                            const dist = Math.hypot(tx - cx, ty - cy);

                            if (dist > R * 0.96) {
                                const angle = Math.atan2(ty - cy, tx - cx);
                                const sx = cx + (R - 2) * Math.cos(angle);
                                const sy = cy + (R - 2) * Math.sin(angle);
                                const ex = cx + (R + 10) * Math.cos(angle);
                                const ey = cy + (R + 10) * Math.sin(angle);
                                const dirX = tx >= cx ? 1 : -1;
                                const endX = ex + dirX * 6;
                                const endY = ey;

                                let customLine = sl.querySelector('path.jardin-leader-line');
                                if (!customLine) {
                                    customLine = doc.createElementNS('http://www.w3.org/2000/svg', 'path');
                                    customLine.setAttribute('class', 'textline jardin-leader-line');
                                    customLine.style.fill = 'none';
                                    customLine.style.stroke = '#1F2937';
                                    customLine.style.strokeWidth = '1.5px';
                                    customLine.style.strokeOpacity = '1';
                                    sl.insertBefore(customLine, stext);
                                }
                                customLine.setAttribute(
                                    'd',
                                    'M' + sx.toFixed(1) + ',' + sy.toFixed(1) +
                                    'L' + ex.toFixed(1) + ',' + ey.toFixed(1) +
                                    'L' + endX.toFixed(1) + ',' + endY.toFixed(1)
                                );
                            } else {
                                const oldLine = sl.querySelector('path.jardin-leader-line');
                                if (oldLine) oldLine.remove();
                            }
                        } catch (e) {}
                    });
                });
            });
        }

        // 5. Dropdown sugerido de las últimas 8 ubicaciones en "2. Ubicación, ¿dónde está?" permitiendo escritura libre
        function configurarDropdownUbicacion() {
            const inp = doc.querySelector('input[aria-label="2. Ubicación, ¿dónde está?"]');
            let menu = doc.getElementById('jardin-ubicacion-dropdown');

            if (!inp || inp.offsetParent === null) {
                if (menu) menu.style.display = 'none';
                return;
            }

            const wrapper = inp.parentElement;
            if (wrapper && !wrapper.querySelector('.jardin-ubic-chevron')) {
                wrapper.style.position = 'relative';
                const chev = doc.createElement('span');
                chev.className = 'jardin-ubic-chevron';
                chev.textContent = '▾';
                chev.style.cssText = 'position:absolute;right:12px;top:50%;transform:translateY(-50%);color:#4B5563;font-size:0.95rem;cursor:pointer;user-select:none;z-index:5;pointer-events:auto;';
                chev.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    inp.focus();
                    mostrarMenuUbicacion(inp, '');
                });
                wrapper.appendChild(chev);
                inp.style.paddingRight = '30px';
            }

            if (!menu) {
                menu = doc.createElement('div');
                menu.id = 'jardin-ubicacion-dropdown';
                menu.style.cssText = 'position:fixed;display:none;background:#FFFFFF;border:1.5px solid #C4B5FD;border-radius:12px;box-shadow:0 8px 22px rgba(91,75,138,0.16);z-index:999999;max-height:260px;overflow-y:auto;padding:4px 0;font-family:sans-serif;';
                doc.body.appendChild(menu);
            }

            function seleccionarUbicacion(valor) {
                const setter = Object.getOwnPropertyDescriptor(win.HTMLInputElement.prototype, 'value').set;
                setter.call(inp, valor);
                inp.dispatchEvent(new Event('input', { bubbles: true }));
                inp.dispatchEvent(new Event('change', { bubbles: true }));
                inp.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
                menu.style.display = 'none';
                setTimeout(() => { try { inp.blur(); } catch (e) {} }, 30);
            }

            function mostrarMenuUbicacion(targetInp, filtroTexto) {
                if (!ubicacionesRecientes || ubicacionesRecientes.length === 0) {
                    menu.style.display = 'none';
                    return;
                }
                const f = (filtroTexto || '').trim().toLowerCase();
                const coincideExacto = ubicacionesRecientes.some(u => u.toLowerCase() === f);
                const filtradas = (!f || coincideExacto)
                    ? ubicacionesRecientes
                    : ubicacionesRecientes.filter(u => u.toLowerCase().includes(f));

                if (filtradas.length === 0) {
                    menu.style.display = 'none';
                    return;
                }

                menu.innerHTML = '';
                const header = doc.createElement('div');
                header.textContent = 'Últimas ubicaciones guardadas';
                header.style.cssText = 'padding:5px 12px;font-size:0.74rem;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:0.4px;border-bottom:1px solid #F3F4F6;';
                menu.appendChild(header);

                filtradas.forEach(ubic => {
                    const item = doc.createElement('div');
                    item.textContent = ubic;
                    item.style.cssText = 'padding:8px 14px;font-size:0.95rem;color:#1F2937;cursor:pointer;transition:background 0.15s ease;font-weight:500;';
                    item.addEventListener('mouseenter', () => {
                        item.style.background = '#F3E8FF';
                        item.style.color = '#4A235A';
                    });
                    item.addEventListener('mouseleave', () => {
                        item.style.background = '#FFFFFF';
                        item.style.color = '#1F2937';
                    });
                    item.addEventListener('mousedown', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        seleccionarUbicacion(ubic);
                    });
                    menu.appendChild(item);
                });

                const rect = targetInp.getBoundingClientRect();
                menu.style.left = rect.left + 'px';
                menu.style.top = (rect.bottom + 4) + 'px';
                menu.style.width = rect.width + 'px';
                menu.style.display = 'block';
            }

            if (inp.getAttribute('data-ubic-bound') !== 'true') {
                inp.setAttribute('data-ubic-bound', 'true');
                inp.addEventListener('focus', function() {
                    mostrarMenuUbicacion(inp, inp.value);
                });
                inp.addEventListener('click', function() {
                    mostrarMenuUbicacion(inp, inp.value);
                });
                inp.addEventListener('input', function() {
                    mostrarMenuUbicacion(inp, inp.value);
                });
                inp.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape' || e.key === 'Enter' || e.key === 'Tab') {
                        menu.style.display = 'none';
                    }
                });
                inp.addEventListener('blur', function() {
                    setTimeout(() => {
                        if (menu) menu.style.display = 'none';
                    }, 160);
                });
            }
        }

        // 6. Tooltip único negro en "3. Cantidad que tenés" (sin tooltip blanco duplicado) y botón Actualizar verde claro
        function configurarTooltipCantidadYBotones() {
            const oldMenu = doc.getElementById('jardin-ubicacion-dropdown');
            if (oldMenu) oldMenu.remove();

            const inpCant = doc.querySelector('input[aria-label="3. Cantidad que tenés"]');
            if (inpCant) {
                inpCant.removeAttribute('title');
                const stInputBox = inpCant.closest('[data-testid="stTextInput"]') || inpCant.parentElement;
                if (stInputBox && textoTooltipCantidad) {
                    stInputBox.classList.add('jardin-cant-tooltip-wrap');
                    stInputBox.setAttribute('data-tooltip', textoTooltipCantidad);
                    stInputBox.querySelectorAll('[title]').forEach(el => el.removeAttribute('title'));
                    const helpTarget = stInputBox.querySelector('[data-testid="stTooltipHoverTarget"]');
                    if (helpTarget) {
                        helpTarget.style.pointerEvents = 'none';
                    }
                }
            }

            // Estilizar el botón "Actualizar" del sidebar con fondo verde claro
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.querySelectorAll('button').forEach(btn => {
                    const txt = (btn.innerText || btn.textContent || '').trim();
                    if (txt.includes('Actualizar')) {
                        btn.style.setProperty('background', '#D8F3DC', 'important');
                        btn.style.setProperty('background-color', '#D8F3DC', 'important');
                        btn.style.setProperty('border', '1.5px solid #74C69D', 'important');
                        btn.style.setProperty('color', '#1B4332', 'important');
                        btn.style.setProperty('font-weight', '700', 'important');
                        btn.style.setProperty('border-radius', '12px', 'important');
                        btn.querySelectorAll('p, span, div').forEach(ch => {
                            ch.style.setProperty('color', '#1B4332', 'important');
                            ch.style.setProperty('font-weight', '700', 'important');
                        });
                    }
                });
            }
        }

        function actualizarInterfaz() {
            estilizarTrebolesSolapas();
            limpiarInputsYPopups();
            estilizarSolapasYBotonesOrden();
            asegurarLineasConectorasTortas();
            configurarTooltipCantidadYBotones();
        }

        if (win.__jardinCleanupListeners) {
            try { win.__jardinCleanupListeners(); } catch (e) {}
        }

        const abortCtrl = new AbortController();
        const sig = abortCtrl.signal;

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
        }, { capture: true, signal: sig });

        doc.addEventListener('click', function() {
            setTimeout(estilizarTrebolesSolapas, 30);
        }, { capture: true, signal: sig });

        let timerObs = null;
        const obs = new MutationObserver(() => {
            clearTimeout(timerObs);
            timerObs = setTimeout(actualizarInterfaz, 90);
        });
        obs.observe(doc.body, { childList: true, subtree: true });

        win.__jardinCleanupListeners = function() {
            abortCtrl.abort();
            obs.disconnect();
        };

        actualizarInterfaz();
        setTimeout(actualizarInterfaz, 150);
        setTimeout(actualizarInterfaz, 450);
    })();
    </script>
    """
    js_final = js_code.replace("__UBICACIONES_JSON__", ubicaciones_json).replace("__TOOLTIP_CANT_JSON__", tooltip_cant_json)
    components.html(js_final, height=0, width=0)




# ----------------- PANEL DINÁMICO 3D DE SALUD FINANCIERA -----------------
def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(round(rgb[0])))),
        max(0, min(255, int(round(rgb[1])))),
        max(0, min(255, int(round(rgb[2]))))
    )


def _lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, float(t)))
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex((r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t))


def _multi_color(stops, score):
    """Interpola continuamente entre una lista de tuplas (pos, '#RRGGBB')."""
    s = max(0.0, min(1.0, float(score)))
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if p0 <= s <= p1:
            local_t = (s - p0) / (p1 - p0) if p1 > p0 else 0.0
            return _lerp_color(c0, c1, local_t)
    return stops[-1][1]


def _construir_svg_canguro(score):
    """Genera el SVG 3D del canguro: esqueleto con moscas en score=0, cansado/triste en medio, feliz/alimentado en alto."""
    if score <= 0.02:
        # Score 0: Tirado muerto en el suelo, únicamente huesos visibles (sin pelaje) y moscas zumbando alrededor
        return (
            '<svg class="jardin-char-svg" viewBox="0 0 170 150" style="overflow: visible;" xmlns="http://www.w3.org/2000/svg">'
            '<defs>'
            '<linearGradient id="bone3DK" x1="0%" y1="0%" x2="0%" y2="100%">'
            '<stop offset="0%" stop-color="#FEFCE8"/>'
            '<stop offset="55%" stop-color="#E7E5E4"/>'
            '<stop offset="100%" stop-color="#A8A29E"/>'
            '</linearGradient>'
            '<filter id="boneShadowK" x="-20%" y="-20%" width="140%" height="140%">'
            '<feDropShadow dx="0" dy="3" stdDeviation="2.5" flood-color="#000000" flood-opacity="0.38"/>'
            '</filter>'
            '</defs>'
            # Sombra en la arena debajo del esqueleto
            '<ellipse cx="86" cy="134" rx="68" ry="9" fill="#000000" opacity="0.28"/>'
            '<g filter="url(#boneShadowK)">'
            # Cola ósea segmentada (vértebras caudales sobre el suelo)
            '<path d="M 10 130 Q 28 134 48 126" stroke="url(#bone3DK)" stroke-width="5.5" stroke-dasharray="6 3" stroke-linecap="round" fill="none"/>'
            # Pelvis 3D
            '<ellipse cx="52" cy="122" rx="11" ry="8" fill="url(#bone3DK)" transform="rotate(-15 52 122)"/>'
            '<circle cx="52" cy="122" r="3.5" fill="#57534E"/>'
            # Fémur, tibia y pie largo óseo de canguro tirado en la arena
            '<line x1="50" y1="124" x2="30" y2="136" stroke="url(#bone3DK)" stroke-width="5.5" stroke-linecap="round"/>'
            '<circle cx="30" cy="136" r="3.8" fill="url(#bone3DK)"/>'
            '<line x1="30" y1="136" x2="56" y2="140" stroke="url(#bone3DK)" stroke-width="4.5" stroke-linecap="round"/>'
            '<line x1="56" y1="140" x2="78" y2="139" stroke="url(#bone3DK)" stroke-width="3.8" stroke-linecap="round"/>'
            # Columna vertebral arqueada en el suelo
            '<path d="M 58 120 Q 84 110 112 122" stroke="url(#bone3DK)" stroke-width="6" stroke-dasharray="7 3" stroke-linecap="round" fill="none"/>'
            # Costillas 3D (arcos óseos sin piel ni pelaje)
            '<path d="M 68 117 Q 70 94 80 102" stroke="url(#bone3DK)" stroke-width="4" stroke-linecap="round" fill="none"/>'
            '<path d="M 77 115 Q 80 90 90 100" stroke="url(#bone3DK)" stroke-width="4" stroke-linecap="round" fill="none"/>'
            '<path d="M 86 115 Q 90 92 99 101" stroke="url(#bone3DK)" stroke-width="4" stroke-linecap="round" fill="none"/>'
            '<path d="M 95 117 Q 98 96 106 104" stroke="url(#bone3DK)" stroke-width="3.8" stroke-linecap="round" fill="none"/>'
            '<path d="M 103 119 Q 106 102 112 108" stroke="url(#bone3DK)" stroke-width="3.4" stroke-linecap="round" fill="none"/>'
            # Huesos del brazo delantero caído en la arena
            '<line x1="106" y1="121" x2="96" y2="136" stroke="url(#bone3DK)" stroke-width="4.2" stroke-linecap="round"/>'
            '<line x1="96" y1="136" x2="112" y2="139" stroke="url(#bone3DK)" stroke-width="3.5" stroke-linecap="round"/>'
            # Cráneo de canguro en 3D recostado sobre la arena (sin orejas ni pelaje)
            '<g transform="translate(116, 114) rotate(18)">'
            '<ellipse cx="10" cy="4" rx="14" ry="10" fill="url(#bone3DK)"/>'
            '<path d="M 18 -2 L 38 3 Q 40 7 35 9 L 16 9 Z" fill="url(#bone3DK)"/>'
            '<path d="M 14 9 L 33 12 L 31 15 L 12 13 Z" fill="#D6D3D1"/>'
            # Cuenca ocular vacía y fosa nasal del cráneo
            '<ellipse cx="14" cy="2" rx="4.5" ry="3.8" fill="#1C1917"/>'
            '<polygon points="33,4 37,5 34,7" fill="#1C1917"/>'
            # Dientes visibles en la mandíbula
            '<line x1="20" y1="9" x2="32" y2="10" stroke="#78716C" stroke-width="1.4" stroke-dasharray="2 2"/>'
            '</g>'
            '</g>'
            # Moscas animadas zumbando alrededor del esqueleto del canguro
            '<g class="jardin-fly-1" transform="translate(78, 78)">'
            '<ellipse cx="-2.5" cy="-2.5" rx="3.2" ry="1.8" fill="#E0F2FE" opacity="0.85" transform="rotate(-25)"/>'
            '<ellipse cx="2.5" cy="-2.5" rx="3.2" ry="1.8" fill="#E0F2FE" opacity="0.85" transform="rotate(25)"/>'
            '<ellipse cx="0" cy="0" rx="3.2" ry="2.2" fill="#111827"/>'
            '</g>'
            '<g class="jardin-fly-2" transform="translate(122, 86)">'
            '<ellipse cx="-2.2" cy="-2.2" rx="2.8" ry="1.6" fill="#E0F2FE" opacity="0.85" transform="rotate(-25)"/>'
            '<ellipse cx="2.2" cy="-2.2" rx="2.8" ry="1.6" fill="#E0F2FE" opacity="0.85" transform="rotate(25)"/>'
            '<ellipse cx="0" cy="0" rx="2.8" ry="1.9" fill="#111827"/>'
            '</g>'
            '<g class="jardin-fly-3" transform="translate(46, 92)">'
            '<ellipse cx="-2.2" cy="-2.2" rx="2.8" ry="1.6" fill="#E0F2FE" opacity="0.85" transform="rotate(-25)"/>'
            '<ellipse cx="2.2" cy="-2.2" rx="2.8" ry="1.6" fill="#E0F2FE" opacity="0.85" transform="rotate(25)"/>'
            '<ellipse cx="0" cy="0" rx="2.8" ry="1.9" fill="#111827"/>'
            '</g>'
            '</svg>'
        )

    # Score > 0.02: Canguro vivo (alto = feliz y bien alimentado; medio/bajo = delgado, cansado y triste)
    fat_scale_x = 0.74 + 0.32 * score
    posture_drop = (1.0 - score) * 12.0
    ear_droop = (1.0 - score) * 26.0
    ribs_opacity = max(0.0, min(0.75, (0.35 - score) / 0.35)) if score < 0.35 else 0.0
    euca_leaf_op = max(0.0, min(1.0, (score - 0.15) / 0.5))
    leaf_col = _multi_color([(0.0, "#A16207"), (0.5, "#EAB308"), (1.0, "#22C55E")], score)

    if score >= 0.65:
        anim_cls = "jardin-kanga-happy"
        mouth_d = "M 82 65 Q 90 73 97 64"
        eyes_svg = (
            '<circle cx="85" cy="50" r="4" fill="#1F2937"/>'
            '<circle cx="86.4" cy="48.6" r="1.4" fill="#FFFFFF"/>'
            '<circle cx="99" cy="50" r="3.6" fill="#1F2937"/>'
            '<circle cx="100.2" cy="48.6" r="1.2" fill="#FFFFFF"/>'
            '<ellipse cx="78" cy="57" rx="4.5" ry="2.5" fill="#F472B6" opacity="0.5"/>'
        )
    else:
        anim_cls = "jardin-animal-tired"
        mouth_d = "M 82 70 Q 90 63 97 70"
        eyes_svg = (
            '<circle cx="85" cy="52" r="3.6" fill="#1F2937"/>'
            '<path d="M 79 47 L 90 50" stroke="#451A03" stroke-width="2.1" stroke-linecap="round"/>'
            '<circle cx="99" cy="52" r="3.4" fill="#1F2937"/>'
            '<path d="M 94 50 L 104 47" stroke="#451A03" stroke-width="2.1" stroke-linecap="round"/>'
            '<path d="M 75 58 Q 73 65 75 68 Q 77 65 75 58 Z" fill="#38BDF8" opacity="0.85"/>'
        )

    return (
        '<svg class="jardin-char-svg" viewBox="0 0 160 220" style="overflow: visible;" xmlns="http://www.w3.org/2000/svg">'
        '<defs>'
        '<radialGradient id="kangaFur3D" cx="35%" cy="30%" r="70%">'
        '<stop offset="0%" stop-color="#F59E0B"/>'
        '<stop offset="55%" stop-color="#D97706"/>'
        '<stop offset="100%" stop-color="#92400E"/>'
        '</radialGradient>'
        '<linearGradient id="kangaBelly3D" x1="0%" y1="0%" x2="0%" y2="100%">'
        '<stop offset="0%" stop-color="#FEF3C7"/>'
        '<stop offset="100%" stop-color="#FDE68A"/>'
        '</linearGradient>'
        '<filter id="kangaShadow3D" x="-20%" y="-20%" width="140%" height="140%">'
        '<feDropShadow dx="0" dy="4" stdDeviation="3" flood-color="#000000" flood-opacity="0.25"/>'
        '</filter>'
        '</defs>'
        '<ellipse cx="82" cy="204" rx="42" ry="9" fill="#000000" opacity="0.22"/>'
        f'<g class="{anim_cls}" transform="translate(0, {posture_drop:.1f})" filter="url(#kangaShadow3D)">'
        '<path d="M 48 152 Q 12 160 10 134 Q 8 120 20 122 Q 30 126 54 138 Z" fill="url(#kangaFur3D)"/>'
        '<ellipse cx="62" cy="164" rx="18" ry="26" fill="url(#kangaFur3D)"/>'
        '<path d="M 48 188 L 96 188 Q 104 188 102 195 L 44 195 Q 38 191 48 188 Z" fill="url(#kangaFur3D)"/>'
        f'<g transform="translate(78, 120) scale({fat_scale_x:.2f}, 1)">'
        '<ellipse cx="0" cy="0" rx="31" ry="46" fill="url(#kangaFur3D)"/>'
        '<ellipse cx="5" cy="4" rx="20" ry="35" fill="url(#kangaBelly3D)"/>'
        '</g>'
        f'<g opacity="{ribs_opacity:.2f}" stroke="#FEF3C7" stroke-width="2.2" stroke-linecap="round" fill="none">'
        '<path d="M 66 102 Q 80 98 91 104"/>'
        '<path d="M 65 113 Q 80 109 92 115"/>'
        '<path d="M 66 124 Q 80 120 91 126"/>'
        '</g>'
        '<path d="M 70 82 L 79 42 L 98 46 L 92 86 Z" fill="url(#kangaFur3D)"/>'
        f'<ellipse cx="75" cy="28" rx="6.5" ry="20" fill="url(#kangaFur3D)" transform="rotate({-16 - ear_droop:.1f} 75 42)"/>'
        f'<ellipse cx="75" cy="28" rx="3.5" ry="13" fill="#FDE68A" transform="rotate({-16 - ear_droop:.1f} 75 42)"/>'
        f'<ellipse cx="95" cy="28" rx="6.5" ry="20" fill="url(#kangaFur3D)" transform="rotate({14 + ear_droop:.1f} 95 42)"/>'
        f'<ellipse cx="95" cy="28" rx="3.5" ry="13" fill="#FDE68A" transform="rotate({14 + ear_droop:.1f} 95 42)"/>'
        '<ellipse cx="88" cy="56" rx="20" ry="17" fill="url(#kangaFur3D)"/>'
        '<ellipse cx="100" cy="60" rx="11" ry="9" fill="url(#kangaBelly3D)"/>'
        '<circle cx="108" cy="57" r="4" fill="#1F2937"/>'
        + eyes_svg +
        f'<path d="{mouth_d}" stroke="#451A03" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
        '<path d="M 84 94 Q 108 102 114 114" stroke="#D97706" stroke-width="7.5" stroke-linecap="round" fill="none"/>'
        f'<g opacity="{euca_leaf_op:.2f}" transform="translate(114, 112)">'
        '<path d="M 0 0 Q 14 -12 22 -20" stroke="#15803D" stroke-width="2.2" fill="none"/>'
        f'<ellipse cx="12" cy="-12" rx="7" ry="4" fill="{leaf_col}" transform="rotate(-30 12 -12)"/>'
        f'<ellipse cx="20" cy="-18" rx="7" ry="4" fill="{leaf_col}" transform="rotate(20 20 -18)"/>'
        '</g>'
        '</g>'
        '</svg>'
    )


def _construir_svg_koala(score):
    """Genera el SVG 3D del koala: esqueleto con moscas en score=0, cansado/triste en medio, feliz/alimentado en alto."""
    if score <= 0.02:
        # Score 0: Tirado muerto en el suelo, únicamente huesos visibles (sin pelaje) y moscas zumbando alrededor
        return (
            '<svg class="jardin-char-svg" viewBox="0 0 170 150" style="overflow: visible;" xmlns="http://www.w3.org/2000/svg">'
            '<defs>'
            '<linearGradient id="bone3DKo" x1="0%" y1="0%" x2="0%" y2="100%">'
            '<stop offset="0%" stop-color="#FEFCE8"/>'
            '<stop offset="55%" stop-color="#E7E5E4"/>'
            '<stop offset="100%" stop-color="#A8A29E"/>'
            '</linearGradient>'
            '<filter id="boneShadowKo" x="-20%" y="-20%" width="140%" height="140%">'
            '<feDropShadow dx="0" dy="3" stdDeviation="2.5" flood-color="#000000" flood-opacity="0.38"/>'
            '</filter>'
            '</defs>'
            '<ellipse cx="86" cy="134" rx="62" ry="9" fill="#000000" opacity="0.28"/>'
            '<g filter="url(#boneShadowKo)">'
            # Pelvis y huesos de las patas traseras en el suelo
            '<ellipse cx="122" cy="123" rx="10" ry="7.5" fill="url(#bone3DKo)" transform="rotate(12 122 123)"/>'
            '<circle cx="122" cy="123" r="3" fill="#57534E"/>'
            '<line x1="124" y1="125" x2="142" y2="137" stroke="url(#bone3DKo)" stroke-width="5" stroke-linecap="round"/>'
            '<line x1="142" y1="137" x2="126" y2="140" stroke="url(#bone3DKo)" stroke-width="4" stroke-linecap="round"/>'
            # Columna vertebral de koala en el suelo
            '<path d="M 62 122 Q 92 112 118 122" stroke="url(#bone3DKo)" stroke-width="6" stroke-dasharray="6 3" stroke-linecap="round" fill="none"/>'
            # Costillas 3D (arcos óseos expuestos sin pelaje)
            '<path d="M 70 119 Q 72 95 80 103" stroke="url(#bone3DKo)" stroke-width="4" stroke-linecap="round" fill="none"/>'
            '<path d="M 79 117 Q 81 92 89 101" stroke="url(#bone3DKo)" stroke-width="4" stroke-linecap="round" fill="none"/>'
            '<path d="M 88 116 Q 90 93 98 102" stroke="url(#bone3DKo)" stroke-width="4" stroke-linecap="round" fill="none"/>'
            '<path d="M 97 117 Q 99 95 106 104" stroke="url(#bone3DKo)" stroke-width="3.8" stroke-linecap="round" fill="none"/>'
            '<path d="M 106 119 Q 108 99 114 107" stroke="url(#bone3DKo)" stroke-width="3.5" stroke-linecap="round" fill="none"/>'
            # Huesos del brazo delantero caído en la arena
            '<line x1="70" y1="122" x2="80" y2="137" stroke="url(#bone3DKo)" stroke-width="4.5" stroke-linecap="round"/>'
            '<line x1="80" y1="137" x2="64" y2="139" stroke="url(#bone3DKo)" stroke-width="3.8" stroke-linecap="round"/>'
            # Cráneo redondeado de koala en 3D recostado sobre la arena (sin pelaje)
            '<g transform="translate(44, 114) rotate(-16)">'
            '<ellipse cx="10" cy="4" rx="16" ry="13" fill="url(#bone3DKo)"/>'
            '<ellipse cx="2" cy="12" rx="11" ry="6" fill="#D6D3D1"/>'
            # Cuencas oculares vacías y cavidad nasal característica del cráneo de koala
            '<circle cx="5" cy="2" r="4.5" fill="#1C1917"/>'
            '<circle cx="16" cy="2" r="4.2" fill="#1C1917"/>'
            '<polygon points="9,6 6,12 13,12" fill="#1C1917"/>'
            '<line x1="3" y1="14" x2="14" y2="14" stroke="#78716C" stroke-width="1.5" stroke-dasharray="2 2"/>'
            '</g>'
            '</g>'
            # Moscas animadas zumbando alrededor del esqueleto del koala
            '<g class="jardin-fly-2" transform="translate(52, 82)">'
            '<ellipse cx="-2.5" cy="-2.5" rx="3.2" ry="1.8" fill="#E0F2FE" opacity="0.85" transform="rotate(-25)"/>'
            '<ellipse cx="2.5" cy="-2.5" rx="3.2" ry="1.8" fill="#E0F2FE" opacity="0.85" transform="rotate(25)"/>'
            '<ellipse cx="0" cy="0" rx="3.2" ry="2.2" fill="#111827"/>'
            '</g>'
            '<g class="jardin-fly-1" transform="translate(96, 78)">'
            '<ellipse cx="-2.2" cy="-2.2" rx="2.8" ry="1.6" fill="#E0F2FE" opacity="0.85" transform="rotate(-25)"/>'
            '<ellipse cx="2.2" cy="-2.2" rx="2.8" ry="1.6" fill="#E0F2FE" opacity="0.85" transform="rotate(25)"/>'
            '<ellipse cx="0" cy="0" rx="2.8" ry="1.9" fill="#111827"/>'
            '</g>'
            '<g class="jardin-fly-3" transform="translate(124, 90)">'
            '<ellipse cx="-2.2" cy="-2.2" rx="2.8" ry="1.6" fill="#E0F2FE" opacity="0.85" transform="rotate(-25)"/>'
            '<ellipse cx="2.2" cy="-2.2" rx="2.8" ry="1.6" fill="#E0F2FE" opacity="0.85" transform="rotate(25)"/>'
            '<ellipse cx="0" cy="0" rx="2.8" ry="1.9" fill="#111827"/>'
            '</g>'
            '</svg>'
        )

    # Score > 0.02: Koala vivo (alto = feliz y bien alimentado; medio/bajo = delgado, cansado y triste)
    fat_scale_x = 0.74 + 0.32 * score
    posture_drop = (1.0 - score) * 12.0
    ear_droop = (1.0 - score) * 22.0
    ribs_opacity = max(0.0, min(0.75, (0.35 - score) / 0.35)) if score < 0.35 else 0.0
    euca_leaf_op = max(0.0, min(1.0, (score - 0.15) / 0.5))
    leaf_col = _multi_color([(0.0, "#A16207"), (0.5, "#EAB308"), (1.0, "#22C55E")], score)

    if score >= 0.65:
        anim_cls = "jardin-koala-happy"
        mouth_d = "M 72 78 Q 80 86 88 78"
        eyes_svg = (
            '<circle cx="68" cy="62" r="4.2" fill="#1F2937"/>'
            '<circle cx="69.4" cy="60.6" r="1.4" fill="#FFFFFF"/>'
            '<circle cx="92" cy="62" r="4.2" fill="#1F2937"/>'
            '<circle cx="93.4" cy="60.6" r="1.4" fill="#FFFFFF"/>'
            '<ellipse cx="61" cy="70" rx="5" ry="2.8" fill="#F472B6" opacity="0.55"/>'
            '<ellipse cx="99" cy="70" rx="5" ry="2.8" fill="#F472B6" opacity="0.55"/>'
        )
    else:
        anim_cls = "jardin-animal-tired"
        mouth_d = "M 72 84 Q 80 77 88 84"
        eyes_svg = (
            '<circle cx="68" cy="64" r="3.6" fill="#1F2937"/>'
            '<path d="M 62 58 L 73 61" stroke="#1F2937" stroke-width="2.1" stroke-linecap="round"/>'
            '<circle cx="92" cy="64" r="3.6" fill="#1F2937"/>'
            '<path d="M 87 61 L 98 58" stroke="#1F2937" stroke-width="2.1" stroke-linecap="round"/>'
            '<path d="M 56 70 Q 54 77 56 80 Q 58 77 56 70 Z" fill="#38BDF8" opacity="0.85"/>'
        )

    return (
        '<svg class="jardin-char-svg" viewBox="0 0 160 220" style="overflow: visible;" xmlns="http://www.w3.org/2000/svg">'
        '<defs>'
        '<radialGradient id="koalaFur3D" cx="35%" cy="30%" r="70%">'
        '<stop offset="0%" stop-color="#9CA3AF"/>'
        '<stop offset="60%" stop-color="#6B7280"/>'
        '<stop offset="100%" stop-color="#374151"/>'
        '</radialGradient>'
        '<linearGradient id="koalaBelly3D" x1="0%" y1="0%" x2="0%" y2="100%">'
        '<stop offset="0%" stop-color="#F3F4F6"/>'
        '<stop offset="100%" stop-color="#D1D5DB"/>'
        '</linearGradient>'
        '<linearGradient id="koalaTrunk3D" x1="0%" y1="0%" x2="100%" y2="0%">'
        '<stop offset="0%" stop-color="#78350F"/>'
        '<stop offset="50%" stop-color="#92400E"/>'
        '<stop offset="100%" stop-color="#451A03"/>'
        '</linearGradient>'
        '<filter id="koalaShadow3D" x="-20%" y="-20%" width="140%" height="140%">'
        '<feDropShadow dx="0" dy="4" stdDeviation="3" flood-color="#000000" flood-opacity="0.25"/>'
        '</filter>'
        '</defs>'
        '<ellipse cx="80" cy="204" rx="40" ry="9" fill="#000000" opacity="0.22"/>'
        '<path d="M 114 206 L 122 55 L 136 55 L 130 206 Z" fill="url(#koalaTrunk3D)" filter="url(#koalaShadow3D)"/>'
        '<path d="M 122 98 Q 96 82 68 88" stroke="#78350F" stroke-width="7" stroke-linecap="round" fill="none"/>'
        f'<g class="{anim_cls}" transform="translate(0, {posture_drop:.1f})" filter="url(#koalaShadow3D)">'
        f'<g transform="translate(80, 134) scale({fat_scale_x:.2f}, 1)">'
        '<ellipse cx="0" cy="0" rx="34" ry="42" fill="url(#koalaFur3D)"/>'
        '<ellipse cx="-2" cy="5" rx="22" ry="30" fill="url(#koalaBelly3D)"/>'
        '</g>'
        f'<g opacity="{ribs_opacity:.2f}" stroke="#F3F4F6" stroke-width="2.2" stroke-linecap="round" fill="none">'
        '<path d="M 66 116 Q 80 112 94 116"/>'
        '<path d="M 64 127 Q 80 123 96 127"/>'
        '<path d="M 66 138 Q 80 134 94 138"/>'
        '</g>'
        '<ellipse cx="56" cy="170" rx="13" ry="16" fill="url(#koalaFur3D)"/>'
        '<ellipse cx="102" cy="170" rx="13" ry="16" fill="url(#koalaFur3D)"/>'
        '<ellipse cx="52" cy="110" rx="12" ry="10" fill="url(#koalaFur3D)"/>'
        '<ellipse cx="108" cy="110" rx="12" ry="10" fill="url(#koalaFur3D)"/>'
        f'<circle cx="48" cy="{48 + int(ear_droop * 0.35)}" r="16" fill="url(#koalaFur3D)"/>'
        f'<circle cx="48" cy="{48 + int(ear_droop * 0.35)}" r="9" fill="#E5E7EB"/>'
        f'<circle cx="112" cy="{48 + int(ear_droop * 0.35)}" r="16" fill="url(#koalaFur3D)"/>'
        f'<circle cx="112" cy="{48 + int(ear_droop * 0.35)}" r="9" fill="#E5E7EB"/>'
        '<ellipse cx="80" cy="66" rx="29" ry="25" fill="url(#koalaFur3D)"/>'
        '<ellipse cx="80" cy="68" rx="8" ry="11.5" fill="#1F2937"/>'
        '<ellipse cx="77.5" cy="64.5" rx="2.6" ry="4" fill="#4B5563"/>'
        + eyes_svg +
        f'<path d="{mouth_d}" stroke="#1F2937" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
        f'<g opacity="{euca_leaf_op:.2f}" transform="translate(44, 102)">'
        f'<ellipse cx="0" cy="0" rx="10" ry="5.5" fill="{leaf_col}" transform="rotate(-25)"/>'
        '</g>'
        '</g>'
        '</svg>'
    )


def construir_html_panel_patrimonio(
    total_patrimonio_ars,
    total_patrimonio_usd,
    cant_activos_contemplados,
    cant_activos_totales,
    ingreso_mensual_ars,
    costo_mensual_ars,
    dolar_b,
    hay_moneda_extranjera=False,
    datos_faltantes=False
):
    tasa_invalida = hay_moneda_extranjera and (dolar_b is None or float(dolar_b) <= 0)
    es_crecimiento = False
    linea_ahorro_positivo_html = ""

    if tasa_invalida:
        score = 0.5
        mensaje_salud = (
            "⚠️ Advertencia: Se detectaron activos o costos en otra moneda "
            "pero no hay un tipo de cambio disponible para convertir a ARS."
        )
    elif datos_faltantes or (ingreso_mensual_ars <= 0 and costo_mensual_ars <= 0):
        score = 0.5
        mensaje_salud = "Cargá ingresos y costos"
    else:
        monthly_saving = float(ingreso_mensual_ars) - float(costo_mensual_ars)

        if abs(monthly_saving) < 0.005:
            score = 1.0
            mensaje_salud = "Estamos bien financieramente: tus ahorros son cero y tu patrimonio se mantiene intacto."
        elif monthly_saving > 0:
            score = 1.0
            es_crecimiento = True
            linea_ahorro_positivo_html = (
                f'<div style="color: #15803D; background: #DCFCE7; border: 1px solid #86EFAC; '
                f'border-radius: 8px; padding: 2px 9px; font-size: 0.86rem; font-weight: 800; '
                f'margin-top: 4px; display: inline-block;">'
                f'Ahorro mensual: +{monthly_saving:,.0f} ARS'
                f'</div>'
            )
            mensaje_salud = (
                f"Estamos muy bien financieramente: ahorrás {monthly_saving:,.0f} ARS por mes y tu patrimonio crece."
            )
        else:
            perdida_mensual = abs(monthly_saving)
            if total_patrimonio_ars <= 0:
                months_left = 0.0
                meses_int = 0
                tiempo_str = "0 meses"
                score = 0.0
                mensaje_salud = "Estamos en llamas financieramente, a este ritmo te quedan 0 meses."
            else:
                months_left = float(total_patrimonio_ars) / float(perdida_mensual)
                meses_int = max(0, int(round(months_left)))
                anios_s = meses_int // 12
                meses_rem = meses_int % 12

                if meses_int <= 12:
                    tiempo_str = f"{meses_int} meses"
                else:
                    tiempo_str = f"{anios_s} años y {meses_rem} meses"

                if months_left >= 60.0:
                    score = 1.0
                elif months_left <= 12.0:
                    score = 0.0
                else:
                    score = (months_left - 12.0) / (60.0 - 12.0)

                if months_left <= 12.0:
                    mensaje_salud = f"Estamos en llamas financieramente, a este ritmo te quedan {tiempo_str}."
                else:
                    mensaje_salud = (
                        f"Tus ahorros mensuales son negativos (−{perdida_mensual:,.0f} ARS): "
                        f"a este ritmo tu patrimonio dura {tiempo_str}."
                    )

    # Interpolación continua de colores del cielo, colinas, suelo y follaje según score (0 a 1)
    sky_top = "#0EA5E9" if es_crecimiento else _multi_color([
        (0.0, "#7F1D1D"),
        (0.25, "#C2410C"),
        (0.55, "#F59E0B"),
        (0.80, "#7DD3FC"),
        (1.0, "#38BDF8")
    ], score)
    sky_mid = "#A5F3FC" if es_crecimiento else _multi_color([
        (0.0, "#DC2626"),
        (0.25, "#EA580C"),
        (0.55, "#FDE68A"),
        (0.80, "#BAE6FD"),
        (1.0, "#CCFBF1")
    ], score)
    sky_bot = "#A7F3D0" if es_crecimiento else _multi_color([
        (0.0, "#F97316"),
        (0.25, "#FDBA74"),
        (0.55, "#FEF3C7"),
        (0.80, "#DCFCE7"),
        (1.0, "#BBF7D0")
    ], score)

    hill_back = _multi_color([
        (0.0, "#9A3412"),
        (0.30, "#B45309"),
        (0.60, "#A16207"),
        (0.85, "#4ADE80"),
        (1.0, "#10B981" if es_crecimiento else "#22C55E")
    ], score)
    hill_mid = _multi_color([
        (0.0, "#B45309"),
        (0.30, "#D97706"),
        (0.60, "#CA8A04"),
        (0.85, "#22C55E"),
        (1.0, "#059669" if es_crecimiento else "#16A34A")
    ], score)
    ground_front = _multi_color([
        (0.0, "#78350F"),
        (0.30, "#92400E"),
        (0.60, "#854D0E"),
        (0.85, "#15803D"),
        (1.0, "#047857" if es_crecimiento else "#166534")
    ], score)

    leaf_main = _multi_color([
        (0.0, "#78350F"),
        (0.25, "#A16207"),
        (0.55, "#EAB308"),
        (0.80, "#4ADE80"),
        (1.0, "#10B981" if es_crecimiento else "#16A34A")
    ], score)
    leaf_light = _multi_color([
        (0.0, "#92400E"),
        (0.25, "#CA8A04"),
        (0.55, "#FDE047"),
        (0.80, "#86EFAC"),
        (1.0, "#6EE7B7" if es_crecimiento else "#4ADE80")
    ], score)
    leaf_dark = _multi_color([
        (0.0, "#451A03"),
        (0.25, "#713F12"),
        (0.55, "#A16207"),
        (0.80, "#15803D"),
        (1.0, "#065F46" if es_crecimiento else "#14532D")
    ], score)

    border_col = _multi_color([
        (0.0, "#EF4444"),
        (0.35, "#F59E0B"),
        (0.70, "#84CC16"),
        (1.0, "#10B981" if es_crecimiento else "#22C55E")
    ], score)

    fire_opacity = max(0.0, min(1.0, ((1.0 - score) ** 1.35)))
    sun_radius = 16.0 + (1.0 - score) * 10.0
    sun_core_col = _multi_color([(0.0, "#FEF08A"), (0.4, "#FDE047"), (1.0, "#FEF9C3")], score)
    sun_outer_col = _multi_color([(0.0, "#DC2626"), (0.4, "#F97316"), (1.0, "#FBBF24")], score)
    tumbleweed_opacity = max(0.0, min(1.0, (0.38 - score) / 0.38)) if score < 0.38 else 0.0
    cracks_opacity = max(0.0, min(1.0, (0.45 - score) / 0.45)) if score < 0.45 else 0.0
    clouds_opacity = max(0.0, min(0.92, (score - 0.15) / 0.85))
    flowers_opacity = max(0.0, min(1.0, (score - 0.55) / 0.45))
    fruits_opacity = 1.0 if es_crecimiento else 0.0
    droop_deg = (1.0 - score) * 34.0

    def _plant_style(threshold):
        if score <= 0.02 or score <= threshold:
            return 0.0, 0.0
        sc = max(0.15, min(1.0, (score - threshold) / (1.0 - threshold)))
        op = max(0.0, min(1.0, (score - threshold) / max(0.18, 1.0 - threshold)))
        mult_s = 0.68 if es_crecimiento else 0.62
        return sc * mult_s, op

    t1_s, t1_o = _plant_style(0.04)
    t2_s, t2_o = _plant_style(0.18)
    t3_s, t3_o = _plant_style(0.35)
    t4_s, t4_o = _plant_style(0.52)
    t5_s, t5_o = _plant_style(0.68)

    pct_salud = int(round(score * 100))
    badge_bg = _multi_color([
        (0.0, "#FEE2E2"),
        (0.35, "#FEF3C7"),
        (0.75, "#DCFCE7"),
        (1.0, "#D1FAE5")
    ], score)
    badge_text = _multi_color([
        (0.0, "#991B1B"),
        (0.35, "#92400E"),
        (0.75, "#166534"),
        (1.0, "#065F46")
    ], score)

    svg_canguro = _construir_svg_canguro(score)
    svg_koala = _construir_svg_koala(score)

    # Frutas y flores en las copas de los árboles cuando monthly_saving > 0 (es_crecimiento)
    frutas_arbol_grande = (
        f'<g opacity="{fruits_opacity:.2f}">'
        '<circle cx="-14" cy="-86" r="5.2" fill="#EF4444"/><circle cx="-15" cy="-87.5" r="1.5" fill="#FCA5A5"/>'
        '<circle cx="15" cy="-84" r="5.2" fill="#F97316"/><circle cx="13.5" cy="-85.5" r="1.5" fill="#FDBA74"/>'
        '<circle cx="0" cy="-66" r="5.2" fill="#EF4444"/><circle cx="-1.5" cy="-67.5" r="1.5" fill="#FCA5A5"/>'
        '<circle cx="-8" cy="-102" r="4.5" fill="#F43F5E"/>'
        '<circle cx="10" cy="-100" r="4.8" fill="#FB923C"/>'
        '<circle cx="-22" cy="-68" r="4.2" fill="#FDE047"/>'
        '<circle cx="22" cy="-68" r="4.2" fill="#F472B6"/>'
        '</g>'
    )
    frutas_arbol_mediano = (
        f'<g opacity="{fruits_opacity:.2f}">'
        '<circle cx="-10" cy="-66" r="4.8" fill="#EF4444"/>'
        '<circle cx="11" cy="-64" r="4.8" fill="#F97316"/>'
        '<circle cx="0" cy="-52" r="4.5" fill="#F43F5E"/>'
        '<circle cx="-14" cy="-52" r="3.8" fill="#FDE047"/>'
        '<circle cx="14" cy="-52" r="3.8" fill="#F472B6"/>'
        '</g>'
    )

    lineas_html = [
        f'<div class="jardin-health-scene" style="border-color: {border_col};">',
        # 1) PANEL DE INFORMACIÓN (IZQUIERDA, 32% EN ESCRITORIO, ALINEADO AL BORDE IZQUIERDO)
        f'<div class="jardin-info-panel" style="border-right-color: {border_col};">',
        '<div class="kpi-title" style="font-size: 1.05rem; color: #1F2937; margin-bottom: 1px;">Patrimonio Total</div>',
        f'<div class="kpi-value" style="font-size: 1.72rem; color: #111827; line-height: 1.12;">{total_patrimonio_ars:,.0f} ARS</div>',
        f'<div class="kpi-usd" style="font-size: 0.96rem; color: #1F2937; background: rgba(255,255,255,0.92); margin-top: 3px; padding: 2px 9px;">{total_patrimonio_usd:,.2f} USD</div>',
        linea_ahorro_positivo_html,
        f'<div class="jardin-status-box" style="background: {badge_bg}; color: {badge_text}; border-color: {border_col};">',
        f'<div style="font-size: 0.84rem; font-weight: 800; line-height: 1.25;">{mensaje_salud}</div>',
        '<div class="jardin-health-bar-track">',
        f'<div class="jardin-health-bar-fill" style="width: {pct_salud}%; background: {border_col};"></div>',
        '</div>',
        '</div>',
        f'<div class="kpi-sub" style="color: #374151; font-weight: 700; font-size: 0.82rem; margin-top: 5px; margin-bottom: 0;">{cant_activos_contemplados} activos de {cant_activos_totales} contemplados</div>',
        '</div>',
        # 2) PANEL DE ESCENA ANIMADA (DERECHA, 68% RESTANTE, CONTIGUO Y SIN ESPACIO INTERMEDIO)
        '<div class="jardin-scene-panel">',
        '<svg class="jardin-scene-svg" viewBox="0 0 900 160" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">',
        '<defs>',
        '<linearGradient id="skyGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
        f'<stop offset="0%" stop-color="{sky_top}"/>',
        f'<stop offset="55%" stop-color="{sky_mid}"/>',
        f'<stop offset="100%" stop-color="{sky_bot}"/>',
        '</linearGradient>',
        '<radialGradient id="sunGrad" cx="50%" cy="50%" r="50%">',
        f'<stop offset="0%" stop-color="{sun_core_col}"/>',
        f'<stop offset="65%" stop-color="{sun_outer_col}"/>',
        f'<stop offset="100%" stop-color="{sun_outer_col}" stop-opacity="0"/>',
        '</radialGradient>',
        '<linearGradient id="hillBackGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
        f'<stop offset="0%" stop-color="{hill_back}"/>',
        f'<stop offset="100%" stop-color="{ground_front}"/>',
        '</linearGradient>',
        '<linearGradient id="hillMidGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
        f'<stop offset="0%" stop-color="{hill_mid}"/>',
        f'<stop offset="100%" stop-color="{ground_front}"/>',
        '</linearGradient>',
        '<linearGradient id="foliage3D" x1="20%" y1="0%" x2="80%" y2="100%">',
        f'<stop offset="0%" stop-color="{leaf_light}"/>',
        f'<stop offset="55%" stop-color="{leaf_main}"/>',
        f'<stop offset="100%" stop-color="{leaf_dark}"/>',
        '</linearGradient>',
        '<linearGradient id="trunk3D" x1="0%" y1="0%" x2="100%" y2="0%">',
        '<stop offset="0%" stop-color="#78350F"/>',
        '<stop offset="45%" stop-color="#92400E"/>',
        '<stop offset="100%" stop-color="#451A03"/>',
        '</linearGradient>',
        '<filter id="softShadow3D" x="-20%" y="-20%" width="140%" height="140%">',
        '<feDropShadow dx="0" dy="3" stdDeviation="2.5" flood-color="#000000" flood-opacity="0.24"/>',
        '</filter>',
        '</defs>',
        '<rect x="0" y="0" width="900" height="160" fill="url(#skyGrad)"/>',
        # Sol / Sol en llamas totalmente visible en el cielo del panel derecho
        f'<g class="jardin-sun-group" transform="translate(450, {34 + int((1.0 - score) * 10)})">',
        f'<circle cx="0" cy="0" r="{sun_radius * 2.1:.1f}" fill="url(#sunGrad)" opacity="{0.45 + 0.45 * fire_opacity:.2f}"/>',
        f'<g class="jardin-sun-flames" opacity="{fire_opacity:.2f}">',
        f'<polygon points="0,-{sun_radius*1.65:.1f} 8,-{sun_radius*0.85:.1f} -8,-{sun_radius*0.85:.1f}" fill="#EF4444"/>',
        f'<polygon points="0,{sun_radius*1.65:.1f} 8,{sun_radius*0.85:.1f} -8,{sun_radius*0.85:.1f}" fill="#EF4444"/>',
        f'<polygon points="-{sun_radius*1.65:.1f},0 -{sun_radius*0.85:.1f},8 -{sun_radius*0.85:.1f},-8" fill="#F97316"/>',
        f'<polygon points="{sun_radius*1.65:.1f},0 {sun_radius*0.85:.1f},8 {sun_radius*0.85:.1f},-8" fill="#F97316"/>',
        f'<polygon points="-{sun_radius*1.2:.1f},-{sun_radius*1.2:.1f} -{sun_radius*0.5:.1f},-{sun_radius*0.9:.1f} -{sun_radius*0.9:.1f},-{sun_radius*0.5:.1f}" fill="#DC2626"/>',
        f'<polygon points="{sun_radius*1.2:.1f},-{sun_radius*1.2:.1f} {sun_radius*0.5:.1f},-{sun_radius*0.9:.1f} {sun_radius*0.9:.1f},-{sun_radius*0.5:.1f}" fill="#DC2626"/>',
        f'<polygon points="-{sun_radius*1.2:.1f},{sun_radius*1.2:.1f} -{sun_radius*0.5:.1f},{sun_radius*0.9:.1f} -{sun_radius*0.9:.1f},{sun_radius*0.5:.1f}" fill="#F59E0B"/>',
        f'<polygon points="{sun_radius*1.2:.1f},{sun_radius*1.2:.1f} {sun_radius*0.5:.1f},{sun_radius*0.9:.1f} {sun_radius*0.9:.1f},{sun_radius*0.5:.1f}" fill="#F59E0B"/>',
        '</g>',
        f'<circle cx="0" cy="0" r="{sun_radius:.1f}" fill="{sun_core_col}" filter="url(#softShadow3D)"/>',
        '</g>',
        # Nubes suaves
        f'<g class="jardin-clouds" opacity="{clouds_opacity:.2f}" fill="#FFFFFF">',
        '<g transform="translate(230, 26) scale(0.75)" opacity="0.82">',
        '<ellipse cx="0" cy="0" rx="34" ry="14"/><ellipse cx="-20" cy="4" rx="20" ry="11"/><ellipse cx="22" cy="4" rx="22" ry="10"/>',
        '</g>',
        '<g transform="translate(670, 24) scale(0.75)" opacity="0.78">',
        '<ellipse cx="0" cy="0" rx="36" ry="15"/><ellipse cx="-22" cy="5" rx="22" ry="11"/><ellipse cx="22" cy="5" rx="20" ry="10"/>',
        '</g>',
        '</g>',
        # Colinas 3D escaladas a la nueva altura
        '<path d="M 0 118 Q 180 86 360 110 T 660 104 T 900 116 L 900 160 L 0 160 Z" fill="url(#hillBackGrad)" opacity="0.88"/>',
        '<path d="M 0 128 Q 220 102 450 124 T 900 122 L 900 160 L 0 160 Z" fill="url(#hillMidGrad)" opacity="0.95"/>',
        f'<path d="M 0 138 Q 270 126 540 139 T 900 136 L 900 160 L 0 160 Z" fill="{ground_front}"/>',
        # Grietas de sequía
        f'<g stroke="#451A03" stroke-width="1.5" fill="none" opacity="{cracks_opacity:.2f}">',
        '<path d="M 220 143 L 238 149 L 228 156 M 238 149 L 256 152"/>',
        '<path d="M 430 146 L 452 151 L 442 158 M 452 151 L 474 149"/>',
        '<path d="M 640 143 L 660 150 L 650 157 M 660 150 L 682 153"/>',
        '</g>',
        # Árboles y plantas con frutas/flores en modo crecimiento
        f'<g class="jardin-sway-tree" opacity="{t1_o:.2f}" transform="translate(215, 132) scale({t1_s:.2f}) rotate({droop_deg * 0.45:.1f})" filter="url(#softShadow3D)">',
        '<path d="M -7 0 L -4 -68 L 4 -68 L 7 0 Z" fill="url(#trunk3D)"/>',
        '<circle cx="0" cy="-82" r="34" fill="url(#foliage3D)"/>',
        '<circle cx="-22" cy="-68" r="25" fill="url(#foliage3D)"/>',
        '<circle cx="22" cy="-68" r="25" fill="url(#foliage3D)"/>',
        '<circle cx="0" cy="-104" r="24" fill="url(#foliage3D)"/>',
        frutas_arbol_grande,
        '</g>',
        f'<g class="jardin-sway-tree-alt" opacity="{t2_o:.2f}" transform="translate(295, 136) scale({t2_s:.2f}) rotate({droop_deg * 0.6:.1f})" filter="url(#softShadow3D)">',
        '<path d="M -5 0 L -3 -52 L 3 -52 L 5 0 Z" fill="url(#trunk3D)"/>',
        '<ellipse cx="0" cy="-64" rx="28" ry="24" fill="url(#foliage3D)"/>',
        '<circle cx="-16" cy="-54" r="18" fill="url(#foliage3D)"/>',
        '<circle cx="16" cy="-54" r="18" fill="url(#foliage3D)"/>',
        frutas_arbol_mediano,
        '</g>',
        f'<g class="jardin-sway-tree" opacity="{t3_o:.2f}" transform="translate(385, 134) scale({t3_s:.2f}) rotate({droop_deg * 0.5:.1f})" filter="url(#softShadow3D)">',
        '<path d="M -6 0 L -3 -58 L 3 -58 L 6 0 Z" fill="url(#trunk3D)"/>',
        '<circle cx="0" cy="-72" r="30" fill="url(#foliage3D)"/>',
        '<circle cx="-18" cy="-58" r="22" fill="url(#foliage3D)"/>',
        '<circle cx="18" cy="-58" r="22" fill="url(#foliage3D)"/>',
        frutas_arbol_mediano,
        '</g>',
        f'<g class="jardin-sway-tree-alt" opacity="{t3_o:.2f}" transform="translate(535, 134) scale({t3_s:.2f}) rotate(-{droop_deg * 0.55:.1f})" filter="url(#softShadow3D)">',
        '<path d="M -6 0 L -3 -58 L 3 -58 L 6 0 Z" fill="url(#trunk3D)"/>',
        '<circle cx="0" cy="-72" r="30" fill="url(#foliage3D)"/>',
        '<circle cx="-18" cy="-58" r="22" fill="url(#foliage3D)"/>',
        '<circle cx="18" cy="-58" r="22" fill="url(#foliage3D)"/>',
        frutas_arbol_mediano,
        '</g>',
        f'<g class="jardin-sway-tree" opacity="{t2_o:.2f}" transform="translate(650, 136) scale({t2_s:.2f}) rotate(-{droop_deg * 0.6:.1f})" filter="url(#softShadow3D)">',
        '<path d="M -5 0 L -3 -52 L 3 -52 L 5 0 Z" fill="url(#trunk3D)"/>',
        '<ellipse cx="0" cy="-64" rx="28" ry="24" fill="url(#foliage3D)"/>',
        '<circle cx="-16" cy="-54" r="18" fill="url(#foliage3D)"/>',
        '<circle cx="16" cy="-54" r="18" fill="url(#foliage3D)"/>',
        frutas_arbol_mediano,
        '</g>',
        f'<g class="jardin-sway-tree-alt" opacity="{t1_o:.2f}" transform="translate(765, 132) scale({t1_s:.2f}) rotate(-{droop_deg * 0.4:.1f})" filter="url(#softShadow3D)">',
        '<path d="M -7 0 L -4 -70 L 4 -70 L 7 0 Z" fill="url(#trunk3D)"/>',
        '<circle cx="0" cy="-86" r="35" fill="url(#foliage3D)"/>',
        '<circle cx="-24" cy="-70" r="25" fill="url(#foliage3D)"/>',
        '<circle cx="24" cy="-70" r="25" fill="url(#foliage3D)"/>',
        '<circle cx="0" cy="-108" r="24" fill="url(#foliage3D)"/>',
        frutas_arbol_grande,
        '</g>',
        f'<g class="jardin-sway-bush" opacity="{t4_o:.2f}" transform="translate(340, 140) scale({t4_s:.2f}) rotate({droop_deg * 0.7:.1f})">',
        '<ellipse cx="0" cy="-14" rx="22" ry="15" fill="url(#foliage3D)"/>',
        '<ellipse cx="-14" cy="-10" rx="16" ry="12" fill="url(#foliage3D)"/>',
        '<ellipse cx="14" cy="-10" rx="16" ry="12" fill="url(#foliage3D)"/>',
        '</g>',
        f'<g class="jardin-sway-bush" opacity="{t4_o:.2f}" transform="translate(460, 141) scale({t5_s:.2f}) rotate({droop_deg * 0.5:.1f})">',
        '<ellipse cx="0" cy="-16" rx="25" ry="16" fill="url(#foliage3D)"/>',
        '<ellipse cx="-15" cy="-11" rx="17" ry="12" fill="url(#foliage3D)"/>',
        '<ellipse cx="15" cy="-11" rx="17" ry="12" fill="url(#foliage3D)"/>',
        '</g>',
        f'<g class="jardin-sway-bush" opacity="{t4_o:.2f}" transform="translate(595, 140) scale({t4_s:.2f}) rotate(-{droop_deg * 0.7:.1f})">',
        '<ellipse cx="0" cy="-14" rx="22" ry="15" fill="url(#foliage3D)"/>',
        '<ellipse cx="-14" cy="-10" rx="16" ry="12" fill="url(#foliage3D)"/>',
        '<ellipse cx="14" cy="-10" rx="16" ry="12" fill="url(#foliage3D)"/>',
        '</g>',
        # Flores
        f'<g opacity="{flowers_opacity:.2f}">',
        '<circle cx="245" cy="144" r="3.8" fill="#F472B6"/><circle cx="245" cy="144" r="1.6" fill="#FEF08A"/>',
        '<circle cx="315" cy="147" r="3.8" fill="#A78BFA"/><circle cx="315" cy="147" r="1.6" fill="#FEF08A"/>',
        '<circle cx="405" cy="145" r="3.5" fill="#FB7185"/><circle cx="405" cy="145" r="1.5" fill="#FEF08A"/>',
        '<circle cx="515" cy="146" r="3.8" fill="#F472B6"/><circle cx="515" cy="146" r="1.6" fill="#FEF08A"/>',
        '<circle cx="620" cy="144" r="3.8" fill="#A78BFA"/><circle cx="620" cy="144" r="1.6" fill="#FEF08A"/>',
        '<circle cx="710" cy="147" r="3.5" fill="#FBBF24"/><circle cx="710" cy="147" r="1.5" fill="#FFFFFF"/>',
        '<circle cx="820" cy="145" r="3.8" fill="#FB7185"/><circle cx="820" cy="145" r="1.6" fill="#FEF08A"/>',
        '</g>',
        # Plantas rodadoras (Tumbleweeds) rodando por el desierto
        f'<g opacity="{tumbleweed_opacity:.2f}">',
        '<g class="jardin-tumbleweed-1">',
        '<circle cx="0" cy="0" r="12" fill="none" stroke="#78350F" stroke-width="1.8" stroke-dasharray="5 3"/>',
        '<ellipse cx="0" cy="0" rx="12" ry="7" fill="none" stroke="#92400E" stroke-width="1.4" transform="rotate(35)"/>',
        '<ellipse cx="0" cy="0" rx="12" ry="7" fill="none" stroke="#78350F" stroke-width="1.4" transform="rotate(-35)"/>',
        '<path d="M -8 -4 L 8 4 M -7 5 L 7 -5" stroke="#92400E" stroke-width="1.2"/>',
        '</g>',
        '<g class="jardin-tumbleweed-2">',
        '<circle cx="0" cy="0" r="10" fill="none" stroke="#78350F" stroke-width="1.6" stroke-dasharray="4 2.5"/>',
        '<ellipse cx="0" cy="0" rx="10" ry="6" fill="none" stroke="#92400E" stroke-width="1.3" transform="rotate(50)"/>',
        '<ellipse cx="0" cy="0" rx="10" ry="6" fill="none" stroke="#78350F" stroke-width="1.3" transform="rotate(-40)"/>',
        '</g>',
        '</g>',
        '</svg>',
        # Canguro y Koala juntos lado a lado en el extremo izquierdo del panel de escena
        f'<div class="jardin-char-wrap jardin-char-left">{svg_canguro}</div>',
        f'<div class="jardin-char-wrap jardin-char-right">{svg_koala}</div>',
        '</div>',
        '</div>'
    ]
    return "\n".join(lineas_html)


# ----------------- GRÁFICO DE TORTA 2D CON 1 DECIMAL Y SIN POP-UPS (REQ 3 y 4) -----------------
def formatear_etiqueta_torta(texto, usar_minusculas=False):
    t = str(texto or "").strip()
    if not t:
        return t
    if usar_minusculas:
        return t[0].upper() + t[1:].lower()
    return t


def crear_torta_2d(df, col_valores, col_nombres, tamano="mediano", usar_minusculas=False):
    valores = df[col_valores].tolist()
    nombres = [formatear_etiqueta_torta(nom, usar_minusculas=usar_minusculas) for nom in df[col_nombres].tolist()]
    total = sum(valores) if sum(valores) > 0 else 1.0
    n = len(valores)

    colores = [PALETA_PASTEL[i % len(PALETA_PASTEL)] for i in range(n)]

    # Etiquetas personalizadas con exactamente 1 decimal en el porcentaje (ej: 57,2% o 0,8%)
    textos_torta = [
        f"{nom}<br>{((v / total) * 100):.1f}%".replace(".", ",")
        for nom, v in zip(nombres, valores)
    ]

    # Sacar hacia afuera las porciones chicas (< 9%) y conectarlas siempre con línea guía
    umbral_externo = 0.09 if tamano == "grande" else 0.08
    posiciones = [
        "outside" if (v / total) < umbral_externo else "inside"
        for v in valores
    ]

    if tamano == "grande":
        altura = 550
        tam_fuente = 14
        min_fuente = 12
        agujero = 0.32
        margenes = dict(t=50, b=50, l=55, r=55)
    elif tamano == "chico":
        altura = 350
        tam_fuente = 14
        min_fuente = 12
        agujero = 0.38
        margenes = dict(t=42, b=42, l=50, r=50)
    else:
        altura = 430
        tam_fuente = 14
        min_fuente = 12
        agujero = 0.36
        margenes = dict(t=40, b=40, l=40, r=40)

    fig = go.Figure(data=[go.Pie(
        labels=nombres,
        values=valores,
        text=textos_torta,
        textinfo="text",
        hoverinfo="skip",
        hovertemplate=None,
        hole=agujero,
        sort=True,
        direction="clockwise",
        textposition=posiciones,
        insidetextorientation="horizontal",
        pull=[0.012] * n,
        automargin=True,
        textfont=dict(
            size=tam_fuente,
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
        uniformtext=dict(minsize=min_fuente, mode="show"),
        height=altura,
        margin=margenes,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode=False,
        hovermode=False
    )
    return fig


# ----------------- GRÁFICO DE BARRAS HORIZONTALES LIMPIO -----------------
def crear_barras_horizontales(df, col_valores, col_nombres):
    df_ord = df.sort_values(by=col_valores, ascending=True).copy()
    valores = df_ord[col_valores].tolist()
    nombres = df_ord[col_nombres].tolist()
    total = sum(valores) if sum(valores) > 0 else 1.0
    max_val = max(valores) if valores else 1.0
    n = len(valores)

    colores = []
    for idx_b, v in enumerate(valores):
        ratio = (idx_b + 1) / max(n, 1)
        if ratio > 0.66:
            colores.append("#F5B7B1")  # Rojo pastel suave
        elif ratio > 0.33:
            colores.append("#F9E79F")  # Amarillo pastel suave
        else:
            colores.append("#ABEBC6")  # Verde pastel suave

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


# ----------------- LISTAS DE 100 ACCIONES Y 100 CRIPTOMONEDAS + UBICACIONES -----------------
ACCIONES_100_BASE = [
    "AAPL (Apple)", "MSFT (Microsoft)", "NVDA (Nvidia)", "GOOGL (Alphabet / Google)",
    "AMZN (Amazon)", "META (Meta Platforms)", "TSLA (Tesla)", "BRK-B (Berkshire Hathaway)",
    "MELI (MercadoLibre)", "KO (Coca-Cola)", "SPY (S&P 500 ETF)", "QQQ (Nasdaq 100 ETF)",
    "DIA (Dow Jones ETF)", "YPFD (YPF)", "GGAL (Grupo Financiero Galicia)", "BMA (Banco Macro)",
    "PAM (Pampa Energía)", "VIST (Vista Energy)", "TGS (Transportadora de Gas del Sur)",
    "CEPU (Central Puerto)", "GLOB (Globant)", "LLY (Eli Lilly)", "AVGO (Broadcom)",
    "JPM (JPMorgan Chase)", "V (Visa)", "WMT (Walmart)", "XOM (Exxon Mobil)",
    "MA (Mastercard)", "UNH (UnitedHealth)", "COST (Costco)", "PG (Procter & Gamble)",
    "JNJ (Johnson & Johnson)", "HD (Home Depot)", "NFLX (Netflix)", "ABBV (AbbVie)",
    "BAC (Bank of America)", "CRM (Salesforce)", "ORCL (Oracle)", "CVX (Chevron)",
    "MRK (Merck)", "AMD (Advanced Micro Devices)", "PEP (PepsiCo)", "TMO (Thermo Fisher)",
    "LIN (Linde)", "CSCO (Cisco Systems)", "ACN (Accenture)", "ADBE (Adobe)",
    "WFC (Wells Fargo)", "MCD (McDonald's)", "ABT (Abbott Laboratories)", "DIS (Walt Disney)",
    "PM (Philip Morris)", "IBM (IBM)", "GE (General Electric)", "INTU (Intuit)",
    "CAT (Caterpillar)", "VZ (Verizon)", "QCOM (Qualcomm)", "TXN (Texas Instruments)",
    "NOW (ServiceNow)", "AMGN (Amgen)", "PFE (Pfizer)", "ISRG (Intuitive Surgical)",
    "UBER (Uber Technologies)", "GS (Goldman Sachs)", "MS (Morgan Stanley)",
    "AXP (American Express)", "RTX (Raytheon)", "SPGI (S&P Global)", "NEE (NextEra Energy)",
    "HON (Honeywell)", "UNP (Union Pacific)", "BKNG (Booking Holdings)", "LOW (Lowe's)",
    "T (AT&T)", "COP (ConocoPhillips)", "BLK (BlackRock)", "SYK (Stryker)",
    "TJX (TJX Companies)", "PGR (Progressive)", "C (Citigroup)", "SCHW (Charles Schwab)",
    "BA (Boeing)", "INTC (Intel)", "NKE (Nike)", "SBUX (Starbucks)", "DE (John Deere)",
    "LMT (Lockheed Martin)", "MDLZ (Mondelez)", "ADP (Automatic Data Processing)",
    "GILD (Gilead Sciences)", "BMY (Bristol-Myers Squibb)", "MU (Micron Technology)",
    "PANW (Palo Alto Networks)", "PLTR (Palantir Technologies)", "SHOP (Shopify)",
    "PYPL (PayPal)", "COIN (Coinbase)", "ABNB (Airbnb)", "TSM (Taiwan Semiconductor)",
    "ASML (ASML Holding)", "NVO (Novo Nordisk)", "TM (Toyota Motor)", "BABA (Alibaba)",
    "SONY (Sony Group)", "PBR (Petrobras)", "VALE (Vale)", "NU (Nu Holdings / Nubank)"
]

CRIPTOS_100_BASE = [
    "BTC (Bitcoin)", "ETH (Ethereum)", "USDT (Tether)", "BNB (BNB / Binance Coin)",
    "SOL (Solana)", "USDC (USD Coin)", "XRP (Ripple)", "DOGE (Dogecoin)",
    "TON (Toncoin)", "ADA (Cardano)", "TRX (TRON)", "AVAX (Avalanche)",
    "SHIB (Shiba Inu)", "LINK (Chainlink)", "DOT (Polkadot)", "BCH (Bitcoin Cash)",
    "NEAR (NEAR Protocol)", "LTC (Litecoin)", "MATIC (Polygon)", "POL (Polygon Ecosystem)",
    "DAI (Dai)", "UNI (Uniswap)", "ICP (Internet Computer)", "APT (Aptos)",
    "KAS (Kaspa)", "ETC (Ethereum Classic)", "XMR (Monero)", "STX (Stacks)",
    "FET (Fetch.ai / ASI)", "XLM (Stellar)", "OKB (OKB)", "FIL (Filecoin)",
    "SUI (Sui)", "ARB (Arbitrum)", "ATOM (Cosmos)", "IMX (Immutable)",
    "RENDER (Render)", "HBAR (Hedera)", "MNT (Mantle)", "CRO (Cronos)",
    "OP (Optimism)", "VET (VeChain)", "INJ (Injective)", "MKR (Maker)",
    "AAVE (Aave)", "GRT (The Graph)", "TAO (Bittensor)", "PEPE (Pepe)",
    "WIF (dogwifhat)", "FLOKI (Floki)", "BONK (Bonk)", "THETA (Theta Network)",
    "RUNE (THORChain)", "AR (Arweave)", "ALGO (Algorand)", "FTM (Fantom)",
    "SEI (Sei)", "FLOW (Flow)", "TIA (Celestia)", "LDO (Lido DAO)",
    "PYTH (Pyth Network)", "QNT (Quant)", "EGLD (MultiversX)", "AXS (Axie Infinity)",
    "SAND (The Sandbox)", "MANA (Decentraland)", "GALA (Gala)", "EOS (EOS)",
    "XTZ (Tezos)", "NEO (Neo)", "KAVA (Kava)", "CHZ (Chiliz)",
    "MINA (Mina Protocol)", "IOTA (IOTA)", "CFX (Conflux)", "JASMY (JasmyCoin)",
    "SNX (Synthetix)", "PENDLE (Pendle)", "STRK (Starknet)", "WLD (Worldcoin)",
    "JUP (Jupiter)", "ENA (Ethena)", "ONDO (Ondo)", "BEAM (Beam)",
    "DYDX (dYdX)", "CRV (Curve DAO)", "1INCH (1inch)", "COMP (Compound)",
    "ENS (Ethereum Name Service)", "CAKE (PancakeSwap)", "ZEC (Zcash)", "DASH (Dash)",
    "ROSE (Oasis Network)", "ZIL (Zilliqa)", "ENJ (Enjin Coin)", "BAT (Basic Attention Token)",
    "LRC (Loopring)", "QTUM (Qtum)", "CELO (Celo)", "ANKR (Ankr)"
]

BONOS_BASE = [
    "AL30 (Bonar 2030 Ley Arg.)", "GD30 (Global 2030 Ley NY)",
    "AL29 (Bonar 2029 Ley Arg.)", "GD29 (Global 2029 Ley NY)",
    "AL35 (Bonar 2035 Ley Arg.)", "GD35 (Global 2035 Ley NY)",
    "AE38 (Bonar 2038 Ley Arg.)", "GD38 (Global 2038 Ley NY)",
    "AL41 (Bonar 2041 Ley Arg.)", "GD41 (Global 2041 Ley NY)",
    "GD46 (Global 2046 Ley NY)", "BPY26 (Bopreal Serie 1 2026)",
    "BPJ25 (Bopreal Serie 2 2025)", "BPO27 (Bopreal Serie 3 2027)",
    "TX26 (Boncer 2026 CER)", "TX28 (Boncer 2028 CER)",
    "TZX26 (Boncer Cero 2026)", "TZX27 (Boncer Cero 2027)",
    "TZX28 (Boncer Cero 2028)", "DICP (Discount Pesos CER)",
    "PARP (Par Pesos CER)", "CUAP (Cuasipar Pesos CER)",
    "PR17 (Bono Consolidación)", "TVPP (Cupón PBI Pesos)",
    "TVPA (Cupón PBI USD Ley Arg.)", "TVPY (Cupón PBI USD Ley NY)",
    "S31E5 (Lecap Enero)", "S28F5 (Lecap Febrero)",
    "S31M5 (Lecap Marzo)", "S30J5 (Lecap Junio)",
    "S30S5 (Lecap Septiembre)", "T15D5 (Boncap Diciembre)",
    "YCA6O (ON YPF 2025)", "YMCHO (ON YPF 2026)",
    "MRCAO (ON Genneia)", "IRCFO (ON IRSA)",
    "TLCTO (ON Telecom)", "PNDCO (ON Pan American Energy)",
    "MGCHO (ON Pampa Energía)", "CS38O (ON Cresud)",
    "SHY (US Treasury 1-3Y)", "IEF (US Treasury 7-10Y)",
    "TLT (US Treasury 20+Y)", "TIP (US TIPS Inflación)"
]

UBICACIONES_BASE = [
    "Binance", "Nexo", "IOL", "Bco Macro",
    "Mercado Pago", "Uala", "NX", "Claro Pay"
]


def reparar_inversiones_corruptas(inversiones):
    """Repara filas cuyo detalle es Pesos ARS o Dólares USD pero quedaron en otra categoría."""
    modificado = False
    for inv in (inversiones or []):
        inv.setdefault("activo_inv", True)
        tipo_norm = normalizar_tipo_activo_inv(inv.get("tipo", "Otros"))
        det_str = str(inv.get("activo", "")).strip()
        det_up = det_str.upper()
        sim_up = str(inv.get("simbolo", "")).strip().upper()

        if det_up in ["PESOS ARS", "PESOS", "A - PESOS ARS", "B - PESOS ARS", "EFECTIVO / BANCO"] or (
            sim_up == "ARS" and tipo_norm in ["Acciones", "Cryptos", "Bonos"]
        ):
            if inv.get("tipo") != "Pesos ARS" or inv.get("activo") != "Pesos ARS" or inv.get("simbolo") != "ARS":
                inv["tipo"] = "Pesos ARS"
                inv["activo"] = "Pesos ARS"
                inv["simbolo"] = "ARS"
                modificado = True
        elif det_up in ["DÓLARES USD", "DOLARES USD", "DÓLAR BILLETE", "DOLAR BILLETE", "A - DÓLAR BILLETE", "B - DÓLARES USD"] or (
            sim_up == "USD" and tipo_norm in ["Acciones", "Cryptos", "Bonos"]
        ):
            if inv.get("tipo") != "Dólares USD" or inv.get("activo") != "Dólares USD" or inv.get("simbolo") != "USD":
                inv["tipo"] = "Dólares USD"
                inv["activo"] = "Dólares USD"
                inv["simbolo"] = "USD"
                modificado = True
        else:
            if inv.get("tipo") != tipo_norm:
                inv["tipo"] = tipo_norm
                modificado = True
            if tipo_norm in ["Cryptos", "Acciones", "Bonos"]:
                det_ticker = det_str.split(" ")[0].upper()
                if det_ticker and det_ticker not in ["USD", "ARS"] and inv.get("simbolo") != det_ticker:
                    inv["simbolo"] = det_ticker
                    modificado = True
    return modificado


def parsear_numero_flexible(texto):
    s = str(texto or "").strip().replace(" ", "")
    if not s:
        return 0.0
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def normalizar_tipo_activo_inv(tipo_raw):
    t = str(tipo_raw or "").strip()
    if t in ["A - Pesos ARS", "B - Pesos ARS", "Pesos ARS", "Efectivo / Banco"]:
        return "Pesos ARS"
    if t in ["B - Dólares USD", "Dólares USD", "Dólar Billete", "A - Dólar Billete"]:
        return "Dólares USD"
    if t in ["C - Acciones", "Acciones", "Acciones / CEDEARs"]:
        return "Acciones"
    if t in ["D - Cryptos", "Cryptos", "D - Criptomonedas", "Criptomonedas"]:
        return "Cryptos"
    if t in ["E - Bonos", "Bonos"]:
        return "Bonos"
    if t in ["F - FCI", "FCI"]:
        return "FCI"
    return "Otros" 


def normalizar_lista_activos_con_base(lista_guardada, lista_base):
    mapa_base = {item.split(" ")[0].upper(): item for item in lista_base}
    resultado = list(lista_base)
    vistos = {item.split(" ")[0].upper() for item in resultado}
    for item in (lista_guardada or []):
        limpio = str(item or "").strip()
        if not limpio:
            continue
        ticker = limpio.split(" ")[0].upper()
        if ticker in mapa_base:
            continue
        if ticker not in vistos:
            resultado.append(limpio if "(" in limpio else limpio.upper())
            vistos.add(ticker)
    return resultado


def registrar_ubicacion_guardada(datos, nueva_ubicacion):
    loc = str(nueva_ubicacion or "").strip()
    if not loc or loc.lower() == "sin especificar":
        return
    actuales = datos.get("ubicaciones_guardadas", list(UBICACIONES_BASE))
    filtradas = [u for u in actuales if str(u).strip() and str(u).strip().lower() != loc.lower()]
    filtradas.insert(0, loc)
    for ub in UBICACIONES_BASE:
        if not any(ub.lower() == u.lower() for u in filtradas):
            filtradas.append(ub)
    datos["ubicaciones_guardadas"] = filtradas
    ult = datos.setdefault("ultimas_selecciones_inv", {})
    ult["ubicacion"] = loc


# ----------------- GESTIÓN Y PERSISTENCIA DE DATOS -----------------
def cargar_datos():
    criptos_base = list(CRIPTOS_100_BASE)
    acciones_base = list(ACCIONES_100_BASE)

    datos_por_defecto = {
        "seguridad": {
            "usuario": "mama",
            "password_actual": "Finanzasmama123",
            "passwords_validas": ["Finanzasmama123", "terapias123"],
            "email_recuperacion": "julianherrero.jh@gmail.com",
            "telefono_recuperacion": "+61493680014",
            "smtp_app_password": "",
            "whatsapp_apikey": ""
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
        "bonos_guardadas": list(BONOS_BASE),
        "ubicaciones_guardadas": list(UBICACIONES_BASE),
        "ultimas_selecciones_inv": {
            "tipo": "A - Pesos ARS",
            "accion": "AAPL (Apple)",
            "cripto": "BTC (Bitcoin)",
            "bono": "AL30 (Bonar 2030 Ley Arg.)",
            "ubicacion": "Bco Nacion"
        },
        "inversiones": [
            {
                "tipo": "Cryptos",
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

            seg = data.get("seguridad", {})
            seg.setdefault("usuario", "mama")
            seg.setdefault("password_actual", "Finanzasmama123")
            pw_val = seg.get("passwords_validas", ["Finanzasmama123", "terapias123"])
            if seg["password_actual"] not in pw_val:
                pw_val.append(seg["password_actual"])
            seg["passwords_validas"] = pw_val
            if not seg.get("email_recuperacion"):
                seg["email_recuperacion"] = "julianherrero.jh@gmail.com"
            if not seg.get("telefono_recuperacion"):
                seg["telefono_recuperacion"] = "+61493680014"
            seg.setdefault("smtp_app_password", "")
            seg.setdefault("whatsapp_apikey", "")
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

            reparar_inversiones_corruptas(data.get("inversiones", []))

            criptos_guardadas_raw = data.get("criptos_guardadas", criptos_base)
            for inv in data.get("inversiones", []):
                if inv.get("tipo") == "Cryptos":
                    sim = inv.get("simbolo", "").upper().strip()
                    if sim:
                        criptos_guardadas_raw.append(sim)
            data["criptos_guardadas"] = normalizar_lista_activos_con_base(criptos_guardadas_raw, CRIPTOS_100_BASE)

            acciones_guardadas_raw = data.get("acciones_guardadas", acciones_base)
            for inv in data.get("inversiones", []):
                if inv.get("tipo") == "Acciones":
                    act_str = str(inv.get("activo", "")).strip()
                    if act_str:
                        acciones_guardadas_raw.append(act_str)
            data["acciones_guardadas"] = normalizar_lista_activos_con_base(acciones_guardadas_raw, ACCIONES_100_BASE)

            bonos_guardados_raw = data.get("bonos_guardadas", list(BONOS_BASE))
            for inv in data.get("inversiones", []):
                if inv.get("tipo") == "Bonos":
                    bon_str = str(inv.get("activo", "")).strip()
                    if bon_str:
                        bonos_guardados_raw.append(bon_str)
            data["bonos_guardadas"] = normalizar_lista_activos_con_base(bonos_guardados_raw, BONOS_BASE)

            # Inicializar ubicaciones garantizando que las opciones por defecto estén siempre disponibles
            ubic_guardadas = [str(u).strip() for u in data.get("ubicaciones_guardadas", []) if str(u).strip()]
            for ub in UBICACIONES_BASE:
                if not any(ub.lower() == u.lower() for u in ubic_guardadas):
                    ubic_guardadas.append(ub)
            for inv in reversed(data.get("inversiones", [])):
                pl = str(inv.get("plataforma", "")).strip()
                if pl and pl.lower() != "sin especificar" and not any(pl.lower() == u.lower() for u in ubic_guardadas):
                    ubic_guardadas.insert(0, pl)
            data["ubicaciones_guardadas"] = ubic_guardadas if ubic_guardadas else list(UBICACIONES_BASE)

            ult_sel = data.get("ultimas_selecciones_inv", {})
            if not isinstance(ult_sel, dict):
                ult_sel = {}
            mapa_tipo_opt = {
                "Pesos ARS": "A - Pesos ARS",
                "B - Pesos ARS": "A - Pesos ARS",
                "A - Pesos ARS": "A - Pesos ARS",
                "Dólares USD": "B - Dólares USD",
                "Dólar Billete": "B - Dólares USD",
                "A - Dólar Billete": "B - Dólares USD",
                "B - Dólares USD": "B - Dólares USD",
                "Acciones": "C - Acciones",
                "C - Acciones": "C - Acciones",
                "Cryptos": "D - Cryptos",
                "Criptomonedas": "D - Cryptos",
                "D - Criptomonedas": "D - Cryptos",
                "D - Cryptos": "D - Cryptos",
                "Bonos": "E - Bonos",
                "E - Bonos": "E - Bonos",
                "FCI": "F - FCI",
                "F - FCI": "F - FCI",
                "Otros": "G - Otros",
                "E - Otros": "G - Otros",
                "G - Otros": "G - Otros"
            }
            ult_sel["tipo"] = mapa_tipo_opt.get(ult_sel.get("tipo", ""), "A - Pesos ARS")
            ult_sel.setdefault("accion", data["acciones_guardadas"][0] if data["acciones_guardadas"] else "AAPL (Apple)")
            ult_sel.setdefault("cripto", data["criptos_guardadas"][0] if data["criptos_guardadas"] else "BTC (Bitcoin)")
            ult_sel.setdefault("bono", data["bonos_guardadas"][0] if data.get("bonos_guardadas") else "AL30 (Bonar 2030 Ley Arg.)")
            ult_sel.setdefault("ubicacion", data["ubicaciones_guardadas"][0] if data["ubicaciones_guardadas"] else "Bco Nacion")
            data["ultimas_selecciones_inv"] = ult_sel

            data.setdefault("historial_cierres", [])
            return data
        except Exception:
            pass

    return datos_por_defecto


def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)


# ----------------- EXPORTACIÓN A EXCEL (.XLSX) AL CERRAR SESIÓN (REQ 4) -----------------
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
        tipo = normalizar_tipo_activo_inv(inv.get("tipo", "Pesos ARS"))
        simbolo = str(inv.get("simbolo", "")).upper().strip().split(" ")[0]
        if tipo == "Dólares USD":
            val_usd = cant
            val_ars = cant * dolar_b
        elif tipo in ["Cryptos", "Acciones"]:
            precio_u = cotizaciones.get(simbolo, 1.0 if tipo == "Cryptos" else 100.0)
            val_usd = cant * precio_u
            val_ars = val_usd * dolar_b
        elif tipo == "Bonos":
            precio_u_ars = cotizaciones.get(f"BONO_ARS_{simbolo}", float(inv.get("precio_unitario_ars", 1120.0)))
            val_ars = cant * precio_u_ars
            val_usd = val_ars / dolar_b if dolar_b > 0 else 0.0
        else:
            precio_u_ars = float(inv.get("precio_unitario_ars", 1.0))
            if simbolo and simbolo not in ["ARS", "USD"] and simbolo in cotizaciones:
                precio_u_ars = cotizaciones[simbolo] * dolar_b
            val_ars = cant * precio_u_ars
            val_usd = val_ars / dolar_b if dolar_b > 0 else 0.0

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
                    rows_xml.append(f'<row r="{r_idx}">{"".join(cells_r)}</row>')
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


def registrar_snapshot_cierre(datos, dolar_b, cotizaciones):
    tz_ar = timezone(timedelta(hours=-3))
    fecha_str = datetime.now(tz_ar).strftime("%Y-%m-%d %H:%M")
    costos_act = sum(c["monto"] for c in datos.get("costos", []) if c.get("activo", True))
    ingresos_act = sum(i["monto"] for i in datos.get("ingresos", []) if i.get("activo", True))
    ahorro_act = ingresos_act - costos_act

    hist = datos.setdefault("historial_cierres", [])
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


# ----------------- ENVÍO SEGURO DE CÓDIGO POR GMAIL Y WHATSAPP/CELULAR (REQ 6) -----------------
def enviar_codigo_por_email(destinatario, codigo, usuario_actual, datos):
    """
    Envía el código de 6 dígitos por correo electrónico sin mostrarlo nunca en pantalla.
    Intenta primero vía SMTP directo (Gmail) y luego vía servicio HTTP FormSubmit AJAX.
    """
    seg = datos.get("seguridad", {})
    smtp_user = seg.get("email_recuperacion", "") or destinatario
    smtp_pass = seg.get("smtp_app_password", "").strip()
    try:
        if not smtp_pass and hasattr(st, "secrets"):
            smtp_user = st.secrets.get("gmail_user", smtp_user)
            smtp_pass = st.secrets.get("gmail_app_password", "")
    except Exception:
        pass

    # 1. Intentar envío por Gmail SMTP directo si tiene Contraseña de Aplicación configurada
    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = destinatario
            msg["Subject"] = "🌿 Código de recuperación - Tu Jardín Financiero"
            cuerpo = (
                f"Hola!\n\n"
                f"Solicitaste recuperar tu acceso a Jardín Financiero.\n\n"
                f"• Tu Usuario es: {usuario_actual}\n"
                f"• Tu Código de seguridad de 6 dígitos es: {codigo}\n\n"
                f"Ingresá este código en la pantalla de la aplicación para restablecer tu contraseña."
            )
            msg.attach(MIMEText(cuerpo, "plain", "utf-8"))
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=7)
            server.login(smtp_user, smtp_pass.replace(" ", ""))
            server.send_message(msg)
            server.quit()
            return True, f"✅ Enviamos tu código de 6 dígitos a **{destinatario}**. Revisá tu bandeja de entrada de Gmail."
        except Exception:
            pass

    # 2. Envío automático vía API HTTP de correo (FormSubmit AJAX) sin requerir clave SMTP previa
    try:
        endpoint_fs = "e0910d6b0f724c30a3a96742a975e668" if destinatario.strip().lower() == "julianherrero.jh@gmail.com" else destinatario
        url_fs = f"https://formsubmit.co/ajax/{endpoint_fs}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://share.streamlit.io",
            "Referer": "https://share.streamlit.io/",
            "User-Agent": "Mozilla/5.0"
        }
        payload = {
            "_subject": "🌿 Código de Recuperación - Jardín Financiero",
            "_template": "box",
            "_captcha": "false",
            "Plataforma": "Jardín Financiero",
            "Usuario": usuario_actual,
            "Codigo_de_Verificacion": codigo,
            "Instrucciones": "Ingresá este código de 6 dígitos en la pantalla de Jardín Financiero para cambiar tu contraseña."
        }
        r = requests.post(url_fs, json=payload, headers=headers, timeout=8)
        if r.status_code == 200:
            resp_json = r.json()
            msg_srv = str(resp_json.get("message", "")).lower()
            if "activate" in msg_srv or "activation" in msg_srv:
                return (
                    True,
                    f"📨 Te enviamos un correo de activación por única vez a **{destinatario}** "
                    f"(revisá Recibidos o Spam y tocá **'Activate Form'**). Luego volvé a tocar el botón de enviar y recibirás todos los códigos al instante."
                )
            return (
                True,
                f"✅ Código enviado a **{destinatario}**. Revisá tu bandeja de entrada (y la carpeta de Spam/Promociones)."
            )
    except Exception:
        pass

    return (
        False,
        f"⚠️ No se pudo conectar con el servidor de correo. Configurá tu clave de aplicación de Gmail en el menú lateral."
    )


def enviar_codigo_por_celular(telefono_limpio, codigo, usuario_actual, datos):
    """
    Envía el código de 6 dígitos al celular por WhatsApp API (CallMeBot) / SMS (Textbelt)
    y envía copia de respaldo al correo registrado sin mostrar jamás el código en la pantalla.
    """
    seg = datos.get("seguridad", {})
    wa_apikey = seg.get("whatsapp_apikey", "").strip()
    try:
        if not wa_apikey and hasattr(st, "secrets"):
            wa_apikey = st.secrets.get("whatsapp_apikey", "")
    except Exception:
        pass

    mensaje_texto = (
        f"🌿 Jardín Financiero: Tu usuario es {usuario_actual} "
        f"y tu código de seguridad es: {codigo}"
    )

    # 1. Intentar WhatsApp automático vía CallMeBot API si está configurada
    if wa_apikey:
        try:
            url_wa = (
                f"https://api.callmebot.com/whatsapp.php?"
                f"phone={telefono_limpio}&text={urllib.parse.quote(mensaje_texto)}&apikey={wa_apikey}"
            )
            r_wa = requests.get(url_wa, timeout=7)
            if r_wa.status_code == 200 and "error" not in r_wa.text.lower():
                return True, f"✅ Código enviado por WhatsApp al número terminado en **...{telefono_limpio[-4:]}**."
        except Exception:
            pass

    # 2. Intentar envío por SMS internacional vía Textbelt
    try:
        r_sms = requests.post(
            "https://textbelt.com/text",
            data={
                "phone": f"+{telefono_limpio}",
                "message": mensaje_texto,
                "key": "textbelt"
            },
            timeout=6
        )
        if r_sms.status_code == 200 and r_sms.json().get("success") is True:
            return True, f"✅ Código enviado por SMS al celular terminado en **...{telefono_limpio[-4:]}**."
    except Exception:
        pass

    # 3. Respaldo automático al correo de su celular para garantizar que el código llegue sin mostrarse en pantalla
    email_respaldo = seg.get("email_recuperacion", "julianherrero.jh@gmail.com")
    if email_respaldo and "@" in email_respaldo:
        ok_mail, msg_mail = enviar_codigo_por_email(email_respaldo, codigo, usuario_actual, datos)
        if ok_mail:
            return (
                True,
                f"📲 Enviamos la notificación con tu código de 6 dígitos a tu celular a través de tu cuenta vinculada (**{email_respaldo}**)."
            )

    return (
        False,
        "⚠️ Para recibir WhatsApp directo automático sin correo de respaldo, activá tu clave gratuita de CallMeBot en el panel lateral."
    )


# ----------------- COTIZACIONES EXTERNAS -----------------
@st.cache_data(ttl=180)
def obtener_cotizaciones(simbolos_acciones, simbolos_cripto, simbolos_bonos=()):
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
        "YPFD": 28.0,
        # Cotizaciones base de bonos en ARS por unidad/lámina
        "BONO_ARS_AL30": 1120.0,
        "BONO_ARS_GD30": 1145.0,
        "BONO_ARS_AL29": 1160.0,
        "BONO_ARS_GD29": 1185.0,
        "BONO_ARS_AL35": 980.0,
        "BONO_ARS_GD35": 1010.0,
        "BONO_ARS_AE38": 1030.0,
        "BONO_ARS_GD38": 1065.0,
        "BONO_ARS_AL41": 940.0,
        "BONO_ARS_GD41": 970.0,
        "BONO_ARS_GD46": 995.0,
        "BONO_ARS_BPY26": 1320.0,
        "BONO_ARS_BPJ25": 1410.0,
        "BONO_ARS_BPO27": 1240.0,
        "BONO_ARS_TX26": 2150.0,
        "BONO_ARS_TX28": 1980.0,
        "BONO_ARS_TZX26": 2340.0,
        "BONO_ARS_TZX27": 2190.0,
        "BONO_ARS_TZX28": 2050.0,
        "BONO_ARS_DICP": 34500.0,
        "BONO_ARS_PARP": 16800.0,
        "BONO_ARS_CUAP": 22400.0,
        "BONO_ARS_PR17": 1850.0,
        "BONO_ARS_TVPP": 18.5,
        "BONO_ARS_TVPA": 420.0,
        "BONO_ARS_TVPY": 450.0,
        "BONO_ARS_S31E5": 1280.0,
        "BONO_ARS_S28F5": 1310.0,
        "BONO_ARS_S31M5": 1345.0,
        "BONO_ARS_S30J5": 1420.0,
        "BONO_ARS_S30S5": 1495.0,
        "BONO_ARS_T15D5": 1580.0,
        "BONO_ARS_YCA6O": 1590.0,
        "BONO_ARS_YMCHO": 1620.0,
        "BONO_ARS_MRCAO": 1550.0,
        "BONO_ARS_IRCFO": 1580.0,
        "BONO_ARS_TLCTO": 1540.0,
        "BONO_ARS_PNDCO": 1610.0,
        "BONO_ARS_MGCHO": 1595.0,
        "BONO_ARS_CS38O": 1530.0
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

    for bono in set(simbolos_bonos or ()):
        b_clean = bono.upper().strip().split(" ")[0]
        if not b_clean or b_clean in ["USD", "ARS"]:
            continue
        try:
            # Intentar primero cotización en ARS en BYMA (.BA) en Yahoo Finance
            url_ba = f"https://query1.finance.yahoo.com/v8/finance/chart/{b_clean}.BA?interval=1d&range=1d"
            r_ba = requests.get(url_ba, headers=headers, timeout=3)
            if r_ba.status_code == 200:
                res_ba = r_ba.json()["chart"]["result"][0]["meta"]
                p_ba = float(res_ba.get("regularMarketPrice", 0))
                currency_ba = str(res_ba.get("currency", "ARS")).upper()
                if p_ba > 0:
                    # En BYMA los bonos soberanos suelen cotizar cada 100 láminas; si supera 20000 en bonos AL/GD ajustamos a unidad
                    if b_clean[:2] in ["AL", "GD", "AE", "BP", "TX", "TZ"] and p_ba > 25000:
                        p_ba = p_ba / 100.0
                    cotiz[f"BONO_ARS_{b_clean}"] = p_ba if currency_ba == "ARS" else (p_ba * cotiz["dolar_blue"])
                    continue
        except Exception:
            pass
        try:
            url_us = f"https://query1.finance.yahoo.com/v8/finance/chart/{b_clean}?interval=1d&range=1d"
            r_us = requests.get(url_us, headers=headers, timeout=3)
            if r_us.status_code == 200:
                res_us = r_us.json()["chart"]["result"][0]["meta"]
                p_us = float(res_us.get("regularMarketPrice", 0))
                currency_us = str(res_us.get("currency", "USD")).upper()
                if p_us > 0:
                    cotiz[f"BONO_ARS_{b_clean}"] = (p_us * cotiz["dolar_blue"]) if currency_us == "USD" else p_us
        except Exception:
            pass

    return cotiz


# ----------------- ESTILOS CSS ACOTADOS Y SEGUROS (LAPTOP + ANDROID) -----------------
st.markdown("""
<style>
    /* 1. Evitar que la barra superior fija de Streamlit tape las solapas o el cuadro de ingreso */
    header[data-testid="stHeader"] {
        background: transparent !important;
        background-color: transparent !important;
    }
    .block-container {
        max-width: 98% !important;
        padding-top: 3.6rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        padding-bottom: 2.5rem !important;
    }

    /* 2. Ocultar el aviso "Press Enter to apply" */
    div[data-testid="InputInstructions"],
    [data-testid="InputInstructions"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* 3. Cuadro de Login */
    .jardin-login-box {
        background: linear-gradient(145deg, #EAF6EE 0%, #F5F0FF 100%);
        border: 2px solid #95D5B2;
        border-radius: 22px;
        padding: 28px 24px 18px 24px;
        box-shadow: 0 8px 20px rgba(45, 106, 79, 0.08);
        text-align: center;
        margin-top: 10px;
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
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(90deg, #40916C 0%, #2D6A4F 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: 2px solid #1B4332 !important;
        min-height: 46px !important;
    }
    div[data-testid="stFormSubmitButton"] button p,
    div[data-testid="stFormSubmitButton"] button span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    /* Botón (+) compacto en verde trébol claro con signo (+) blanco y ancho mínimo dentro de categorías */
    details div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button,
    button.btn-mas-trebol {
        background: #57CC99 !important;
        background-color: #57CC99 !important;
        border: 1.5px solid #38A3A5 !important;
        color: #FFFFFF !important;
        width: 38px !important;
        min-width: 38px !important;
        max-width: 38px !important;
        height: 38px !important;
        min-height: 38px !important;
        padding: 0px !important;
        border-radius: 10px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 6px rgba(87, 204, 153, 0.25) !important;
    }
    details div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover,
    button.btn-mas-trebol:hover {
        background: #48B886 !important;
        background-color: #48B886 !important;
        border-color: #2D6A4F !important;
    }
    details div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button p,
    details div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button span,
    button.btn-mas-trebol p,
    button.btn-mas-trebol span {
        color: #FFFFFF !important;
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    /* 4. CAMBIO 1: Solapas principales en forma de píldora verde menta con 🍀 (visibles y sin recortes) */
    .stTabs {
        overflow: visible !important;
    }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"],
    div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {
        display: none !important;
        height: 0px !important;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px !important;
        margin-bottom: 1.25rem !important;
        padding: 8px 4px !important;
        height: auto !important;
        min-height: 72px !important;
        overflow: visible !important;
        background: transparent !important;
        border: none !important;
        align-items: center !important;
        flex-wrap: wrap !important;
    }
    .stTabs button[data-baseweb="tab"] {
        min-height: 58px !important;
        height: auto !important;
        padding: 12px 32px !important;
        background-color: #F9FAFB !important;
        border-radius: 999px !important;
        border: 1.5px solid #D8ECE3 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.25s ease-in-out !important;
        overflow: visible !important;
    }
    .stTabs button[data-baseweb="tab"]:hover {
        background-color: #F0FBF6 !important;
        border-color: #A8DFC4 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 12px rgba(45, 106, 79, 0.10) !important;
    }
    .stTabs button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #E6F7EF !important;
        border: 2px solid #A8DFC4 !important;
        border-radius: 999px !important;
        box-shadow: 0 4px 14px rgba(45, 106, 79, 0.14) !important;
    }
    .stTabs button[data-baseweb="tab"] [data-testid="stMarkdownContainer"] p,
    .stTabs button[data-baseweb="tab"] p {
        font-size: 1.22rem !important;
        font-weight: 800 !important;
        color: #4B5563 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.4px !important;
        margin: 0 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
        line-height: 1.2 !important;
    }
    .stTabs button[data-baseweb="tab"][aria-selected="true"] [data-testid="stMarkdownContainer"] p,
    .stTabs button[data-baseweb="tab"][aria-selected="true"] p {
        color: #1B4332 !important;
    }
    .stTabs button[data-baseweb="tab"] .trebol-tab-icon {
        font-size: 1.3em !important;
        line-height: 1 !important;
        vertical-align: middle !important;
        display: inline-block !important;
        opacity: 0.5 !important;
        transition: opacity 0.25s ease-in-out !important;
    }
    .stTabs button[data-baseweb="tab"][aria-selected="true"] .trebol-tab-icon {
        opacity: 1 !important;
    }

    /* 5. CAMBIO 2: Botones "+ AGREGAR NUEVA CATEGORÍA DE COSTOS" y "DE INGRESOS" */
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-costo),
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-ingreso) {
        display: none !important;
    }
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-costo) + div[data-testid="stElementContainer"] details,
    details[data-add-cat="costo"] {
        background-color: #FFF2EE !important;
        border: 2px solid #E07A5F !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 12px rgba(224, 122, 95, 0.14) !important;
        margin-bottom: 12px !important;
        overflow: hidden !important;
    }
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-costo) + div[data-testid="stElementContainer"] details > summary,
    details[data-add-cat="costo"] > summary {
        background-color: #FADBD8 !important;
        color: #922B21 !important;
        font-weight: 800 !important;
        padding: 12px 16px !important;
        border-radius: 14px !important;
        transition: background-color 0.2s ease !important;
    }
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-costo) + div[data-testid="stElementContainer"] details > summary:hover,
    details[data-add-cat="costo"] > summary:hover {
        background-color: #F5B7B1 !important;
    }
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-costo) + div[data-testid="stElementContainer"] details > summary p,
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-costo) + div[data-testid="stElementContainer"] details > summary span,
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-costo) + div[data-testid="stElementContainer"] details > summary svg,
    details[data-add-cat="costo"] > summary p,
    details[data-add-cat="costo"] > summary span,
    details[data-add-cat="costo"] > summary svg {
        color: #922B21 !important;
        fill: #922B21 !important;
        font-weight: 800 !important;
    }

    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-ingreso) + div[data-testid="stElementContainer"] details,
    details[data-add-cat="ingreso"] {
        background-color: #ECFDF5 !important;
        border: 2px solid #48C9B0 !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 12px rgba(72, 201, 176, 0.14) !important;
        margin-bottom: 12px !important;
        overflow: hidden !important;
    }
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-ingreso) + div[data-testid="stElementContainer"] details > summary,
    details[data-add-cat="ingreso"] > summary {
        background-color: #D1F2EB !important;
        color: #0E6251 !important;
        font-weight: 800 !important;
        padding: 12px 16px !important;
        border-radius: 14px !important;
        transition: background-color 0.2s ease !important;
    }
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-ingreso) + div[data-testid="stElementContainer"] details > summary:hover,
    details[data-add-cat="ingreso"] > summary:hover {
        background-color: #A3E4D7 !important;
    }
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-ingreso) + div[data-testid="stElementContainer"] details > summary p,
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-ingreso) + div[data-testid="stElementContainer"] details > summary span,
    div[data-testid="stElementContainer"]:has(> div > .hook-agregar-ingreso) + div[data-testid="stElementContainer"] details > summary svg,
    details[data-add-cat="ingreso"] > summary p,
    details[data-add-cat="ingreso"] > summary span,
    details[data-add-cat="ingreso"] > summary svg {
        color: #0E6251 !important;
        fill: #0E6251 !important;
        font-weight: 800 !important;
    }

    /* 6. Botones apilados ▲ y ▼ exclusivamente en la columna hija de flechas (sin afectar la columna principal) */
    div[data-testid="stElementContainer"]:has(> div > .flechas-cat-stack) {
        display: none !important;
    }
    div[data-testid="stColumn"]:not(:has([data-testid="stColumn"])):has(.flechas-cat-stack) > div > div[data-testid="stVerticalBlock"] {
        gap: 2px !important;
    }
    button.btn-flecha-cat,
    div[data-testid="stColumn"]:not(:has([data-testid="stColumn"])):has(.flechas-cat-stack) div[data-testid="stButton"] button {
        height: 21px !important;
        min-height: 21px !important;
        max-height: 21px !important;
        width: 28px !important;
        min-width: 28px !important;
        padding: 0px !important;
        margin: 0px !important;
        border-radius: 6px !important;
        line-height: 1 !important;
    }
    button.btn-flecha-cat p,
    div[data-testid="stColumn"]:not(:has([data-testid="stColumn"])):has(.flechas-cat-stack) div[data-testid="stButton"] button p {
        font-size: 0.68rem !important;
        line-height: 1 !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    /* 6b. Botón de eliminar categoría vacía: solo ícono 🗑️ a tamaño 1.5x con tooltip */
    div[data-testid="stElementContainer"]:has(> div > .hook-del-cat-vacia) {
        display: none !important;
    }
    button.btn-eliminar-cat-vacia,
    div[data-testid="stElementContainer"]:has(> div > .hook-del-cat-vacia) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 46px !important;
        min-width: 46px !important;
        max-width: 46px !important;
        height: 44px !important;
        min-height: 44px !important;
        padding: 0px !important;
        border-radius: 10px !important;
        background-color: #FFF5F5 !important;
        border: 1.5px solid #F5B7B1 !important;
        box-shadow: 0 2px 5px rgba(224, 122, 95, 0.08) !important;
        transition: all 0.2s ease-in-out !important;
    }
    button.btn-eliminar-cat-vacia:hover,
    div[data-testid="stElementContainer"]:has(> div > .hook-del-cat-vacia) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button:hover {
        background-color: #FADBD8 !important;
        border-color: #E07A5F !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 10px rgba(192, 57, 43, 0.14) !important;
    }
    button.btn-eliminar-cat-vacia p,
    button.btn-eliminar-cat-vacia span,
    div[data-testid="stElementContainer"]:has(> div > .hook-del-cat-vacia) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button p,
    div[data-testid="stElementContainer"]:has(> div > .hook-del-cat-vacia) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button span {
        font-size: 1.5rem !important;
        line-height: 1 !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    /* 7. Tarjetas KPI y encabezados de tabla originales */
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
        font-size: 0.95rem;
        font-weight: 600;
        opacity: 0.9;
        margin-top: 0.45rem;
    }
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

    /* Campos bloqueados (solo lectura) en la tabla de Mis Activos */
    div[data-testid="stTextInput"] input:disabled {
        color: #1F2937 !important;
        -webkit-text-fill-color: #1F2937 !important;
        background-color: #F3F4F6 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
        cursor: default !important;
    }

    /* Banner horizontal continuo dividido en dos paneles contiguos (32% Info izquierda + 68% Escena derecha) */
    .jardin-health-scene {
        position: relative;
        width: 100%;
        max-width: 100%;
        margin: 0 0 1.1rem 0;
        border-radius: 18px;
        border: 3px solid #22C55E;
        overflow: hidden;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
        min-height: 142px;
        display: flex;
        flex-direction: row;
        align-items: stretch;
        padding: 0;
        box-sizing: border-box;
    }
    .jardin-info-panel {
        flex: 0 0 32%;
        width: 32%;
        min-width: 280px;
        background: #FDFBF7;
        border-right: 2px solid #22C55E;
        padding: 8px 14px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-sizing: border-box;
        z-index: 2;
    }
    .jardin-scene-panel {
        flex: 1 1 68%;
        width: 68%;
        position: relative;
        overflow: hidden;
        min-height: 142px;
        box-sizing: border-box;
    }
    .jardin-scene-svg {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        z-index: 1;
        pointer-events: none;
    }
    .jardin-char-wrap {
        position: absolute;
        bottom: 4px;
        width: 82px;
        height: 112px;
        z-index: 3;
        pointer-events: none;
        overflow: visible !important;
        display: flex;
        align-items: flex-end;
        justify-content: center;
    }
    .jardin-char-left {
        left: 10px;
    }
    .jardin-char-right {
        left: 92px;
        right: auto;
    }
    /* Tooltip CSS sobre el campo "3. Cantidad que tenés" (hover en desktop + focus en móvil) */
    .jardin-cant-tooltip-wrap {
        position: relative !important;
    }
    .jardin-cant-tooltip-wrap::after {
        content: attr(data-tooltip);
        position: absolute;
        left: 0;
        bottom: calc(100% + 6px);
        width: max-content;
        max-width: 100%;
        background: #1F2937;
        color: #FFFFFF;
        font-size: 0.82rem;
        font-weight: 600;
        line-height: 1.35;
        padding: 8px 12px;
        border-radius: 10px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.22);
        pointer-events: none;
        opacity: 0;
        visibility: hidden;
        transform: translateY(4px);
        transition: opacity 0.2s ease, transform 0.2s ease, visibility 0.2s ease;
        z-index: 9999;
        white-space: normal;
    }
    .jardin-cant-tooltip-wrap:hover::after,
    .jardin-cant-tooltip-wrap:focus-within::after {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
    }
    .jardin-cant-tooltip-wrap [data-testid="stTooltipHoverTarget"] {
        pointer-events: none !important;
    }
    /* Flecha chevron (⌄) idéntica en forma, tamaño y color en todos los dropdowns de la app */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
        width: 20px !important;
        height: 20px !important;
        color: #1F2937 !important;
        fill: #1F2937 !important;
    }
    .jardin-char-svg {
        width: 100%;
        height: 100%;
        overflow: visible !important;
    }
    .jardin-status-box {
        margin-top: 5px;
        padding: 6px 10px;
        border-radius: 10px;
        border: 1.5px solid;
        width: 100%;
        box-sizing: border-box;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    }
    .jardin-health-bar-track {
        width: 100%;
        height: 6px;
        background: rgba(255, 255, 255, 0.78);
        border-radius: 999px;
        overflow: hidden;
        margin-top: 5px;
        border: 1px solid rgba(0,0,0,0.08);
    }
    .jardin-health-bar-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.5s ease;
    }

    @keyframes jardinKangaBounce {
        0%, 100% { transform: translateY(0px) scaleY(1); }
        45% { transform: translateY(-7px) scaleY(1.03); }
        55% { transform: translateY(-7px) scaleY(1.03); }
    }
    @keyframes jardinKoalaSway {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-3px) rotate(-2.5deg); }
    }
    @keyframes jardinTiredBreath {
        0%, 100% { transform: translateY(4px) scaleY(0.98); }
        50% { transform: translateY(7px) scaleY(0.95); }
    }
    @keyframes jardinSunFireSpin {
        0% { transform: rotate(0deg) scale(1); }
        50% { transform: translateY(-1px) rotate(180deg) scale(1.09); }
        100% { transform: rotate(360deg) scale(1); }
    }
    @keyframes jardinTumbleweedRoll1 {
        0% { transform: translate(115px, 141px) rotate(0deg); }
        25% { transform: translate(295px, 131px) rotate(180deg); }
        50% { transform: translate(475px, 142px) rotate(360deg); }
        75% { transform: translate(640px, 132px) rotate(540deg); }
        100% { transform: translate(780px, 141px) rotate(720deg); }
    }
    @keyframes jardinTumbleweedRoll2 {
        0% { transform: translate(190px, 145px) rotate(0deg); }
        50% { transform: translate(470px, 135px) rotate(360deg); }
        100% { transform: translate(730px, 144px) rotate(720deg); }
    }
    @keyframes jardinFlyBuzz1 {
        0% { transform: translate(65px, 78px) rotate(0deg); }
        25% { transform: translate(82px, 66px) rotate(25deg); }
        50% { transform: translate(98px, 80px) rotate(-15deg); }
        75% { transform: translate(76px, 90px) rotate(20deg); }
        100% { transform: translate(65px, 78px) rotate(0deg); }
    }
    @keyframes jardinFlyBuzz2 {
        0% { transform: translate(112px, 86px) rotate(0deg); }
        33% { transform: translate(96px, 72px) rotate(-25deg); }
        66% { transform: translate(124px, 74px) rotate(18deg); }
        100% { transform: translate(112px, 86px) rotate(0deg); }
    }
    @keyframes jardinFlyBuzz3 {
        0% { transform: translate(44px, 90px) rotate(0deg); }
        33% { transform: translate(58px, 76px) rotate(22deg); }
        66% { transform: translate(36px, 78px) rotate(-20deg); }
        100% { transform: translate(44px, 90px) rotate(0deg); }
    }

    .jardin-kanga-happy {
        animation: jardinKangaBounce 2.4s ease-in-out infinite;
        transform-origin: 82px 195px;
    }
    .jardin-koala-happy {
        animation: jardinKoalaSway 2.8s ease-in-out infinite;
        transform-origin: 80px 180px;
    }
    .jardin-animal-tired {
        animation: jardinTiredBreath 3.4s ease-in-out infinite;
        transform-origin: center bottom;
    }
    .jardin-sun-flames {
        animation: jardinSunFireSpin 7s linear infinite;
    }
    .jardin-tumbleweed-1 {
        animation: jardinTumbleweedRoll1 7.5s linear infinite;
    }
    .jardin-tumbleweed-2 {
        animation: jardinTumbleweedRoll2 9.5s linear infinite;
    }
    .jardin-fly-1 {
        animation: jardinFlyBuzz1 1.3s ease-in-out infinite;
    }
    .jardin-fly-2 {
        animation: jardinFlyBuzz2 1.1s ease-in-out infinite;
    }
    .jardin-fly-3 {
        animation: jardinFlyBuzz3 1.5s ease-in-out infinite;
    }

    @media (prefers-reduced-motion: reduce) {
        .jardin-kanga-happy,
        .jardin-koala-happy,
        .jardin-animal-tired,
        .jardin-sun-flames,
        .jardin-tumbleweed-1,
        .jardin-tumbleweed-2,
        .jardin-fly-1,
        .jardin-fly-2,
        .jardin-fly-3 {
            animation: none !important;
        }
    }

    @media (max-width: 768px) {
        .jardin-health-scene {
            flex-direction: column !important;
            width: 100% !important;
            max-width: 100% !important;
            min-height: auto !important;
        }
        .jardin-info-panel {
            flex: 1 1 100% !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            border-right: none !important;
            border-bottom: 2px solid #D1D5DB !important;
            padding: 10px 12px !important;
        }
        .jardin-scene-panel {
            flex: 1 1 100% !important;
            width: 100% !important;
            max-width: 100% !important;
            height: 145px !important;
            min-height: 145px !important;
        }
        .jardin-char-wrap {
            width: 72px !important;
            height: 100px !important;
            bottom: 4px !important;
        }
        .jardin-char-left {
            left: 6px !important;
        }
        .jardin-char-right {
            left: 76px !important;
            right: auto !important;
        }
        .block-container {
            max-width: 100% !important;
            padding-top: 3.2rem !important;
            padding-left: 0.65rem !important;
            padding-right: 0.65rem !important;
        }
        .kpi-value {
            font-size: 1.65rem !important;
        }
        .stTabs button[data-baseweb="tab"] {
            padding: 10px 18px !important;
            min-height: 48px !important;
        }
        .stTabs button[data-baseweb="tab"] [data-testid="stMarkdownContainer"] p {
            font-size: 1.05rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

datos = cargar_datos()

# ----------------- PERSISTENCIA DE SESIÓN DE 7 DÍAS CON TOKEN FIRMADO (SIN CONTRASEÑA) -----------------
def _obtener_secreto_token(datos):
    seg = datos.setdefault("seguridad", {})
    if not seg.get("token_secret"):
        seg["token_secret"] = hashlib.sha256(f"jardin_{random.random()}_{time.time()}".encode()).hexdigest()
        guardar_datos(datos)
    return str(seg["token_secret"])


def generar_token_sesion_7dias(datos, usuario):
    secreto = _obtener_secreto_token(datos)
    exp_ts = int(time.time()) + (7 * 86400)
    usr_clean = str(usuario or "mama").strip().lower()
    payload = f"{usr_clean}:{exp_ts}"
    firma = hmac.new(secreto.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    raw_token = f"{payload}:{firma}"
    token_b64 = base64.urlsafe_b64encode(raw_token.encode("utf-8")).decode("utf-8").rstrip("=")
    datos.setdefault("seguridad", {})["sesion_token_activo"] = token_b64
    datos["seguridad"]["sesion_exp_ts"] = exp_ts
    guardar_datos(datos)
    try:
        st.query_params["sesion"] = token_b64
    except Exception:
        pass
    return token_b64


def verificar_token_sesion_7dias(datos):
    secreto = _obtener_secreto_token(datos)
    seg = datos.get("seguridad", {})
    token_q = ""
    try:
        token_q = str(st.query_params.get("sesion", "") or "").strip()
    except Exception:
        pass
    token_candidato = token_q or str(seg.get("sesion_token_activo", "") or "").strip()
    if not token_candidato:
        return False
    try:
        pad = "=" * ((4 - len(token_candidato) % 4) % 4)
        decoded = base64.urlsafe_b64decode((token_candidato + pad).encode("utf-8")).decode("utf-8")
        usr_tok, exp_str, firma_tok = decoded.split(":")
        exp_ts = int(exp_str)
        if time.time() > exp_ts:
            return False
        payload = f"{usr_tok}:{exp_ts}"
        firma_esp = hmac.new(secreto.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        if hmac.compare_digest(firma_tok, firma_esp):
            if not token_q:
                try:
                    st.query_params["sesion"] = token_candidato
                except Exception:
                    pass
            return True
    except Exception:
        pass
    return False


def limpiar_token_sesion(datos):
    seg = datos.setdefault("seguridad", {})
    seg["sesion_token_activo"] = ""
    seg["sesion_exp_ts"] = 0
    guardar_datos(datos)
    try:
        if "sesion" in st.query_params:
            del st.query_params["sesion"]
    except Exception:
        pass


# ----------------- PANTALLA DE LOGIN Y RECUPERACIÓN SEGURA (REQ 6) -----------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = verificar_token_sesion_7dias(datos)
elif not st.session_state.autenticado:
    if verificar_token_sesion_7dias(datos):
        st.session_state.autenticado = True
if "login_fallido" not in st.session_state:
    st.session_state.login_fallido = False
if "mostrar_recuperacion" not in st.session_state:
    st.session_state.mostrar_recuperacion = False
if "codigo_recuperacion" not in st.session_state:
    st.session_state.codigo_recuperacion = None
if "codigo_verificado" not in st.session_state:
    st.session_state.codigo_verificado = False
if "mensaje_envio_rec" not in st.session_state:
    st.session_state.mensaje_envio_rec = ""
if "envio_exitoso_rec" not in st.session_state:
    st.session_state.envio_exitoso_rec = False

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
                    generar_token_sesion_7dias(datos, usuario_esperado)
                    st.session_state.autenticado = True
                    st.session_state.login_fallido = False
                    st.session_state.mostrar_recuperacion = False
                    st.session_state.codigo_recuperacion = None
                    st.session_state.codigo_verificado = False
                    st.rerun()
                else:
                    st.session_state.login_fallido = True
                    st.session_state.mostrar_recuperacion = True

        if st.session_state.login_fallido:
            st.error("Usuario o contraseña incorrectos.")

        if st.button("🔑 Me olvidé mi contraseña / Recuperar acceso", use_container_width=True):
            st.session_state.mostrar_recuperacion = not st.session_state.mostrar_recuperacion

        if st.session_state.mostrar_recuperacion:
            st.markdown("""
            <div style="background-color: #F3E8FF; border: 2px solid #C084FC; border-radius: 16px; padding: 16px; margin-top: 8px; margin-bottom: 10px;">
                <b style="color: #4A235A; font-size: 1.1rem;">🔐 Recuperación Segura de Contraseña</b><br>
                <span style="font-size: 0.95rem; color: #374151;">
                    ¿Cómo preferís recibir tu código privado de verificación de 6 dígitos?
                </span>
            </div>
            """, unsafe_allow_html=True)

            metodo_rec = st.radio(
                "Elegí el método de envío:",
                ["📧 Recibir código por Mail (Gmail)", "📲 Recibir código por WhatsApp / Celular"],
                horizontal=True
            )

            seg_data = datos.get("seguridad", {})
            usr_actual = seg_data.get("usuario", "mama")

            if metodo_rec.startswith("📧"):
                email_input = st.text_input(
                    "Ingresá tu correo electrónico registrado:",
                    value=seg_data.get("email_recuperacion", "julianherrero.jh@gmail.com"),
                    placeholder="ejemplo@gmail.com",
                    key="rec_email_input"
                )
                if st.button("📨 Enviar código a mi Mail", use_container_width=True, key="btn_send_mail"):
                    correo_limpio = email_input.strip().lower()
                    correo_reg = seg_data.get("email_recuperacion", "").strip().lower()
                    if not correo_limpio or "@" not in correo_limpio:
                        st.warning("Por favor ingresá una dirección de correo válida.")
                    elif correo_reg and correo_limpio != correo_reg:
                        st.error("El correo ingresado no coincide con el correo de recuperación registrado.")
                    else:
                        datos["seguridad"]["email_recuperacion"] = email_input.strip()
                        guardar_datos(datos)
                        nuevo_cod = f"{random.randint(100000, 999999)}"
                        st.session_state.codigo_recuperacion = nuevo_cod
                        st.session_state.codigo_verificado = False
                        st.session_state["input_verificar_codigo"] = ""
                        ok_env, msg_env = enviar_codigo_por_email(
                            email_input.strip(), nuevo_cod, usr_actual, datos
                        )
                        st.session_state.envio_exitoso_rec = ok_env
                        st.session_state.mensaje_envio_rec = msg_env
            else:
                tel_input = st.text_input(
                    "Ingresá tu número de celular registrado (con código de país):",
                    value=seg_data.get("telefono_recuperacion", "+61493680014"),
                    placeholder="Ej: +61493680014 o +549381...",
                    key="rec_tel_input"
                )
                if st.button("📲 Enviar código por WhatsApp / Celular", use_container_width=True, key="btn_send_wa"):
                    limpio_tel = "".join(ch for ch in tel_input if ch.isdigit())
                    reg_tel = "".join(ch for ch in seg_data.get("telefono_recuperacion", "") if ch.isdigit())
                    if len(limpio_tel) < 7:
                        st.warning("Por favor ingresá un número de celular válido.")
                    elif reg_tel and limpio_tel != reg_tel:
                        st.error("El número ingresado no coincide con el celular de recuperación registrado.")
                    else:
                        datos["seguridad"]["telefono_recuperacion"] = tel_input.strip()
                        guardar_datos(datos)
                        nuevo_cod = f"{random.randint(100000, 999999)}"
                        st.session_state.codigo_recuperacion = nuevo_cod
                        st.session_state.codigo_verificado = False
                        st.session_state["input_verificar_codigo"] = ""
                        ok_env, msg_env = enviar_codigo_por_celular(
                            limpio_tel, nuevo_cod, usr_actual, datos
                        )
                        st.session_state.envio_exitoso_rec = ok_env
                        st.session_state.mensaje_envio_rec = msg_env

            # Mostrar estado del envío (NUNCA muestra el código en la pantalla)
            if st.session_state.codigo_recuperacion:
                if st.session_state.envio_exitoso_rec:
                    st.info(st.session_state.mensaje_envio_rec)
                else:
                    st.warning(st.session_state.mensaje_envio_rec)

                col_v1, col_v2 = st.columns([2.2, 1.2])
                with col_v1:
                    cod_ingresado = st.text_input(
                        "Ingresá el código de 6 dígitos que recibiste:",
                        value="",
                        placeholder="Escribí los 6 números...",
                        max_chars=6,
                        key="input_verificar_codigo"
                    )
                with col_v2:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    btn_validar = st.button("✅ Validar Código", use_container_width=True)

                if btn_validar or (len(cod_ingresado.strip()) == 6):
                    if cod_ingresado.strip() == st.session_state.codigo_recuperacion:
                        st.session_state.codigo_verificado = True
                    elif btn_validar:
                        st.error("❌ El código ingresado no es correcto. Revisá el mensaje recibido.")

                if st.session_state.codigo_verificado:
                    st.success(f"✅ Código verificado correctamente. Tu usuario es: **{usr_actual}**")
                    nueva_pass = st.text_input(
                        "Escribí tu nueva contraseña:",
                        type="password",
                        placeholder="Nueva contraseña...",
                        key="input_nueva_pass_rec"
                    )
                    if st.button("💾 Guardar nueva contraseña e Ingresar", use_container_width=True):
                        if nueva_pass.strip():
                            datos["seguridad"]["password_actual"] = nueva_pass.strip()
                            if nueva_pass.strip() not in datos["seguridad"]["passwords_validas"]:
                                datos["seguridad"]["passwords_validas"].append(nueva_pass.strip())
                            guardar_datos(datos)
                            generar_token_sesion_7dias(datos, usr_actual)
                            st.session_state.autenticado = True
                            st.session_state.login_fallido = False
                            st.session_state.mostrar_recuperacion = False
                            st.session_state.codigo_recuperacion = None
                            st.session_state.codigo_verificado = False
                            st.rerun()
                        else:
                            st.warning("Por favor escribí una nueva contraseña.")
    activar_interactividad_avanzada()
    st.stop()


# ----------------- APP PRINCIPAL -----------------
tickers_acc = [
    str(inv.get("simbolo", "AAPL")).split(" ")[0].upper().strip()
    for inv in datos.get("inversiones", [])
    if normalizar_tipo_activo_inv(inv.get("tipo")) in ["Acciones", "FCI", "Otros"]
]

tickers_cri = [
    str(inv.get("simbolo", "BTC")).split(" ")[0].upper().strip()
    for inv in datos.get("inversiones", [])
    if normalizar_tipo_activo_inv(inv.get("tipo")) == "Cryptos"
]

tickers_bon = [
    str(inv.get("simbolo", "AL30")).split(" ")[0].upper().strip()
    for inv in datos.get("inversiones", [])
    if normalizar_tipo_activo_inv(inv.get("tipo")) == "Bonos"
]

cotizaciones = obtener_cotizaciones(tuple(tickers_acc), tuple(tickers_cri), tuple(tickers_bon))
dolar_b = cotizaciones["dolar_blue"]

# ----------------- SIDEBAR, HORA AUSTRALIA/SYDNEY, ACTUALIZAR Y CIERRE DE SESIÓN -----------------
tz_sydney = ZoneInfo("Australia/Sydney")
ahora = datetime.now(tz_sydney)
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
    limpiar_token_sesion(datos)
    st.session_state.confirmar_cierre = False
    st.session_state.autenticado = False


with st.sidebar:
    st.markdown(
        "<h2 style='color: #2D6A4F;'>🌿 Mi Panel</h2>",
        unsafe_allow_html=True
    )
    st.markdown(f"🗓️ **{fecha_hora_texto}**")
    if st.button("🔄 Actualizar", key="btn_sidebar_actualizar", use_container_width=True):
        st.cache_data.clear()
        for k_reset in [
            "inv_detalle_manual_acc",
            "inv_detalle_manual_cri",
            "inv_detalle_manual_bon",
            "inv_detalle_manual_fci",
            "inv_detalle_manual_otros",
            "inv_ubicacion_nueva_manual"
        ]:
            st.session_state.pop(k_reset, None)
        st.rerun()
    st.markdown("---")
    st.markdown(f"💵 **Dólar Blue:** `{dolar_b:,.0f} ARS`")
    st.markdown(f"🪙 **Bitcoin:** `{cotizaciones['BTC']:,.0f} USD`")
    st.markdown("---")

    with st.expander("🔐 Mis Datos de Recuperación"):
        seg_actual = datos.get("seguridad", {})
        em_conf = st.text_input(
            "Correo de recuperación:",
            value=seg_actual.get("email_recuperacion", "julianherrero.jh@gmail.com"),
            key="side_email_rec"
        )
        tel_conf = st.text_input(
            "Celular de recuperación:",
            value=seg_actual.get("telefono_recuperacion", "+61493680014"),
            key="side_tel_rec"
        )
        smtp_conf = st.text_input(
            "Clave App Gmail (opcional p/ envío directo):",
            value=seg_actual.get("smtp_app_password", ""),
            help="Contraseña de aplicación de 16 letras de Google (opcional).",
            key="side_smtp_rec"
        )
        wa_conf = st.text_input(
            "API Key WhatsApp CallMeBot (opcional):",
            value=seg_actual.get("whatsapp_apikey", ""),
            help="Enviá 'I allow callmebot to send me messages' al +34 644 52 74 88 por WhatsApp para obtener tu clave gratis.",
            key="side_wa_rec"
        )
        if (
            em_conf != seg_actual.get("email_recuperacion", "")
            or tel_conf != seg_actual.get("telefono_recuperacion", "")
            or smtp_conf != seg_actual.get("smtp_app_password", "")
            or wa_conf != seg_actual.get("whatsapp_apikey", "")
        ):
            datos["seguridad"]["email_recuperacion"] = em_conf.strip()
            datos["seguridad"]["telefono_recuperacion"] = tel_conf.strip()
            datos["seguridad"]["smtp_app_password"] = smtp_conf.strip()
            datos["seguridad"]["whatsapp_apikey"] = wa_conf.strip()
            guardar_datos(datos)
            st.toast("✅ Datos de recuperación actualizados")

    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        registrar_snapshot_cierre(datos, dolar_b, cotizaciones)
        st.session_state.confirmar_cierre = True
        st.rerun()

# Cuadro simplificado al apretar Cerrar Sesión (Req 4)
if st.session_state.confirmar_cierre:
    st.markdown("""
    <div style="background: linear-gradient(145deg, #EAF6EE 0%, #F3E8FF 100%);
                border: 2px solid #7E22CE; border-radius: 18px; padding: 20px; margin-bottom: 16px;
                box-shadow: 0 8px 24px rgba(126, 34, 206, 0.14);">
        <h3 style="color: #1B4332; margin-top: 0; margin-bottom: 8px;">✅ ¡Tus cambios ya se guardaron automáticamente en la plataforma!</h3>
        <p style="font-size: 1.15rem; color: #374151; font-weight: 700; margin-bottom: 0;">
            ¿Deseás descargar una planilla con tus cambios antes de salir?
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_dl1, col_dl2 = st.columns(2, gap="medium")
    with col_dl1:
        st.download_button(
            label="📥 SÍ, DESCARGAR Y CERRAR",
            data=generar_excel_bytes(datos, dolar_b, cotizaciones),
            file_name=f"Finanzas_Mama_{stamp_archivo}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            on_click=finalizar_sesion
        )
    with col_dl2:
        if st.button("🚪 NO, CERRAR", use_container_width=True):
            finalizar_sesion()
            st.rerun()


# ----------------- CALLBACKS DE GUARDADO AUTOMÁTICO -----------------
def sync_orden_costos_cb():
    raw = st.session_state.get("sync_orden_costos_input", "")
    if not raw:
        return
    try:
        parsed = json.loads(raw)
        nuevo_orden = parsed.get("orden", []) if isinstance(parsed, dict) else parsed
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
        parsed = json.loads(raw)
        nuevo_orden = parsed.get("orden", []) if isinstance(parsed, dict) else parsed
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
    nuevo_icono = st.session_state.get(f"edit_ico_c_{nombre_viejo}")
    nuevo_nombre = st.session_state.get(f"edit_nom_c_{nombre_viejo}", "").strip()
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
    nuevo_icono = st.session_state.get(f"edit_ico_i_{nombre_viejo_i}")
    nuevo_nombre = st.session_state.get(f"edit_nom_i_{nombre_viejo_i}", "").strip()
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


def mover_categoria_costo(idx_actual, direccion):
    cats = datos.get("categorias_costos", [])
    nuevo_idx = idx_actual + direccion
    if 0 <= idx_actual < len(cats) and 0 <= nuevo_idx < len(cats):
        cats[idx_actual], cats[nuevo_idx] = cats[nuevo_idx], cats[idx_actual]
        datos["categorias_costos"] = cats
        guardar_datos(datos)


def mover_categoria_ingreso(idx_actual, direccion):
    cats = datos.get("categorias_ingresos", [])
    nuevo_idx = idx_actual + direccion
    if 0 <= idx_actual < len(cats) and 0 <= nuevo_idx < len(cats):
        cats[idx_actual], cats[nuevo_idx] = cats[nuevo_idx], cats[idx_actual]
        datos["categorias_ingresos"] = cats
        guardar_datos(datos)


# ----------------- PESTAÑAS PRINCIPALES CON 🍀 (CAMBIO 1) -----------------
pestana1, pestana2 = st.tabs([
    "🍀 COSTOS E INGRESOS",
    "🍀 PATRIMONIO TOTAL"
])

# =========================================================================
# =========================== PESTAÑA 1 ===================================
# =========================================================================
with pestana1:
    total_items_costos = len(datos["costos"])
    costos_activos = [c for c in datos["costos"] if c.get("activo", True)]
    total_costos = sum(c["monto"] for c in costos_activos)

    total_items_ingresos = len(datos["ingresos"])
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

    # Tarjetas KPI con formato "XX activos de YY" (Req 7)
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3, gap="medium")
    with col_kpi1:
        st.markdown(f"""
        <div class="metric-card metric-card-costo">
            <div class="kpi-title">Costo Mensual</div>
            <div class="kpi-value">{total_costos:,.0f} ARS</div>
            <div class="kpi-usd">≈ {costos_usd:,.2f} USD</div>
            <div class="kpi-sub">{len(costos_activos)} activos de {total_items_costos}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
        <div class="metric-card metric-card-ingreso">
            <div class="kpi-title">Ingreso Mensual</div>
            <div class="kpi-value">{total_ingresos:,.0f} ARS</div>
            <div class="kpi-usd">≈ {ingresos_usd:,.2f} USD</div>
            <div class="kpi-sub">{len(ingresos_activos)} activos de {total_items_ingresos}</div>
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

    col_izq, col_der = st.columns(2, gap="medium")

    # ---------------- COSTOS ----------------
    with col_izq:
        st.markdown("<h3 style='color: #A04000; margin-bottom: 6px;'>📉 Mis Costos Mensuales</h3>", unsafe_allow_html=True)
        st.markdown("<div class='hook-agregar-costo' style='display:none;'></div>", unsafe_allow_html=True)

        with st.expander("➕ AGREGAR NUEVA CATEGORÍA DE COSTOS"):
            c_nc1, c_nc2 = st.columns([3.6, 0.45])
            with c_nc1:
                st.text_input(
                    "Nombre de la Categoría (ej. IMPUESTOS, AUTO, SALUD)",
                    placeholder="Escribí el nombre de la categoría...",
                    key="input_nueva_cat_costo",
                    on_change=crear_categoria_costo_auto
                )
            with c_nc2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("+", key="btn_crear_cat_c", help="Agregar categoría"):
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

            titulo_cat = f"{icono_cat} **{cat_nombre}** — subt= **{sub_ars:,.0f} ARS** ({sub_usd:,.1f} USD)"
            col_exp_c, col_arrows_c = st.columns([0.94, 0.06], gap="small")
            with col_arrows_c:
                st.markdown("<div class='flechas-cat-stack'></div>", unsafe_allow_html=True)
                st.button(
                    "▲",
                    key=f"btn_up_c_{cat_nombre}",
                    disabled=(cat_idx == 0),
                    help=f"Subir {cat_nombre}",
                    on_click=mover_categoria_costo,
                    args=(cat_idx, -1)
                )
                st.button(
                    "▼",
                    key=f"btn_down_c_{cat_nombre}",
                    disabled=(cat_idx == len(datos["categorias_costos"]) - 1),
                    help=f"Bajar {cat_nombre}",
                    on_click=mover_categoria_costo,
                    args=(cat_idx, 1)
                )
            with col_exp_c.expander(titulo_cat, expanded=False):
                editar_cat = st.checkbox(
                    "✏️ Editar nombre o ícono de la categoría",
                    key=f"chk_edit_c_{cat_nombre}"
                )
                if editar_cat:
                    opciones_ico = list(dict.fromkeys([icono_cat] + ICONOS_DISPONIBLES))
                    ec1, ec2 = st.columns([1.0, 3.0])
                    with ec1:
                        st.selectbox(
                            "Ícono",
                            options=opciones_ico,
                            index=0,
                            key=f"edit_ico_c_{cat_nombre}",
                            label_visibility="collapsed",
                            on_change=auto_editar_cat_costo,
                            args=(cat_idx, cat_nombre)
                        )
                    with ec2:
                        st.text_input(
                            "Nombre Categoría",
                            value=cat_nombre,
                            key=f"edit_nom_c_{cat_nombre}",
                            label_visibility="collapsed",
                            on_change=auto_editar_cat_costo,
                            args=(cat_idx, cat_nombre)
                        )

                if items_cat:
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

                with st.form(f"form_sub_costo_{cat_nombre}", clear_on_submit=True):
                    sc1, sc2, sc3 = st.columns([2.55, 1.55, 0.5])
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
                        btn_sub_c = st.form_submit_button("+", help="Agregar categoría")
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
                    st.markdown("<div class='hook-del-cat-vacia'></div>", unsafe_allow_html=True)
                    if st.button(
                        "🗑️",
                        key=f"del_cat_c_{cat_nombre}",
                        help="Eliminar categoría"
                    ):
                        datos["categorias_costos"].remove(cat_nombre)
                        guardar_datos(datos)
                        st.rerun()

        if costos_modificados:
            guardar_datos(datos)
            st.rerun()

    # ---------------- INGRESOS ----------------
    with col_der:
        st.markdown("<h3 style='color: #117864; margin-bottom: 6px;'>📈 Mis Ingresos Mensuales</h3>", unsafe_allow_html=True)
        st.markdown("<div class='hook-agregar-ingreso' style='display:none;'></div>", unsafe_allow_html=True)

        with st.expander("➕ AGREGAR NUEVA CATEGORÍA DE INGRESOS"):
            c_ni1, c_ni2 = st.columns([3.6, 0.45])
            with c_ni1:
                st.text_input(
                    "Nombre de la Categoría (ej. Trabajo, Consultorio, Otros)",
                    placeholder="Escribí el nombre de la categoría...",
                    key="input_nueva_cat_ingreso",
                    on_change=crear_categoria_ingreso_auto
                )
            with c_ni2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("+", key="btn_crear_cat_i", help="Agregar categoría"):
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

            titulo_cat_i = f"{icono_cat_i} **{cat_nombre_i}** — subt= **{sub_ars_i:,.0f} ARS** ({sub_usd_i:,.1f} USD)"
            col_exp_i, col_arrows_i = st.columns([0.94, 0.06], gap="small")
            with col_arrows_i:
                st.markdown("<div class='flechas-cat-stack'></div>", unsafe_allow_html=True)
                st.button(
                    "▲",
                    key=f"btn_up_i_{cat_nombre_i}",
                    disabled=(cat_idx_i == 0),
                    help=f"Subir {cat_nombre_i}",
                    on_click=mover_categoria_ingreso,
                    args=(cat_idx_i, -1)
                )
                st.button(
                    "▼",
                    key=f"btn_down_i_{cat_nombre_i}",
                    disabled=(cat_idx_i == len(datos["categorias_ingresos"]) - 1),
                    help=f"Bajar {cat_nombre_i}",
                    on_click=mover_categoria_ingreso,
                    args=(cat_idx_i, 1)
                )
            with col_exp_i.expander(titulo_cat_i, expanded=False):
                editar_cat_i = st.checkbox(
                    "✏️ Editar nombre o ícono de la categoría",
                    key=f"chk_edit_i_{cat_nombre_i}"
                )
                if editar_cat_i:
                    opciones_ico_i = list(dict.fromkeys([icono_cat_i] + ICONOS_DISPONIBLES))
                    ei1, ei2 = st.columns([1.0, 3.0])
                    with ei1:
                        st.selectbox(
                            "Ícono",
                            options=opciones_ico_i,
                            index=0,
                            key=f"edit_ico_i_{cat_nombre_i}",
                            label_visibility="collapsed",
                            on_change=auto_editar_cat_ingreso,
                            args=(cat_idx_i, cat_nombre_i)
                        )
                    with ei2:
                        st.text_input(
                            "Nombre Categoría",
                            value=cat_nombre_i,
                            key=f"edit_nom_i_{cat_nombre_i}",
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

                with st.form(f"form_sub_ing_{cat_nombre_i}", clear_on_submit=True):
                    si1, si2, si3 = st.columns([2.55, 1.55, 0.5])
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
                        btn_sub_i = st.form_submit_button("+", help="Agregar categoría")
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
                    st.markdown("<div class='hook-del-cat-vacia'></div>", unsafe_allow_html=True)
                    if st.button(
                        "🗑️",
                        key=f"del_cat_i_{cat_nombre_i}",
                        help="Eliminar categoría"
                    ):
                        datos["categorias_ingresos"].remove(cat_nombre_i)
                        guardar_datos(datos)
                        st.rerun()

        if ingresos_modificados:
            guardar_datos(datos)
            st.rerun()

    st.markdown("---")

    st.markdown(
        "<h3 style='color: #5B4B8A;'>📊 Gráficos y Tablas</h3>",
        unsafe_allow_html=True
    )
    modo_grafico = st.radio(
        "Modo de gráficos",
        ["Por Categoría (Subtotales)", "Detallado por cada Subcategoría"],
        horizontal=True,
        label_visibility="collapsed"
    )

    proporcion_cols_grafico = [1.4, 0.9] if modo_grafico.startswith("Por Categoría") else [1, 1]
    col_chart_c, col_chart_i = st.columns(proporcion_cols_grafico, gap="medium")

    with col_chart_c:
        st.markdown(
            "<h4 style='color: #A04000; text-align: center;'>Distribución de Costos</h4>",
            unsafe_allow_html=True
        )
        if costos_activos and total_costos > 0:
            df_c_raw = pd.DataFrame(costos_activos)
            if modo_grafico.startswith("Por Categoría"):
                df_pie_c = df_c_raw.groupby("grupo", as_index=False)["monto"].sum().sort_values(by="monto", ascending=False)
                col_label_c = "grupo"
                titulo_col_c = "Categoría"
                fig_c = crear_torta_2d(df_pie_c, "monto", col_label_c, tamano="grande", usar_minusculas=True)
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
            "<h4 style='color: #117864; text-align: center;'>Distribución de Ingresos</h4>",
            unsafe_allow_html=True
        )
        if ingresos_activos and total_ingresos > 0:
            df_i_raw = pd.DataFrame(ingresos_activos)
            if modo_grafico.startswith("Por Categoría"):
                df_pie_i = df_i_raw.groupby("grupo", as_index=False)["monto"].sum().sort_values(by="monto", ascending=False)
                col_label_i = "grupo"
                titulo_col_i = "Categoría"
                fig_i = crear_torta_2d(df_pie_i, "monto", col_label_i, tamano="chico", usar_minusculas=True)
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
    if reparar_inversiones_corruptas(inversiones):
        guardar_datos(datos)

    filas = []
    advertencias_precios = []

    for inv in inversiones:
        cant = float(inv.get("cantidad", 0))
        tipo = normalizar_tipo_activo_inv(inv.get("tipo", "Pesos ARS"))
        activo_nom = str(inv.get("activo", tipo)).strip()
        if activo_nom in ["Dólar Billete", "A - Dólar Billete"]:
            activo_nom = "Dólares USD"

        simbolo = str(inv.get("simbolo", "")).upper().strip().split(" ")[0]
        if tipo in ["Cryptos", "Acciones", "Bonos"]:
            det_t = activo_nom.split(" ")[0].upper()
            if det_t and det_t not in ["USD", "ARS"]:
                simbolo = det_t

        esta_activo = inv.get("activo_inv", True)
        precio_valido = True

        # Pesos ARS y Dólares USD jamás se multiplican por ningún precio de activo
        if tipo == "Pesos ARS":
            precio_unit_ars = 1.0
            val_ars = cant
            val_usd = cant / dolar_b if dolar_b > 0 else 0.0
            cotiz_actual_str = f"1 USD = {dolar_b:,.0f} ARS"
        elif tipo == "Dólares USD":
            precio_unit_ars = dolar_b
            val_usd = cant
            val_ars = cant * dolar_b
            cotiz_actual_str = f"1 USD = {dolar_b:,.0f} ARS"
        elif tipo == "Cryptos":
            precio_u = cotizaciones.get(simbolo)
            if precio_u is None or float(precio_u) <= 0:
                precio_valido = False
                precio_unit_ars = 0.0
                val_usd = 0.0
                val_ars = 0.0
                cotiz_actual_str = f"⚠️ Sin cotización para {simbolo}"
                if esta_activo:
                    advertencias_precios.append(f"{activo_nom} ({tipo})")
            else:
                precio_u = float(precio_u)
                precio_unit_ars = precio_u * dolar_b
                val_usd = cant * precio_u
                val_ars = cant * precio_unit_ars
                cotiz_actual_str = f"1 {simbolo} = {precio_u:,.2f} USD ({precio_unit_ars:,.0f} ARS)"
        elif tipo == "Acciones":
            precio_u = cotizaciones.get(simbolo)
            if precio_u is None or float(precio_u) <= 0:
                precio_valido = False
                precio_unit_ars = 0.0
                val_usd = 0.0
                val_ars = 0.0
                cotiz_actual_str = f"⚠️ Sin cotización para {simbolo}"
                if esta_activo:
                    advertencias_precios.append(f"{activo_nom} ({tipo})")
            else:
                precio_u = float(precio_u)
                precio_unit_ars = precio_u * dolar_b
                val_usd = cant * precio_u
                val_ars = cant * precio_unit_ars
                cotiz_actual_str = f"1 {simbolo} = {precio_u:,.2f} USD ({precio_unit_ars:,.0f} ARS)"
        elif tipo == "Bonos":
            precio_bono = cotizaciones.get(f"BONO_ARS_{simbolo}", inv.get("precio_unitario_ars"))
            if precio_bono is None or float(precio_bono) <= 0:
                precio_valido = False
                precio_unit_ars = 0.0
                val_ars = 0.0
                val_usd = 0.0
                cotiz_actual_str = f"⚠️ Sin cotización para {simbolo}"
                if esta_activo:
                    advertencias_precios.append(f"{activo_nom} ({tipo})")
            else:
                precio_unit_ars = float(precio_bono)
                val_ars = cant * precio_unit_ars
                val_usd = val_ars / dolar_b if dolar_b > 0 else 0.0
                cotiz_actual_str = f"1 {simbolo} = {precio_unit_ars:,.0f} ARS ({precio_unit_ars / dolar_b if dolar_b > 0 else 0:,.2f} USD)"
        else:
            # FCI u Otros
            if simbolo and simbolo not in ["ARS", "USD"] and simbolo in cotizaciones and float(cotizaciones[simbolo]) > 0:
                precio_unit_ars = float(cotizaciones[simbolo]) * dolar_b
                cotiz_actual_str = f"1 {simbolo} = {precio_unit_ars:,.0f} ARS"
            elif f"BONO_ARS_{simbolo}" in cotizaciones and float(cotizaciones[f"BONO_ARS_{simbolo}"]) > 0:
                precio_unit_ars = float(cotizaciones[f"BONO_ARS_{simbolo}"])
                cotiz_actual_str = f"1 {simbolo} = {precio_unit_ars:,.0f} ARS"
            else:
                precio_unit_ars = float(inv.get("precio_unitario_ars", 1.0))
                if precio_unit_ars <= 0:
                    precio_valido = False
                    precio_unit_ars = 0.0
                    cotiz_actual_str = f"⚠️ Precio inválido"
                    if esta_activo:
                        advertencias_precios.append(f"{activo_nom} ({tipo})")
                else:
                    cotiz_actual_str = f"1 ud. = {precio_unit_ars:,.0f} ARS" if precio_unit_ars != 1.0 else f"1 USD = {dolar_b:,.0f} ARS"
            val_ars = cant * precio_unit_ars if precio_valido else 0.0
            val_usd = (val_ars / dolar_b if dolar_b > 0 else 0.0) if precio_valido else 0.0

        filas.append({
            "Tipo": tipo,
            "Activo": activo_nom,
            "Simbolo": simbolo,
            "Plataforma": inv.get("plataforma", ""),
            "Cantidad_Num": cant,
            "Cantidad": formatear_cant(cant),
            "Precio_Unit_ARS": precio_unit_ars,
            "Precio_Valido": precio_valido,
            "Cotización Actual": cotiz_actual_str,
            "Valor en ARS": val_ars,
            "Valor en USD": val_usd,
            "Activo_Flag": esta_activo
        })

    if advertencias_precios:
        st.warning(
            "⚠️ No se encontró cotización válida para: "
            + ", ".join(advertencias_precios)
            + ". No se multiplicó su valor para evitar distorsionar el Patrimonio Total."
        )

    df_inv_todos = pd.DataFrame(filas)
    if not df_inv_todos.empty:
        df_inv_activos = df_inv_todos[df_inv_todos["Activo_Flag"] == True]
    else:
        df_inv_activos = pd.DataFrame()

    total_patrimonio_ars = df_inv_activos["Valor en ARS"].sum() if not df_inv_activos.empty else 0
    total_patrimonio_usd = df_inv_activos["Valor en USD"].sum() if not df_inv_activos.empty else 0

    # Calcular ingresos y costos mensuales activos en ARS en vivo desde la pestaña "Costos e Ingresos"
    costos_activos_live = [c for c in datos.get("costos", []) if c.get("activo", True)]
    ingresos_activos_live = [i for i in datos.get("ingresos", []) if i.get("activo", True)]

    costo_mensual_vivir_ars = 0.0
    hay_costo_usd = False
    for c_item in costos_activos_live:
        monto_c = float(c_item.get("monto", 0))
        moneda_c = str(c_item.get("moneda", "ARS")).upper().strip()
        if moneda_c == "USD":
            hay_costo_usd = True
            costo_mensual_vivir_ars += monto_c * dolar_b if dolar_b and dolar_b > 0 else 0.0
        else:
            costo_mensual_vivir_ars += monto_c

    ingreso_mensual_vivir_ars = 0.0
    hay_ingreso_usd = False
    for i_item in ingresos_activos_live:
        monto_i = float(i_item.get("monto", 0))
        moneda_i = str(i_item.get("moneda", "ARS")).upper().strip()
        if moneda_i == "USD":
            hay_ingreso_usd = True
            ingreso_mensual_vivir_ars += monto_i * dolar_b if dolar_b and dolar_b > 0 else 0.0
        else:
            ingreso_mensual_vivir_ars += monto_i

    hay_activo_usd = any(
        inv.get("activo_inv", True) and normalizar_tipo_activo_inv(inv.get("tipo")) in ["Dólares USD", "Cryptos", "Acciones"]
        for inv in inversiones
    )
    hay_moneda_ext = hay_costo_usd or hay_ingreso_usd or hay_activo_usd
    datos_cyi_faltantes = (not costos_activos_live) or (not ingresos_activos_live)

    if not dolar_b or dolar_b <= 0:
        dolar_b = st.number_input(
            "Tipo de cambio USD a ARS (requerido para unificar moneda en ARS):",
            min_value=1.0,
            value=1575.0,
            step=10.0,
            key="input_tasa_cambio_fallback"
        )

    html_panel_salud = construir_html_panel_patrimonio(
        total_patrimonio_ars=total_patrimonio_ars,
        total_patrimonio_usd=total_patrimonio_usd,
        cant_activos_contemplados=len(df_inv_activos),
        cant_activos_totales=len(inversiones),
        ingreso_mensual_ars=ingreso_mensual_vivir_ars,
        costo_mensual_ars=costo_mensual_vivir_ars,
        dolar_b=dolar_b,
        hay_moneda_extranjera=hay_moneda_ext,
        datos_faltantes=datos_cyi_faltantes
    )
    st.markdown(html_panel_salud, unsafe_allow_html=True)

    st.markdown("---")

    col_inv_izq, col_inv_der = st.columns([1.05, 1.85], gap="medium")

    # ---------------- AGREGAR ACTIVO ----------------
    with col_inv_izq:
        st.markdown(
            "<h3 style='color: #5B4B8A;'>➕ Agregar Activo</h3>",
            unsafe_allow_html=True
        )
        opciones_tipo = [
            "A - Pesos ARS",
            "B - Dólares USD",
            "C - Acciones",
            "D - Cryptos",
            "E - Bonos",
            "F - FCI",
            "G - Otros"
        ]

        # Garantizar lista de ubicaciones nunca vacía con las 8 ubicaciones por defecto
        opciones_ubicacion = [str(u).strip() for u in datos.get("ubicaciones_guardadas", []) if str(u).strip()]
        for ub_def in UBICACIONES_BASE:
            if not any(ub_def.lower() == u.lower() for u in opciones_ubicacion):
                opciones_ubicacion.append(ub_def)
        if not opciones_ubicacion:
            opciones_ubicacion = list(UBICACIONES_BASE)
        datos["ubicaciones_guardadas"] = opciones_ubicacion

        ult_sel = datos.setdefault("ultimas_selecciones_inv", {
            "tipo": "A - Pesos ARS",
            "accion": "AAPL (Apple)",
            "cripto": "BTC (Bitcoin)",
            "bono": "AL30 (Bonar 2030 Ley Arg.)",
            "ubicacion": opciones_ubicacion[0]
        })

        if "_pending_inv_widget_sync" in st.session_state:
            for k_sync, v_sync in st.session_state.pop("_pending_inv_widget_sync").items():
                st.session_state[k_sync] = v_sync

        tipo_guardado = ult_sel.get("tipo", "A - Pesos ARS")
        if tipo_guardado not in opciones_tipo:
            tipo_guardado = "A - Pesos ARS"

        if "inv_tipo_select" not in st.session_state or st.session_state["inv_tipo_select"] not in opciones_tipo:
            st.session_state["inv_tipo_select"] = tipo_guardado

        def on_cambio_tipo_inv():
            datos.setdefault("ultimas_selecciones_inv", {})["tipo"] = st.session_state["inv_tipo_select"]
            guardar_datos(datos)

        tipo_elegido = st.selectbox(
            "1. Tipo de Activo",
            opciones_tipo,
            key="inv_tipo_select",
            on_change=on_cambio_tipo_inv
        )

        # Contenedor aislado para los selectores específicos del tipo de activo
        contenedor_selector_especifico = st.container()
        simbolo_elegido = "ARS"
        detalle_manual = ""

        with contenedor_selector_especifico:
            if tipo_elegido == "C - Acciones":
                lista_acc_actual = datos.get("acciones_guardadas", list(ACCIONES_100_BASE))
                acc_recordada = ult_sel.get("accion", lista_acc_actual[0])
                if acc_recordada not in lista_acc_actual:
                    coinc_acc = [a for a in lista_acc_actual if a.split(" ")[0].upper() == str(acc_recordada).split(" ")[0].upper()]
                    acc_recordada = coinc_acc[0] if coinc_acc else lista_acc_actual[0]

                if "inv_accion_select" not in st.session_state or st.session_state["inv_accion_select"] not in lista_acc_actual:
                    st.session_state["inv_accion_select"] = acc_recordada

                def on_cambio_accion_inv():
                    datos.setdefault("ultimas_selecciones_inv", {})["accion"] = st.session_state["inv_accion_select"]
                    guardar_datos(datos)

                simbolo_elegido = st.selectbox(
                    "Seleccioná la Acción de la lista",
                    lista_acc_actual,
                    key="inv_accion_select",
                    on_change=on_cambio_accion_inv
                )
                detalle_manual = st.text_input(
                    "¿No está en la lista? Escribila a mano acá y quedará grabada (ej. DIS, V):",
                    key="inv_detalle_manual_acc"
                )
            elif tipo_elegido == "D - Cryptos":
                lista_cri_actual = datos.get("criptos_guardadas", list(CRIPTOS_100_BASE))
                cri_recordada = ult_sel.get("cripto", lista_cri_actual[0])
                if cri_recordada not in lista_cri_actual:
                    coinc_cri = [c for c in lista_cri_actual if c.split(" ")[0].upper() == str(cri_recordada).split(" ")[0].upper()]
                    cri_recordada = coinc_cri[0] if coinc_cri else lista_cri_actual[0]

                if "inv_cripto_select" not in st.session_state or st.session_state["inv_cripto_select"] not in lista_cri_actual:
                    st.session_state["inv_cripto_select"] = cri_recordada

                def on_cambio_cripto_inv():
                    datos.setdefault("ultimas_selecciones_inv", {})["cripto"] = st.session_state["inv_cripto_select"]
                    guardar_datos(datos)

                simbolo_elegido = st.selectbox(
                    "Seleccioná la Criptomoneda de la lista",
                    lista_cri_actual,
                    key="inv_cripto_select",
                    on_change=on_cambio_cripto_inv
                )
                detalle_manual = st.text_input(
                    "¿No está en la lista? Escribí la sigla a mano acá y quedará grabada (ej. DFT, ADA):",
                    key="inv_detalle_manual_cri"
                )
            elif tipo_elegido == "E - Bonos":
                lista_bon_actual = datos.setdefault("bonos_guardadas", list(BONOS_BASE))
                bon_recordado = ult_sel.get("bono", lista_bon_actual[0])
                if bon_recordado not in lista_bon_actual:
                    coinc_bon = [b for b in lista_bon_actual if b.split(" ")[0].upper() == str(bon_recordado).split(" ")[0].upper()]
                    bon_recordado = coinc_bon[0] if coinc_bon else lista_bon_actual[0]

                if "inv_bono_select" not in st.session_state or st.session_state["inv_bono_select"] not in lista_bon_actual:
                    st.session_state["inv_bono_select"] = bon_recordado

                def on_cambio_bono_inv():
                    datos.setdefault("ultimas_selecciones_inv", {})["bono"] = st.session_state["inv_bono_select"]
                    guardar_datos(datos)

                simbolo_elegido = st.selectbox(
                    "Seleccioná el Bono de la lista",
                    lista_bon_actual,
                    key="inv_bono_select",
                    on_change=on_cambio_bono_inv
                )
                detalle_manual = st.text_input(
                    "¿No está en la lista? Escribilo a mano acá y quedará grabado (ej. AL30, GD35):",
                    key="inv_detalle_manual_bon"
                )
            elif tipo_elegido == "F - FCI":
                detalle_manual = st.text_input(
                    "Nombre o ticker del FCI (ej. Fima Premium, Mercado Fondo):",
                    key="inv_detalle_manual_fci"
                )
            elif tipo_elegido == "G - Otros":
                detalle_manual = st.text_input(
                    "Detalle qué es (ej. FRASCO NX, PF UVA)",
                    key="inv_detalle_manual_otros"
                )

        # Widget único y estable para "2. Ubicación, ¿dónde está?" (st.selectbox con key fija)
        ubic_recordada = str(ult_sel.get("ubicacion", opciones_ubicacion[0])).strip()
        coinc_u = [u for u in opciones_ubicacion if u.lower() == ubic_recordada.lower()]
        ubic_default_valida = coinc_u[0] if coinc_u else opciones_ubicacion[0]

        if "inv_ubicacion_select" not in st.session_state or st.session_state["inv_ubicacion_select"] not in opciones_ubicacion:
            st.session_state["inv_ubicacion_select"] = ubic_default_valida

        def on_cambio_ubicacion_select():
            val_sel = st.session_state.get("inv_ubicacion_select", opciones_ubicacion[0])
            if val_sel:
                datos.setdefault("ultimas_selecciones_inv", {})["ubicacion"] = val_sel
                guardar_datos(datos)

        plat_select = st.selectbox(
            "2. Ubicación, ¿dónde está?",
            options=opciones_ubicacion,
            key="inv_ubicacion_select",
            on_change=on_cambio_ubicacion_select
        )

        def on_enter_nueva_ubicacion():
            nueva_u = st.session_state.get("inv_ubicacion_nueva_manual", "").strip()
            if nueva_u:
                registrar_ubicacion_guardada(datos, nueva_u)
                guardar_datos(datos)
                st.session_state["inv_ubicacion_select"] = nueva_u
                st.session_state["inv_ubicacion_nueva_manual"] = ""

        nueva_ubic_manual = st.text_input(
            "¿Otra ubicación? Escribila acá y quedará guardada:",
            placeholder="Ej: Brubank, Balanz, Caja de seguridad...",
            key="inv_ubicacion_nueva_manual",
            on_change=on_enter_nueva_ubicacion
        )

        # Tooltip único negro para "3. Cantidad que tenés" según el tipo de activo seleccionado
        if tipo_elegido == "A - Pesos ARS":
            tooltip_cant_actual = "Ingresá el monto en pesos argentinos. Ej: 2500000"
        elif tipo_elegido == "B - Dólares USD":
            tooltip_cant_actual = "Ingresá el monto en dólares. Ej: 1500"
        else:
            tooltip_cant_actual = (
                "Ingresá la cantidad de unidades, no su equivalente en pesos. "
                "Ej: 2 o 5 (acciones o bonos), 0,0005 (BTC). El valor en pesos se calcula automáticamente."
            )

        with st.form("form_guardar_activo_inv", clear_on_submit=True):
            cant_texto = st.text_input(
                "3. Cantidad que tenés",
                placeholder="Ej: 40000 o 0,0005",
                help=tooltip_cant_actual
            )
            btn_guardar_inv = st.form_submit_button(
                "Guardar Activo",
                use_container_width=True
            )

            if btn_guardar_inv:
                try:
                    cant_num = parsear_numero_flexible(cant_texto) if cant_texto.strip() else 0.0
                except ValueError:
                    cant_num = -1.0

                if cant_num > 0:
                    # Asignar la categoría estrictamente desde el tipo de activo seleccionado al momento de guardar
                    tipo_momento_guardar = st.session_state.get("inv_tipo_select", tipo_elegido)

                    if tipo_momento_guardar == "A - Pesos ARS":
                        tipo_guardar = "Pesos ARS"
                        nombre_act = "Pesos ARS"
                        simbolo_final = "ARS"
                    elif tipo_momento_guardar == "B - Dólares USD":
                        tipo_guardar = "Dólares USD"
                        nombre_act = "Dólares USD"
                        simbolo_final = "USD"
                    elif tipo_momento_guardar == "C - Acciones":
                        tipo_guardar = "Acciones"
                        if detalle_manual.strip():
                            nuevo_acc = detalle_manual.strip().upper()
                            if nuevo_acc not in datos["acciones_guardadas"]:
                                datos["acciones_guardadas"].append(nuevo_acc)
                            nombre_act = nuevo_acc
                            simbolo_final = nuevo_acc.split(" ")[0]
                            st.session_state["_pending_inv_widget_sync"] = {
                                "inv_accion_select": nuevo_acc,
                                "inv_detalle_manual_acc": ""
                            }
                        else:
                            nombre_act = simbolo_elegido
                            simbolo_final = simbolo_elegido.split(" ")[0].upper()
                        datos.setdefault("ultimas_selecciones_inv", {})["accion"] = nombre_act
                    elif tipo_momento_guardar == "D - Cryptos":
                        tipo_guardar = "Cryptos"
                        if detalle_manual.strip():
                            nueva_cri_raw = detalle_manual.strip().upper()
                            nueva_cri_sim = nueva_cri_raw.split(" ")[0]
                            coinc_c = [c for c in datos["criptos_guardadas"] if c.split(" ")[0].upper() == nueva_cri_sim]
                            if coinc_c:
                                item_lista_cri = coinc_c[0]
                            else:
                                item_lista_cri = nueva_cri_raw
                                datos["criptos_guardadas"].append(item_lista_cri)
                            nombre_act = nueva_cri_sim
                            simbolo_final = nueva_cri_sim
                            st.session_state["_pending_inv_widget_sync"] = {
                                "inv_cripto_select": item_lista_cri,
                                "inv_detalle_manual_cri": ""
                            }
                        else:
                            item_lista_cri = simbolo_elegido
                            simbolo_final = simbolo_elegido.split(" ")[0].upper().strip()
                            nombre_act = simbolo_final
                        datos.setdefault("ultimas_selecciones_inv", {})["cripto"] = item_lista_cri
                    elif tipo_momento_guardar == "E - Bonos":
                        tipo_guardar = "Bonos"
                        lista_b = datos.setdefault("bonos_guardadas", list(BONOS_BASE))
                        if detalle_manual.strip():
                            nuevo_bon = detalle_manual.strip().upper()
                            nuevo_bon_sim = nuevo_bon.split(" ")[0]
                            coinc_b = [b for b in lista_b if b.split(" ")[0].upper() == nuevo_bon_sim]
                            if coinc_b:
                                item_lista_bon = coinc_b[0]
                            else:
                                item_lista_bon = nuevo_bon
                                lista_b.append(item_lista_bon)
                            nombre_act = item_lista_bon
                            simbolo_final = nuevo_bon_sim
                            st.session_state["_pending_inv_widget_sync"] = {
                                "inv_bono_select": item_lista_bon,
                                "inv_detalle_manual_bon": ""
                            }
                        else:
                            item_lista_bon = simbolo_elegido
                            nombre_act = simbolo_elegido
                            simbolo_final = simbolo_elegido.split(" ")[0].upper().strip()
                        datos.setdefault("ultimas_selecciones_inv", {})["bono"] = item_lista_bon
                    elif tipo_momento_guardar == "F - FCI":
                        tipo_guardar = "FCI"
                        nombre_act = detalle_manual.strip() if detalle_manual.strip() else "FCI"
                        simbolo_final = nombre_act.split(" ")[0].upper()
                        if detalle_manual.strip():
                            st.session_state["_pending_inv_widget_sync"] = {
                                "inv_detalle_manual_fci": ""
                            }
                    else:
                        tipo_guardar = "Otros"
                        nombre_act = detalle_manual.strip() if detalle_manual.strip() else "Otros"
                        simbolo_final = nombre_act.split(" ")[0].upper() if detalle_manual.strip() else "ARS"
                        if detalle_manual.strip():
                            st.session_state["_pending_inv_widget_sync"] = {
                                "inv_detalle_manual_otros": ""
                            }

                    ubicacion_elegida_final = nueva_ubic_manual.strip() if nueva_ubic_manual.strip() else plat_select.strip()
                    if not ubicacion_elegida_final:
                        ubicacion_elegida_final = opciones_ubicacion[0]

                    registrar_ubicacion_guardada(datos, ubicacion_elegida_final)
                    sync_dict = st.session_state.get("_pending_inv_widget_sync", {})
                    sync_dict["inv_ubicacion_select"] = ubicacion_elegida_final
                    sync_dict["inv_ubicacion_nueva_manual"] = ""
                    st.session_state["_pending_inv_widget_sync"] = sync_dict

                    datos.setdefault("ultimas_selecciones_inv", {})["tipo"] = tipo_momento_guardar

                    datos["inversiones"].append({
                        "tipo": tipo_guardar,
                        "activo": nombre_act,
                        "simbolo": simbolo_final,
                        "cantidad": int(cant_num) if cant_num.is_integer() else cant_num,
                        "plataforma": ubicacion_elegida_final,
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
            "Pesos ARS",
            "Dólares USD",
            "Acciones",
            "Cryptos",
            "Bonos",
            "FCI",
            "Otros"
        ]

        if inversiones:
            inv_cambios = False
            for cat_inv in orden_categorias_inv:
                items_cat_inv = [
                    (idx, inv) for idx, inv in enumerate(inversiones)
                    if normalizar_tipo_activo_inv(inv.get("tipo", "Otros")) == cat_inv
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
                    f"📂 **{cat_inv}** — subt= "
                    f"**{sub_inv_ars:,.0f} ARS** ({sub_inv_usd:,.2f} USD)"
                )
                with st.expander(titulo_exp_inv, expanded=True):
                    hc1, hc2, hc3, hc4, hc5 = st.columns([0.45, 1.15, 1.85, 1.10, 0.45])
                    hc1.markdown("<div class='col-header'>ACT.</div>", unsafe_allow_html=True)
                    hc2.markdown("<div class='col-header'>DETALLE</div>", unsafe_allow_html=True)
                    hc3.markdown("<div class='col-header'>CANTIDAD</div>", unsafe_allow_html=True)
                    hc4.markdown("<div class='col-header'>UBICACIÓN</div>", unsafe_allow_html=True)
                    hc5.markdown("<div class='col-header'>BORRAR</div>", unsafe_allow_html=True)

                    for idx, inv in items_cat_inv:
                        st_act = inv.get("activo_inv", True)
                        c_chk, c_nom, c_cant, c_plat, c_del = st.columns([0.45, 1.15, 1.85, 1.10, 0.45])

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
                            val_detalle_mostrar = "Dólares USD" if inv.get("activo", "") in ["Dólar Billete", "A - Dólar Billete"] else inv.get("activo", "")
                            st.text_input(
                                "Detalle",
                                value=val_detalle_mostrar,
                                key=f"inv_nom_{idx}",
                                label_visibility="collapsed",
                                disabled=True
                            )

                        with c_cant:
                            cant_num_actual = float(inv.get("cantidad", 0))
                            cant_str_actual = formatear_cant(cant_num_actual)
                            nueva_cant_str = st.text_input(
                                "Cantidad",
                                value=cant_str_actual,
                                key=f"inv_cant_{idx}",
                                label_visibility="collapsed",
                                disabled=not st_act
                            )
                            try:
                                nueva_cant_val = parsear_numero_flexible(nueva_cant_str)
                                if nueva_cant_val > 0 and abs(nueva_cant_val - cant_num_actual) > 1e-9:
                                    inv["cantidad"] = int(nueva_cant_val) if nueva_cant_val.is_integer() else nueva_cant_val
                                    cant_num_actual = nueva_cant_val
                                    cant_str_actual = formatear_cant(cant_num_actual)
                                    inv_cambios = True
                            except ValueError:
                                pass

                            # Desglose en vivo (unidades × precio unitario en ARS = total ARS) con salto de línea permitido
                            # para que nunca se corte, excluyendo Pesos ARS y Dólares USD
                            if cat_inv not in ["Pesos ARS", "Dólares USD"]:
                                if not filas[idx].get("Precio_Valido", True):
                                    st.markdown(
                                        "<div style='font-size: 0.75rem; font-weight: 700; color: #991B1B; "
                                        "background: #FEF2F2; border: 1px solid #FECACA; border-radius: 7px; "
                                        "padding: 4px 7px; margin-top: -8px; margin-bottom: 6px; "
                                        "white-space: normal; word-break: break-word; line-height: 1.25;'>"
                                        "⚠️ Precio inválido o no disponible"
                                        "</div>",
                                        unsafe_allow_html=True
                                    )
                                else:
                                    precio_u_ars_fila = float(filas[idx]["Precio_Unit_ARS"])
                                    total_ars_fila = cant_num_actual * precio_u_ars_fila
                                    precio_u_fmt = (
                                        f"{precio_u_ars_fila:,.0f}"
                                        if precio_u_ars_fila >= 10 or precio_u_ars_fila.is_integer()
                                        else f"{precio_u_ars_fila:,.2f}"
                                    )
                                    st.markdown(
                                        f"<div style='font-size: 0.75rem; font-weight: 700; color: #4A235A; "
                                        f"background: #F5F3FF; border: 1px solid #DDD6FE; border-radius: 7px; "
                                        f"padding: 4px 7px; margin-top: -8px; margin-bottom: 6px; "
                                        f"white-space: normal; word-break: break-word; overflow-wrap: anywhere; "
                                        f"line-height: 1.25;'>"
                                        f"{cant_str_actual} × {precio_u_fmt} = {total_ars_fila:,.0f} ARS"
                                        f"</div>",
                                        unsafe_allow_html=True
                                    )

                        with c_plat:
                            st.text_input(
                                "Ubicación",
                                value=inv.get("plataforma", ""),
                                key=f"inv_p_{idx}",
                                label_visibility="collapsed",
                                disabled=True
                            )

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

    st.markdown(
        "<h3 style='color: #5B4B8A;'>💼 Distribución de mi Patrimonio</h3>",
        unsafe_allow_html=True
    )
    if not df_inv_activos.empty and total_patrimonio_ars > 0:
        col_g_inv1, col_g_inv2 = st.columns(2, gap="medium")

        with col_g_inv1:
            st.markdown(
                "<h4 style='color: #5B4B8A; text-align: center;'>Según tipo de Activo</h4>",
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
                "<h4 style='color: #5B4B8A; text-align: center;'>Según Ubicación</h4>",
                unsafe_allow_html=True
            )
            df_det = df_inv_activos.sort_values(by="Valor en ARS", ascending=False).copy()
            df_det["%"] = (df_det["Valor en ARS"] / total_patrimonio_ars) * 100

            # Agrupar por Ubicación (una sola porción por plataforma/ubicación sumando todos sus activos)
            df_ubic_grp = df_inv_activos.copy()
            df_ubic_grp["Ubicacion_Limpia"] = df_ubic_grp["Plataforma"].astype(str).str.strip()
            df_ubic_grp.loc[df_ubic_grp["Ubicacion_Limpia"] == "", "Ubicacion_Limpia"] = "Sin especificar"

            mapa_ubic_display = {}
            for u_raw in df_ubic_grp["Ubicacion_Limpia"]:
                u_key = u_raw.lower()
                if u_key not in mapa_ubic_display or (u_raw != u_raw.upper() and mapa_ubic_display[u_key] == mapa_ubic_display[u_key].upper()):
                    mapa_ubic_display[u_key] = u_raw
            df_ubic_grp["Ubicacion_Final"] = df_ubic_grp["Ubicacion_Limpia"].apply(lambda x: mapa_ubic_display.get(x.lower(), x))

            resumen_ubic = df_ubic_grp.groupby("Ubicacion_Final", as_index=False).agg({
                "Valor en ARS": "sum",
                "Valor en USD": "sum"
            }).sort_values(by="Valor en ARS", ascending=False)
            resumen_ubic["%"] = (resumen_ubic["Valor en ARS"] / total_patrimonio_ars) * 100

            # Agrupar porciones menores al 2% en "Otras" cuando hay más de una para evitar superposición de etiquetas
            menores_2pct = resumen_ubic[resumen_ubic["%"] < 2.0]
            if len(menores_2pct) > 1:
                mayores_2pct = resumen_ubic[resumen_ubic["%"] >= 2.0].copy()
                fila_otras = pd.DataFrame([{
                    "Ubicacion_Final": "Otras",
                    "Valor en ARS": menores_2pct["Valor en ARS"].sum(),
                    "Valor en USD": menores_2pct["Valor en USD"].sum(),
                    "%": menores_2pct["%"].sum()
                }])
                df_pie_ubic = pd.concat([mayores_2pct, fila_otras], ignore_index=True)
            else:
                df_pie_ubic = resumen_ubic.copy()

            fig_inv_det = crear_torta_2d(df_pie_ubic, "Valor en ARS", "Ubicacion_Final")
            st.plotly_chart(fig_inv_det, use_container_width=True, config={"displayModeBar": False})

            # Filtro por Activo o por Ubicación / Plataforma y cálculo de subtotales
            activos_unicos = list(dict.fromkeys(df_det["Activo"].dropna().astype(str).tolist()))
            ubicaciones_unicas = list(dict.fromkeys(df_det["Plataforma"].dropna().astype(str).tolist()))
            opciones_filtro = ["Todos (ver todo)"]
            for a_item in activos_unicos:
                if a_item and a_item not in opciones_filtro:
                    opciones_filtro.append(a_item)
            for u_item in ubicaciones_unicas:
                if u_item and u_item not in opciones_filtro:
                    opciones_filtro.append(u_item)

            filtro_sel = st.selectbox(
                "🔎 Filtrar por Activo o Ubicación (ej. BTC, NEXO, Binance):",
                options=opciones_filtro,
                key="filtro_tabla_final_inv"
            )

            if filtro_sel != "Todos (ver todo)":
                f_low = filtro_sel.strip().lower()
                mask_f = (
                    (df_det["Activo"].astype(str).str.lower() == f_low)
                    | (df_det["Simbolo"].astype(str).str.lower() == f_low)
                    | (df_det["Plataforma"].astype(str).str.lower() == f_low)
                    | (df_det["Tipo"].astype(str).str.lower() == f_low)
                )
                df_det_mostrar = df_det[mask_f].copy()
            else:
                df_det_mostrar = df_det.copy()

            cols_d = [
                "Tipo", "Activo", "Plataforma", "Cantidad",
                "Cotización Actual", "Valor en ARS", "Valor en USD", "%"
            ]
            tabla_d = df_det_mostrar[cols_d].copy()
            tabla_d.columns = [
                "Categoría", "Activo", "Ubicación", "Cantidad",
                "Cotización Actual Tomada", "Valor en ARS", "Valor en USD", "%"
            ]
            tabla_d["Valor en ARS"] = tabla_d["Valor en ARS"].apply(lambda x: f"{x:,.0f} ARS")
            tabla_d["Valor en USD"] = tabla_d["Valor en USD"].apply(lambda x: f"{x:,.2f} USD")
            tabla_d["%"] = tabla_d["%"].apply(lambda x: f"{x:.1f}%")

            if filtro_sel != "Todos (ver todo)" and not df_det_mostrar.empty:
                sub_f_ars = df_det_mostrar["Valor en ARS"].sum()
                sub_f_usd = df_det_mostrar["Valor en USD"].sum()
                sub_f_pct = (sub_f_ars / total_patrimonio_ars) * 100 if total_patrimonio_ars > 0 else 0.0
                cant_f_total = df_det_mostrar["Cantidad_Num"].sum()
                es_mismo_activo = df_det_mostrar["Activo"].nunique() == 1
                cant_f_str = formatear_cant(cant_f_total) if es_mismo_activo else f"{len(df_det_mostrar)} ítems"

                fila_subtotal = pd.DataFrame([{
                    "Categoría": "SUBTOTAL",
                    "Activo": filtro_sel,
                    "Ubicación": "Total filtrado",
                    "Cantidad": cant_f_str,
                    "Cotización Actual Tomada": "—",
                    "Valor en ARS": f"{sub_f_ars:,.0f} ARS",
                    "Valor en USD": f"{sub_f_usd:,.2f} USD",
                    "%": f"{sub_f_pct:.1f}%"
                }])
                tabla_d = pd.concat([tabla_d, fila_subtotal], ignore_index=True)

                st.markdown(f"""
                <div style="background-color: #F3E8FF; border: 1.5px solid #C084FC; border-left: 6px solid #7E22CE;
                            border-radius: 12px; padding: 10px 14px; margin-bottom: 10px; color: #4A235A; font-size: 0.98rem;">
                    <b>Subtotal ({filtro_sel}):</b> <b>{sub_f_usd:,.2f} USD</b> &nbsp;|&nbsp;
                    <b>{sub_f_ars:,.0f} ARS</b> &nbsp;|&nbsp;
                    <b>{sub_f_pct:.1f}%</b> del patrimonio total
                </div>
                """, unsafe_allow_html=True)

            st.dataframe(tabla_d, use_container_width=True, hide_index=True)

activar_interactividad_avanzada(
    datos.get('categorias_costos', []),
    datos.get('categorias_ingresos', []),
    datos.get('ubicaciones_guardadas', []),
    tooltip_cant_actual
)
