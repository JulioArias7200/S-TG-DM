# -*- coding: utf-8 -*-
"""
database/queries.py
-------------------
Consultas analíticas SQL de alto rendimiento para el Dashboard y Telemetría.
"""
from sqlalchemy import text
from database.connection import engine

def get_dashboard_kpis():
    """Retorna las métricas clave del corpus de mensajes y entidades académicas."""
    query = text("""
        SELECT 
            (SELECT COUNT(*) FROM mensajes) AS total_mensajes,
            (SELECT COUNT(DISTINCT usuario_id) FROM mensajes) AS usuarios_unicos,
            (SELECT COUNT(*) FROM docentes) AS total_docentes,
            (SELECT COUNT(*) FROM materias) AS total_materias,
            (SELECT COUNT(*) FROM menciones_docentes) AS total_menciones,
            (SELECT COUNT(*) FROM ocr_cache) AS total_ocr,
            (SELECT COUNT(*) FROM gifs_animaciones) AS total_gifs,
            (SELECT COUNT(*) FROM reacciones_granular) AS total_reacciones,
            (SELECT COUNT(*) FROM modismos_mensajes) AS total_modismos,
            (SELECT COUNT(*) FROM oferta_horarios) AS total_paralelos
    """)
    with engine.connect() as conn:
        r = conn.execute(query).mappings().one()
        total_msgs = r["total_mensajes"] or 0
        usuarios = r["usuarios_unicos"] or 1
        total_multimodal = (r["total_ocr"] or 0) + (r["total_gifs"] or 0) + (r["total_reacciones"] or 0) + (r["total_modismos"] or 0)
        return {
            "total_mensajes": total_msgs,
            "usuarios_unicos": usuarios,
            "promedio_msgs_usuario": round(total_msgs / usuarios, 1),
            "total_docentes": r["total_docentes"],
            "total_materias": r["total_materias"],
            "total_menciones": r["total_menciones"],
            "total_paralelos": r["total_paralelos"],
            "total_multimodal": total_multimodal,
            "total_ocr": r["total_ocr"],
            "total_gifs": r["total_gifs"],
            "total_reacciones": r["total_reacciones"],
            "total_modismos": r["total_modismos"]
        }

def get_kpi_summary():
    """Compatibilidad hacia atrás con endpoints existentes."""
    return get_dashboard_kpis()

def get_top_docentes_ranking(limit=7):
    """Retorna el ranking de docentes con más menciones, calculado con porcentajes de barra relativa."""
    query = text("""
        SELECT 
            docente_id,
            docente,
            total_menciones,
            total_reacciones_recibidas,
            consultas_estudiantiles
        FROM vista_ranking_docentes
        ORDER BY total_menciones DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = [dict(r) for r in conn.execute(query, {"limit": limit}).mappings().all()]
        if not rows:
            return []
        max_menciones = max(r["total_menciones"] for r in rows) or 1
        for r in rows:
            r["width_pct"] = round((r["total_menciones"] / max_menciones) * 100, 1)
        return rows

def get_docentes_directory(limit=50):
    """Directorio completo para la tabla ejecutiva del Dashboard."""
    query = text("""
        SELECT 
            d.docente_id,
            d.nombre_completo AS docente,
            COALESCE(d.materias_que_dicta, 'Informática') AS departamento,
            COALESCE(v.total_menciones, 0) AS total_menciones,
            COALESCE(v.total_reacciones_recibidas, 0) AS total_reacciones,
            COALESCE(v.consultas_estudiantiles, 0) AS consultas
        FROM docentes d
        LEFT JOIN vista_ranking_docentes v ON d.docente_id = v.docente_id
        ORDER BY total_menciones DESC, docente ASC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(query, {"limit": limit}).mappings().all()]

def get_top_reacciones_telegram(limit=8):
    """Retorna los emojis más utilizados en las reacciones con alturas porcentuales relativas."""
    query = text("""
        SELECT 
            emoji,
            SUM(conteo) AS total
        FROM reacciones_granular
        WHERE emoji IS NOT NULL AND emoji != ''
        GROUP BY emoji
        ORDER BY total DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = [dict(r) for r in conn.execute(query, {"limit": limit}).mappings().all()]
        if not rows:
            return []
        max_total = max(r["total"] for r in rows) or 1
        for r in rows:
            r["height_pct"] = max(18, round((r["total"] / max_total) * 100, 1))
        return rows

def get_modalidad_chat_distribution():
    """Calcula la tipología modal del chat (Texto puro, OCR, Preguntas, Stickers) y coordenadas para SVG Donut."""
    query = text("""
        SELECT 
            COUNT(*) AS total,
            COUNT(CASE WHEN tiene_imagen OR imagen_texto_ocr IS NOT NULL THEN 1 END) AS ocr_imagenes,
            COUNT(CASE WHEN es_pregunta THEN 1 END) AS preguntas,
            COUNT(CASE WHEN es_sticker THEN 1 END) AS stickers
        FROM mensajes
    """)
    with engine.connect() as conn:
        r = conn.execute(query).mappings().one()
        total = r["total"] or 1
        ocr = r["ocr_imagenes"] or 0
        preguntas = r["preguntas"] or 0
        stickers = r["stickers"] or 0
        texto_puro = max(0, total - (ocr + preguntas + stickers))

        pct_texto = round((texto_puro / total) * 100, 1)
        pct_ocr = round((ocr / total) * 100, 1)
        pct_preguntas = round((preguntas / total) * 100, 1)
        pct_stickers = round((stickers / total) * 100, 1)

        # Circunferencia del donut SVG (r=100 -> C = 2 * PI * 100 ≈ 628.32)
        c = 628.32
        len_texto = round(c * (pct_texto / 100), 2)
        len_preguntas = round(c * (pct_preguntas / 100), 2)
        len_ocr = round(c * (pct_ocr / 100), 2)
        len_stickers = round(c * (pct_stickers / 100), 2)

        off_preguntas = round(-len_texto, 2)
        off_ocr = round(-(len_texto + len_preguntas), 2)
        off_stickers = round(-(len_texto + len_preguntas + len_ocr), 2)

        return {
            "total": total,
            "texto_puro": texto_puro,
            "ocr": ocr,
            "preguntas": preguntas,
            "stickers": stickers,
            "pct_texto": pct_texto,
            "pct_ocr": pct_ocr,
            "pct_preguntas": pct_preguntas,
            "pct_stickers": pct_stickers,
            "circumference": c,
            "len_texto": len_texto,
            "len_preguntas": len_preguntas,
            "len_ocr": len_ocr,
            "len_stickers": len_stickers,
            "off_preguntas": off_preguntas,
            "off_ocr": off_ocr,
            "off_stickers": off_stickers
        }

def get_tendencia_temporal_resumen():
    """Retorna la serie cronológica mensual histórica para la visualización de actividad."""
    query = text("""
        SELECT 
            anio,
            mes,
            total_mensajes,
            total_preguntas,
            total_imagenes,
            total_reacciones
        FROM vista_tendencia_temporal_sentimiento
        WHERE anio >= 2021
        ORDER BY anio ASC, mes ASC
    """)
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(query).mappings().all()]

def get_neon_health_telemetry():
    """Telemetría del servidor de base de datos Neon Serverless."""
    query = text("""
        SELECT 
            version() AS db_version,
            current_database() AS db_name,
            inet_server_port() AS db_port,
            pg_size_pretty(pg_database_size(current_database())) AS db_size
    """)
    with engine.connect() as conn:
        r = conn.execute(query).mappings().one()
        return {
            "status": "Online (Pooler Active)",
            "engine": "Neon Serverless PostgreSQL",
            "version": r["db_version"].split(" on ")[0] if r["db_version"] else "PostgreSQL 18.6",
            "database": r["db_name"],
            "region": "sa-east-1 (AWS São Paulo)",
            "size": r["db_size"],
            "tables_count": 14,
            "views_count": 4
        }

def get_tfidf_keywords(entidad_tipo="DOCENTE", entidad_id=None, limit=15):
    """Retorna los términos más distintivos calculados con TF-IDF por Docente, Materia o Ciclo."""
    if entidad_id:
        query = text("""
            SELECT entidad_tipo, entidad_id, termino, score_tfidf, ranking_pos
            FROM tfidf_entidades
            WHERE entidad_tipo = :tipo AND (LOWER(entidad_id) = LOWER(:id) OR entidad_id ILIKE :like_id)
            ORDER BY ranking_pos ASC
            LIMIT :limit
        """)
        params = {"tipo": entidad_tipo, "id": entidad_id, "like_id": f"%{entidad_id}%", "limit": limit}
    else:
        query = text("""
            SELECT entidad_tipo, entidad_id, termino, score_tfidf, ranking_pos
            FROM tfidf_entidades
            WHERE entidad_tipo = :tipo
            ORDER BY score_tfidf DESC
            LIMIT :limit
        """)
        params = {"tipo": entidad_tipo, "limit": limit}

    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(query, params).mappings().all()]

def get_lda_topics_summary():
    """Retorna los tópicos descubiertos por Latent Dirichlet Allocation (LDA) con su vocabulario Beta y conteo Gamma."""
    query_topics = text("""
        SELECT 
            t.topico_id,
            t.nombre_etiqueta,
            COUNT(DISTINCT m.mensaje_id) AS total_mensajes_asignados,
            ROUND((COUNT(DISTINCT m.mensaje_id)::numeric / NULLIF((SELECT COUNT(*) FROM mensajes), 0)) * 100, 1) AS porcentaje_corpus
        FROM lda_topicos t
        LEFT JOIN mensajes m ON t.topico_id = m.topico_lda_id
        GROUP BY t.topico_id, t.nombre_etiqueta
        ORDER BY t.topico_id ASC
    """)
    query_vocab = text("""
        SELECT topico_id, termino, beta_prob, ranking_pos
        FROM lda_topicos
        WHERE ranking_pos <= 10
        ORDER BY topico_id ASC, ranking_pos ASC
    """)
    with engine.connect() as conn:
        topics = [dict(r) for r in conn.execute(query_topics).mappings().all()]
        vocab = [dict(r) for r in conn.execute(query_vocab).mappings().all()]
        
        # Agrupar vocabulario por tópico
        for t in topics:
            t_id = t["topico_id"]
            t["vocabulario_top"] = [v for v in vocab if v["topico_id"] == t_id]
        return topics

def get_perfil_emocional_docentes(limit=50):
    """Retorna el desglose de emociones UMSA y polaridad por docente desde la vista SQL analítica."""
    query = text("""
        SELECT 
            docente_id,
            docente,
            departamento,
            total_menciones,
            score_sentimiento_promedio,
            menciones_positivas,
            menciones_negativas,
            menciones_neutrales,
            emo_alivio,
            emo_frustracion,
            emo_incertidumbre,
            emo_conformidad,
            emo_descontento
        FROM vista_perfil_emocional_docentes
        ORDER BY total_menciones DESC, docente ASC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(query, {"limit": limit}).mappings().all()]

def get_perfil_emocional_docente(docente_id):
    """Retorna el perfil emocional específico de un docente o por nombre."""
    query = text("""
        SELECT *
        FROM vista_perfil_emocional_docentes
        WHERE docente_id = :id OR docente ILIKE :like_nom
        LIMIT 1
    """)
    with engine.connect() as conn:
        row = conn.execute(query, {"id": docente_id, "like_nom": f"%{docente_id}%"}).mappings().first()
        return dict(row) if row else None

def get_nlp_kpis_summary():
    """Consolida métricas ejecutivas de NLP (Tópicos, Emociones Propias y NRC)."""
    query = text("""
        SELECT 
            (SELECT COUNT(*) FROM lda_topicos) AS total_terminos_lda,
            (SELECT COUNT(*) FROM tfidf_entidades) AS total_descriptores_tfidf,
            (SELECT COUNT(*) FROM mensajes WHERE sentimiento_propio = 'positivo') AS total_positivos,
            (SELECT COUNT(*) FROM mensajes WHERE sentimiento_propio = 'negativo') AS total_negativos,
            (SELECT COUNT(*) FROM mensajes WHERE sentimiento_propio = 'neutral') AS total_neutrales,
            (SELECT COUNT(*) FROM mensajes WHERE emocion_propia = 'incertidumbre_ansiedad') AS emo_ansiedad,
            (SELECT COUNT(*) FROM mensajes WHERE emocion_propia = 'conformidad_recomendacion') AS emo_conformidad,
            (SELECT COUNT(*) FROM mensajes WHERE emocion_propia = 'alivio_aprobacion') AS emo_alivio,
            (SELECT COUNT(*) FROM mensajes WHERE emocion_propia = 'frustracion_dificultad') AS emo_frustracion,
            (SELECT COUNT(*) FROM mensajes WHERE emocion_propia = 'descontento_critica') AS emo_descontento,
            (SELECT COUNT(*) FROM mensajes WHERE nrc_emocion_top = 'trust') AS nrc_trust,
            (SELECT COUNT(*) FROM mensajes WHERE nrc_emocion_top = 'fear') AS nrc_fear,
            (SELECT COUNT(*) FROM mensajes WHERE nrc_emocion_top = 'anticipation') AS nrc_anticipation
    """)
    with engine.connect() as conn:
        r = conn.execute(query).mappings().one()
        return dict(r)

