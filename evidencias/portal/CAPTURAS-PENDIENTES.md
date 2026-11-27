# CAPTURAS COMPLETADAS — portal

Cinco PNG originales del archivo `capturas_portal_p6.zip` cubren las seis vistas solicitadas. `02-detalle-c2-con-imagen.png` muestra tanto el detalle de C2 como su imagen asociada. Los archivos están en `evidencias/portal/` y se verificaron visualmente contra los IDs definitivos de `evidencias/escenarios/manifest.json`.

| Evidencia visual | Archivo | ID relacionado | Qué demuestra | URL local |
| --- | --- | --- | --- | --- |
| 1. Lista Events | [03-lista-eventos.png](03-lista-eventos.png) | C1 `3f58257b-7de3-460b-8822-29e3eba3e77c`; C2 `558a9f31-57a3-4655-9b86-917a329d576c` | Listado de eventos, fuentes, confidence, zona y estado. | `http://127.0.0.1:8000/events` |
| 2. Detalle C1 | [01-detalle-c1.png](01-detalle-c1.png) | Evento `3f58257b-7de3-460b-8822-29e3eba3e77c` | `ACCEPTED_BY_POLICY`, confidence ≈ `0.8417` y tres detecciones. | `http://127.0.0.1:8000/events/3f58257b-7de3-460b-8822-29e3eba3e77c` |
| 3. Detalle C2 | [02-detalle-c2-con-imagen.png](02-detalle-c2-con-imagen.png) | Evento `558a9f31-57a3-4655-9b86-917a329d576c` | `LOW_CONFIDENCE`, confidence ≈ `0.3968` y detecciones. | `http://127.0.0.1:8000/events/558a9f31-57a3-4655-9b86-917a329d576c` |
| 4. Lista Alerts | [04-lista-alertas.png](04-lista-alertas.png) | Alerta C2 `1a12681f-a90d-4adf-a2f1-fb0cfc00f291` | Alertas persistidas, severidad, regla, estado y evento relacionado. | `http://127.0.0.1:8000/alerts` |
| 5. Detalle alerta C2 | [05-detalle-alerta-c2.png](05-detalle-alerta-c2.png) | Alerta `1a12681f-a90d-4adf-a2f1-fb0cfc00f291`; evento C2 `558a9f31-57a3-4655-9b86-917a329d576c` | `LOW_CONFIDENCE_ALERT`, `WARNING`, `ACTIVE`, enlace al evento e imagen. | `http://127.0.0.1:8000/alerts/1a12681f-a90d-4adf-a2f1-fb0cfc00f291` |
| 6. Imagen C2 | [02-detalle-c2-con-imagen.png](02-detalle-c2-con-imagen.png) | Evento `558a9f31-57a3-4655-9b86-917a329d576c` | Imagen asociada visible debajo de las detecciones del evento C2. | `http://127.0.0.1:8000/events/558a9f31-57a3-4655-9b86-917a329d576c` |

Estas URLs requieren la base SQLite con las corridas definitivas. Una reproducción nueva genera IDs distintos. Los PNG son evidencia del portal; la captura original vinculada al evento C2 se conserva en `evidencias/escenarios/baja-confianza/capturas/`.

| Archivo en `evidencias/portal/` | SHA-256 |
| --- | --- |
| `01-detalle-c1.png` | `b1f0f29e387c46f03f99a89ed80f59027e2e33622f288a38d776f5e6a7f06355` |
| `02-detalle-c2-con-imagen.png` | `0dbe014a1d3c89eedb6fcfa03aaa8711eef30f37eb9cd0c28768657e07091af1` |
| `03-lista-eventos.png` | `70f8684a542946a282c8a8c10e8fd09d06f43178895e147ba778c9aa7a205df6` |
| `04-lista-alertas.png` | `8adbc254cf5d2ac15401efbab56caf2d40a27241b23ddb6a4123a40187b22551` |
| `05-detalle-alerta-c2.png` | `bb9c99316e49299499f9dc907b1fde02717daad2137584acf7ac1bfb6a9d643e` |
