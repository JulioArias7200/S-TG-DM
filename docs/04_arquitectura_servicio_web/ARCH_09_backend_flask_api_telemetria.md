# ARCH-09: Backend Flask 3.x, Application Factory y API RESTful v1 de Telemetría

## 1. Identificación y Propósito
* **Archivos Fuente:** [`app/__init__.py`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/app/__init__.py), [`app/config.py`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/app/config.py), [`app/routes/api_v1/telemetry.py`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/app/routes/api_v1/telemetry.py) y [`run.py`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/run.py).
* **Objetivo:** Implementar la capa de servicio backend basada en el patrón de diseño **Application Factory**, aislando la presentación web HTML/Jinja2 de los servicios de telemetría e interoperabilidad en formato JSON mediante la API RESTful `/api/v1`, soportando entornos locales y servidores WSGI en producción (Gunicorn / Render).

---

## 2. Especificación de Endpoints RESTful (`/api/v1`)

| Método | Endpoint | Parámetros Query | Código HTTP | Descripción y Contrato JSON |
| :---: | :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/health` | Ninguno | `200 OK` | Probe de liveness para orquestadores en Render/Kubernetes (`{"status": "healthy"}`). |
| `GET` | `/api/v1/stats` | Ninguno | `200 OK` | Resumen cuantitativo en tiempo real del corpus desde Neon PostgreSQL (mensajes, usuarios, OCR, stickers). |
| `POST` | `/api/v1/re-run` | Ninguno | `202 Accepted` | Trigger de re-ejecución asíncrona de inferencia en segundo plano. |
| `GET` | `/api/v1/nlp/summary` | Ninguno | `200 OK` | Estadísticas agregadas de PLN (distribución de 4 temas LDA y sentimiento dominante). |
| `GET` | `/api/v1/nlp/tfidf` | `tipo` (`DOCENTE`, `MATERIA`, `CICLO`), `id`, `limit` | `200 OK` | Ranking de términos con mayor peso estadístico TF-IDF filtrados por entidad. |
| `GET` | `/api/v1/nlp/topics` | Ninguno | `200 OK` | Detalle de los 4 tópicos LDA (Matriz Beta de vocabulario y distribución porcentual Gamma). |
| `GET` | `/api/v1/nlp/emotions/docentes` | `limit` (default 10) | `200 OK` | Perfil emocional relativo de docentes (alivio, recomendación, frustración, crítica). |

---

## 3. Arquitectura de Blueprints y Ciclo de Vida

```mermaid
flowchart TD
    A[Punto de Entrada: run.py / wsgi] --> B[create_app config_name]
    B --> C[Carga de Configuración: DevelopmentConfig / ProductionConfig]
    B --> D[Inicialización de Extensiones: db.init_app, migrate]
    
    B --> E[Registro de Blueprints]
    E --> F[web_bp: Prefijo '/' -> dashboard_view]
    E --> G[api_v1_bp: Prefijo '/api/v1' -> Endpoints JSON]
    
    G --> H1[/api/v1/health]
    G --> H2[/api/v1/stats]
    G --> H3[/api/v1/nlp/*]
    
    H2 --> I[database/queries.py]
    H3 --> I
    I --> J[Pool SQLAlchemy pre_ping]
    J --> K[(Neon PostgreSQL Serverless)]
```

---

## 4. Lógica de Configuración y Normalización de Entornos

En [`app/config.py`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/app/config.py), la aplicación resuelve de manera transparente las discrepancias de dialecto entre proveedores PaaS (Render inyecta cadenas con prefijo obsoleto `postgres://`) y los estándares de SQLAlchemy 2.0:

```python
raw_db_url = os.getenv("DATABASE_URL", "sqlite:///sentix_local.db")
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif raw_db_url.startswith("postgresql://") and not raw_db_url.startswith("postgresql+"):
    raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
```

---

## 5. Implementación en Código y Referencias
* Application Factory: [`create_app()` en app/__init__.py](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/app/__init__.py#L12-L31)
* Endpoints de API RESTful: [`app/routes/api_v1/telemetry.py`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/app/routes/api_v1/telemetry.py#L8-L128)
* Consultas analíticas SQL desacopladas: [`database/queries.py`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/database/queries.py)

---

## 6. Integración con el Ecosistema del Proyecto
* **Capa Inferior:** Consume consultas SQL optimizadas desde `database/queries.py` conectadas al motor SQLAlchemy.
* **Capa Superior:** Es consumida de forma asíncrona mediante llamadas AJAX/Fetch desde [`app/static/js/main.js`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/app/static/js/main.js) para actualización de telemetría sin recarga de página.

---

## 7. Instrucciones de Reproducción y Verificación

### Iniciar Servidor Local:
```powershell
python run.py
```

### Probar Endpoints de Telemetría (PowerShell / cURL):
```powershell
# Verificar Salud
curl http://127.0.0.1:5000/api/v1/health

# Consultar Estadísticas en Tiempo Real
curl http://127.0.0.1:5000/api/v1/stats

# Consultar Tópicos LDA
curl http://127.0.0.1:5000/api/v1/nlp/topics
```

---

## 8. Consideraciones Técnicas y Rendimiento
* **Manejo de Errores Defensivo:** Cada endpoint captura excepciones de base de datos (`try/except`) y retorna respuestas degradadas con código 200 en fallback estadístico o errores JSON estructurados con código 500, impidiendo caídas catastróficas del servidor WSGI.
* **Compatibilidad WSGI:** Compatible de fábrica con Gunicorn para producción:
  ```bash
  gunicorn --workers=2 --threads=4 --timeout=120 "app:create_app('production')"
  ```
