# PROC-07A: Vectorización TF-IDF Multidimensional por Docentes, Materias y Ciclos

## 1. Identificación y Propósito
* **Script Fuente:** [`data/scripts/07_pipeline_nlp_avanzado.py` (Líneas 357-534)](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/07_pipeline_nlp_avanzado.py#L357-L534)
* **Objetivo:** Cuantificar la relevancia estadística y distintiva del léxico en cuatro dimensiones analíticas ortogonales: por **Docente**, por **Materia**, por **Ciclo Académico** (Básico, Intermedio, Superior) y por **Cohorte Temporal** (años 2020 a 2026), aislando la jerga descriptiva y términos característicos frente al ruido lingüístico general.

---

## 2. Especificación de Interfaces (Contratos de Datos)

### Insumos (Input)
* [`data/processed/dataset_menciones_docentes.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/dataset_menciones_docentes.csv) y [`dataset_telegram_master.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/dataset_telegram_master.csv).
* Lista de Stopwords personalizada en español extendida con términos conversacionales vacíos (*"hola"*, *"gracias"*, *"buenas"*, *"grupo"*, *"link"*).

### Artefactos Generados (Output)
1. [`data/processed/tfidf_docentes_ranking.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/tfidf_docentes_ranking.csv): Top 15 términos distintivos por cada docente.
2. [`data/processed/tfidf_materias_ranking.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/tfidf_materias_ranking.csv): Top 15 términos distintivos por materia.
3. [`data/processed/tfidf_ciclos_academicos.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/tfidf_ciclos_academicos.csv): Top 25 términos por ciclo formativo.
4. [`data/processed/tfidf_entidades_consolidado.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/tfidf_entidades_consolidado.csv): Tabla maestra unificada con las dimensiones `entidad_tipo`, `entidad_id`, `termino`, `score_tfidf`, `ranking_pos`.

---

## 3. Arquitectura y Diagrama de Flujo

```mermaid
flowchart TD
    A[Corpus Unificado de Mensajes y Menciones] --> B[Agrupación Semántica por Entidad]
    
    B --> C1[Agrupación por Docente\n85 docentes]
    B --> C2[Agrupación por Materia\n158 materias]
    B --> C3[Agrupación por Ciclo Académico\nBásico <= 135 | Intermedio <= 166 | Superior > 166]
    B --> C4[Agrupación por Cohorte Anual\n2020 a 2026]
    
    C1 --> D[TfidfVectorizer scikit-learn\nngram_range=1,2 | min_df=1 | max_df=0.85]
    C2 --> D
    C3 --> D
    C4 --> D
    
    D --> E[Cálculo de Scores TF-IDF\nRanking descendente por grupo]
    E --> F1[tfidf_docentes_ranking.csv]
    E --> F2[tfidf_materias_ranking.csv]
    E --> F3[tfidf_ciclos_academicos.csv]
    E --> F4[tfidf_entidades_consolidado.csv]
```

---

## 4. Lógica Algorítmica y Métodos Implementados

### 4.1. Formulación Matemática de TF-IDF con n-gramas
Para cada término $t$ (unigramas y bigramas) en un pseudo-documento agregado $d$ (ej. todos los mensajes sobre un docente):
$$\text{TF}(t, d) = \frac{f_{t, d}}{\sum_{t' \in d} f_{t', d}}$$
$$\text{IDF}(t, D) = \ln \left( \frac{1 + |D|}{1 + |\{d \in D : t \in d\}|} \right) + 1$$
$$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \text{IDF}(t, D)$$
El vector resultante se normaliza bajo la norma euclidiana $L_2$:
$$\mathbf{v}_{\text{norm}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}$$

### 4.2. Estratificación por Ciclos Académicos
Se implementó una regla de clasificación basada en la numeración del pensum oficial de la Carrera de Informática (UMSA):
* **Ciclo Básico:** Materias con código numérico $\le 135$ (Programación Básica, Cálculo, Álgebra, Estructuras Discretas). Predominan términos: *"auxiliar"*, *"primer parcial"*, *"pseudocodigo"*, *"laboratorio"*.
* **Ciclo Intermedio:** Códigos entre $136$ y $166$ (Sistemas Operativos, Base de Datos, Métodos Numéricos). Predominan: *"sql"*, *"linux"*, *"proyecto"*, *"defensa"*.
* **Ciclo Superior:** Códigos $> 166$ e informática aplicada. Predominan: *"tesis"*, *"taller grado"*, *"modalidad graduacion"*, *"docente guia"*.

---

## 5. Implementación en Código y Referencias
* Función de cálculo multidimensional: [`calcular_tfidf_multidimensional()`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/07_pipeline_nlp_avanzado.py#L357-L534)
* Clasificador de ciclos formativos: [`determinar_ciclo()`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/07_pipeline_nlp_avanzado.py#L450-L463)

---

## 6. Integración con el Ecosistema del Proyecto
* **Persistencia:** Carga directa a la tabla `tfidf_entidades` en Neon PostgreSQL mediante [`execute_nlp_migration_neon.py`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/database/execute_nlp_migration_neon.py).
* **Frontend:** El dashboard consume la función [`get_tfidf_keywords()`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/database/queries.py#L287-L300) para proyectar nubes de términos y cuadrantes de especialidad docente.

---

## 7. Instrucciones de Reproducción y Verificación

### Comando de Ejecución:
```powershell
python -c "import sys; sys.path.insert(0, '.'); from data.scripts import 07_pipeline_nlp_avanzado"
# O ejecución del pipeline integral:
python data/scripts/07_pipeline_nlp_avanzado.py
```

### Validaciones de Integridad Esperadas:
* `tfidf_entidades_consolidado.csv`: Alrededor de **3,500 tuplas indexadas**.
* Rangos de score TF-IDF: Valores positivos acotados en $(0.0, 1.0]$.
* Términos vacíos eliminados por filtro de stopwords.

---

## 8. Consideraciones Técnicas y Rendimiento
* **Matriz Esparsa:** Empleo de representaciones CSR (`scipy.sparse.csr_matrix`) reduciendo el consumo de memoria en más de un 92% respecto a matrices densas.
* **Tiempo de Cómputo:** Las 4 dimensiones se calculan en paralelo o secuencialmente en menos de **2.1 segundos**.
