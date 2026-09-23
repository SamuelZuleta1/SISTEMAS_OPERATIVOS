# Taller: Simulador de algoritmos de despacho

**Autor:** Samuel Zuleta — UTP, Sistemas Operativos

App web en Streamlit que simula cuatro algoritmos de planificación de CPU sobre procesos ingresados manualmente y compara sus diagramas de Gantt, tiempos de sistema y tiempos de espera.

## Instalación

Requiere Python 3.10 o superior.

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

## Algoritmos

- **FIFO / FCFS:** no expropiativo; atiende los procesos en orden de llegada.
- **SJF:** no expropiativo; entre los procesos listos elige el de menor tiempo de CPU.
- **Prioridad:** no expropiativo; entre los listos elige el de menor número de prioridad (mayor prioridad).
- **Round Robin:** expropiativo; cada proceso usa la CPU como máximo un quantum (configurable) y vuelve al final de la cola.

Empates: se resuelven por tiempo de llegada y luego por el orden en la tabla.

## Fórmulas

- T. sistema = Fin − Llegada
- T. espera = T. sistema − CPU
- Promedio = suma / número de procesos
