# Sistema Sentix Intelligence: Índice Maestro de Documentación Técnica

Bienvenido al repositorio maestro de documentación técnica y operativa de **Sentix Intelligence**, la plataforma de ingesta multimodal, procesamiento de lenguaje natural (PLN/NLP), minería de datos y telemetría analítica basada en las interacciones de la comunidad estudiantil de la Carrera de Informática (Universidad Mayor de San Andrés - UMSA).

---

## 🗺️ Mapa de Navegación del Sistema

Toda la documentación está organizada de forma modular siguiendo el flujo de ciclo de vida del dato (Ingesta $\rightarrow$ Enriquecimiento $\rightarrow$ Minería $\rightarrow$ Persistencia $\rightarrow$ Exposición y Visualización):

```
docs/
├── README.md                                          # Este documento (Índice Maestro)
│
├── 01_ingenieria_datos_etl/
│   ├── PROC_01_extraccion_ontologia_academica.md      # Parsing vectorial de PDF y ontología académica
│   ├── PROC_02_limpieza_multimodal_ocr.md             # Normalización NFKC, deduplicación MD5 y OCR Tesseract
│   ├── PROC_03_vinculacion_entidades_hilos.md         # Entity Linking Docentes/Materias y resolución de hilos
│   └── PROC_04_05_mineria_jergas_modismos.md          # Minería de modismos bolivianos, concordancias KWIC y jergas
│
├── 02_procesamiento_lenguaje_natural/
│   ├── PROC_06_analisis_multimodal_imagenes.md        # Visión computacional, memes y taxonomía de stickers
│   ├── PROC_07A_tfidf_multidimensional.md             # TF-IDF por Docente, Materia y Ciclos Académicos
│   ├── PROC_07B_modelado_topicos_lda.md               # Modelado Temático Latente (LDA k=4, Matrices Beta/Gamma)
│   └── PROC_07C_analisis_sentimiento_dual.md          # Sentimiento Heurístico Context-Aware vs NRCLex Plutchik
│
├── 03_base_datos_persistencia/
│   └── ARCH_08_persistencia_neon_postgresql.md        # Esquema DDL, Integridad Referencial, FTS y Pooling Serverless
│
└── 04_arquitectura_servicio_web/
    ├── ARCH_09_backend_flask_api_telemetria.md        # Application Factory, Blueprints REST v1 y Queries SQL
    └── ARCH_10_frontend_dashboard_visualizaciones.md   # Jinja2, Tailwind Dark/Light, Gráficos SVG y Resiliencia
```

---

## 📋 Matriz de Procesos y Artefactos

| Código | Módulo | Script Principal | Entradas Principales | Salidas Clave |
| :--- | :--- | :--- | :--- | :--- |
| **PROC-01** | [Extracción de Ontología Académica](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/docs/01_ingenieria_datos_etl/PROC_01_extraccion_ontologia_academica.md) | `data/scripts/01_parse_horarios_pdf.py` | `data/raw/horarios.pdf` | `catalogo_docentes_umsa.csv`<br>`catalogo_materias_umsa.csv`<br>`oferta_horarios_umsa.csv` |
| **PROC-02** | [Limpieza Multimodal y OCR](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/docs/01_ingenieria_datos_etl/PROC_02_limpieza_multimodal_ocr.md) | `data/scripts/02_pipeline_limpieza_multimodal.py` | `data/raw/result.json`<br>`data/media/photos/` | `dataset_telegram_master.csv`<br>`eventos_servicio_log.csv`<br>`ocr_cache.json` |
| **PROC-03** | [Entity Linking y Resolución de Hilos](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/docs/01_ingenieria_datos_etl/PROC_03_vinculacion_entidades_hilos.md) | `data/scripts/03_entity_linking_docentes.py` | `dataset_telegram_master.csv`<br>Catálogos ontológicos | `dataset_menciones_docentes.csv`<br>`ranking_docentes_menciones.csv` |
| **PROC-04-05** | [Minería de Jergas y Modismos](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/docs/01_ingenieria_datos_etl/PROC_04_05_mineria_jergas_modismos.md) | `data/scripts/04_mineria_modismos_y_concordancias.py`<br>`data/scripts/05_extractor_diccionario_jergas.py` | `dataset_telegram_master.csv` | `catalogo_modismos_umsa.csv`<br>`diccionario_jergas_y_modismos_umsa.csv` |
| **PROC-06** | [Análisis Multimodal de Imágenes y Memes](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/docs/02_procesamiento_lenguaje_natural/PROC_06_analisis_multimodal_imagenes.md) | `data/scripts/06_analisis_multimodal_imagenes_sentimiento.py` | `data/media/photos/`<br>`data/media/stickers/` | `catalogo_gifs_animaciones.csv`<br>Taxonomías emocionales |
| **PROC-07A** | [TF-IDF Multidimensional](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/docs/02_procesamiento_lenguaje_natural/PROC_07A_tfidf_multidimensional.md) | `data/scripts/07_pipeline_nlp_avanzado.py` | `dataset_menciones_docentes.csv` | `tfidf_docentes_ranking.csv`<br>`tfidf_materias_ranking.csv`<br>`tfidf_ciclos_academicos.csv` |
| **PROC-07B** | [Modelado Temático LDA (k=4)](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/docs/02_procesamiento_lenguaje_natural/PROC_07B_modelado_topicos_lda.md) | `data/scripts/07_pipeline_nlp_avanzado.py` | Mensajes tokenizados | `lda_topicos_vocabulario.csv`<br>Distribuciones tópicas |
| **PROC-07C** | [Análisis Dual de Sentimientos](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/docs/02_procesamiento_lenguaje_natural/PROC_07C_analisis_sentimiento_dual.md) | `data/scripts/07_pipeline_nlp_avanzado.py` | Contenido textual unificado | `lexico_emociones_umsa.json`<br>`nrc_spanish_lexicon.json` |
| **ARCH-08** | [Persistencia Neon PostgreSQL](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/docs/03_base_datos_persistencia/ARCH_08_persistencia_neon_postgresql.md) | `database/schema.sql`<br>`database/connection.py` | Datasets procesados CSV | Esquema DDL en Neon (14 tablas, 4 vistas, índices FTS GIN) |
| **ARCH-09** | [Backend Flask y API REST](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/docs/04_arquitectura_servicio_web/ARCH_09_backend_flask_api_telemetria.md) | `app/__init__.py`<br>`app/routes/api_v1/telemetry.py` | HTTP REST requests | Endpoints `/api/v1/health`, `/api/v1/stats`, telemetría en vivo |
| **ARCH-10** | [Dashboard Ejecutivo y UI](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/docs/04_arquitectura_servicio_web/ARCH_10_frontend_dashboard_visualizaciones.md) | `app/routes/web/dashboard.py`<br>`app/templates/` | Contexto Jinja2 | Dashboard interactivo Dark/Light, Gráficos SVG puros |

---

## ⚡ Estándar de Ejecución y Reproducibilidad

El pipeline de datos y la aplicación pueden ejecutarse de manera desacoplada o integral siguiendo las instrucciones detalladas en cada sección.

Para ejecutar la aplicación web en entorno de desarrollo local:
```powershell
python run.py
```

Para re-ejecutar el pipeline analítico completo de procesamiento de lenguaje natural:
```powershell
python data/scripts/07_pipeline_nlp_avanzado.py
python database/execute_nlp_migration_neon.py
```
