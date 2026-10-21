# PROC-04-05: Minería de Jergas, Modismos Regionales y Concordancias KWIC

## 1. Identificación y Propósito
* **Scripts Fuente:** [`data/scripts/04_mineria_modismos_y_concordancias.py`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/04_mineria_modismos_y_concordancias.py) y [`data/scripts/05_extractor_diccionario_jergas.py`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/05_extractor_diccionario_jergas.py).
* **Objetivo:** Descubrir, catalogar y medir el impacto semántico del vocabulario no estándar, la jerga universitaria paceña y los modismos bolivianos empleados en las evaluaciones docentes y consultas académicas, generando colocaciones **KWIC (Key Word in Context)**, asignando polaridades emocionales contextuales y detectando ironía o sarcasmo.

---

## 2. Especificación de Interfaces (Contratos de Datos)

### Insumos (Input)
* [`data/processed/dataset_telegram_master.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/dataset_telegram_master.csv): Mensajes normalizados con menciones a entidades y reacciones.
* Catálogo de expresiones regulares y taxonomías léxicas definidas en [`CATALOGO_PATRONES_MODISMOS`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/04_mineria_modismos_y_concordancias.py#L23-L72) y [`BASE_JERGAS_SIGNIFICADOS`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/05_extractor_diccionario_jergas.py#L24-L120).

### Artefactos Generados (Output)
1. [`data/processed/dataset_modismos_mensajes.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/dataset_modismos_mensajes.csv) (**538 ocurrencias indexadas**):
   * `id`, `mensaje_id`, `fecha`, `usuario_nombre`, `modismo_nombre`, `categoria_modismo`, `polaridad_asignada`, `kwic_antes`, `kwic_termino`, `kwic_despues`, `docente_asociado`, `materia_asociada`, `es_sarcasmo`.
2. [`data/processed/catalogo_modismos_umsa.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/catalogo_modismos_umsa.csv):
   * Métricas agregadas por modismo: `total_ocurrencias`, `mensajes_unicos`, `menciones_con_docente`, `menciones_con_materia`, `menciones_con_sarcasmo`, `ejemplo_kwic`.
3. [`data/processed/diccionario_jergas_y_modismos_umsa.csv`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/processed/diccionario_jergas_y_modismos_umsa.csv):
   * Diccionario lexicográfico formal: término, significado en el contexto UMSA, polaridad base $[-2.5, +2.5]$ y ejemplo real extraído del chat.

---

## 3. Arquitectura y Diagrama de Flujo

```mermaid
flowchart TD
    A[dataset_telegram_master.csv] --> B[Iteración de Mensajes de Texto]
    B --> C[Compilación de Patrones de Jergas & Modismos]
    
    C --> D{Coincidencia de Patrón en Texto?}
    D -->|Sí| E[Extracción de Ventana KWIC\n6 palabras antes | Término | 6 palabras después]
    
    E --> F{Presencia de Emojis de Sarcasmo?\n💀, 🤡, ⚰️, 🤣, xD, :v}
    F -->|Sí| G[Flag es_sarcasmo = True\nInversión / Atenuación de Polaridad]
    F -->|No| H[Polaridad Nominal Asignada]
    
    G --> I[dataset_modismos_mensajes.csv]
    H --> I
    
    I --> J[Agregación Estadística por Término]
    J --> K[catalogo_modismos_umsa.csv]
    J --> L[diccionario_jergas_y_modismos_umsa.csv]
```

---

## 4. Lógica Algorítmica y Métodos Implementados

### 4.1. Taxonomía de Expresiones Estudiantiles UMSA
Los patrones están clasificados en 6 categorías operativas:
1. **Facilidad y Aprobación:** *"barco"*, *"suave nomás"*, *"pichi"*, *"pan comido"*, *"regala nota"*, *"tranqui"*.
2. **Dificultad y Exigencia:** *"yuca"*, *"fregado"*, *"filtro"*, *"materia colador"*, *"matador"*, *"masacre"*.
3. **Reprobación y Frustración:** *"tirarse"*, *"aplazar"*, *"morir"*, *"rip"*, *"llorar"*, *"fletear"*.
4. **Calidad y Reconocimiento:** *"capo"*, *"crack"*, *"enseña bien"*, *"buena onda"*, *"conviene"*.
5. **Deficiencia y Mal Trato:** *"no enseña"*, *"faltón"*, *"no sube notas"*, *"prepotente"*, *"enseñanza antigua"*.
6. **Sarcasmo e Ironía:** Mensajes con elogios ficticios yuxtapuestos con emojis de burla o resignación (`🤡`, `💀`, `⚰️`).

### 4.2. Algoritmo KWIC (Key Word In Context)
Para preservar la evidencia empírica de cada uso léxico, [`extraer_kwic()`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/04_mineria_modismos_y_concordancias.py#L76-L84) recorta una ventana dinámica:
$$\text{KWIC}(t) = \left[ w_{-k}, \dots, w_{-1} \right] \ \mathbf{t} \ \left[ w_{+1}, \dots, w_{+k} \right]$$
donde $k=6$ palabras hacia la izquierda y derecha del token detectado.

---

## 5. Implementación en Código y Referencias
* Definición de patrones y categorías: [`04_mineria_modismos_y_concordancias.py` (Líneas 23-72)](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/04_mineria_modismos_y_concordancias.py#L23-L72)
* Extracción de concordancias KWIC: [`extraer_kwic()`](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/04_mineria_modismos_y_concordancias.py#L76-L84)
* Detección de sarcasmo y agregación: [`04_mineria_modismos_y_concordancias.py` (Líneas 100-220)](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/04_mineria_modismos_y_concordancias.py#L100-L220)
* Base lexicográfica explicativa: [`05_extractor_diccionario_jergas.py` (Líneas 24-120)](file:///c:/Users/julio/Downloads/INF_2_2026/DM/DMProyAnalisisSentimiento/data/scripts/05_extractor_diccionario_jergas.py#L24-L120)

---

## 6. Integración con el Ecosistema del Proyecto
* **Alimentación hacia la Base de Datos:** Los registros pueblan las tablas `catalogo_modismos`, `diccionario_jergas` y `modismos_mensajes` en Neon PostgreSQL.
* **Alimentación hacia PLN:** Provee los pesos y polaridades base que alimentan el **Léxico Heurístico Context-Aware** de **PROC-07C**.

---

## 7. Instrucciones de Reproducción y Verificación

### Comandos de Ejecución:
```powershell
python data/scripts/04_mineria_modismos_y_concordancias.py
python data/scripts/05_extractor_diccionario_jergas.py
```

### Validaciones de Integridad Esperadas:
* Ocurrencias individuales registradas en `dataset_modismos_mensajes.csv`: **538 filas**.
* Modismos catalogados en `catalogo_modismos_umsa.csv`: **38 modismos clave**.
* Términos lexicográficos con definición en `diccionario_jergas_y_modismos_umsa.csv`: **31 términos**.

---

## 8. Consideraciones Técnicas y Rendimiento
* **Manejo de Variaciones Morfológicas:** Las expresiones regulares incluyen sufijos flexivos propios del habla coloquial (`barco`, `barcos`, `fregado`, `fregados`, `friegan`).
* **Tiempo de Ejecución:** Menos de **0.75 segundos** para analizar los 23,462 mensajes completos.
