"""Algoritmos de despacho (planificación de CPU): FIFO, SJF, Prioridad y Round Robin."""

from collections import deque
from dataclasses import dataclass

import pandas as pd


@dataclass
class Proceso:
    """Proceso ingresado por el usuario. `orden` es su posición en la tabla."""

    id: str
    llegada: int
    cpu: int
    prioridad: int
    orden: int


# Segmento del Gantt: (id del proceso, inicio, fin)
Segmento = tuple[str, int, int]


def _no_expropiativo(procesos: list[Proceso], clave) -> list[Segmento]:
    """Ejecuta procesos completos, eligiendo entre los listos el de menor `clave`."""
    pendientes = sorted(procesos, key=lambda p: (p.llegada, p.orden))
    tiempo = 0
    segmentos: list[Segmento] = []
    while pendientes:
        listos = [p for p in pendientes if p.llegada <= tiempo]
        if not listos:
            # CPU ociosa: saltar a la siguiente llegada
            tiempo = pendientes[0].llegada
            continue
        elegido = min(listos, key=lambda p: (clave(p), p.llegada, p.orden))
        segmentos.append((elegido.id, tiempo, tiempo + elegido.cpu))
        tiempo += elegido.cpu
        pendientes.remove(elegido)
    return segmentos


def fifo(procesos: list[Proceso]) -> list[Segmento]:
    """FIFO / FCFS: atiende por orden de llegada."""
    return _no_expropiativo(procesos, lambda p: 0)


def sjf(procesos: list[Proceso]) -> list[Segmento]:
    """SJF no expropiativo: entre los listos, el de menor tiempo de CPU."""
    return _no_expropiativo(procesos, lambda p: p.cpu)


def prioridad(procesos: list[Proceso]) -> list[Segmento]:
    """Prioridad no expropiativa: menor número = mayor prioridad."""
    return _no_expropiativo(procesos, lambda p: p.prioridad)


def round_robin(procesos: list[Proceso], quantum: int) -> list[Segmento]:
    """Round Robin: cada proceso usa la CPU a lo sumo `quantum` unidades por turno.

    Los procesos que llegan durante un turno entran a la cola antes que el
    proceso expropiado al final de ese turno.
    """
    por_llegar = deque(sorted(procesos, key=lambda p: (p.llegada, p.orden)))
    restante = {p.id: p.cpu for p in procesos}
    cola: deque[Proceso] = deque()
    tiempo = 0
    segmentos: list[Segmento] = []

    def admitir_hasta(t: int) -> None:
        while por_llegar and por_llegar[0].llegada <= t:
            cola.append(por_llegar.popleft())

    while por_llegar or cola:
        admitir_hasta(tiempo)
        if not cola:
            tiempo = por_llegar[0].llegada
            continue
        actual = cola.popleft()
        uso = min(quantum, restante[actual.id])
        # Unir con el segmento anterior si el mismo proceso sigue en CPU
        if segmentos and segmentos[-1][0] == actual.id and segmentos[-1][2] == tiempo:
            segmentos[-1] = (actual.id, segmentos[-1][1], tiempo + uso)
        else:
            segmentos.append((actual.id, tiempo, tiempo + uso))
        tiempo += uso
        restante[actual.id] -= uso
        admitir_hasta(tiempo)
        if restante[actual.id] > 0:
            cola.append(actual)
    return segmentos


def calcular_metricas(procesos: list[Proceso], segmentos: list[Segmento]) -> pd.DataFrame:
    """Tabla por proceso con Fin, T. sistema y T. espera (sin fila de promedios)."""
    fin = {}
    for pid, _, f in segmentos:
        fin[pid] = max(fin.get(pid, 0), f)
    filas = []
    for p in sorted(procesos, key=lambda p: p.orden):
        t_sistema = fin[p.id] - p.llegada
        filas.append(
            {
                "ID": p.id,
                "Llegada": p.llegada,
                "CPU": p.cpu,
                "Fin": fin[p.id],
                "T. sistema": t_sistema,
                "T. espera": t_sistema - p.cpu,
            }
        )
    return pd.DataFrame(filas)


def simular(
    procesos: list[Proceso], quantum: int
) -> dict[str, tuple[list[Segmento], pd.DataFrame]]:
    """Ejecuta los 4 algoritmos y devuelve {nombre: (segmentos, métricas)}."""
    resultados = {}
    for nombre, algoritmo in [
        ("FIFO / FCFS", fifo),
        ("SJF (no expropiativo)", sjf),
        ("Prioridad (no expropiativo)", prioridad),
        (f"Round Robin (q = {quantum})", lambda ps: round_robin(ps, quantum)),
    ]:
        segmentos = algoritmo(procesos)
        resultados[nombre] = (segmentos, calcular_metricas(procesos, segmentos))
    return resultados
