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


# ----------------- INTERACTIVIDAD: DRAG & DROP INFINITO, CONECTORES TORTA Y ANTI-POPUP -----------------
def activar_interactividad_avanzada(cats_costos=None, cats_ingresos=None):
    js_code = """
    <script>
    (function() {
        const win = window.parent;
        const doc = win.document;

        // Inyectamos el motor directamente en window.parent.document.head
        // para que viva en la ventana principal y NUNCA muera al cambiar de pantalla o re-renderizar iframes.
        const engineCode = `
        (function() {
            const win = window;
            const doc = document;

            if (win.__jardinCleanup) {
                try { win.__jardinCleanup(); } catch (e) {}
            }

            const abortCtrl = new AbortController();
            const sig = abortCtrl.signal;

            function closestEl(node, selector) {
                let el = (node && node.nodeType === 1) ? node : (node ? node.parentElement : null);
                return (el && el.closest) ? el.closest(selector) : null;
            }

            // 1. Ocultar "Press Enter to apply" y blindar inputs contra el popup de contraseñas guardadas (Req 5)
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

                    // En el panel lateral ("Mis Datos de Recuperación"), evitar que Chrome/Brave abra el gestor de contraseñas
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

            // 2. Diseño moderno tipo cápsula tecnológica para las solapas de AGREGAR NUEVA CATEGORÍA
            function estilizarSolapasCategorias() {
                const todosDetails = Array.from(doc.querySelectorAll('details'));
                todosDetails.forEach(det => {
                    const sum = det.querySelector('summary');
                    if (!sum) return;
                    const txt = (sum.innerText || '').toUpperCase();

                    if (txt.includes('AGREGAR NUEVA CATEGORÍA DE COSTOS')) {
                        det.style.background = 'linear-gradient(135deg, #FFF5F5 0%, #FFE3E3 100%)';
                        det.style.border = '1.5px solid #FDA4AF';
                        det.style.borderRadius = det.open ? '22px' : '999px';
                        det.style.marginBottom = '12px';
                        det.style.boxShadow = '0 6px 18px rgba(244, 63, 94, 0.12)';
                        det.style.transition = 'all 0.25s ease';
                        sum.style.background = 'linear-gradient(135deg, #FFE4E6 0%, #FECDD3 100%)';
                        sum.style.color = '#881337';
                        sum.style.fontWeight = '800';
                        sum.style.borderRadius = det.open ? '20px 20px 12px 12px' : '999px';
                        sum.style.padding = '11px 18px';
                        sum.querySelectorAll('p, span').forEach(el => {
                            el.style.color = '#881337';
                            el.style.fontWeight = '800';
                        });
                    } else if (txt.includes('AGREGAR NUEVA CATEGORÍA DE INGRESOS')) {
                        det.style.background = 'linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%)';
                        det.style.border = '1.5px solid #6EE7B7';
                        det.style.borderRadius = det.open ? '22px' : '999px';
                        det.style.marginBottom = '12px';
                        det.style.boxShadow = '0 6px 18px rgba(16, 185, 129, 0.12)';
                        det.style.transition = 'all 0.25s ease';
                        sum.style.background = 'linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%)';
                        sum.style.color = '#064E3B';
                        sum.style.fontWeight = '800';
                        sum.style.borderRadius = det.open ? '20px 20px 12px 12px' : '999px';
                        sum.style.padding = '11px 18px';
                        sum.querySelectorAll('p, span').forEach(el => {
                            el.style.color = '#064E3B';
                            el.style.fontWeight = '800';
                        });
                    }
                });
            }

            // 3. Asegurar líneas conectoras (estilo Impuestos) en todas las etiquetas externas del gráfico de torta (Req 4)
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
                                // Obtener posición real considerando transformaciones de Plotly sobre g.slicetext o text
                                const textNode = stext.querySelector('text') || stext;
                                let tx = tb.x + tb.width / 2;
                                let ty = tb.y + tb.height / 2;
                                const trAttr = textNode.getAttribute('transform') || stext.getAttribute('transform') || '';
                                const m = trAttr.match(/translate\\(\\s*([-0-9.]+)[,\\s]+([-0-9.]+)/);
                                if (m && Math.abs(tb.x) < 60 && Math.abs(tb.y) < 60) {
                                    tx = parseFloat(m[1]);
                                    ty = parseFloat(m[2]);
                                }

                                const dist = Math.hypot(tx - cx, ty - cy);

                                // Si la etiqueta está fuera del círculo exterior de la torta, dibujar línea conectora con codo
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

            // 4. Etiquetar todos los bloques de categorías
            function obtenerBloqueMovible(det, refDet) {
                let curr = det;
                while (curr && curr.parentElement && !curr.parentElement.contains(refDet)) {
                    curr = curr.parentElement;
                }
                return curr;
            }

            function etiquetarCategorias() {
                limpiarInputsYPopups();
                estilizarSolapasCategorias();
                asegurarLineasConectorasTortas();

                const expanders = Array.from(doc.querySelectorAll('details'));
                const detsPorTipo = { costo: [], ingreso: [] };

                const h3s = Array.from(doc.querySelectorAll('h3'));
                const h3Ingresos = h3s.find(el => (el.innerText || '').includes('Mis Ingresos Mensuales'));

                expanders.forEach(det => {
                    const summary = det.querySelector('summary');
                    if (!summary) return;
                    const texto = summary.innerText || summary.textContent || '';
                    if (!texto.includes('Subtotal:') || !texto.includes('⠿')) return;

                    const rawTc = summary.textContent || '';
                    let tipo = 'costo';
                    if (rawTc.includes('\\u200c')) {
                        tipo = 'ingreso';
                    } else if (rawTc.includes('\\u200b')) {
                        tipo = 'costo';
                    } else if (h3Ingresos) {
                        const pos = h3Ingresos.compareDocumentPosition(det);
                        tipo = (pos & Node.DOCUMENT_POSITION_FOLLOWING) ? 'ingreso' : 'costo';
                    }

                    let catNombre = '';
                    const strongEl = summary.querySelector('strong');
                    if (strongEl && strongEl.innerText) {
                        catNombre = strongEl.innerText.replace(/[\\u200b\\u200c]/g, '').trim();
                    } else {
                        const parte = texto.split('— Subtotal:')[0].replace('⠿', '').replace(/[\\u200b\\u200c]/g, '').trim();
                        const tokens = parte.split(' ');
                        if (tokens.length > 1) tokens.shift();
                        catNombre = tokens.join(' ').trim();
                    }

                    det.setAttribute('data-cat-nombre', catNombre);
                    det.setAttribute('data-cat-tipo', tipo);
                    det.setAttribute('draggable', 'false');

                    summary.style.cursor = 'grab';
                    summary.style.userSelect = 'none';
                    summary.style.webkitUserSelect = 'none';
                    summary.style.touchAction = 'none';
                    summary.setAttribute('draggable', 'false');

                    detsPorTipo[tipo].push(det);
                });

                ['costo', 'ingreso'].forEach(tipo => {
                    const listaDets = detsPorTipo[tipo];
                    if (listaDets.length < 2) return;
                    listaDets.forEach((d, i) => {
                        const otro = listaDets[i === 0 ? 1 : 0];
                        const b = obtenerBloqueMovible(d, otro);
                        if (b) {
                            b.setAttribute('data-cat-block-tipo', tipo);
                            b.setAttribute('data-cat-block-nombre', d.getAttribute('data-cat-nombre'));
                        }
                    });
                });
            }

            win.__jardinEtiquetar = etiquetarCategorias;

            // 5. Navegación con flechas Arriba/Abajo entre inputs
            doc.addEventListener('keydown', function(e) {
                const active = doc.activeElement;
                if (!active || active.tagName !== 'INPUT') return;

                if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                    const inputs = Array.from(
                        doc.querySelectorAll(
                            'input:not([disabled]):not([type="hidden"]):not([type="checkbox"])'
                        )
                    ).filter(el => el.offsetParent !== null &&
                                   el.placeholder !== 'SYNC_ORDEN_COSTOS' &&
                                   el.placeholder !== 'SYNC_ORDEN_INGRESOS');

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

            // 6. Enviar nuevo orden a Streamlit (compatible con React 18)
            function enviarNuevoOrdenAStreamlit(placeholderKey, nuevoOrdenArray) {
                const inputs = Array.from(doc.querySelectorAll('input[type="text"]'));
                const targetInput = inputs.find(
                    el => el.placeholder === placeholderKey || el.getAttribute('aria-label') === placeholderKey
                );
                if (!targetInput) return;

                const valorJson = JSON.stringify({ orden: nuevoOrdenArray, ts: Date.now() });

                targetInput.readOnly = false;
                targetInput.focus({ preventScroll: true });

                const nativeSetter = Object.getOwnPropertyDescriptor(
                    win.HTMLInputElement.prototype,
                    'value'
                ).set;
                nativeSetter.call(targetInput, valorJson);

                if (targetInput._valueTracker) {
                    targetInput._valueTracker.setValue('');
                }

                targetInput.dispatchEvent(new win.Event('input', { bubbles: true, composed: true }));
                targetInput.dispatchEvent(new win.Event('change', { bubbles: true, composed: true }));

                setTimeout(() => {
                    targetInput.focus({ preventScroll: true });
                    const enterOpts = {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        charCode: 13,
                        bubbles: true,
                        cancelable: true,
                        composed: true
                    };
                    targetInput.dispatchEvent(new win.KeyboardEvent('keydown', enterOpts));
                    targetInput.dispatchEvent(new win.KeyboardEvent('keypress', enterOpts));
                    targetInput.dispatchEvent(new win.KeyboardEvent('keyup', enterOpts));
                    targetInput.blur();
                }, 45);
            }

            // 7. Drag & Drop infinito en window.parent (Mouse, Pad de Notebook y Táctil Android)
            let dragState = null;
            let suppressNextSummaryClick = false;

            doc.addEventListener('dragstart', function(e) {
                const sum = closestEl(e.target, 'summary');
                if (sum && (sum.innerText || '').includes('⠿')) {
                    e.preventDefault();
                }
            }, { capture: true, signal: sig });

            doc.addEventListener('pointerdown', function(e) {
                if (e.button !== undefined && e.button !== 0) return;
                const tgtEl = (e.target && e.target.nodeType === 1) ? e.target : (e.target ? e.target.parentElement : null);
                if (!tgtEl) return;
                if (['INPUT', 'SELECT', 'BUTTON', 'TEXTAREA'].includes(tgtEl.tagName)) return;

                const summary = closestEl(tgtEl, 'summary');
                if (!summary) return;
                const texto = summary.innerText || summary.textContent || '';
                if (!texto.includes('Subtotal:') || !texto.includes('⠿')) return;

                etiquetarCategorias();

                const det = closestEl(summary, 'details');
                if (!det) return;
                const tipo = det.getAttribute('data-cat-tipo');
                const block = closestEl(det, '[data-cat-block-tipo="' + tipo + '"]');
                if (!block || !block.parentElement) return;

                const sharedParent = block.parentElement;
                const bloquesIniciales = Array.from(
                    sharedParent.querySelectorAll('[data-cat-block-tipo="' + tipo + '"]')
                );
                if (bloquesIniciales.length < 2) return;

                dragState = {
                    summary: summary,
                    det: det,
                    block: block,
                    tipo: tipo,
                    sharedParent: sharedParent,
                    ordenNombresInicial: bloquesIniciales.map(b => b.getAttribute('data-cat-block-nombre')),
                    startY: e.clientY,
                    pointerId: e.pointerId,
                    isDragging: false
                };
            }, { capture: true, signal: sig });

            doc.addEventListener('pointermove', function(e) {
                if (!dragState) return;
                const dy = e.clientY - dragState.startY;

                if (!dragState.isDragging && Math.abs(dy) > 4) {
                    dragState.isDragging = true;
                    try {
                        if (dragState.pointerId !== null && dragState.summary.setPointerCapture) {
                            dragState.summary.setPointerCapture(dragState.pointerId);
                        }
                    } catch (err) {}
                    dragState.summary.style.cursor = 'grabbing';
                    dragState.block.style.opacity = '0.84';
                    dragState.block.style.transform = 'scale(1.01)';
                    dragState.block.style.boxShadow = '0 12px 28px rgba(124, 58, 237, 0.26)';
                    dragState.block.style.zIndex = '999';
                    dragState.block.style.position = 'relative';
                }

                if (dragState.isDragging) {
                    if (e.cancelable) e.preventDefault();
                    const { sharedParent, tipo, block } = dragState;
                    const otros = Array.from(
                        sharedParent.querySelectorAll('[data-cat-block-tipo="' + tipo + '"]')
                    ).filter(h => h !== block);

                    if (otros.length > 0) {
                        let siguiente = null;
                        for (const herm of otros) {
                            const rect = herm.getBoundingClientRect();
                            const centro = rect.top + rect.height / 2;
                            if (e.clientY < centro) {
                                siguiente = herm;
                                break;
                            }
                        }
                        if (siguiente) {
                            if (block.nextElementSibling !== siguiente) {
                                sharedParent.insertBefore(block, siguiente);
                            }
                        } else {
                            const ultimo = otros[otros.length - 1];
                            if (ultimo.nextElementSibling !== block) {
                                sharedParent.insertBefore(block, ultimo.nextSibling);
                            }
                        }
                    }
                }
            }, { passive: false, capture: true, signal: sig });

            function finalizarDragGlobal(e) {
                if (!dragState) return;
                const st = dragState;
                dragState = null;

                if (st.isDragging) {
                    try {
                        if (st.pointerId !== null && st.summary.releasePointerCapture) {
                            st.summary.releasePointerCapture(st.pointerId);
                        }
                    } catch (err) {}

                    st.summary.style.cursor = 'grab';
                    st.block.style.opacity = '1';
                    st.block.style.transform = 'none';
                    st.block.style.boxShadow = 'none';
                    st.block.style.zIndex = '';

                    suppressNextSummaryClick = true;
                    setTimeout(() => { suppressNextSummaryClick = false; }, 300);

                    const nuevoOrden = Array.from(
                        st.sharedParent.querySelectorAll('[data-cat-block-tipo="' + st.tipo + '"]')
                    ).map(el => el.getAttribute('data-cat-block-nombre')).filter(Boolean);

                    if (JSON.stringify(nuevoOrden) !== JSON.stringify(st.ordenNombresInicial)) {
                        const placeholderKey = st.tipo === 'costo' ? 'SYNC_ORDEN_COSTOS' : 'SYNC_ORDEN_INGRESOS';
                        enviarNuevoOrdenAStreamlit(placeholderKey, nuevoOrden);
                    }
                }
            }

            doc.addEventListener('pointerup', finalizarDragGlobal, { capture: true, signal: sig });
            doc.addEventListener('pointercancel', finalizarDragGlobal, { capture: true, signal: sig });

            doc.addEventListener('click', function(e) {
                if (suppressNextSummaryClick) {
                    const sum = closestEl(e.target, 'summary');
                    if (sum) {
                        e.preventDefault();
                        e.stopPropagation();
                        suppressNextSummaryClick = false;
                    }
                }
            }, { capture: true, signal: sig });

            let timerObs = null;
            const obs = new MutationObserver(() => {
                clearTimeout(timerObs);
                timerObs = setTimeout(() => {
                    if (!dragState) {
                        etiquetarCategorias();
                    }
                }, 110);
            });
            obs.observe(doc.body, { childList: true, subtree: true });

            win.__jardinCleanup = function() {
                abortCtrl.abort();
                obs.disconnect();
            };

            etiquetarCategorias();
            setTimeout(etiquetarCategorias, 180);
            setTimeout(etiquetarCategorias, 500);
        })();
        `;

        if (!win.__jardinEngineVersion || win.__jardinEngineVersion !== 5) {
            win.__jardinEngineVersion = 5;
            const prevScript = doc.getElementById('jardin-parent-engine');
            if (prevScript) prevScript.remove();
            const scriptEl = doc.createElement('script');
            scriptEl.id = 'jardin-parent-engine';
            scriptEl.textContent = engineCode;
            (doc.head || doc.documentElement).appendChild(scriptEl);
        } else if (win.__jardinEtiquetar) {
            win.__jardinEtiquetar();
            setTimeout(win.__jardinEtiquetar, 150);
            setTimeout(win.__jardinEtiquetar, 450);
        }
    })();
    </script>
    """
    components.html(js_code, height=0, width=0)


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


# ----------------- ESTILOS CSS OPTIMIZADOS (LAPTOP + ANDROID) -----------------
st.markdown("""
<style>
    html, body, [class*="css"], p, span, label, div {
        font-size: 16px;
        color: #374151;
    }

    /* Ocultar TODOS los carteles "Press Enter to apply" / "Press Enter to submit" (Req 3) */
    div[data-testid="InputInstructions"],
    [data-testid="InputInstructions"],
    div[data-testid="InputInstructions"] > span {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0px !important;
        width: 0px !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }

    /* Aprovechar al máximo el ancho de la pantalla en notebook y celular */
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

    /* Solapas principales estilo Cápsula Tecnológica Flotante (Req 7) */
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
        height: 0px !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 14px !important;
        margin-bottom: 1.35rem !important;
        padding: 8px 10px !important;
        background: linear-gradient(135deg, rgba(234, 246, 238, 0.9) 0%, rgba(243, 232, 255, 0.95) 100%) !important;
        border-radius: 999px !important;
        border: 1.5px solid rgba(192, 132, 252, 0.35) !important;
        box-shadow: 0 10px 28px rgba(91, 75, 138, 0.10), inset 0 1px 2px rgba(255, 255, 255, 0.9) !important;
        width: fit-content !important;
        max-width: 100% !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 54px !important;
        padding: 10px 28px !important;
        background: rgba(255, 255, 255, 0.72) !important;
        border-radius: 999px !important;
        border: 1px solid rgba(216, 180, 254, 0.45) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1) !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.96) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(124, 58, 237, 0.15) !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #5B21B6 0%, #7C3AED 52%, #2D6A4F 100%) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.65) !important;
        box-shadow: 0 8px 22px rgba(124, 58, 237, 0.38) !important;
        transform: translateY(-1px) !important;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        color: #4A235A !important;
        text-transform: uppercase !important;
        letter-spacing: 0.7px !important;
        margin: 0 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.22) !important;
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
        font-size: 0.95rem;
        font-weight: 600;
        opacity: 0.9;
        margin-top: 0.45rem;
    }

    /* Encabezado de tabla en un solo renglón sin cortarse nunca (ACT.) */
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

    div[data-testid="stButton"] button,
    div[data-testid="stDownloadButton"] button {
        border-radius: 10px !important;
        border: 1px solid #D1D5DB !important;
        background-color: #FFFFFF !important;
        padding: 0.4rem 0.65rem !important;
        min-width: 44px !important;
        min-height: 44px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stButton"] button p,
    div[data-testid="stDownloadButton"] button p {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        line-height: 1.1 !important;
        margin: 0 !important;
        overflow: visible !important;
    }
    div[data-testid="stButton"] button:hover,
    div[data-testid="stDownloadButton"] button:hover {
        background-color: #F3E8FF !important;
        border-color: #C084FC !important;
    }

    details {
        border-radius: 18px !important;
        border: 1px solid #E5E7EB !important;
        background: #FFFFFF !important;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.03) !important;
        transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
    }
    details:hover {
        border-color: #C084FC !important;
        box-shadow: 0 6px 16px rgba(124, 58, 237, 0.08) !important;
    }

    /* Ocultar los inputs puente usados para sincronizar el Drag & Drop */
    div[data-testid="stTextInput"]:has(input[placeholder="SYNC_ORDEN_COSTOS"]),
    div[data-testid="stTextInput"]:has(input[placeholder="SYNC_ORDEN_INGRESOS"]) {
        position: fixed !important;
        left: -9999px !important;
        top: -9999px !important;
        width: 1px !important;
        height: 1px !important;
        overflow: hidden !important;
        opacity: 0 !important;
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


# Inputs puente invisibles para sincronizar el orden al arrastrar categorías
st.text_input(
    "SYNC_ORDEN_COSTOS",
    key="sync_orden_costos_input",
    placeholder="SYNC_ORDEN_COSTOS",
    label_visibility="collapsed",
    on_change=sync_orden_costos_cb
)
st.text_input(
    "SYNC_ORDEN_INGRESOS",
    key="sync_orden_ingresos_input",
    placeholder="SYNC_ORDEN_INGRESOS",
    label_visibility="collapsed",
    on_change=sync_orden_ingresos_cb
)

# ----------------- PESTAÑAS EN MAYÚSCULAS (REQ 5) -----------------
pestana1, pestana2 = st.tabs([
    "📊 COSTOS E INGRESOS",
    "💎 CARTERA DE INVERSIONES"
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

        with st.expander("➕ AGREGAR NUEVA CATEGORÍA DE COSTOS"):
            c_nc1, c_nc2 = st.columns([2.8, 1.2])
            with c_nc1:
                st.text_input(
                    "Nombre de la Categoría (ej. IMPUESTOS, AUTO, SALUD)",
                    placeholder="Escribí el nombre de la categoría...",
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

            # \u200b identifica de manera unívoca a las categorías de Costos para el Drag & Drop
            titulo_cat = f"⠿\u200b {icono_cat} **{cat_nombre}** — Subtotal: **{sub_ars:,.0f} ARS** ({sub_usd:,.1f} USD)"
            with st.expander(titulo_cat, expanded=False):
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
                    if st.button(f"🗑️ Eliminar categoría vacía '{cat_nombre}'", key=f"del_cat_c_{cat_nombre}"):
                        datos["categorias_costos"].remove(cat_nombre)
                        guardar_datos(datos)
                        st.rerun()

        if costos_modificados:
            guardar_datos(datos)
            st.rerun()

    # ---------------- INGRESOS ----------------
    with col_der:
        st.markdown("<h3 style='color: #117864; margin-bottom: 6px;'>📈 Mis Ingresos Mensuales</h3>", unsafe_allow_html=True)

        with st.expander("➕ AGREGAR NUEVA CATEGORÍA DE INGRESOS"):
            c_ni1, c_ni2 = st.columns([2.8, 1.2])
            with c_ni1:
                st.text_input(
                    "Nombre de la Categoría (ej. Trabajo, Consultorio, Otros)",
                    placeholder="Escribí el nombre de la categoría...",
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

            # \u200c identifica de manera unívoca a las categorías de Ingresos para el Drag & Drop
            titulo_cat_i = f"⠿\u200c {icono_cat_i} **{cat_nombre_i}** — Subtotal: **{sub_ars_i:,.0f} ARS** ({sub_usd_i:,.1f} USD)"
            with st.expander(titulo_cat_i, expanded=False):
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
                    if st.button(f"🗑️ Eliminar categoría vacía '{cat_nombre_i}'", key=f"del_cat_i_{cat_nombre_i}"):
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

    st.markdown(f"""
    <div class="metric-card metric-card-lila" style="text-align: center;">
        <div class="kpi-title" style="font-size: 1.25rem;">Patrimonio Total</div>
        <div class="kpi-value" style="font-size: 2.35rem;">{total_patrimonio_ars:,.0f} ARS</div>
        <div class="kpi-usd" style="font-size: 1.2rem;">{total_patrimonio_usd:,.2f} USD</div>
        <div class="kpi-sub">{len(df_inv_activos)} activos de {len(inversiones)} contemplados</div>
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

activar_interactividad_avanzada(datos.get('categorias_costos', []), datos.get('categorias_ingresos', []))
