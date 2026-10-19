# -*- coding: utf-8 -*-
"""
Paquete database: Gestión centralizada de base de datos para Neon PostgreSQL.
"""
from database.connection import engine, SessionLocal, Base, get_db, check_connection
from database.queries import (
    get_dashboard_kpis,
    get_kpi_summary,
    get_top_docentes_ranking,
    get_docentes_directory,
    get_top_reacciones_telegram,
    get_modalidad_chat_distribution,
    get_tendencia_temporal_resumen,
    get_neon_health_telemetry,
    get_tfidf_keywords,
    get_lda_topics_summary,
    get_perfil_emocional_docentes,
    get_perfil_emocional_docente,
    get_nlp_kpis_summary
)

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "check_connection",
    "get_dashboard_kpis",
    "get_kpi_summary",
    "get_top_docentes_ranking",
    "get_docentes_directory",
    "get_top_reacciones_telegram",
    "get_modalidad_chat_distribution",
    "get_tendencia_temporal_resumen",
    "get_neon_health_telemetry",
    "get_tfidf_keywords",
    "get_lda_topics_summary",
    "get_perfil_emocional_docentes",
    "get_perfil_emocional_docente",
    "get_nlp_kpis_summary"
]
