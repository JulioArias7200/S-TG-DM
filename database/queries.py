# -*- coding: utf-8 -*-
"""
database/queries.py
-------------------
Consultas analíticas SQL de alto rendimiento para el Dashboard y Telemetría.
"""
from sqlalchemy import text
from database.connection import engine

def get_kpi_summary():
    """Retorna las métricas clave para las tarjetas ejecutivas del Dashboard."""
    query = text("""
        SELECT 
            (SELECT COUNT(*) FROM mensajes) AS total_mensajes,
            (SELECT COUNT(DISTINCT usuario_id) FROM mensajes) AS usuarios_unicos,
            (SELECT COUNT(*) FROM menciones_docentes) AS total_menciones,
            (SELECT COUNT(*) FROM reacciones_granular) AS total_reacciones,
            (SELECT COUNT(*) FROM catalogo_modismos) AS total_modismos
    """)
    with engine.connect() as conn:
        row = conn.execute(query).fetchone()
        return {
            "total_mensajes": row[0],
            "usuarios_unicos": row[1],
            "total_menciones": row[2],
            "total_reacciones": row[3],
            "total_modismos": row[4]
        }

def get_docentes_ranking(limit=10):
    """Retorna el ranking de docentes con más menciones y consultas."""
    query = text("""
        SELECT 
            docente_mencionado AS docente,
            COUNT(*) AS total_menciones,
            SUM(total_reacciones) AS reacciones,
            COUNT(CASE WHEN es_pregunta THEN 1 END) AS consultas
        FROM menciones_docentes
        WHERE docente_mencionado IS NOT NULL AND docente_mencionado != 'Ninguno'
        GROUP BY docente_mencionado
        ORDER BY total_menciones DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"limit": limit}).fetchall()
        return [
            {
                "docente": r[0],
                "menciones": r[1],
                "reacciones": r[2] or 0,
                "consultas": r[3]
            }
            for r in rows
        ]

def get_sentiment_distribution():
    """Calcula la distribución de sentimiento a partir de las emociones de stickers y modismos."""
    query = text("""
        SELECT 
            COALESCE(sticker_emocion, 'sin_sticker') AS emocion,
            COUNT(*) AS total
        FROM mensajes
        GROUP BY sticker_emocion
        ORDER BY total DESC
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()
        return {r[0]: r[1] for r in rows}
