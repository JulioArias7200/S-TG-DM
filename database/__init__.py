# -*- coding: utf-8 -*-
"""
Paquete database: Gestión centralizada de base de datos para Neon PostgreSQL.
"""
from database.connection import engine, SessionLocal, Base, get_db, check_connection
from database.queries import get_kpi_summary, get_docentes_ranking, get_sentiment_distribution

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "check_connection",
    "get_kpi_summary",
    "get_docentes_ranking",
    "get_sentiment_distribution"
]
