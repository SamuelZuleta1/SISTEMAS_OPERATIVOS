"""Simulador de algoritmos de despacho — interfaz Streamlit."""

import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pandas.io.formats.style import Styler

from algoritmos import Proceso, Segmento, simular

COLUMNAS = ["ID", "Llegada", "CPU", "Prioridad"]
FILAS_INICIALES = 3
PALETA = px.colors.qualitative.Plotly + px.colors.qualitative.Set2 + px.colors.qualitative.Pastel
VERDE = "#b7e4c7"


def tabla_vacia(filas: int) -> pd.DataFrame:
    """DataFrame vacío con las columnas de ingreso de procesos."""
    return pd.DataFrame(
        {
            "ID": pd.Series([None] * filas, dtype="object"),
            "Llegada": pd.Series([None] * filas, dtype="float"),
            "CPU": pd.Series([None] * filas, dtype="float"),
            "Prioridad": pd.Series([None] * filas, dtype="float"),
        }
    )


def _vacio(valor) -> bool:
    return valor is None or (isinstance(valor, float) and math.isnan(valor)) or str(valor).strip() == ""


def validar(df: pd.DataFrame) -> tuple[list[Proceso], list[str]]:
    """Convierte la tabla en procesos. Devuelve (procesos, errores)."""
    procesos: list[Proceso] = []
    errores: list[str] = []
    ids_vistos: set[str] = set()

    for i, fila in enumerate(df.to_dict("records")):
        n = i + 1
        if all(_vacio(fila.get(c)) for c in COLUMNAS):
            continue  # fila totalmente vacía: se ignora
        faltan = [c for c in COLUMNAS if _vacio(fila.get(c))]
        if faltan:
            errores.append(f"Fila {n}: falta {', '.join(faltan)}.")
            continue

        pid = str(fila["ID"]).strip()
        llegada, cpu, prio = fila["Llegada"], fila["CPU"], fila["Prioridad"]
        if pid in ids_vistos:
            errores.append(f"Fila {n}: el ID «{pid}» está repetido.")
        if any(float(v) != int(v) for v in (llegada, cpu, prio)):
            errores.append(f"Fila {n}: Llegada, CPU y Prioridad deben ser enteros.")
            continue
        if llegada < 0:
            errores.append(f"Fila {n}: la llegada debe ser ≥ 0.")
        if cpu <= 0:
            errores.append(f"Fila {n}: el CPU debe ser > 0.")
        if prio < 1:
            errores.append(f"Fila {n}: la prioridad debe ser ≥ 1.")

        ids_vistos.add(pid)
        procesos.append(Proceso(pid, int(llegada), int(cpu), int(prio), orden=i))

    if not procesos and not errores:
        errores.append("La tabla está vacía: ingresa al menos un proceso.")
    return procesos, errores


def diagrama_gantt(titulo: str, segmentos: list[Segmento], colores: dict[str, str], orden_ids: list[str]) -> go.Figure:
    """Gantt con barras horizontales: una fila por proceso, eje X = tiempo."""
    fig = go.Figure()
    for pid in orden_ids:
        propios = [s for s in segmentos if s[0] == pid]
        fig.add_trace(
            go.Bar(
                name=pid,
                y=[pid] * len(propios),
                x=[fin - inicio for _, inicio, fin in propios],
                base=[inicio for _, inicio, _ in propios],
                orientation="h",
                marker=dict(color=colores[pid], line=dict(color="#333", width=1)),
                text=[f"{inicio}–{fin}" for _, inicio, fin in propios],
                textposition="inside",
                insidetextanchor="middle",
                hovertemplate=f"{pid}: %{{base}} → %{{customdata}}<extra></extra>",
                customdata=[fin for _, _, fin in propios],
            )
        )
    fin_total = max(f for _, _, f in segmentos)
    fig.update_layout(
        title=titulo,
        barmode="overlay",
        height=120 + 45 * len(orden_ids),
        margin=dict(l=10, r=10, t=50, b=40),
        xaxis=dict(title="Tiempo", range=[0, fin_total], dtick=1 if fin_total <= 40 else None),
        yaxis=dict(autorange="reversed", title=None, categoryorder="array", categoryarray=orden_ids),
        showlegend=False,
    )
    return fig


def _fmt(v) -> str:
    if _vacio(v):
        return ""
    return f"{v:.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def tabla_con_promedios(metricas: pd.DataFrame) -> Styler:
    """Agrega la fila de promedios al final de la tabla de métricas."""
    promedio = {
        "ID": "Promedio",
        "T. sistema": metricas["T. sistema"].mean(),
        "T. espera": metricas["T. espera"].mean(),
    }
    tabla = pd.concat([metricas.astype(object), pd.DataFrame([promedio])], ignore_index=True)
    return tabla.style.format(_fmt).apply(
        lambda fila: ["font-weight: bold" if fila["ID"] == "Promedio" else "" for _ in fila], axis=1
    )


# ---------------------------------------------------------------- interfaz

st.set_page_config(page_title="Algoritmos de despacho", layout="wide")
st.title("Simulador de algoritmos de despacho")
st.caption("FIFO · SJF · Prioridad · Round Robin — Taller de Sistemas Operativos, UTP")

if "tabla" not in st.session_state:
    st.session_state.tabla = tabla_vacia(FILAS_INICIALES)
    st.session_state.version = 0
    st.session_state.resultados = None

col_tabla, col_opciones = st.columns([3, 1])

with col_tabla:
    st.subheader("Procesos")
    editada = st.data_editor(
        st.session_state.tabla,
        key=f"editor_{st.session_state.version}",
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "ID": st.column_config.TextColumn("ID", help="Nombre del proceso, p. ej. P1"),
            "Llegada": st.column_config.NumberColumn("Llegada", min_value=0, step=1, format="%d"),
            "CPU": st.column_config.NumberColumn("CPU", min_value=1, step=1, format="%d"),
            "Prioridad": st.column_config.NumberColumn(
                "Prioridad", min_value=1, step=1, format="%d", help="Menor número = mayor prioridad"
            ),
        },
    )
    b1, b2, _ = st.columns([1, 1, 3])
    if b1.button("+ Agregar proceso", use_container_width=True):
        st.session_state.tabla = pd.concat([editada, tabla_vacia(1)], ignore_index=True)
        st.session_state.version += 1
        st.rerun()
    if b2.button("Limpiar todo", use_container_width=True):
        st.session_state.tabla = tabla_vacia(FILAS_INICIALES)
        st.session_state.version += 1
        st.session_state.resultados = None
        st.rerun()

with col_opciones:
    st.subheader("Opciones")
    quantum = st.number_input("Quantum (Round Robin)", min_value=1, value=2, step=1)

if st.button("▶ Ejecutar simulación", type="primary", use_container_width=True):
    procesos, errores = validar(editada)
    if errores:
        st.session_state.resultados = None
        st.error("No se puede ejecutar la simulación:\n\n" + "\n".join(f"- {e}" for e in errores))
    else:
        st.session_state.resultados = (procesos, simular(procesos, int(quantum)))

# ---------------------------------------------------------------- resultados

if st.session_state.resultados:
    procesos, resultados = st.session_state.resultados
    orden_ids = [p.id for p in procesos]
    colores = {pid: PALETA[i % len(PALETA)] for i, pid in enumerate(orden_ids)}

    st.divider()
    st.header("Resultados")
    st.markdown(
        " ".join(
            f"<span style='background:{colores[pid]};padding:2px 10px;border-radius:4px;"
            f"margin-right:6px;color:#000'>{pid}</span>"
            for pid in orden_ids
        ),
        unsafe_allow_html=True,
    )

    resumen = []
    for nombre, (segmentos, metricas) in resultados.items():
        st.plotly_chart(diagrama_gantt(nombre, segmentos, colores, orden_ids), use_container_width=True)
        st.dataframe(tabla_con_promedios(metricas), hide_index=True)
        resumen.append(
            {
                "Algoritmo": nombre,
                "T. sistema promedio": metricas["T. sistema"].mean(),
                "T. espera promedio": metricas["T. espera"].mean(),
            }
        )

    st.divider()
    st.subheader("Comparación de algoritmos")
    comparativa = pd.DataFrame(resumen)
    st.dataframe(
        comparativa.style.format(_fmt, subset=["T. sistema promedio", "T. espera promedio"]).highlight_min(
            subset=["T. sistema promedio", "T. espera promedio"], color=VERDE
        ),
        hide_index=True,
        use_container_width=True,
    )

    barras = comparativa.melt(id_vars="Algoritmo", var_name="Métrica", value_name="Tiempo")
    fig = px.bar(
        barras,
        x="Algoritmo",
        y="Tiempo",
        color="Métrica",
        barmode="group",
        text=barras["Tiempo"].map(_fmt),
        title="Promedios por algoritmo",
    )
    fig.update_layout(yaxis_title="Tiempo promedio", legend_title=None)
    st.plotly_chart(fig, use_container_width=True)
