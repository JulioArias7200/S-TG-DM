# -*- coding: utf-8 -*-
"""
database/execute_final_migration.py
-----------------------------------
Aplica las fases 1, 2, 3 y 4 del plan maestro de implementación:
1. Creación de tablas restantes: modismos_mensajes, gifs_animaciones, ocr_cache.
2. Inyección de datos desde CSV y JSON.
3. Creación de Vistas SQL Analíticas Dinámicas.
4. Creación del índice Full-Text Search (GIN) en español.
"""
import os
import sys
import json
import time
import pandas as pd

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from database.connection import engine
import sqlalchemy

def execute():
    print("=" * 70)
    print("🚀 EJECUTANDO PLAN MAESTRO DE IMPLEMENTACIÓN EN NEON POSTGRESQL")
    print("=" * 70)

    # -------------------------------------------------------------
    # FASE 1: DDL TABLAS RESTANTES
    # -------------------------------------------------------------
    print("\n🔨 1. Creando tablas restantes en Neon...")
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS modismos_mensajes (
            id SERIAL PRIMARY KEY,
            mensaje_id BIGINT,
            fecha TIMESTAMP WITHOUT TIME ZONE,
            usuario_nombre TEXT,
            modismo_nombre VARCHAR(100),
            termino_exacto VARCHAR(100),
            categoria VARCHAR(100),
            polaridad_asignada DOUBLE PRECISION,
            es_sarcasmo_potencial BOOLEAN DEFAULT FALSE,
            docente_mencionado TEXT,
            materia_mencionada TEXT,
            contexto_kwic TEXT,
            reacciones TEXT,
            texto_completo TEXT,
            CONSTRAINT fk_modismos_msg_mensaje FOREIGN KEY (mensaje_id) REFERENCES mensajes(mensaje_id) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS gifs_animaciones (
            id SERIAL PRIMARY KEY,
            mensaje_id BIGINT,
            fecha TIMESTAMP WITHOUT TIME ZONE,
            usuario_nombre TEXT,
            gif_nombre TEXT,
            archivo_adjunto TEXT,
            thumbnail_adjunto TEXT,
            texto_limpio TEXT,
            contenido_multimodal_unificado TEXT,
            CONSTRAINT fk_gifs_msg_mensaje FOREIGN KEY (mensaje_id) REFERENCES mensajes(mensaje_id) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS ocr_cache (
            clave_imagen TEXT PRIMARY KEY,
            texto_ocr TEXT,
            longitud_caracteres INTEGER,
            tiene_texto BOOLEAN DEFAULT FALSE,
            fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]

    with engine.connect() as conn:
        for stmt in ddl_statements:
            conn.execute(sqlalchemy.text(stmt))
        conn.commit()
    print("   ✅ Tablas modismos_mensajes, gifs_animaciones, ocr_cache creadas.")

    # -------------------------------------------------------------
    # FASE 2: SIEMBRA DE DATOS
    # -------------------------------------------------------------
    print("\n📦 2. Sembrando datos en las nuevas tablas...")

    # 2.1 modismos_mensajes
    csv_modismos = os.path.join(ROOT_DIR, "data", "processed", "dataset_modismos_mensajes.csv")
    if os.path.exists(csv_modismos):
        df_mod = pd.read_csv(csv_modismos, encoding="utf-8-sig", low_memory=False)
        df_mod["fecha"] = pd.to_datetime(df_mod["fecha"], errors="coerce")
        df_mod["es_sarcasmo_potencial"] = df_mod["es_sarcasmo_potencial"].astype(bool)
        df_mod = df_mod.where(pd.notnull(df_mod), None)
        with engine.connect() as conn:
            c = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM modismos_mensajes")).scalar()
            if c == 0:
                df_mod.to_sql("modismos_mensajes", con=engine, if_exists="append", index=False, chunksize=500, method="multi")
                print(f"   ✅ modismos_mensajes poblada con {len(df_mod):,} registros.")
            else:
                print(f"   ℹ️ modismos_mensajes ya contiene {c:,} registros.")

    # 2.2 gifs_animaciones
    csv_gifs = os.path.join(ROOT_DIR, "data", "processed", "catalogo_gifs_animaciones.csv")
    if os.path.exists(csv_gifs):
        df_gifs = pd.read_csv(csv_gifs, encoding="utf-8-sig", low_memory=False)
        df_gifs["fecha"] = pd.to_datetime(df_gifs["fecha"], errors="coerce")
        df_gifs = df_gifs.where(pd.notnull(df_gifs), None)
        with engine.connect() as conn:
            c = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM gifs_animaciones")).scalar()
            if c == 0:
                df_gifs.to_sql("gifs_animaciones", con=engine, if_exists="append", index=False, chunksize=100, method="multi")
                print(f"   ✅ gifs_animaciones poblada con {len(df_gifs):,} registros.")
            else:
                print(f"   ℹ️ gifs_animaciones ya contiene {c:,} registros.")

    # 2.3 ocr_cache
    json_ocr = os.path.join(ROOT_DIR, "data", "processed", "ocr_cache.json")
    if os.path.exists(json_ocr):
        with open(json_ocr, "r", encoding="utf-8") as f:
            ocr_dict = json.load(f)
        rows_ocr = []
        for h, txt in ocr_dict.items():
            txt_clean = txt.strip() if txt else ""
            rows_ocr.append({
                "clave_imagen": h,
                "texto_ocr": txt_clean if txt_clean else None,
                "longitud_caracteres": len(txt_clean),
                "tiene_texto": bool(txt_clean)
            })
        df_ocr = pd.DataFrame(rows_ocr)
        with engine.connect() as conn:
            c = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM ocr_cache")).scalar()
            if c == 0:
                df_ocr.to_sql("ocr_cache", con=engine, if_exists="append", index=False, chunksize=1000, method="multi")
                print(f"   ✅ ocr_cache poblada con {len(df_ocr):,} registros.")
            else:
                print(f"   ℹ️ ocr_cache ya contiene {c:,} registros.")

    # -------------------------------------------------------------
    # FASE 3: VISTAS ANALITICAS DINAMICAS
    # -------------------------------------------------------------
    print("\n📊 3. Creando Vistas Analíticas Dinámicas en SQL...")
    views = [
        """
        CREATE OR REPLACE VIEW vista_ranking_docentes AS
        SELECT 
            d.docente_id,
            d.nombre_completo AS docente,
            COUNT(DISTINCT md.mensaje_id) AS total_menciones,
            COALESCE(SUM(md.total_reacciones), 0) AS total_reacciones_recibidas,
            COUNT(CASE WHEN md.es_pregunta THEN 1 END) AS consultas_estudiantiles
        FROM docentes d
        JOIN menciones_docentes md ON md.docente_id = d.docente_id OR md.docente_mencionado ILIKE concat('%%', d.nombre_completo, '%%')
        GROUP BY d.docente_id, d.nombre_completo
        ORDER BY total_menciones DESC;
        """,
        """
        CREATE OR REPLACE VIEW vista_resumen_materias AS
        SELECT 
            mat.codigo_materia,
            mat.nombre_materia,
            COUNT(DISTINCT md.mensaje_id) AS total_menciones,
            COUNT(CASE WHEN md.es_pregunta THEN 1 END) AS consultas_estudiantiles
        FROM materias mat
        JOIN menciones_docentes md ON md.codigo_materia = mat.codigo_materia OR md.materia_mencionada ILIKE concat('%%', mat.codigo_materia, '%%')
        GROUP BY mat.codigo_materia, mat.nombre_materia
        ORDER BY total_menciones DESC;
        """,
        """
        CREATE OR REPLACE VIEW vista_tendencia_temporal_sentimiento AS
        SELECT 
            anio,
            mes,
            COUNT(*) AS total_mensajes,
            COUNT(CASE WHEN es_pregunta THEN 1 END) AS total_preguntas,
            COUNT(CASE WHEN tiene_imagen THEN 1 END) AS total_imagenes,
            COUNT(CASE WHEN es_sticker THEN 1 END) AS total_stickers,
            SUM(total_reacciones) AS total_reacciones
        FROM mensajes
        GROUP BY anio, mes
        ORDER BY anio, mes;
        """
    ]

    with engine.connect() as conn:
        for v in views:
            conn.execute(sqlalchemy.text(v))
        conn.commit()
    print("   ✅ Vistas creadas: vista_ranking_docentes, vista_resumen_materias, vista_tendencia_temporal_sentimiento.")

    # -------------------------------------------------------------
    # FASE 4: INDICE GIN FULL-TEXT SEARCH
    # -------------------------------------------------------------
    print("\n⚡ 4. Creando Índice Full-Text Search GIN en Español...")
    fts_sql = """
    CREATE INDEX IF NOT EXISTS idx_mensajes_fts_es 
    ON mensajes 
    USING gin(to_tsvector('spanish', coalesce(texto_limpio, '')));
    """
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text(fts_sql))
        conn.commit()
    print("   ✅ Índice GIN idx_mensajes_fts_es creado sobre mensajes(texto_limpio).")

    # -------------------------------------------------------------
    # AUDITORIA GENERAL
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 AUDITORÍA GENERAL DE TABLAS Y VISTAS EN NEON POSTGRESQL:")
    print("=" * 70)
    with engine.connect() as conn:
        inspector = sqlalchemy.inspect(engine)
        print("📁 TABLAS FÍSICAS:")
        for t in sorted(inspector.get_table_names()):
            c = conn.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"   • {t:<26} : {c:>7,} filas")

        print("\n📈 VISTAS DINÁMICAS:")
        for v in sorted(inspector.get_view_names()):
            c = conn.execute(sqlalchemy.text(f"SELECT COUNT(*) FROM {v}")).scalar()
            print(f"   • {v:<35} : {c:>7,} filas calculadas")

    print("=" * 70)
    print("🎉 IMPLEMENTACIÓN COMPLETADA AL 100% CON ÉXITO.")

if __name__ == "__main__":
    execute()
