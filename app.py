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
# Tonos 400: con texto oscuro encima se leen bien en tema claro y oscuro
PALETA = [
    "#60A5FA", "#FBBF24", "#34D399", "#A78BFA", "#F87171", "#22D3EE",
    "#F472B6", "#A3E635", "#FB923C", "#818CF8", "#2DD4BF", "#E879F9",
]
TEXTO_BARRA = "#0F172A"
REJILLA = "rgba(148, 163, 184, 0.25)"
RESALTADO = "background-color: #BBF7D0; color: #14532D; font-weight: 600"
COLORES_METRICAS = ["#2563EB", "#F59E0B"]


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


def diagrama_gantt(segmentos: list[Segmento], colores: dict[str, str], orden_ids: list[str]) -> go.Figure:
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
                marker=dict(color=colores[pid], line=dict(width=0), cornerradius=4),
                text=[f"{inicio}–{fin}" for _, inicio, fin in propios],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color=TEXTO_BARRA, size=12),
                hovertemplate=f"{pid}: %{{base}} → %{{customdata}}<extra></extra>",
                customdata=[fin for _, _, fin in propios],
            )
        )
    fin_total = max(f for _, _, f in segmentos)
    fig.update_layout(
        barmode="overlay",
        bargap=0.3,
        height=90 + 42 * len(orden_ids),
        margin=dict(l=10, r=10, t=10, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="Tiempo",
            range=[0, fin_total],
            dtick=1 if fin_total <= 40 else None,
            gridcolor=REJILLA,
            zeroline=False,
        ),
        yaxis=dict(autorange="reversed", title=None, categoryorder="array", categoryarray=orden_ids, showgrid=False),
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

col_tabla, col_opciones = st.columns([3, 1], gap="medium")

with col_tabla.container(border=True):
    st.subheader("Procesos")
    editada = st.data_editor(
        st.session_state.tabla,
        key=f"editor_{st.session_state.version}",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        placeholder="",
        column_config={
            "ID": st.column_config.TextColumn("ID", help="Nombre del proceso, p. ej. P1"),
            "Llegada": st.column_config.NumberColumn("Llegada", min_value=0, step=1, format="%d"),
            "CPU": st.column_config.NumberColumn("CPU", min_value=1, step=1, format="%d"),
            "Prioridad": st.column_config.NumberColumn(
                "Prioridad", min_value=1, step=1, format="%d", help="Menor número = mayor prioridad"
            ),
        },
    )
    b1, b2, _ = st.columns([1, 1, 2])
    if b1.button("Agregar proceso", icon=":material/add:", width="stretch"):
        st.session_state.tabla = pd.concat([editada, tabla_vacia(1)], ignore_index=True)
        st.session_state.version += 1
        st.rerun()
    if b2.button("Limpiar todo", icon=":material/delete_sweep:", width="stretch"):
        st.session_state.tabla = tabla_vacia(FILAS_INICIALES)
        st.session_state.version += 1
        st.session_state.resultados = None
        st.rerun()

with col_opciones.container(border=True):
    st.subheader("Opciones")
    quantum = st.number_input("Quantum (Round Robin)", min_value=1, value=2, step=1)
    st.caption("En Prioridad, el número menor se atiende primero. Los empates se resuelven por llegada y luego por orden en la tabla.")

if st.button("Ejecutar simulación", type="primary", icon=":material/play_arrow:", width="stretch"):
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
    metricas_prom = ["T. sistema promedio", "T. espera promedio"]
    comparativa = pd.DataFrame(
        [
            {
                "Algoritmo": nombre,
                "T. sistema promedio": metricas["T. sistema"].mean(),
                "T. espera promedio": metricas["T. espera"].mean(),
            }
            for nombre, (_, metricas) in resultados.items()
        ]
    )

    st.divider()
    st.header("Resultados")

    for col, metrica in zip(st.columns(2), metricas_prom):
        minimo = comparativa[metrica].min()
        mejores = comparativa.loc[comparativa[metrica] == minimo, "Algoritmo"]
        with col.container(border=True):
            st.metric(f"Menor {metrica}", _fmt(minimo))
            st.caption(" · ".join(mejores))

    for tab, (nombre, (segmentos, metricas)) in zip(st.tabs(list(resultados)), resultados.items()):
        with tab:
            st.plotly_chart(diagrama_gantt(segmentos, colores, orden_ids), width="stretch", key=f"gantt_{nombre}")
            st.dataframe(tabla_con_promedios(metricas), hide_index=True, width="stretch", placeholder="")

    st.subheader("Comparación de algoritmos")
    col_comp, col_graf = st.columns([2, 3], gap="medium")
    col_comp.dataframe(
        comparativa.style.format(_fmt, subset=metricas_prom).highlight_min(subset=metricas_prom, props=RESALTADO),
        hide_index=True,
        width="stretch",
    )
    col_comp.caption("En verde, el menor promedio de cada columna.")

    barras = comparativa.melt(id_vars="Algoritmo", var_name="Métrica", value_name="Tiempo")
    fig = px.bar(
        barras,
        x="Algoritmo",
        y="Tiempo",
        color="Métrica",
        barmode="group",
        text=barras["Tiempo"].map(_fmt),
        color_discrete_sequence=COLORES_METRICAS,
    )
    fig.update_traces(marker_cornerradius=4, textposition="outside", cliponaxis=False)
    fig.update_layout(
        yaxis_title="Tiempo promedio",
        xaxis_title=None,
        legend=dict(title=None, orientation="h", y=1.12, x=0),
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor=REJILLA),
    )
    col_graf.plotly_chart(fig, width="stretch")
