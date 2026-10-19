# -*- coding: utf-8 -*-
"""
database/execute_nlp_migration_neon.py
=======================================
Aplica la migración de esquemas y siembra analítica en Neon PostgreSQL:
1. Agrega columnas NLP a las tablas `mensajes` y `menciones_docentes`.
2. Crea las tablas `lda_topicos` y `tfidf_entidades` con índices btree y tipos TEXT.
3. Actualiza en batch las columnas NLP de `mensajes` y `menciones_docentes`.
4. Siembra `lda_topicos` y `tfidf_entidades` desde los CSV precalculados.
5. Crea la vista analítica `vista_perfil_emocional_docentes`.
"""
import os
import sys
import time
import pandas as pd
import sqlalchemy
from sqlalchemy import text

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from database.connection import engine

DATA_PROCESSED = os.path.join(ROOT_DIR, "data", "processed")
MASTER_CSV = os.path.join(DATA_PROCESSED, "dataset_telegram_master.csv")
MENCIONES_CSV = os.path.join(DATA_PROCESSED, "dataset_menciones_docentes.csv")
LDA_CSV = os.path.join(DATA_PROCESSED, "lda_topicos_vocabulario.csv")
TFIDF_CSV = os.path.join(DATA_PROCESSED, "tfidf_entidades_consolidado.csv")


def execute():
    print("=" * 70)
    print("🚀 EJECUTANDO MIGRACIÓN Y SIEMBRA DE NLP EN NEON POSTGRESQL")
    print("=" * 70)

    # 1. DDL: Nuevas Columnas e Índices
    print("\n🔨 1. Aplicando DDL en Neon Serverless...")
    ddl_statements = [
        # Nuevas columnas en mensajes
        """
        ALTER TABLE mensajes ADD COLUMN IF NOT EXISTS topico_lda_id INTEGER DEFAULT 0;
        ALTER TABLE mensajes ADD COLUMN IF NOT EXISTS topico_lda_prob DOUBLE PRECISION DEFAULT 0.0;
        ALTER TABLE mensajes ADD COLUMN IF NOT EXISTS sentimiento_propio VARCHAR(50) DEFAULT 'neutral';
        ALTER TABLE mensajes ADD COLUMN IF NOT EXISTS sentimiento_propio_score DOUBLE PRECISION DEFAULT 0.0;
        ALTER TABLE mensajes ADD COLUMN IF NOT EXISTS emocion_propia VARCHAR(50) DEFAULT 'neutral';
        ALTER TABLE mensajes ADD COLUMN IF NOT EXISTS nrc_emocion_top VARCHAR(50) DEFAULT 'none';
        """,
        # Nuevas columnas en menciones_docentes
        """
        ALTER TABLE menciones_docentes ADD COLUMN IF NOT EXISTS topico_lda_id INTEGER DEFAULT 0;
        ALTER TABLE menciones_docentes ADD COLUMN IF NOT EXISTS topico_lda_prob DOUBLE PRECISION DEFAULT 0.0;
        ALTER TABLE menciones_docentes ADD COLUMN IF NOT EXISTS sentimiento_propio VARCHAR(50) DEFAULT 'neutral';
        ALTER TABLE menciones_docentes ADD COLUMN IF NOT EXISTS sentimiento_propio_score DOUBLE PRECISION DEFAULT 0.0;
        ALTER TABLE menciones_docentes ADD COLUMN IF NOT EXISTS emocion_propia VARCHAR(50) DEFAULT 'neutral';
        ALTER TABLE menciones_docentes ADD COLUMN IF NOT EXISTS nrc_emocion_top VARCHAR(50) DEFAULT 'none';
        """,
        # Recrear tabla lda_topicos con tipos flexibles
        """
        CREATE TABLE IF NOT EXISTS lda_topicos (
            id SERIAL PRIMARY KEY,
            topico_id INTEGER NOT NULL,
            nombre_etiqueta TEXT NOT NULL,
            termino TEXT NOT NULL,
            beta_prob DOUBLE PRECISION NOT NULL,
            ranking_pos INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_lda_topicos_id ON lda_topicos(topico_id);
        CREATE INDEX IF NOT EXISTS idx_lda_termino ON lda_topicos(termino);
        """,
        # Recrear tabla tfidf_entidades con tipos TEXT para permitir nombres y términos largos
        """
        CREATE TABLE IF NOT EXISTS tfidf_entidades (
            id SERIAL PRIMARY KEY,
            entidad_tipo VARCHAR(50) NOT NULL,
            entidad_id TEXT NOT NULL,
            termino TEXT NOT NULL,
            score_tfidf DOUBLE PRECISION NOT NULL,
            ranking_pos INTEGER NOT NULL
        );
        ALTER TABLE tfidf_entidades ALTER COLUMN entidad_id TYPE TEXT;
        ALTER TABLE tfidf_entidades ALTER COLUMN termino TYPE TEXT;
        CREATE INDEX IF NOT EXISTS idx_tfidf_entidad ON tfidf_entidades(entidad_tipo, entidad_id);
        CREATE INDEX IF NOT EXISTS idx_tfidf_termino ON tfidf_entidades(termino);
        """,
        # Vista Analítica de Perfil Emocional por Docente
        """
        CREATE OR REPLACE VIEW vista_perfil_emocional_docentes AS
        SELECT 
            d.docente_id,
            d.nombre_completo AS docente,
            COALESCE(d.materias_que_dicta, 'Informática') AS departamento,
            COUNT(m.id) AS total_menciones,
            ROUND(COALESCE(AVG(m.sentimiento_propio_score), 0)::numeric, 3) AS score_sentimiento_promedio,
            COUNT(CASE WHEN m.sentimiento_propio = 'positivo' THEN 1 END) AS menciones_positivas,
            COUNT(CASE WHEN m.sentimiento_propio = 'negativo' THEN 1 END) AS menciones_negativas,
            COUNT(CASE WHEN m.sentimiento_propio = 'neutral' THEN 1 END) AS menciones_neutrales,
            COUNT(CASE WHEN m.emocion_propia = 'alivio_aprobacion' THEN 1 END) AS emo_alivio,
            COUNT(CASE WHEN m.emocion_propia = 'frustracion_dificultad' THEN 1 END) AS emo_frustracion,
            COUNT(CASE WHEN m.emocion_propia = 'incertidumbre_ansiedad' THEN 1 END) AS emo_incertidumbre,
            COUNT(CASE WHEN m.emocion_propia = 'conformidad_recomendacion' THEN 1 END) AS emo_conformidad,
            COUNT(CASE WHEN m.emocion_propia = 'descontento_critica' THEN 1 END) AS emo_descontento
        FROM docentes d
        LEFT JOIN menciones_docentes m ON d.nombre_completo = m.docente_mencionado
        GROUP BY d.docente_id, d.nombre_completo, d.materias_que_dicta;
        """
    ]

    with engine.connect() as conn:
        for stmt in ddl_statements:
            conn.execute(text(stmt))
        conn.commit()
    print("   ✅ DDL aplicado exitosamente (Columnas, Tablas lda_topicos / tfidf_entidades y Vista analítica).")

    # 2. Siembra de lda_topicos
    print("\n📦 2. Sembrando lda_topicos...")
    if os.path.exists(LDA_CSV):
        df_lda = pd.read_csv(LDA_CSV, encoding="utf-8-sig")
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE lda_topicos RESTART IDENTITY CASCADE;"))
            conn.commit()
        df_lda.to_sql("lda_topicos", engine, if_exists="append", index=False, method="multi", chunksize=1000)
        print(f"   ✅ {len(df_lda)} términos de tópicos LDA sembrados.")

    # 3. Siembra de tfidf_entidades
    print("\n📦 3. Sembrando tfidf_entidades...")
    if os.path.exists(TFIDF_CSV):
        df_tfidf = pd.read_csv(TFIDF_CSV, encoding="utf-8-sig")
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE tfidf_entidades RESTART IDENTITY CASCADE;"))
            conn.commit()
        df_tfidf.to_sql("tfidf_entidades", engine, if_exists="append", index=False, method="multi", chunksize=1000)
        print(f"   ✅ {len(df_tfidf)} descriptores TF-IDF multidimensionales sembrados.")

    # 4. Actualización en Batch de menciones_docentes y mensajes con staging tables
    print("\n📦 4. Actualizando atributos NLP en menciones_docentes...")
    if os.path.exists(MENCIONES_CSV):
        df_menc = pd.read_csv(MENCIONES_CSV, encoding="utf-8-sig", low_memory=False)
        cols_nlp = ["mensaje_id", "topico_lda_id", "topico_lda_prob", "sentimiento_propio", "sentimiento_propio_score", "emocion_propia", "nrc_emocion_top"]
        df_menc_sub = df_menc[cols_nlp].dropna(subset=["mensaje_id"]).drop_duplicates(subset=["mensaje_id"])
        
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS _staging_menciones_nlp;"))
            conn.execute(text("""
                CREATE TABLE _staging_menciones_nlp (
                    mensaje_id BIGINT PRIMARY KEY,
                    topico_lda_id INTEGER,
                    topico_lda_prob DOUBLE PRECISION,
                    sentimiento_propio VARCHAR(50),
                    sentimiento_propio_score DOUBLE PRECISION,
                    emocion_propia VARCHAR(50),
                    nrc_emocion_top VARCHAR(50)
                );
            """))
            conn.commit()
        
        df_menc_sub.to_sql("_staging_menciones_nlp", engine, if_exists="append", index=False, method="multi", chunksize=1000)
        
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE menciones_docentes m
                SET 
                    topico_lda_id = t.topico_lda_id,
                    topico_lda_prob = t.topico_lda_prob,
                    sentimiento_propio = t.sentimiento_propio,
                    sentimiento_propio_score = t.sentimiento_propio_score,
                    emocion_propia = t.emocion_propia,
                    nrc_emocion_top = t.nrc_emocion_top
                FROM _staging_menciones_nlp t
                WHERE m.mensaje_id = t.mensaje_id;
            """))
            conn.execute(text("DROP TABLE IF EXISTS _staging_menciones_nlp;"))
            conn.commit()
        print(f"   ✅ {len(df_menc_sub)} menciones docentes actualizadas con telemetría NLP.")

    # 5. Actualización en Batch de mensajes
    print("\n📦 5. Actualizando atributos NLP en mensajes...")
    if os.path.exists(MASTER_CSV):
        df_master = pd.read_csv(MASTER_CSV, encoding="utf-8-sig", low_memory=False)
        cols_nlp = ["mensaje_id", "topico_lda_id", "topico_lda_prob", "sentimiento_propio", "sentimiento_propio_score", "emocion_propia", "nrc_emocion_top"]
        df_master_sub = df_master[cols_nlp].dropna(subset=["mensaje_id"]).drop_duplicates(subset=["mensaje_id"])
        
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS _staging_mensajes_nlp;"))
            conn.execute(text("""
                CREATE TABLE _staging_mensajes_nlp (
                    mensaje_id BIGINT PRIMARY KEY,
                    topico_lda_id INTEGER,
                    topico_lda_prob DOUBLE PRECISION,
                    sentimiento_propio VARCHAR(50),
                    sentimiento_propio_score DOUBLE PRECISION,
                    emocion_propia VARCHAR(50),
                    nrc_emocion_top VARCHAR(50)
                );
            """))
            conn.commit()
            
        df_master_sub.to_sql("_staging_mensajes_nlp", engine, if_exists="append", index=False, method="multi", chunksize=1000)
        
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE mensajes m
                SET 
                    topico_lda_id = t.topico_lda_id,
                    topico_lda_prob = t.topico_lda_prob,
                    sentimiento_propio = t.sentimiento_propio,
                    sentimiento_propio_score = t.sentimiento_propio_score,
                    emocion_propia = t.emocion_propia,
                    nrc_emocion_top = t.nrc_emocion_top
                FROM _staging_mensajes_nlp t
                WHERE m.mensaje_id = t.mensaje_id;
            """))
            conn.execute(text("DROP TABLE IF EXISTS _staging_mensajes_nlp;"))
            conn.commit()
        print(f"   ✅ {len(df_master_sub)} mensajes actualizados con telemetría NLP.")

    # 6. Verificación de Integridad
    print("\n🔍 6. Comprobación de estado final:")
    with engine.connect() as conn:
        r_topicos = conn.execute(text("SELECT COUNT(*) FROM lda_topicos")).scalar()
        r_tfidf = conn.execute(text("SELECT COUNT(*) FROM tfidf_entidades")).scalar()
        r_view = conn.execute(text("SELECT COUNT(*) FROM vista_perfil_emocional_docentes")).scalar()
        sample_doc = conn.execute(text("SELECT docente, score_sentimiento_promedio, menciones_positivas, menciones_negativas, emo_alivio, emo_frustracion FROM vista_perfil_emocional_docentes WHERE total_menciones > 10 ORDER BY total_menciones DESC LIMIT 3")).mappings().all()
        
        print(f"   -> Total en lda_topicos: {r_topicos}")
        print(f"   -> Total en tfidf_entidades: {r_tfidf}")
        print(f"   -> Filas en vista_perfil_emocional_docentes: {r_view}")
        print("   -> Muestra perfil emocional top docentes:")
        for d in sample_doc:
            print(f"      {d['docente']}: Score {d['score_sentimiento_promedio']} | +{d['menciones_positivas']} -{d['menciones_negativas']} | Alivio: {d['emo_alivio']} | Frustración: {d['emo_frustracion']}")

    print("\n" + "=" * 70)
    print("✅ MIGRACIÓN Y SIEMBRA NLP EN NEON SERVERLESS COMPLETADA CON ÉXITO")
    print("=" * 70)

if __name__ == "__main__":
    execute()
