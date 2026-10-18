# Sentix Intelligence: Plataforma de Analitica, Mineria de Datos y Analisis de Sentimiento

Sistema de ingesta multimodal, procesamiento de lenguaje natural (NLP) y telemetria analitica desarrollado sobre interacciones de la comunidad estudiantil de la Carrera de Informatica (Universidad Mayor de San Andres - UMSA).

La plataforma integra un pipeline ETL de mineria de datos desacoplado, persistencia relacional optimizada para PostgreSQL Serverless (Neon), una API RESTful en Flask y una interfaz web ejecutiva para monitoreo C-Level con soporte de temas claro y oscuro.

---

## 1. Arquitectura del Sistema

El proyecto esta disenado bajo el principio de separacion de responsabilidades (SoC), dividiendo la solucion en dos capas operativas principales:

```
+------------------------------------------------------------------------+
|                            FUENTES DE DATOS                            |
|      Telegram Export (result.json)  +  Oferta Academica (horarios.pdf) |
+------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                      CAPA ETL / DATA PIPELINE                          |
|             data/scripts/ (01 -> 02 -> 03 -> 04 -> 05 -> 06)           |
|        - Parsing de PDF y construccion de ontologia academica          |
|        - Limpieza, normalizacion NFKC y extraccion OCR (Tesseract)     |
|        - Entity Linking (Docentes / Materias) y analisis de jerga      |
+------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                        CAPA DE PERSISTENCIA                            |
|       - data/processed/ (*.csv bajo estandar RFC-4180 utf-8-sig)       |
|       - Base de datos Neon Serverless PostgreSQL (SQLAlchemy Engine)   |
+------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                          CAPA DE SERVICIO                              |
|           Flask 3.x Application Factory (app:create_app)               |
|            - Blueprints: web_bp (HTML/Jinja2), api_v1_bp (REST)        |
|            - WSGI Server: Gunicorn (Produccion) / Werkzeug (Dev)       |
+------------------------------------------------------------------------+
```

---

## 2. Pila Tecnologica (Tech Stack)

### Backend y Servidor Web
* **Python 3.12.x**
* **Flask 3.0.x:** Framework web basado en el patron Application Factory.
* **Gunicorn 21.2.x / 23.x:** Servidor WSGI para entornos Unix/Linux de produccion.
* **Werkzeug 3.0.x:** Enrutamiento WSGI y utilidades base.
* **python-dotenv:** Carga de variables de entorno desde archivos `.env`.

### Base de Datos y ORM
* **Neon PostgreSQL:** Instancia Serverless optimizada con `pool_pre_ping`, `pool_recycle` y reintentos contra desbalanceo de conexiones.
* **SQLAlchemy 2.0.x / Flask-SQLAlchemy 3.1.x:** Capa de mapeo objeto-relacional.
* **psycopg2-binary 2.9.x:** Driver nativo de PostgreSQL para Python.
* **Alembic / Flask-Migrate:** Control de versiones de esquemas de datos.

### Data Science, NLP y Extraccion Multimodal
* **Pandas 2.2.x & NumPy 1.26.x:** Procesamiento matricial y transformaciones tabulares.
* **PyMuPDF (fitz):** Extraccion de texto y coordenadas vectoriales de documentos PDF.
* **Pillow (PIL) & PyTesseract:** Procesamiento de imagenes y reconocimiento optico de caracteres (OCR Tesseract v5.x).
* **Scikit-learn & SciPy:** Algoritmos estadisticos y clasificacion complementaria.

### Frontend
* **Jinja2:** Motor de plantillas server-side modularizado en componentes.
* **Tailwind CSS (CDN):** Sistema de diseno utilitario configurado para modo oscuro por clases (`darkMode: "class"`).
* **Google Material Symbols & Typography:** Inter, Plus Jakarta Sans y JetBrains Mono.
* **Motor de Temas:** Persistencia de estado en `localStorage` con script anti-FOUC en bloque `<head>`.

---

## 3. Estructura del Directorio

```text
DMProyAnalisisSentimiento/
├── app/                                # Nucleo de la aplicacion web Flask
│   ├── __init__.py                     # Factory method create_app() y registro de Blueprints
│   ├── config.py                       # Entornos DevelopmentConfig, ProductionConfig y Neon DB URI
│   ├── models/                         # Modelos declarativos SQLAlchemy
│   ├── routes/
│   │   ├── api_v1/
│   │   │   ├── __init__.py             # Definicion de api_v1_bp (/api/v1)
│   │   │   └── telemetry.py            # Endpoints /health, /stats, /re-run
│   │   └── web/
│   │       ├── __init__.py             # Definicion de web_bp (/)
│   │       └── dashboard.py            # Controlador de vista principal
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css                # Estilos base, scrollbar adaptativo y transiciones de tema
│   │   └── js/
│   │       └── main.js                 # Logica de navegacion móvil, alternancia de tema y triggers API
│   └── templates/
│       ├── base.html                   # Layout maestro con variables de color y tailwind config
│       ├── components/
│       │   ├── header.html             # Barra de navegacion superior y selectores de corpus
│       │   ├── sidebar.html            # Navegacion lateral con telemetria de motor SQLite/Postgres
│       │   ├── footer.html             # SLA y metadatos de modelos Transformer
│       │   └── dashboard/
│       │       ├── action_header.html  # Cabecera ejecutiva y boton de re-ejecucion
│       │       ├── kpi_cards.html      # 5 bloques ejecutivos de metricas clave
│       │       ├── charts_section.html # Visualizaciones analiticas en SVG (dona, barras, serie temporal)
│       │       └── database_table.html # Tabla de auditoria de corridas y snapshot de base de datos
│       └── dashboard/
│           └── index.html              # Vista principal ensamblada mediante directivas include
│
├── data/                               # Ecosistema desacoplado de ingenieria de datos
│   ├── raw/                            # Insumos originales inmutables (result.json, horarios.pdf)
│   ├── media/                          # Archivos de medios referenciados por los mensajes
│   │   ├── photos/                     # 2,485 imagenes extraidas del chat
│   │   ├── stickers/                   # 152 stickers clasificados taxonomicamente
│   │   └── video_files/                # 64 archivos multimedia complementarios
│   ├── processed/                      # Datasets estructurados finales en formato CSV y cache JSON
│   │   ├── dataset_telegram_master.csv # Dataset principal enriquecido (23,462 mensajes)
│   │   ├── catalogo_docentes_umsa.csv  # Base de conocimiento ontologica de docentes y regex
│   │   ├── catalogo_materias_umsa.csv  # Base de conocimiento de materias y paralelos
│   │   ├── dataset_menciones_docentes.csv
│   │   ├── dataset_modismos_mensajes.csv
│   │   ├── catalogo_modismos_umsa.csv
│   │   ├── diccionario_jergas_y_modismos_umsa.csv
│   │   ├── dataset_reacciones_granular.csv
│   │   ├── oferta_horarios_umsa.csv
│   │   ├── ranking_docentes_menciones.csv
│   │   ├── resumen_materias_menciones.csv
│   │   ├── eventos_servicio_log.csv
│   │   └── ocr_cache.json              # Indice de aceleracion hash MD5 -> texto OCR
│   ├── scripts/                        # Modulos ejecutables del pipeline ETL
│   │   ├── 01_parse_horarios_pdf.py
│   │   ├── 02_pipeline_limpieza_multimodal.py
│   │   ├── 03_entity_linking_docentes.py
│   │   ├── 04_mineria_modismos_y_concordancias.py
│   │   ├── 05_extractor_diccionario_jergas.py
│   │   ├── 06_analisis_multimodal_imagenes_sentimiento.py
│   │   └── buscador_terminos.py
│   ├── seeds/                          # Scripts para migracion e inyeccion a base de datos
│   ├── INFORME_DETALLADO_IMPLEMENTACION.md
│   └── neon.md
│
├── .env                                # Variables de entorno locales (ignorado por Git)
├── .gitignore                          # Exclusiones estrictas para entornos productivos
├── Procfile                            # Definicion del proceso web para Render
├── render.yaml                         # Blueprint de infraestructura como codigo (IaC)
├── requirements.txt                    # Dependencias congeladas del entorno
├── run.py                              # Punto de entrada para servidor de desarrollo
└── runtime.txt                         # Especificacion de version de Python (python-3.12.10)
```

---

## 4. Pipeline ETL y Orden de Ejecucion

Los scripts ubicados en `data/scripts/` deben ejecutarse secuencialmente si se requiere reconstruir los datasets consolidados desde los insumos crudos:

### Paso 1: Parseo de Oferta Academica y Ontologia Base
```bash
python data/scripts/01_parse_horarios_pdf.py
```
* **Entrada:** `data/raw/horarios.pdf`.
* **Proceso:** Extraccion de texto estructurado con PyMuPDF, identificacion de materias, docentes y asignacion de aulas. Compilacion de patrones regex para deteccion coloquial de nombres.
* **Salida:** `catalogo_docentes_umsa.csv`, `catalogo_materias_umsa.csv`, `oferta_horarios_umsa.csv` en `data/processed/`.

### Paso 2: Limpieza Maestro, Enriquecimiento Multimodal y Entity Linking
```bash
python data/scripts/02_pipeline_limpieza_multimodal.py
```
* **Entrada:** `data/raw/result.json`, `data/media/photos/`, catalogos de docentes y materias.
* **Proceso:** Filtrado de eventos de servicio vs. mensajes de usuario. Normalizacion NFKC de cadenas de texto. Ejecucion de OCR concurrente sobre imagenes sin texto explicito. Mapeo de stickers y emojis a taxonomias de 6 dimensiones emocionales. Propagacion de contexto semantico en arboles de respuesta (`reply_to_message_id`).
* **Salida:** `dataset_telegram_master.csv`, `dataset_menciones_docentes.csv`, `dataset_reacciones_granular.csv`, `eventos_servicio_log.csv`.

### Paso 3: Agregacion de Metricas por Docente y Materia
```bash
python data/scripts/03_entity_linking_docentes.py
```
* **Entrada:** `data/processed/dataset_menciones_docentes.csv`.
* **Proceso:** Consolidacion de volumen de consultas, conteo de reacciones sociales acumuladas y ratio de dudas por entidad.
* **Salida:** `ranking_docentes_menciones.csv`, `resumen_materias_menciones.csv`.

### Paso 4: Mineria de Modismos y Concordancias en Contexto (KWIC)
```bash
python data/scripts/04_mineria_modismos_y_concordancias.py
```
* **Entrada:** `data/processed/dataset_telegram_master.csv`.
* **Proceso:** Evaluacion de 34 expresiones idiomaticas regionales y de jerga academica UMSA (e.g., "barco", "fregado", "tirarse", "matador", "capo"). Generacion de ventanas de contexto previo/posterior y control de falsos positivos sintacticos.
* **Salida:** `dataset_modismos_mensajes.csv`, `catalogo_modismos_umsa.csv`.

### Paso 5: Compilacion del Diccionario Lexicografico
```bash
python data/scripts/05_extractor_diccionario_jergas.py
```
* **Entrada:** `data/processed/dataset_telegram_master.csv`.
* **Proceso:** Catalogacion de jerga en cuatro categorias ontologicas: Evaluacion Docente, Rendimiento Estudiantil, Terminologia UMSA y Jerga de Internet. Asignacion de scores de polaridad (-2.0 a +2.0).
* **Salida:** `diccionario_jergas_y_modismos_umsa.csv`.

### Paso 6: Analisis Multimodal Integral y Sincronizacion Final
```bash
python data/scripts/06_analisis_multimodal_imagenes_sentimiento.py
```
* **Entrada:** Imagenes locales en `data/media/photos/`, stickers y dataset maestro.
* **Proceso:** Deduplicacion estricta mediante suma de comprobacion MD5, clasificacion de intenciones visuales (Avisos de Kardex, Comprobantes de Deposito Bancario CPT, Errores de Sistema, Memes) y actualizacion del dataset maestro unificado.
* **Salida:** `catalogo_multimodal_imagenes_stickers.csv`.

### Herramienta de Consulta CLI (Buscador Lexico)
```bash
# Busqueda de patrones con comodin:
python data/scripts/buscador_terminos.py --buscar "facil*" "barco*" "fregad*"

# Analisis de co-ocurrencias de sarcasmo:
python data/scripts/buscador_terminos.py --descubrir_sarcasmo

# Filtro exclusivo sobre mensajes con docentes identificados:
python data/scripts/buscador_terminos.py --buscar "recomiend*" --solo_menciones
```

---

## 5. Configuracion del Entorno y Ejecucion Local

### Requisitos Previos
* Python 3.12 instalado.
* Git.
* (Opcional para re-ejecutar OCR completo) Tesseract OCR instalado en el sistema operativo.

### Instalacion Paso a Paso

1. Clonar el repositorio y posicionarse en la raiz del proyecto:
   ```bash
   git clone <URL_REPOSITORIO>
   cd DMProyAnalisisSentimiento
   ```

2. Crear y activar un entorno virtual aislado:
   ```bash
   # En Windows PowerShell / CMD:
   python -m venv venv
   .\venv\Scripts\activate

   # En Linux / macOS:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Instalar las dependencias fijadas:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno en el archivo `.env`:
   ```ini
   FLASK_ENV=development
   SECRET_KEY=clave-secreta-desarrollo-local-2026
   DATABASE_URL=sqlite:///sentix_local.db
   PORT=5000
   ```
   *Nota:* Para conectar contra Neon PostgreSQL en desarrollo local, reemplace el valor de `DATABASE_URL` con la cadena de conexion proporcionada por la consola de Neon:
   ```ini
   DATABASE_URL=postgresql://<USUARIO>:<PASSWORD>@<HOST_NEON>.neon.tech/<DB_NAME>?sslmode=require
   ```

5. Iniciar la aplicacion web en modo de desarrollo:
   ```bash
   python run.py
   ```
   El servidor estara disponible en `http://localhost:5000/`.

---

## 6. Especificacion de la API REST (`/api/v1`)

### `GET /api/v1/health`
Endpoint de monitoreo utilizado por sondas de salud (Health Checkers) de Render u orquestadores de contenedores.
* **Respuesta Exitosa (200 OK):**
  ```json
  {
    "engine": "Neon Serverless PostgreSQL Ready",
    "service": "sentix-intelligence-api",
    "status": "healthy"
  }
  ```

### `GET /api/v1/stats`
Retorna agregados analiticos globales, umbrales de confianza del modelo y desglose porcentual de polaridad.
* **Respuesta Exitosa (200 OK):**
  ```json
  {
    "confidence_threshold": 0.75,
    "lexical_coverage": "94.2%",
    "sentiment_distribution": {
      "indeterminate": 8.4,
      "negative": 13.5,
      "neutral": 32.4,
      "positive": 45.7
    },
    "total_messages": 142850,
    "unique_senders": 8940
  }
  ```

### `POST /api/v1/re-run`
Dispara la ejecucion asincrona o batch del pipeline de inferencia sobre nuevas particiones de datos.
* **Respuesta Exitosa (202 Accepted):**
  ```json
  {
    "message": "Inferencia de telemetria iniciada exitosamente en el cluster.",
    "status": "accepted"
  }
  ```

---

## 7. Despliegue en Produccion (Render)

El repositorio incluye la infraestructura necesaria para despliegue automatizado en **Render Web Services**:

### Archivos de Configuracion de Despliegue
* **`runtime.txt`:** Fija la version de ejecucion en `python-3.12.10`.
* **`Procfile`:** Declara el comando de arranque de Gunicorn:
  ```text
  web: gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
  ```
* **`render.yaml`:** Manifiesto de infraestructura con comprobacion automatica de salud en `/api/v1/health`.
* **`app/config.py`:** Normaliza en tiempo de ejecucion el prefijo `postgres://` a `postgresql://` requerido por SQLAlchemy 2.x al consumir la variable de entorno de Render.

### Variables de Entorno en el Dashboard de Render
Configurar en la seccion de *Environment Variables* del servicio:

| Variable | Valor / Descripcion |
| :--- | :--- |
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | Generar un hash criptografico aleatorio (e.g., `openssl rand -hex 32`) |
| `DATABASE_URL` | URI de conexion segura de Neon PostgreSQL (`postgresql://...sslmode=require`) |
| `PYTHON_VERSION` | `3.12.10` |

---

## 8. Estandar de Codificacion y Reproducibilidad de Datos

* **Codificacion:** Todos los datasets generados en `data/processed/` se exportan bajo la especificacion **RFC-4180** utilizando codificacion **`utf-8-sig` (UTF-8 con marca de orden de bytes BOM)**, previniendo la corrupcion de diacriticos, acentos y caracteres especiales al ser consumidos desde Python (Pandas), R, Microsoft Excel o motores SQL.
* **Control de Exclusiones (`.gitignore`):** El repositorio excluye entornos virtuales (`venv/`), archivos de configuracion sensible (`.env`), bases de datos SQLite locales y artefactos temporales de compilacion Python (`__pycache__/`).
