# Sistemas Operativos — UTP

**Autor:** Samuel Zuleta

Trabajos de la asignatura. Cada uno está en su propia carpeta.

| # | Trabajo | Carpeta | Demo |
|---|---------|---------|------|
| 1 | Simulador de algoritmos de despacho (FIFO, SJF, Prioridad, Round Robin) | [`trabajo-1-algoritmos-despacho`](trabajo-1-algoritmos-despacho/) | [simulador-despacho-utp.streamlit.app](https://simulador-despacho-utp.streamlit.app/) |
| 2 | Pendiente | [`trabajo-2`](trabajo-2/) | — |
| 3 | Pendiente | [`trabajo-3`](trabajo-3/) | — |

## Ejecutar el trabajo 1 localmente

Desde la raíz del repositorio:

```bash
python3 -m venv .venv
.venv/bin/pip install -r trabajo-1-algoritmos-despacho/requirements.txt
.venv/bin/streamlit run trabajo-1-algoritmos-despacho/app.py
```
