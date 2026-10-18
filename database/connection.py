# -*- coding: utf-8 -*-
"""
database/connection.py
----------------------
Gestión centralizada del motor y sesiones de base de datos para Neon Serverless PostgreSQL.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_database_url():
    url = os.getenv("DATABASE_URL", "sqlite:///sentix_local.db")
    # Normalizar para psycopg2 (driver compatible con Neon y Render)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

DATABASE_URL = get_database_url()

# Motor optimizado para PostgreSQL Serverless (Neon)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

def get_db():
    """Generador de sesiones de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_connection():
    """Comprueba la conectividad con Neon y retorna la versión de PostgreSQL."""
    with engine.connect() as conn:
        from sqlalchemy import text
        res = conn.execute(text("SELECT version();")).scalar()
        return res
