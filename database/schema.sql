-- ============================================================================
-- SENTIX INTELLIGENCE - ESQUEMA DDL POSTGRESQL 18 / NEON SERVERLESS
-- ============================================================================

-- 1. Catálogo de Docentes
CREATE TABLE IF NOT EXISTS docentes (
    docente_id VARCHAR(100) PRIMARY KEY,
    nombre_completo VARCHAR(255) NOT NULL,
    materias_que_dicta TEXT,
    alias_regex TEXT
);

-- 2. Catálogo de Materias
CREATE TABLE IF NOT EXISTS materias (
    codigo_materia VARCHAR(50) PRIMARY KEY,
    nombre_materia VARCHAR(255) NOT NULL,
    paralelos_disponibles VARCHAR(100),
    docentes_asignados TEXT,
    alias_regex TEXT
);

-- 3. Oferta de Horarios y Aulas
CREATE TABLE IF NOT EXISTS oferta_horarios (
    id SERIAL PRIMARY KEY,
    codigo_materia VARCHAR(50),
    nombre_materia VARCHAR(255),
    paralelo VARCHAR(20),
    docente VARCHAR(255),
    horarios TEXT
);

-- 4. Dataset Maestro de Mensajes (Fact Table de Telemetría)
CREATE TABLE IF NOT EXISTS mensajes (
    mensaje_id BIGINT PRIMARY KEY,
    fecha TIMESTAMP WITHOUT TIME ZONE,
    anio INTEGER,
    mes INTEGER,
    dia INTEGER,
    hora INTEGER,
    usuario_id VARCHAR(100),
    usuario_nombre TEXT,
    es_respuesta BOOLEAN DEFAULT FALSE,
    respuesta_a_id BIGINT,
    padre_existe BOOLEAN DEFAULT FALSE,
    texto_mensaje_padre TEXT,
    texto_original TEXT,
    texto_limpio TEXT,
    longitud_caracteres INTEGER,
    conteo_palabras INTEGER,
    es_pregunta BOOLEAN DEFAULT FALSE,
    tiene_url BOOLEAN DEFAULT FALSE,
    menciones_usuarios TEXT,
    tiene_imagen BOOLEAN DEFAULT FALSE,
    ruta_imagen TEXT,
    imagen_texto_ocr TEXT,
    es_sticker BOOLEAN DEFAULT FALSE,
    sticker_emoji VARCHAR(50),
    sticker_emocion VARCHAR(50),
    es_gif BOOLEAN DEFAULT FALSE,
    gif_nombre TEXT,
    archivo_adjunto TEXT,
    thumbnail_adjunto TEXT,
    total_reacciones INTEGER DEFAULT 0,
    reaccion_principal VARCHAR(50),
    reacciones_resumen TEXT,
    docente_mencionado TEXT,
    materia_mencionada TEXT,
    entidad_heredada_hilo BOOLEAN DEFAULT FALSE,
    contenido_multimodal_unificado TEXT
);

-- 5. Menciones a Docentes y Consultas
CREATE TABLE IF NOT EXISTS menciones_docentes (
    id SERIAL PRIMARY KEY,
    mensaje_id BIGINT,
    docente_mencionado TEXT,
    materia_mencionada TEXT,
    fecha TIMESTAMP WITHOUT TIME ZONE,
    usuario_nombre TEXT,
    texto_limpio TEXT,
    es_pregunta BOOLEAN DEFAULT FALSE,
    total_reacciones INTEGER DEFAULT 0,
    contenido_multimodal_unificado TEXT
);

-- 6. Reacciones Granulares por Emoji
CREATE TABLE IF NOT EXISTS reacciones_granular (
    id SERIAL PRIMARY KEY,
    mensaje_id BIGINT,
    fecha_mensaje TIMESTAMP WITHOUT TIME ZONE,
    emoji VARCHAR(50),
    conteo INTEGER DEFAULT 1,
    emocion_reaccion VARCHAR(100)
);

-- 7. Catálogo de Modismos Regionales UMSA
CREATE TABLE IF NOT EXISTS catalogo_modismos (
    id SERIAL PRIMARY KEY,
    modismo_nombre VARCHAR(100) UNIQUE,
    categoria VARCHAR(100),
    polaridad_base DOUBLE PRECISION,
    total_ocurrencias INTEGER DEFAULT 0,
    mensajes_unicos INTEGER DEFAULT 0,
    menciones_con_docente INTEGER DEFAULT 0,
    menciones_con_materia INTEGER DEFAULT 0,
    menciones_con_sarcasmo INTEGER DEFAULT 0,
    ejemplo_kwic TEXT
);

-- 8. Diccionario de Jerga y Minería de Opinión
CREATE TABLE IF NOT EXISTS diccionario_jergas (
    id SERIAL PRIMARY KEY,
    termino_jerga VARCHAR(100),
    categoria VARCHAR(100),
    significado_en_contexto_umsa TEXT,
    polaridad_base DOUBLE PRECISION,
    total_ocurrencias INTEGER DEFAULT 0,
    mensajes_afectados INTEGER DEFAULT 0,
    ejemplo_real_del_chat TEXT
);

-- 9. Registro de Auditoría de Eventos de Servicio
CREATE TABLE IF NOT EXISTS eventos_servicio (
    id BIGINT PRIMARY KEY,
    fecha TIMESTAMP WITHOUT TIME ZONE,
    actor VARCHAR(255),
    actor_id VARCHAR(100),
    accion TEXT
);

-- Índices de alto rendimiento para consultas analíticas
CREATE INDEX IF NOT EXISTS idx_mensajes_fecha ON mensajes(fecha);
CREATE INDEX IF NOT EXISTS idx_mensajes_docente ON mensajes(docente_mencionado);
CREATE INDEX IF NOT EXISTS idx_mensajes_materia ON mensajes(materia_mencionada);
CREATE INDEX IF NOT EXISTS idx_menciones_docente ON menciones_docentes(docente_mencionado);
CREATE INDEX IF NOT EXISTS idx_reacciones_mensaje ON reacciones_granular(mensaje_id);

-- Restricciones de Clave Foránea (Foreign Keys) para Relaciones e Integridad Referencial
-- 1. Relaciones de la tabla principal 'mensajes'
ALTER TABLE mensajes 
    ADD CONSTRAINT fk_mensajes_docentes 
    FOREIGN KEY (docente_id) REFERENCES docentes(docente_id) ON DELETE SET NULL;

ALTER TABLE mensajes 
    ADD CONSTRAINT fk_mensajes_materias 
    FOREIGN KEY (codigo_materia) REFERENCES materias(codigo_materia) ON DELETE SET NULL;

ALTER TABLE mensajes 
    ADD CONSTRAINT fk_mensajes_hilo 
    FOREIGN KEY (respuesta_a_id) REFERENCES mensajes(mensaje_id) ON DELETE SET NULL;

-- 2. Relaciones de 'menciones_docentes'
ALTER TABLE menciones_docentes 
    ADD CONSTRAINT fk_menciones_mensajes 
    FOREIGN KEY (mensaje_id) REFERENCES mensajes(mensaje_id) ON DELETE CASCADE;

ALTER TABLE menciones_docentes 
    ADD CONSTRAINT fk_menciones_docentes 
    FOREIGN KEY (docente_id) REFERENCES docentes(docente_id) ON DELETE SET NULL;

ALTER TABLE menciones_docentes 
    ADD CONSTRAINT fk_menciones_materias 
    FOREIGN KEY (codigo_materia) REFERENCES materias(codigo_materia) ON DELETE SET NULL;

-- 3. Relaciones de 'oferta_horarios'
ALTER TABLE oferta_horarios 
    ADD CONSTRAINT fk_oferta_materias 
    FOREIGN KEY (codigo_materia) REFERENCES materias(codigo_materia) ON DELETE CASCADE;

ALTER TABLE oferta_horarios 
    ADD CONSTRAINT fk_oferta_docentes 
    FOREIGN KEY (docente_id) REFERENCES docentes(docente_id) ON DELETE SET NULL;

-- 4. Relaciones de 'reacciones_granular'
ALTER TABLE reacciones_granular 
    ADD CONSTRAINT fk_reacciones_mensajes 
    FOREIGN KEY (mensaje_id) REFERENCES mensajes(mensaje_id) ON DELETE CASCADE;

-- 5. Tabla de ocurrencias de Modismos por Mensaje
CREATE TABLE IF NOT EXISTS modismos_mensajes (
    id SERIAL PRIMARY KEY,
    mensaje_id BIGINT NOT NULL,
    modismo VARCHAR(100) NOT NULL,
    conteo INTEGER DEFAULT 1,
    CONSTRAINT fk_modismos_mensajes FOREIGN KEY (mensaje_id) REFERENCES mensajes(mensaje_id) ON DELETE CASCADE
);

-- 6. Tabla de GIFs y Animaciones
CREATE TABLE IF NOT EXISTS gifs_animaciones (
    id SERIAL PRIMARY KEY,
    mensaje_id BIGINT NOT NULL,
    archivo_ruta VARCHAR(500) NOT NULL,
    ancho INTEGER,
    alto INTEGER,
    duracion_segundos NUMERIC(6, 2),
    mime_type VARCHAR(100),
    thumbnail_ruta VARCHAR(500),
    CONSTRAINT fk_gifs_mensajes FOREIGN KEY (mensaje_id) REFERENCES mensajes(mensaje_id) ON DELETE CASCADE
);

-- 7. Tabla de Cache OCR de Imágenes
CREATE TABLE IF NOT EXISTS ocr_cache (
    clave_imagen TEXT PRIMARY KEY,
    texto_extraido TEXT,
    confianza NUMERIC(5, 4),
    palabras_clave TEXT,
    fecha_procesamiento TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Índice Full-Text Search (FTS) en Español para Mensajes
CREATE INDEX IF NOT EXISTS idx_mensajes_fts_es 
ON mensajes USING gin(to_tsvector('spanish', coalesce(texto_limpio, '')));

-- ====================================================================
-- VISTAS ANALÍTICAS (DYNAMIC VIEWS)
-- ====================================================================

-- Vista 1: Ranking Analítico de Docentes
CREATE OR REPLACE VIEW vista_ranking_docentes AS
SELECT 
    d.docente_id,
    d.nombre_normalizado,
    d.departamento,
    COUNT(m.id) AS total_menciones,
    ROUND(AVG(m.sentimiento_score)::numeric, 4) AS score_sentimiento_promedio,
    ROUND(SUM(CASE WHEN m.sentimiento_label = 'POS' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(m.id), 0), 2) AS pct_positivo,
    ROUND(SUM(CASE WHEN m.sentimiento_label = 'NEG' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(m.id), 0), 2) AS pct_negativo,
    ROUND(SUM(CASE WHEN m.sentimiento_label = 'NEU' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(m.id), 0), 2) AS pct_neutral
FROM docentes d
JOIN menciones_docentes m ON d.docente_id = m.docente_id
GROUP BY d.docente_id, d.nombre_normalizado, d.departamento;

-- Vista 2: Resumen Analítico de Materias
CREATE OR REPLACE VIEW vista_resumen_materias AS
SELECT 
    mat.codigo_materia,
    mat.nombre_materia,
    mat.departamento,
    COUNT(m.id) AS total_menciones,
    ROUND(AVG(m.sentimiento_score)::numeric, 4) AS score_sentimiento_promedio,
    COUNT(DISTINCT m.docente_id) AS docentes_asociados
FROM materias mat
JOIN menciones_docentes m ON mat.codigo_materia = m.codigo_materia
GROUP BY mat.codigo_materia, mat.nombre_materia, mat.departamento;

-- Vista 3: Tendencia Temporal Mensual de Sentimiento
CREATE OR REPLACE VIEW vista_tendencia_temporal_sentimiento AS
SELECT 
    TO_CHAR(fecha, 'YYYY-MM') AS cohorte_mes,
    COUNT(*) AS total_mensajes,
    ROUND(AVG(compound)::numeric, 4) AS compound_promedio,
    ROUND(SUM(CASE WHEN label_sentimiento = 'POS' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS pct_positivo,
    ROUND(SUM(CASE WHEN label_sentimiento = 'NEG' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS pct_negativo,
    ROUND(SUM(CASE WHEN label_sentimiento = 'NEU' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS pct_neutral
FROM mensajes
WHERE fecha IS NOT NULL
GROUP BY TO_CHAR(fecha, 'YYYY-MM')
ORDER BY cohorte_mes;


