# PROC-01: Extracción de Ontología Académica y Parsing Vectorial de Horarios

## 1. Identificación y Propósito
* **Script Fuente:** [`data/scripts/01_parse_horarios_pdf.py`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/01_parse_horarios_pdf.py)
* **Objetivo:** Transformar el documento oficial de oferta académica no estructurado ([`horarios.pdf`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/raw/horarios.pdf), 9 páginas en formato PDF vectorial) de la Carrera de Informática (UMSA) en una base ontológica relacional y normalizada que sirve como verdad de terreno (*ground truth*) para los catálogos de docentes, materias, paralelos, horarios y expresiones regulares de detección coloquial.

---

## 2. Especificación de Interfaces (Contratos de Datos)

### Insumos (Input)
* **Archivo:** `data/raw/horarios.pdf` (fallback a `data/horarios.pdf`).
* **Formato:** Documento PDF vectorial con tablas desprovistas de bordes rígidos, organizadas jerárquicamente por:
  - Cabecera de materia (`CODIGO - NOMBRE DE MATERIA`, ej. `INF-111 INTRODUCCION A LA INFORMATICA`).
  - Filas de asignación: `PARALELO`, `DOCENTE` y bloques multilínea de `HORARIO` y `AULA`.

### Artefactos Generados (Output)
1. [`data/processed/oferta_horarios_umsa.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/oferta_horarios_umsa.csv) (267 filas):
   * Esquema: `codigo_materia` (string), `nombre_materia` (string), `paralelo` (string), `docente` (string), `horarios` (string concatenado con ` // `).
2. [`data/processed/catalogo_docentes_umsa.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/catalogo_docentes_umsa.csv) (85 filas):
   * Esquema: `docente_id` (`DOC_001` a `DOC_085`), `nombre_completo`, `materias_que_dicta` (lista delimitada por ` ; `), `alias_regex` (patrones regex para captura de menciones).
3. [`data/processed/catalogo_materias_umsa.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/catalogo_materias_umsa.csv) (158 filas):
   * Esquema: `codigo_materia`, `nombre_materia`, `paralelos_disponibles`, `docentes_asignados`, `alias_regex`.

Todos los archivos CSV se emiten bajo el estándar **RFC-4180** con codificación **`utf-8-sig` (UTF-8 con BOM)** para compatibilidad nativa con Microsoft Excel, pandas y PostgreSQL.

---

## 3. Arquitectura y Diagrama de Flujo

```mermaid
flowchart TD
    A[horarios.pdf\n9 páginas vectoriales] --> B[PyMuPDF / fitz.open]
    B --> C[Extracción de líneas de texto plano\npage.get_text]
    C --> D[Filtro de cabeceras institucionales\n'FACULTAD', 'PENSUM', etc.]
    
    D --> E{Evaluación por línea de texto}
    E -->|Regex: ^[A-Z]{3}-\d{3} -| F[Detecta Nueva Materia\nFlush registro anterior]
    E -->|Longitud == 1 y Mayúscula| G[Detecta Paralelo\nEj: 'A', 'B', 'C']
    E -->|Prefijo Día LUNES..SABADO| H[Acumula Horario y Aula]
    E -->|Mayúsculas > 4 chars sin dígitos| I[Detecta Nombre Docente]
    
    F --> J[Estructuración de Registros en Memoria]
    G --> J
    H --> J
    I --> J
    
    J --> K[Generador de Expresiones Regulares\nbuild_teacher_regex]
    K --> L1[oferta_horarios_umsa.csv]
    K --> L2[catalogo_docentes_umsa.csv]
    K --> L3[catalogo_materias_umsa.csv]
```

---

## 4. Lógica Algorítmica y Métodos Implementados

### 4.1. Máquina de Estados Finita para Parsing Jerárquico
El extractor itera sobre cada flujo de líneas manteniendo un estado contextual (`current_sub_code`, `current_sub_name`, `current_paralelo`, `current_teacher`, `current_schedules`). Cada vez que se detecta un cambio de materia o un nuevo paralelo, la función `flush_record()` vuelca de forma atómica la tupla estructurada antes de reiniciar el acumulador de horarios.

### 4.2. Construcción Automática de Expresiones Regulares (Alias Regex)
Para maximizar el *recall* en el análisis de mensajes de chat sin sacrificar la *precisión*:
* Se separan nombres propios de apellidos paterno y materno.
* Se generan combinaciones con títulos honoríficos facultativos:
  $$\text{Prefijos: } \texttt{(?:lic\.?|docente|ing\.?|profe|profesor|profesora)?}$$
* **Protección contra Falsos Positivos:** Apellidos extremadamente frecuentes en la región andina (`MAMANI`, `QUISPE`, `FLORES`, `ROJAS`, `PEREZ`, `LOPEZ`) son bloqueados para coincidencia solitaria aislada y forzados a combinarse con el nombre de pila o título.

---

## 5. Implementación en Código y Referencias

* Función extractora principal: [`extract_academic_data()`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/01_parse_horarios_pdf.py#L21-L102)
* Generador de expresiones regulares de docentes: [`build_teacher_regex()`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/01_parse_horarios_pdf.py#L104-L125)
* Orquestador y exportación CSV: [`main()`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/01_parse_horarios_pdf.py#L126-L194)

---

## 6. Integración con el Ecosistema del Proyecto

```
[horarios.pdf]
      │
      ▼
(PROC-01: 01_parse_horarios_pdf.py)
      │
      ├───────────────────────┬───────────────────────┐
      ▼                       ▼                       ▼
catalogo_docentes_umsa   catalogo_materias_umsa   oferta_horarios_umsa
      │                       │                       │
      ├───────────────────────┴───────────────────────┘
      ▼
(PROC-03: Entity Linking) ──► menciones_docentes
      │
      ▼
(ARCH-08: Neon PostgreSQL) ──► Tablas 'docentes', 'materias', 'oferta_horarios'
```

---

## 7. Instrucciones de Reproducción y Verificación

### Comando de Ejecución:
```powershell
python data/scripts/01_parse_horarios_pdf.py
```

### Validaciones de Integridad Esperadas:
* `oferta_horarios_umsa.csv`: Exactamente **267 asignaciones de paralelos**.
* `catalogo_docentes_umsa.csv`: Exactamente **85 docentes académicos**.
* `catalogo_materias_umsa.csv`: Exactamente **158 materias únicas**.
* Salida en consola: `Total de registros de oferta extraídos: 267`.

---

## 8. Consideraciones Técnicas y Rendimiento
* **Rendimiento:** Procesa el documento completo de 9 páginas en **menos de 0.45 segundos** en CPU estándar.
* **Tolerancia a Fallos:** Maneja automáticamente páginas sin docentes explícitos asignando el valor de sustitución `"Sin Docente"`.
* **Codificación:** Utiliza `utf-8-sig` garantizando la preservación de caracteres diacríticos (`Á`, `É`, `Í`, `Ó`, `Ú`, `Ñ`) propios de los nombres de los docentes de la carrera.
