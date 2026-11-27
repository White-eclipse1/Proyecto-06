# Capturas visuales pendientes

Iniciar `python scripts/run_portal.py` y capturar manualmente:

1. Lista `http://127.0.0.1:8000/events`.
2. Detalle C1 `http://127.0.0.1:8000/events/3f58257b-7de3-460b-8822-29e3eba3e77c`.
3. Detalle C2 `http://127.0.0.1:8000/events/558a9f31-57a3-4655-9b86-917a329d576c`.
4. Lista `http://127.0.0.1:8000/alerts`.
5. Detalle de alerta C2 `http://127.0.0.1:8000/alerts/1a12681f-a90d-4adf-a2f1-fb0cfc00f291` con el enlace al evento.
6. Evento C2 `http://127.0.0.1:8000/events/558a9f31-57a3-4655-9b86-917a329d576c` mostrando la imagen.

IDs definitivos según `evidencias/escenarios/manifest.json`: C1 evento `3f58257b-7de3-460b-8822-29e3eba3e77c`; C2 evento `558a9f31-57a3-4655-9b86-917a329d576c` y alerta `1a12681f-a90d-4adf-a2f1-fb0cfc00f291`. Las URLs requieren iniciar el portal con la base de datos que contiene estas corridas; una instalación nueva genera IDs distintos. Si se reejecuta un escenario sobre la evidencia definitiva, este documento debe actualizarse.
