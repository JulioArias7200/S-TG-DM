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
