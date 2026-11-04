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
def activar_interactividad_avanzada(cats_costos=None, cats_ingresos=None, ubicaciones_guardadas=None):
    ubicaciones_json = json.dumps((ubicaciones_guardadas or [])[:8], ensure_ascii=False)
    js_code = r"""
    <script>
    (function() {
        const win = window.parent;
        const doc = win.document;
        const ubicacionesRecientes = __UBICACIONES_JSON__;

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

        function actualizarInterfaz() {
            estilizarTrebolesSolapas();
            limpiarInputsYPopups();
            estilizarSolapasYBotonesOrden();
            asegurarLineasConectorasTortas();
            configurarDropdownUbicacion();
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
    components.html(js_code.replace("__UBICACIONES_JSON__", ubicaciones_json), height=0, width=0)




# ----------------- PANEL DINÁMICO 3D DE SALUD FINANCIERA Y RUNWAY -----------------
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


def construir_html_panel_patrimonio(
    total_patrimonio_ars,
    total_patrimonio_usd,
    cant_activos_contemplados,
    cant_activos_totales,
    costo_mensual_ars,
    dolar_b,
    hay_moneda_extranjera=False
):
    tasa_invalida = hay_moneda_extranjera and (dolar_b is None or float(dolar_b) <= 0)

    if tasa_invalida:
        runway_months = None
        score = 0.5
        runway_display = "⚠️ Tasa USD/ARS no disponible"
        mensaje_salud = (
            "⚠️ Advertencia: Se detectaron activos o costos en moneda extranjera (USD) "
            "pero no hay un tipo de cambio válido para convertir ambos valores a ARS."
        )
    elif costo_mensual_ars <= 0:
        runway_months = None
        score = 1.0 if total_patrimonio_ars > 0 else 0.5
        runway_display = "Sin costos cargados"
        mensaje_salud = (
            "Sin costos cargados: activá o cargá tus costos mensuales en 'Costos e Ingresos' "
            "para calcular cuántos años y meses podés vivir sin nuevos ingresos."
        )
    else:
        runway_months = float(total_patrimonio_ars) / float(costo_mensual_ars)
        runway_meses_int = max(0, int(round(runway_months)))
        anios_rw = runway_meses_int // 12
        meses_rem_rw = runway_meses_int % 12

        if runway_meses_int <= 12:
            runway_display = f"{runway_meses_int} meses"
        else:
            runway_display = f"{anios_rw} años y {meses_rem_rw} meses"

        if runway_months >= 180.0:
            score = 1.0
        elif runway_months <= 24.0:
            score = 0.0
        else:
            score = (runway_months - 24.0) / (180.0 - 24.0)

        if runway_months >= 180.0:
            mensaje_salud = (
                f"Estamos muy bien financieramente, te quedan {anios_rw} años y {meses_rem_rw} meses "
                f"de vivir sin nuevos ingresos"
            )
        elif runway_months <= 24.0:
            mensaje_salud = (
                f"Estamos en llamas financieramente, te quedan {runway_meses_int} meses "
                f"de sobrevivir sin ingresos"
            )
        elif score >= 0.70:
            mensaje_salud = (
                f"Estamos bien financieramente, con buena reserva: te quedan {runway_display} "
                f"de vivir sin nuevos ingresos"
            )
        elif score >= 0.40:
            mensaje_salud = (
                f"Atención financiera: el jardín empieza a secarse, te quedan {runway_display} "
                f"de vivir sin nuevos ingresos"
            )
        else:
            mensaje_salud = (
                f"Alerta financiera: sequía severa en progreso, te quedan apenas {runway_display} "
                f"de sobrevivir sin nuevos ingresos"
            )

    # Interpolación continua de colores del cielo, colinas, suelo y follaje según score (0 a 1)
    sky_top = _multi_color([
        (0.0, "#7F1D1D"),
        (0.25, "#C2410C"),
        (0.55, "#F59E0B"),
        (0.80, "#7DD3FC"),
        (1.0, "#38BDF8")
    ], score)
    sky_mid = _multi_color([
        (0.0, "#DC2626"),
        (0.25, "#EA580C"),
        (0.55, "#FDE68A"),
        (0.80, "#BAE6FD"),
        (1.0, "#CCFBF1")
    ], score)
    sky_bot = _multi_color([
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
        (1.0, "#22C55E")
    ], score)
    hill_mid = _multi_color([
        (0.0, "#B45309"),
        (0.30, "#D97706"),
        (0.60, "#CA8A04"),
        (0.85, "#22C55E"),
        (1.0, "#16A34A")
    ], score)
    ground_front = _multi_color([
        (0.0, "#78350F"),
        (0.30, "#92400E"),
        (0.60, "#854D0E"),
        (0.85, "#15803D"),
        (1.0, "#166534")
    ], score)

    leaf_main = _multi_color([
        (0.0, "#78350F"),
        (0.25, "#A16207"),
        (0.55, "#EAB308"),
        (0.80, "#4ADE80"),
        (1.0, "#16A34A")
    ], score)
    leaf_light = _multi_color([
        (0.0, "#92400E"),
        (0.25, "#CA8A04"),
        (0.55, "#FDE047"),
        (0.80, "#86EFAC"),
        (1.0, "#4ADE80")
    ], score)
    leaf_dark = _multi_color([
        (0.0, "#451A03"),
        (0.25, "#713F12"),
        (0.55, "#A16207"),
        (0.80, "#15803D"),
        (1.0, "#14532D")
    ], score)

    border_col = _multi_color([
        (0.0, "#EF4444"),
        (0.35, "#F59E0B"),
        (0.70, "#84CC16"),
        (1.0, "#22C55E")
    ], score)

    # Parámetros físicos continuos para plantas, sol en llamas y rodadoras (tumbleweeds)
    fire_opacity = max(0.0, min(1.0, ((1.0 - score) ** 1.35)))
    sun_radius = 28.0 + (1.0 - score) * 18.0
    sun_core_col = _multi_color([(0.0, "#FEF08A"), (0.4, "#FDE047"), (1.0, "#FEF9C3")], score)
    sun_outer_col = _multi_color([(0.0, "#DC2626"), (0.4, "#F97316"), (1.0, "#FBBF24")], score)
    tumbleweed_opacity = max(0.0, min(1.0, (0.38 - score) / 0.38)) if score < 0.38 else 0.0
    cracks_opacity = max(0.0, min(1.0, (0.45 - score) / 0.45)) if score < 0.45 else 0.0
    clouds_opacity = max(0.0, min(0.92, (score - 0.15) / 0.85))
    flowers_opacity = max(0.0, min(1.0, (score - 0.55) / 0.45))

    # Ángulo de caída/marchitamiento de las plantas y escala por umbral
    droop_deg = (1.0 - score) * 34.0

    def _plant_style(threshold):
        if score <= 0.001 or score <= threshold:
            return 0.0, 0.0
        sc = max(0.15, min(1.0, (score - threshold) / (1.0 - threshold)))
        op = max(0.0, min(1.0, (score - threshold) / max(0.18, 1.0 - threshold)))
        return sc, op

    t1_s, t1_o = _plant_style(0.04)
    t2_s, t2_o = _plant_style(0.18)
    t3_s, t3_o = _plant_style(0.35)
    t4_s, t4_o = _plant_style(0.52)
    t5_s, t5_o = _plant_style(0.68)

    # Morfología y estado de los personajes (Canguro y Koala) según score
    ribs_opacity = max(0.0, min(0.95, (0.32 - score) / 0.32)) if score < 0.32 else 0.0
    fat_scale_x = 0.72 + 0.34 * score  # 1.06 en score=1 (bien alimentado), 0.72 en score=0 (famélico)
    posture_drop = (1.0 - score) * 14.0
    ear_droop = (1.0 - score) * 28.0

    if score > 0.65:
        kanga_anim_class = "jardin-kanga-happy"
        koala_anim_class = "jardin-koala-happy"
        mouth_kanga = "M 92 103 Q 100 111 107 102"
        mouth_koala = "M 1094 114 Q 1102 122 1110 114"
        eye_state = "happy"
    elif score > 0.15:
        kanga_anim_class = "jardin-animal-tired"
        koala_anim_class = "jardin-animal-tired"
        mouth_kanga = "M 92 108 Q 100 101 107 108"
        mouth_koala = "M 1094 120 Q 1102 113 1110 120"
        eye_state = "sad"
    else:
        kanga_anim_class = "jardin-animal-collapse"
        koala_anim_class = "jardin-animal-collapse"
        mouth_kanga = "M 91 109 Q 100 100 108 109"
        mouth_koala = "M 1093 121 Q 1102 112 1111 121"
        eye_state = "dying"

    # Ojos expresivos según el estado
    if eye_state == "happy":
        kanga_eyes_svg = (
            '<circle cx="96" cy="87" r="4.2" fill="#1F2937"/>'
            '<circle cx="97.5" cy="85.5" r="1.5" fill="#FFFFFF"/>'
            '<circle cx="110" cy="87" r="3.8" fill="#1F2937"/>'
            '<circle cx="111.2" cy="85.5" r="1.3" fill="#FFFFFF"/>'
        )
        koala_eyes_svg = (
            '<circle cx="1090" cy="96" r="4.3" fill="#1F2937"/>'
            '<circle cx="1091.5" cy="94.5" r="1.5" fill="#FFFFFF"/>'
            '<circle cx="1114" cy="96" r="4.3" fill="#1F2937"/>'
            '<circle cx="1115.5" cy="94.5" r="1.5" fill="#FFFFFF"/>'
            '<ellipse cx="1083" cy="104" rx="5" ry="3" fill="#F472B6" opacity="0.55"/>'
            '<ellipse cx="1121" cy="104" rx="5" ry="3" fill="#F472B6" opacity="0.55"/>'
        )
        tongue_kanga_svg = ""
        tongue_koala_svg = ""
    elif eye_state == "sad":
        kanga_eyes_svg = (
            '<circle cx="96" cy="89" r="3.8" fill="#1F2937"/>'
            '<path d="M 90 84 L 101 87" stroke="#451A03" stroke-width="2.2" stroke-linecap="round"/>'
            '<circle cx="110" cy="89" r="3.5" fill="#1F2937"/>'
            '<path d="M 105 87 L 115 84" stroke="#451A03" stroke-width="2.2" stroke-linecap="round"/>'
            '<path d="M 86 95 Q 84 102 86 105 Q 88 102 86 95 Z" fill="#38BDF8" opacity="0.85"/>'
        )
        koala_eyes_svg = (
            '<circle cx="1090" cy="98" r="3.8" fill="#1F2937"/>'
            '<path d="M 1084 92 L 1095 95" stroke="#1F2937" stroke-width="2.2" stroke-linecap="round"/>'
            '<circle cx="1114" cy="98" r="3.8" fill="#1F2937"/>'
            '<path d="M 1109 95 L 1120 92" stroke="#1F2937" stroke-width="2.2" stroke-linecap="round"/>'
            '<path d="M 1078 104 Q 1076 111 1078 114 Q 1080 111 1078 104 Z" fill="#38BDF8" opacity="0.85"/>'
        )
        tongue_kanga_svg = ""
        tongue_koala_svg = ""
    else:
        kanga_eyes_svg = (
            '<path d="M 92 84 L 99 91 M 99 84 L 92 91" stroke="#1F2937" stroke-width="2.4" stroke-linecap="round"/>'
            '<path d="M 106 84 L 113 91 M 113 84 L 106 91" stroke="#1F2937" stroke-width="2.4" stroke-linecap="round"/>'
        )
        koala_eyes_svg = (
            '<path d="M 1086 93 L 1094 101 M 1094 93 L 1086 101" stroke="#1F2937" stroke-width="2.4" stroke-linecap="round"/>'
            '<path d="M 1110 93 L 1118 101 M 1118 93 L 1110 101" stroke="#1F2937" stroke-width="2.4" stroke-linecap="round"/>'
        )
        tongue_kanga_svg = '<path d="M 100 106 Q 103 118 98 121 Q 94 119 96 106 Z" fill="#EF4444" stroke="#991B1B" stroke-width="1"/>'
        tongue_koala_svg = '<path d="M 1102 117 Q 1105 128 1100 130 Q 1096 128 1098 117 Z" fill="#EF4444" stroke="#991B1B" stroke-width="1"/>'

    # Ramita de eucalipto fresca cuando el score es alto vs seca cuando es bajo
    euca_leaf_op = max(0.0, min(1.0, (score - 0.12) / 0.5))

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

    lineas_html = [
        f'<div class="jardin-health-scene" style="border-color: {border_col};">',
        f'<svg class="jardin-scene-svg" viewBox="0 0 1200 320" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">',
        '<defs>',
        f'<linearGradient id="skyGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
        f'<stop offset="0%" stop-color="{sky_top}"/>',
        f'<stop offset="55%" stop-color="{sky_mid}"/>',
        f'<stop offset="100%" stop-color="{sky_bot}"/>',
        '</linearGradient>',
        f'<radialGradient id="sunGrad" cx="50%" cy="50%" r="50%">',
        f'<stop offset="0%" stop-color="{sun_core_col}"/>',
        f'<stop offset="65%" stop-color="{sun_outer_col}"/>',
        f'<stop offset="100%" stop-color="{sun_outer_col}" stop-opacity="0"/>',
        '</radialGradient>',
        f'<linearGradient id="hillBackGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
        f'<stop offset="0%" stop-color="{hill_back}"/>',
        f'<stop offset="100%" stop-color="{ground_front}"/>',
        '</linearGradient>',
        f'<linearGradient id="hillMidGrad" x1="0%" y1="0%" x2="0%" y2="100%">',
        f'<stop offset="0%" stop-color="{hill_mid}"/>',
        f'<stop offset="100%" stop-color="{ground_front}"/>',
        '</linearGradient>',
        f'<linearGradient id="foliage3D" x1="20%" y1="0%" x2="80%" y2="100%">',
        f'<stop offset="0%" stop-color="{leaf_light}"/>',
        f'<stop offset="55%" stop-color="{leaf_main}"/>',
        f'<stop offset="100%" stop-color="{leaf_dark}"/>',
        '</linearGradient>',
        '<linearGradient id="trunk3D" x1="0%" y1="0%" x2="100%" y2="0%">',
        '<stop offset="0%" stop-color="#78350F"/>',
        '<stop offset="45%" stop-color="#92400E"/>',
        '<stop offset="100%" stop-color="#451A03"/>',
        '</linearGradient>',
        '<radialGradient id="kangaFur3D" cx="35%" cy="30%" r="70%">',
        '<stop offset="0%" stop-color="#F59E0B"/>',
        '<stop offset="55%" stop-color="#D97706"/>',
        '<stop offset="100%" stop-color="#92400E"/>',
        '</radialGradient>',
        '<linearGradient id="kangaBelly3D" x1="0%" y1="0%" x2="0%" y2="100%">',
        '<stop offset="0%" stop-color="#FEF3C7"/>',
        '<stop offset="100%" stop-color="#FDE68A"/>',
        '</linearGradient>',
        '<radialGradient id="koalaFur3D" cx="35%" cy="30%" r="70%">',
        '<stop offset="0%" stop-color="#9CA3AF"/>',
        '<stop offset="60%" stop-color="#6B7280"/>',
        '<stop offset="100%" stop-color="#374151"/>',
        '</radialGradient>',
        '<linearGradient id="koalaBelly3D" x1="0%" y1="0%" x2="0%" y2="100%">',
        '<stop offset="0%" stop-color="#F3F4F6"/>',
        '<stop offset="100%" stop-color="#D1D5DB"/>',
        '</linearGradient>',
        '<filter id="softShadow3D" x="-20%" y="-20%" width="140%" height="140%">',
        '<feDropShadow dx="0" dy="5" stdDeviation="4" flood-color="#000000" flood-opacity="0.24"/>',
        '</filter>',
        '</defs>',
        # Cielo de fondo
        '<rect x="0" y="0" width="1200" height="320" fill="url(#skyGrad)"/>',
        # Sol / Sol en llamas (cuando el score baja)
        f'<g class="jardin-sun-group" transform="translate(600, {68 + int((1.0 - score) * 18)})">',
        f'<circle cx="0" cy="0" r="{sun_radius * 2.1:.1f}" fill="url(#sunGrad)" opacity="{0.45 + 0.45 * fire_opacity:.2f}"/>',
        f'<g class="jardin-sun-flames" opacity="{fire_opacity:.2f}">',
        f'<polygon points="0,-{sun_radius*1.65:.1f} 12,-{sun_radius*0.85:.1f} -12,-{sun_radius*0.85:.1f}" fill="#EF4444"/>',
        f'<polygon points="0,{sun_radius*1.65:.1f} 12,{sun_radius*0.85:.1f} -12,{sun_radius*0.85:.1f}" fill="#EF4444"/>',
        f'<polygon points="-{sun_radius*1.65:.1f},0 -{sun_radius*0.85:.1f},12 -{sun_radius*0.85:.1f},-12" fill="#F97316"/>',
        f'<polygon points="{sun_radius*1.65:.1f},0 {sun_radius*0.85:.1f},12 {sun_radius*0.85:.1f},-12" fill="#F97316"/>',
        f'<polygon points="-{sun_radius*1.2:.1f},-{sun_radius*1.2:.1f} -{sun_radius*0.5:.1f},-{sun_radius*0.9:.1f} -{sun_radius*0.9:.1f},-{sun_radius*0.5:.1f}" fill="#DC2626"/>',
        f'<polygon points="{sun_radius*1.2:.1f},-{sun_radius*1.2:.1f} {sun_radius*0.5:.1f},-{sun_radius*0.9:.1f} {sun_radius*0.9:.1f},-{sun_radius*0.5:.1f}" fill="#DC2626"/>',
        f'<polygon points="-{sun_radius*1.2:.1f},{sun_radius*1.2:.1f} -{sun_radius*0.5:.1f},{sun_radius*0.9:.1f} -{sun_radius*0.9:.1f},{sun_radius*0.5:.1f}" fill="#F59E0B"/>',
        f'<polygon points="{sun_radius*1.2:.1f},{sun_radius*1.2:.1f} {sun_radius*0.5:.1f},{sun_radius*0.9:.1f} {sun_radius*0.9:.1f},{sun_radius*0.5:.1f}" fill="#F59E0B"/>',
        '</g>',
        f'<circle cx="0" cy="0" r="{sun_radius:.1f}" fill="{sun_core_col}" filter="url(#softShadow3D)"/>',
        '</g>',
        # Nubes suaves en escenario saludable
        f'<g class="jardin-clouds" opacity="{clouds_opacity:.2f}" fill="#FFFFFF">',
        '<g transform="translate(220, 48)" opacity="0.82">',
        '<ellipse cx="0" cy="0" rx="36" ry="15"/><ellipse cx="-22" cy="4" rx="22" ry="12"/><ellipse cx="24" cy="4" rx="24" ry="11"/>',
        '</g>',
        '<g transform="translate(940, 42)" opacity="0.78">',
        '<ellipse cx="0" cy="0" rx="40" ry="16"/><ellipse cx="-25" cy="5" rx="24" ry="12"/><ellipse cx="25" cy="5" rx="22" ry="11"/>',
        '</g>',
        '</g>',
        # Colinas 3D con parallax y sombras
        '<path d="M 0 235 Q 190 175 410 220 T 830 210 T 1200 230 L 1200 320 L 0 320 Z" fill="url(#hillBackGrad)" opacity="0.88"/>',
        '<path d="M 0 255 Q 260 205 560 248 T 1200 245 L 1200 320 L 0 320 Z" fill="url(#hillMidGrad)" opacity="0.95"/>',
        f'<path d="M 0 276 Q 360 252 720 278 T 1200 272 L 1200 320 L 0 320 Z" fill="{ground_front}"/>',
        # Grietas de sequía en el suelo cuando el score es bajo
        f'<g stroke="#451A03" stroke-width="1.8" fill="none" opacity="{cracks_opacity:.2f}">',
        '<path d="M 250 286 L 272 296 L 260 310 M 272 296 L 295 302"/>',
        '<path d="M 520 292 L 548 301 L 535 316 M 548 301 L 575 297"/>',
        '<path d="M 860 285 L 885 298 L 874 314 M 885 298 L 912 303"/>',
        '</g>',
        # Bosque / Jardín 3D (se reduce, amarillea y se inclina al bajar el score; desaparece en score=0)
        f'<g class="jardin-sway-tree" opacity="{t1_o:.2f}" transform="translate(225, 255) scale({t1_s:.2f}) rotate({droop_deg * 0.45:.1f})" filter="url(#softShadow3D)">',
        '<path d="M -7 0 L -4 -68 L 4 -68 L 7 0 Z" fill="url(#trunk3D)"/>',
        '<circle cx="0" cy="-82" r="34" fill="url(#foliage3D)"/>',
        '<circle cx="-22" cy="-68" r="25" fill="url(#foliage3D)"/>',
        '<circle cx="22" cy="-68" r="25" fill="url(#foliage3D)"/>',
        '<circle cx="0" cy="-104" r="24" fill="url(#foliage3D)"/>',
        '</g>',
        f'<g class="jardin-sway-tree-alt" opacity="{t2_o:.2f}" transform="translate(310, 265) scale({t2_s:.2f}) rotate({droop_deg * 0.6:.1f})" filter="url(#softShadow3D)">',
        '<path d="M -5 0 L -3 -52 L 3 -52 L 5 0 Z" fill="url(#trunk3D)"/>',
        '<ellipse cx="0" cy="-64" rx="28" ry="24" fill="url(#foliage3D)"/>',
        '<circle cx="-16" cy="-54" r="18" fill="url(#foliage3D)"/>',
        '<circle cx="16" cy="-54" r="18" fill="url(#foliage3D)"/>',
        '</g>',
        f'<g class="jardin-sway-tree" opacity="{t3_o:.2f}" transform="translate(890, 262) scale({t3_s:.2f}) rotate(-{droop_deg * 0.55:.1f})" filter="url(#softShadow3D)">',
        '<path d="M -6 0 L -3 -58 L 3 -58 L 6 0 Z" fill="url(#trunk3D)"/>',
        '<circle cx="0" cy="-72" r="30" fill="url(#foliage3D)"/>',
        '<circle cx="-18" cy="-58" r="22" fill="url(#foliage3D)"/>',
        '<circle cx="18" cy="-58" r="22" fill="url(#foliage3D)"/>',
        '</g>',
        f'<g class="jardin-sway-tree-alt" opacity="{t1_o:.2f}" transform="translate(975, 254) scale({t1_s:.2f}) rotate(-{droop_deg * 0.4:.1f})" filter="url(#softShadow3D)">',
        '<path d="M -7 0 L -4 -70 L 4 -70 L 7 0 Z" fill="url(#trunk3D)"/>',
        '<circle cx="0" cy="-86" r="35" fill="url(#foliage3D)"/>',
        '<circle cx="-24" cy="-70" r="25" fill="url(#foliage3D)"/>',
        '<circle cx="24" cy="-70" r="25" fill="url(#foliage3D)"/>',
        '<circle cx="0" cy="-108" r="24" fill="url(#foliage3D)"/>',
        '</g>',
        # Arbustos y helechos adicionales en niveles altos de salud
        f'<g class="jardin-sway-bush" opacity="{t4_o:.2f}" transform="translate(380, 275) scale({t4_s:.2f}) rotate({droop_deg * 0.7:.1f})">',
        '<ellipse cx="0" cy="-14" rx="22" ry="15" fill="url(#foliage3D)"/>',
        '<ellipse cx="-14" cy="-10" rx="16" ry="12" fill="url(#foliage3D)"/>',
        '<ellipse cx="14" cy="-10" rx="16" ry="12" fill="url(#foliage3D)"/>',
        '</g>',
        f'<g class="jardin-sway-bush" opacity="{t4_o:.2f}" transform="translate(820, 275) scale({t4_s:.2f}) rotate(-{droop_deg * 0.7:.1f})">',
        '<ellipse cx="0" cy="-14" rx="22" ry="15" fill="url(#foliage3D)"/>',
        '<ellipse cx="-14" cy="-10" rx="16" ry="12" fill="url(#foliage3D)"/>',
        '<ellipse cx="14" cy="-10" rx="16" ry="12" fill="url(#foliage3D)"/>',
        '</g>',
        f'<g class="jardin-sway-tree" opacity="{t5_o:.2f}" transform="translate(170, 272) scale({t5_s:.2f})">',
        '<ellipse cx="0" cy="-18" rx="24" ry="16" fill="url(#foliage3D)"/>',
        '<circle cx="-12" cy="-24" r="14" fill="url(#foliage3D)"/>',
        '<circle cx="12" cy="-24" r="14" fill="url(#foliage3D)"/>',
        '</g>',
        f'<g class="jardin-sway-tree-alt" opacity="{t5_o:.2f}" transform="translate(1030, 272) scale({t5_s:.2f})">',
        '<ellipse cx="0" cy="-18" rx="24" ry="16" fill="url(#foliage3D)"/>',
        '<circle cx="-12" cy="-24" r="14" fill="url(#foliage3D)"/>',
        '<circle cx="12" cy="-24" r="14" fill="url(#foliage3D)"/>',
        '</g>',
        # Flores vibrantes cuando la salud es alta
        f'<g opacity="{flowers_opacity:.2f}">',
        '<circle cx="205" cy="278" r="4.5" fill="#F472B6"/><circle cx="205" cy="278" r="2" fill="#FEF08A"/>',
        '<circle cx="268" cy="283" r="4.5" fill="#A78BFA"/><circle cx="268" cy="283" r="2" fill="#FEF08A"/>',
        '<circle cx="348" cy="280" r="4" fill="#FB7185"/><circle cx="348" cy="280" r="1.8" fill="#FEF08A"/>',
        '<circle cx="855" cy="282" r="4.5" fill="#F472B6"/><circle cx="855" cy="282" r="2" fill="#FEF08A"/>',
        '<circle cx="935" cy="279" r="4.5" fill="#A78BFA"/><circle cx="935" cy="279" r="2" fill="#FEF08A"/>',
        '<circle cx="1008" cy="284" r="4" fill="#FBBF24"/><circle cx="1008" cy="284" r="1.8" fill="#FFFFFF"/>',
        '</g>',
        # Plantas rodadoras del desierto (Tumbleweeds) rodando por la arena en escenarios críticos
        f'<g opacity="{tumbleweed_opacity:.2f}">',
        '<g class="jardin-tumbleweed-1">',
        '<circle cx="0" cy="0" r="18" fill="none" stroke="#78350F" stroke-width="2.2" stroke-dasharray="7 4"/>',
        '<ellipse cx="0" cy="0" rx="18" ry="10" fill="none" stroke="#92400E" stroke-width="1.8" transform="rotate(35)"/>',
        '<ellipse cx="0" cy="0" rx="18" ry="10" fill="none" stroke="#78350F" stroke-width="1.8" transform="rotate(-35)"/>',
        '<path d="M -12 -6 L 12 6 M -10 8 L 10 -8" stroke="#92400E" stroke-width="1.5"/>',
        '</g>',
        '<g class="jardin-tumbleweed-2">',
        '<circle cx="0" cy="0" r="14" fill="none" stroke="#78350F" stroke-width="2" stroke-dasharray="5 3"/>',
        '<ellipse cx="0" cy="0" rx="14" ry="8" fill="none" stroke="#92400E" stroke-width="1.6" transform="rotate(50)"/>',
        '<ellipse cx="0" cy="0" rx="14" ry="8" fill="none" stroke="#78350F" stroke-width="1.6" transform="rotate(-40)"/>',
        '</g>',
        '</g>',
        # =================================================================
        # PERSONAJE IZQUIERDO: CANGURO 3D ANIMADO
        # =================================================================
        '<ellipse cx="95" cy="292" rx="46" ry="10" fill="#000000" opacity="0.22"/>',
        f'<g class="{kanga_anim_class}" transform="translate(0, {posture_drop:.1f})" filter="url(#softShadow3D)">',
        # Cola 3D del canguro
        '<path d="M 58 232 Q 18 242 14 212 Q 12 196 24 198 Q 36 202 64 216 Z" fill="url(#kangaFur3D)"/>',
        # Pierna trasera y pata grande
        '<ellipse cx="72" cy="246" rx="20" ry="28" fill="url(#kangaFur3D)"/>',
        '<path d="M 58 272 L 108 272 Q 116 272 114 280 L 54 280 Q 48 276 58 272 Z" fill="url(#kangaFur3D)"/>',
        # Torso y panza 3D (se ensancha en score alto y se adelgaza en score bajo)
        f'<g transform="translate(90, 195) scale({fat_scale_x:.2f}, 1)">',
        '<ellipse cx="0" cy="0" rx="34" ry="52" fill="url(#kangaFur3D)"/>',
        '<ellipse cx="6" cy="4" rx="22" ry="40" fill="url(#kangaBelly3D)"/>',
        '</g>',
        # Costillas y huesos visibles cuando el score se acerca a 0
        f'<g opacity="{ribs_opacity:.2f}" stroke="#FEF3C7" stroke-width="2.6" stroke-linecap="round" fill="none">',
        '<path d="M 76 172 Q 92 168 104 175"/>',
        '<path d="M 74 184 Q 92 180 105 187"/>',
        '<path d="M 75 196 Q 92 192 104 199"/>',
        '<path d="M 77 208 Q 92 204 102 210"/>',
        '<circle cx="68" cy="242" r="5" fill="#FEF3C7" stroke="none"/>',
        '<line x1="68" y1="244" x2="88" y2="274" stroke="#FEF3C7" stroke-width="3.2"/>',
        '</g>',
        # Cuello y Cabeza 3D del canguro
        '<path d="M 80 152 L 90 104 L 110 108 L 104 156 Z" fill="url(#kangaFur3D)"/>',
        # Orejas (erguidas en score alto, caídas en score bajo)
        f'<ellipse cx="86" cy="64" rx="7" ry="22" fill="url(#kangaFur3D)" transform="rotate({-18 - ear_droop:.1f} 86 78)"/>',
        f'<ellipse cx="86" cy="64" rx="3.8" ry="15" fill="#FDE68A" transform="rotate({-18 - ear_droop:.1f} 86 78)"/>',
        f'<ellipse cx="106" cy="64" rx="7" ry="22" fill="url(#kangaFur3D)" transform="rotate({14 + ear_droop:.1f} 106 78)"/>',
        f'<ellipse cx="106" cy="64" rx="3.8" ry="15" fill="#FDE68A" transform="rotate({14 + ear_droop:.1f} 106 78)"/>',
        '<ellipse cx="99" cy="94" rx="22" ry="19" fill="url(#kangaFur3D)"/>',
        '<ellipse cx="112" cy="98" rx="12" ry="10" fill="url(#kangaBelly3D)"/>',
        '<circle cx="120" cy="95" r="4.5" fill="#1F2937"/>',
        kanga_eyes_svg,
        tongue_kanga_svg,
        f'<path d="{mouth_kanga}" stroke="#451A03" stroke-width="2.3" fill="none" stroke-linecap="round"/>',
        # Brazos y ramita de trébol/eucalipto
        '<path d="M 96 164 Q 122 174 128 186" stroke="#D97706" stroke-width="8" stroke-linecap="round" fill="none"/>',
        f'<g opacity="{euca_leaf_op:.2f}" transform="translate(128, 184)">',
        f'<path d="M 0 0 Q 16 -14 26 -24" stroke="#15803D" stroke-width="2.5" fill="none"/>',
        f'<ellipse cx="14" cy="-14" rx="8" ry="4.5" fill="{leaf_light}" transform="rotate(-30 14 -14)"/>',
        f'<ellipse cx="24" cy="-22" rx="8" ry="4.5" fill="{leaf_main}" transform="rotate(20 24 -22)"/>',
        '</g>',
        '</g>',
        # =================================================================
        # PERSONAJE DERECHO: KOALA 3D ANIMADO
        # =================================================================
        '<ellipse cx="1102" cy="292" rx="44" ry="10" fill="#000000" opacity="0.22"/>',
        # Tronco de eucalipto del Koala
        '<path d="M 1136 296 L 1144 125 L 1160 125 L 1154 296 Z" fill="url(#trunk3D)" filter="url(#softShadow3D)"/>',
        '<path d="M 1146 165 Q 1115 145 1085 152" stroke="#78350F" stroke-width="8" stroke-linecap="round" fill="none"/>',
        f'<g class="{koala_anim_class}" transform="translate(0, {posture_drop:.1f})" filter="url(#softShadow3D)">',
        # Cuerpo 3D del Koala (se ensancha en score alto y se adelgaza en score bajo)
        f'<g transform="translate(1102, 202) scale({fat_scale_x:.2f}, 1)">',
        '<ellipse cx="0" cy="0" rx="38" ry="46" fill="url(#koalaFur3D)"/>',
        '<ellipse cx="-2" cy="6" rx="25" ry="34" fill="url(#koalaBelly3D)"/>',
        '</g>',
        # Costillas y huesos visibles en el Koala cuando el score se acerca a 0
        f'<g opacity="{ribs_opacity:.2f}" stroke="#F3F4F6" stroke-width="2.6" stroke-linecap="round" fill="none">',
        '<path d="M 1086 182 Q 1102 177 1118 182"/>',
        '<path d="M 1084 194 Q 1102 189 1120 194"/>',
        '<path d="M 1085 206 Q 1102 201 1119 206"/>',
        '<path d="M 1088 218 Q 1102 213 1116 218"/>',
        '<circle cx="1078" cy="242" r="4.5" fill="#F3F4F6" stroke="none"/>',
        '<line x1="1078" y1="242" x2="1096" y2="266" stroke="#F3F4F6" stroke-width="3"/>',
        '</g>',
        # Patas y brazos del Koala
        '<ellipse cx="1076" cy="242" rx="14" ry="18" fill="url(#koalaFur3D)"/>',
        '<ellipse cx="1126" cy="242" rx="14" ry="18" fill="url(#koalaFur3D)"/>',
        '<ellipse cx="1072" cy="176" rx="13" ry="11" fill="url(#koalaFur3D)"/>',
        '<ellipse cx="1132" cy="176" rx="13" ry="11" fill="url(#koalaFur3D)"/>',
        # Orejas redondas peludas del Koala
        f'<circle cx="1068" cy="{82 + int(ear_droop * 0.35)}" r="18" fill="url(#koalaFur3D)"/>',
        f'<circle cx="1068" cy="{82 + int(ear_droop * 0.35)}" r="10" fill="#E5E7EB"/>',
        f'<circle cx="1136" cy="{82 + int(ear_droop * 0.35)}" r="18" fill="url(#koalaFur3D)"/>',
        f'<circle cx="1136" cy="{82 + int(ear_droop * 0.35)}" r="10" fill="#E5E7EB"/>',
        # Cabeza y nariz icónica 3D del Koala
        '<ellipse cx="1102" cy="100" rx="32" ry="27" fill="url(#koalaFur3D)"/>',
        '<ellipse cx="1102" cy="102" rx="9" ry="13" fill="#1F2937"/>',
        '<ellipse cx="1099" cy="98" rx="3" ry="4.5" fill="#4B5563"/>',
        koala_eyes_svg,
        tongue_koala_svg,
        f'<path d="{mouth_koala}" stroke="#1F2937" stroke-width="2.3" fill="none" stroke-linecap="round"/>',
        # Hojita de eucalipto en la mano del Koala
        f'<g opacity="{euca_leaf_op:.2f}" transform="translate(1062, 168)">',
        f'<ellipse cx="0" cy="0" rx="11" ry="6" fill="{leaf_light}" transform="rotate(-25)"/>',
        '</g>',
        '</g>',
        '</svg>',
        # Contenido central legible con efecto cristal (glassmorphism) sobre la escena 3D
        '<div class="jardin-health-overlay">',
        '<div class="kpi-title" style="font-size: 1.28rem; color: #1F2937;">Patrimonio Total</div>',
        f'<div class="kpi-value" style="font-size: 2.35rem; color: #111827;">{total_patrimonio_ars:,.0f} ARS</div>',
        f'<div class="kpi-usd" style="font-size: 1.18rem; color: #1F2937; background: rgba(255,255,255,0.88);">{total_patrimonio_usd:,.2f} USD</div>',
        f'<div class="kpi-sub" style="color: #374151; font-weight: 700;">{cant_activos_contemplados} activos de {cant_activos_totales} contemplados</div>',
        f'<div class="jardin-runway-box" style="background: {badge_bg}; color: {badge_text}; border-color: {border_col};">',
        f'<div style="font-size: 1.12rem; font-weight: 800; margin-bottom: 3px;">⏱️ Autonomía Financiera (Runway): {runway_display}</div>',
        f'<div style="font-size: 0.88rem; font-weight: 700; opacity: 0.92; margin-bottom: 5px;">'
        f'Patrimonio: {total_patrimonio_ars:,.0f} ARS &nbsp;÷&nbsp; Costo mensual de vida: {costo_mensual_ars:,.0f} ARS '
        f'(Tasa aplicada: 1 USD = {dolar_b:,.0f} ARS)'
        f'</div>',
        f'<div style="font-size: 0.98rem; font-weight: 800; line-height: 1.35;">{mensaje_salud}</div>',
        '<div class="jardin-health-bar-track">',
        f'<div class="jardin-health-bar-fill" style="width: {pct_salud}%; background: {border_col};"></div>',
        '</div>',
        '</div>',
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

UBICACIONES_BASE = [
    "Bco Nacion", "Uala", "Mercado Pago", "Binance",
    "IOL", "Naranja X", "NEXO", "Kraken"
]


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
    filtradas = [u for u in actuales if str(u).strip().lower() != loc.lower()]
    filtradas.insert(0, loc)
    datos["ubicaciones_guardadas"] = filtradas[:8]
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
        "ubicaciones_guardadas": list(UBICACIONES_BASE),
        "ultimas_selecciones_inv": {
            "tipo": "Dólares USD",
            "accion": "AAPL (Apple)",
            "cripto": "BTC (Bitcoin)",
            "ubicacion": "Bco Nacion"
        },
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

            for inv in data.get("inversiones", []):
                inv.setdefault("activo_inv", True)
                if inv.get("tipo") == "Acciones / CEDEARs":
                    inv["tipo"] = "Acciones"
                elif inv.get("tipo") == "Efectivo / Banco":
                    inv["tipo"] = "Pesos ARS"
                elif inv.get("tipo") in ["Dólar Billete", "A - Dólar Billete"]:
                    inv["tipo"] = "Dólares USD"

                if inv.get("activo") in ["Dólar Billete", "A - Dólar Billete"]:
                    inv["activo"] = "Dólares USD"

                # Sincronizar símbolo con el detalle en caso de ediciones previas (ej. ETH con símbolo BTC)
                if inv.get("tipo") in ["Criptomonedas", "Acciones"]:
                    det_ticker = str(inv.get("activo", "")).strip().split(" ")[0].upper()
                    if det_ticker and det_ticker not in ["USD", "ARS"]:
                        inv["simbolo"] = det_ticker

            criptos_guardadas_raw = data.get("criptos_guardadas", criptos_base)
            for inv in data.get("inversiones", []):
                if inv.get("tipo") == "Criptomonedas":
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

            # Inicializar y conservar las últimas 8 ubicaciones distintas (más reciente primero)
            ubic_guardadas = data.get("ubicaciones_guardadas", [])
            if not isinstance(ubic_guardadas, list):
                ubic_guardadas = []
            if not ubic_guardadas:
                # Tomar las plataformas ya cargadas en inversiones (de más reciente a más antigua) + base
                for inv in reversed(data.get("inversiones", [])):
                    pl = str(inv.get("plataforma", "")).strip()
                    if pl and pl.lower() != "sin especificar":
                        if not any(pl.lower() == u.lower() for u in ubic_guardadas):
                            ubic_guardadas.append(pl)
                for ub in UBICACIONES_BASE:
                    if not any(ub.lower() == u.lower() for u in ubic_guardadas):
                        ubic_guardadas.append(ub)
            data["ubicaciones_guardadas"] = ubic_guardadas[:8]

            ult_sel = data.get("ultimas_selecciones_inv", {})
            if not isinstance(ult_sel, dict):
                ult_sel = {}
            if ult_sel.get("tipo") in ["A - Dólar Billete", "Dólar Billete", None, ""]:
                ult_sel["tipo"] = "Dólares USD"
            ult_sel.setdefault("accion", data["acciones_guardadas"][0] if data["acciones_guardadas"] else "AAPL (Apple)")
            ult_sel.setdefault("cripto", data["criptos_guardadas"][0] if data["criptos_guardadas"] else "BTC (Bitcoin)")
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
        tipo = inv.get("tipo", "Pesos ARS")
        simbolo = inv.get("simbolo", "").upper().strip()
        if tipo in ["Dólares USD", "Dólar Billete"]:
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

    /* Escena animada 3D de Salud Financiera (Patrimonio Total y Runway) */
    .jardin-health-scene {
        position: relative;
        border-radius: 22px;
        border: 3px solid #22C55E;
        overflow: hidden;
        margin-bottom: 1.1rem;
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.14), inset 0 2px 8px rgba(255, 255, 255, 0.35);
        min-height: 290px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 18px 175px;
    }
    .jardin-scene-svg {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        z-index: 1;
        pointer-events: none;
    }
    .jardin-health-overlay {
        position: relative;
        z-index: 2;
        background: rgba(255, 255, 255, 0.84);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1.5px solid rgba(255, 255, 255, 0.92);
        border-radius: 18px;
        padding: 14px 24px;
        text-align: center;
        max-width: 680px;
        width: 100%;
        box-shadow: 0 8px 24px rgba(17, 24, 39, 0.12);
    }
    .jardin-runway-box {
        margin-top: 10px;
        padding: 10px 14px;
        border-radius: 13px;
        border: 1.5px solid;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06);
    }
    .jardin-health-bar-track {
        width: 100%;
        height: 8px;
        background: rgba(255, 255, 255, 0.75);
        border-radius: 999px;
        overflow: hidden;
        margin-top: 7px;
        border: 1px solid rgba(0,0,0,0.08);
    }
    .jardin-health-bar-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.5s ease;
    }

    @keyframes jardinTreeSway {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-2px) rotate(2.2deg); }
    }
    @keyframes jardinKangaBounce {
        0%, 100% { transform: translateY(0px) scaleY(1); }
        45% { transform: translateY(-10px) scaleY(1.03); }
        55% { transform: translateY(-10px) scaleY(1.03); }
    }
    @keyframes jardinKoalaSway {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-4px) rotate(-2.5deg); }
    }
    @keyframes jardinTiredBreath {
        0%, 100% { transform: translateY(8px) scaleY(0.98); }
        50% { transform: translateY(11px) scaleY(0.95); }
    }
    @keyframes jardinCollapseTremble {
        0%, 100% { transform: translateY(16px) rotate(-4deg); }
        25% { transform: translateY(17px) rotate(-5.2deg); }
        75% { transform: translateY(16px) rotate(-2.8deg); }
    }
    @keyframes jardinSunFireSpin {
        0% { transform: rotate(0deg) scale(1); }
        50% { transform: translateY(-1px) rotate(180deg) scale(1.09); }
        100% { transform: rotate(360deg) scale(1); }
    }
    @keyframes jardinTumbleweedRoll1 {
        0% { transform: translate(160px, 278px) rotate(0deg); }
        25% { transform: translate(420px, 262px) rotate(180deg); }
        50% { transform: translate(680px, 280px) rotate(360deg); }
        75% { transform: translate(910px, 264px) rotate(540deg); }
        100% { transform: translate(1080px, 279px) rotate(720deg); }
    }
    @keyframes jardinTumbleweedRoll2 {
        0% { transform: translate(260px, 285px) rotate(0deg); }
        50% { transform: translate(640px, 270px) rotate(360deg); }
        100% { transform: translate(990px, 284px) rotate(720deg); }
    }

    .jardin-kanga-happy {
        animation: jardinKangaBounce 2.4s ease-in-out infinite;
        transform-origin: 95px 280px;
    }
    .jardin-koala-happy {
        animation: jardinKoalaSway 2.8s ease-in-out infinite;
        transform-origin: 1102px 240px;
    }
    .jardin-animal-tired {
        animation: jardinTiredBreath 3.4s ease-in-out infinite;
        transform-origin: center bottom;
    }
    .jardin-animal-collapse {
        animation: jardinCollapseTremble 1.6s ease-in-out infinite;
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

    @media (prefers-reduced-motion: reduce) {
        .jardin-kanga-happy,
        .jardin-koala-happy,
        .jardin-animal-tired,
        .jardin-animal-collapse,
        .jardin-sun-flames,
        .jardin-tumbleweed-1,
        .jardin-tumbleweed-2 {
            animation: none !important;
        }
    }

    @media (max-width: 768px) {
        .jardin-health-scene {
            padding: 14px 12px !important;
            min-height: 320px !important;
        }
        .jardin-health-overlay {
            padding: 12px 14px !important;
            background: rgba(255, 255, 255, 0.88) !important;
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

# ----------------- PANTALLA DE LOGIN Y RECUPERACIÓN SEGURA (REQ 6) -----------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
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
    if inv.get("tipo") == "Acciones"
]

tickers_cri = [
    str(inv.get("simbolo", "BTC")).split(" ")[0].upper().strip()
    for inv in datos.get("inversiones", [])
    if inv.get("tipo") == "Criptomonedas"
]

cotizaciones = obtener_cotizaciones(tuple(tickers_acc), tuple(tickers_cri))
dolar_b = cotizaciones["dolar_blue"]

# ----------------- SIDEBAR Y CIERRE DE SESIÓN (REQ 4) -----------------
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
    filas = []

    for inv in inversiones:
        cant = float(inv.get("cantidad", 0))
        tipo_raw = inv.get("tipo", "Pesos ARS")
        tipo = "Dólares USD" if tipo_raw in ["Dólar Billete", "A - Dólar Billete", "Dólares USD"] else tipo_raw
        activo_nom = inv.get("activo", tipo)
        if activo_nom in ["Dólar Billete", "A - Dólar Billete"]:
            activo_nom = "Dólares USD"

        simbolo = str(inv.get("simbolo", "")).upper().strip().split(" ")[0]
        if tipo in ["Criptomonedas", "Acciones"]:
            det_t = str(activo_nom).strip().split(" ")[0].upper()
            if det_t and det_t not in ["USD", "ARS"]:
                simbolo = det_t

        esta_activo = inv.get("activo_inv", True)

        if tipo == "Dólares USD":
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
            "Activo": activo_nom,
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

    # Calcular el costo mensual de vida en ARS en vivo desde la pestaña "Costos e Ingresos"
    costos_activos_live = [c for c in datos.get("costos", []) if c.get("activo", True)]
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

    hay_activo_usd = any(
        inv.get("activo_inv", True) and inv.get("tipo") in ["Dólares USD", "Dólar Billete", "A - Dólar Billete", "Criptomonedas", "Acciones"]
        for inv in inversiones
    )
    hay_moneda_ext = hay_costo_usd or hay_activo_usd

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
        costo_mensual_ars=costo_mensual_vivir_ars,
        dolar_b=dolar_b,
        hay_moneda_extranjera=hay_moneda_ext
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
            "Dólares USD",
            "B - Pesos ARS",
            "C - Acciones",
            "D - Criptomonedas",
            "E - Otros"
        ]

        ult_sel = datos.setdefault("ultimas_selecciones_inv", {
            "tipo": "Dólares USD",
            "accion": "AAPL (Apple)",
            "cripto": "BTC (Bitcoin)",
            "ubicacion": (datos.get("ubicaciones_guardadas") or ["Bco Nacion"])[0]
        })

        tipo_guardado = ult_sel.get("tipo", "Dólares USD")
        if tipo_guardado not in opciones_tipo:
            tipo_guardado = "Dólares USD"

        if "_pending_inv_widget_sync" in st.session_state:
            for k_sync, v_sync in st.session_state.pop("_pending_inv_widget_sync").items():
                st.session_state[k_sync] = v_sync

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

        simbolo_elegido = "USD"
        detalle_manual = ""

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
        elif tipo_elegido == "D - Criptomonedas":
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
        elif tipo_elegido == "E - Otros":
            detalle_manual = st.text_input(
                "Detalle qué es (ej. FRASCO NX, FCI, PF UVA)",
                key="inv_detalle_manual_otros"
            )

        if "inv_ubicacion_input" not in st.session_state:
            st.session_state["inv_ubicacion_input"] = ult_sel.get(
                "ubicacion",
                (datos.get("ubicaciones_guardadas") or ["Bco Nacion"])[0]
            )

        def on_enter_ubicacion_inv():
            val_u = st.session_state.get("inv_ubicacion_input", "").strip()
            if val_u:
                registrar_ubicacion_guardada(datos, val_u)
                guardar_datos(datos)

        plat_act = st.text_input(
            "2. Ubicación, ¿dónde está?",
            key="inv_ubicacion_input",
            on_change=on_enter_ubicacion_inv
        )

        with st.form("form_guardar_activo_inv", clear_on_submit=True):
            cant_texto = st.text_input(
                "3. Cantidad que tenés",
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
                    if tipo_elegido == "Dólares USD":
                        tipo_guardar = "Dólares USD"
                        nombre_act = "Dólares USD"
                        simbolo_final = "USD"
                    elif tipo_elegido == "B - Pesos ARS":
                        tipo_guardar = "Pesos ARS"
                        nombre_act = "Pesos ARS"
                        simbolo_final = "ARS"
                    elif tipo_elegido == "C - Acciones":
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
                    elif tipo_elegido == "D - Criptomonedas":
                        tipo_guardar = "Criptomonedas"
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
                    else:
                        tipo_guardar = "Otros"
                        nombre_act = detalle_manual.strip() if detalle_manual.strip() else "Otros"
                        simbolo_final = "ARS"
                        if detalle_manual.strip():
                            st.session_state["_pending_inv_widget_sync"] = {
                                "inv_detalle_manual_otros": ""
                            }

                    ubicacion_final = plat_act.strip() if plat_act.strip() else "Sin especificar"
                    if plat_act.strip():
                        registrar_ubicacion_guardada(datos, plat_act.strip())

                    datos.setdefault("ultimas_selecciones_inv", {})["tipo"] = tipo_elegido

                    datos["inversiones"].append({
                        "tipo": tipo_guardar,
                        "activo": nombre_act,
                        "simbolo": simbolo_final,
                        "cantidad": int(cant_num) if cant_num.is_integer() else cant_num,
                        "plataforma": ubicacion_final,
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
            "Dólares USD",
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
                    if ("Dólares USD" if inv.get("tipo") in ["Dólar Billete", "A - Dólar Billete", "Dólares USD"] else inv.get("tipo", "Otros")) == cat_inv
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
                            val_detalle_mostrar = "Dólares USD" if inv.get("activo", "") in ["Dólar Billete", "A - Dólar Billete"] else inv.get("activo", "")
                            st.text_input(
                                "Detalle",
                                value=val_detalle_mostrar,
                                key=f"inv_nom_{idx}",
                                label_visibility="collapsed",
                                disabled=True
                            )

                        with c_cant:
                            cant_str_actual = formatear_cant(inv.get("cantidad", 0)).replace(",", "")
                            st.text_input(
                                "Cantidad",
                                value=cant_str_actual,
                                key=f"inv_cant_{idx}",
                                label_visibility="collapsed",
                                disabled=True
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
    datos.get('ubicaciones_guardadas', [])
)
