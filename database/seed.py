# -*- coding: utf-8 -*-
"""
database/seed.py
----------------
Script maestro de siembra y sincronización de datos desde data/processed/ hacia Neon PostgreSQL.
"""
import os
import sys
import time
import pandas as pd
from datetime import datetime
from sqlalchemy import text, inspect

# Añadir la raíz al path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from database.connection import engine
from app import create_app
from app.extensions import db

PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")

def run_seed():
    print("=" * 70)
    print("🚀 INICIANDO MIGRACIÓN Y SIEMBRA MASTER DESDE database/seed.py")
    print(f"⏰ Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    app = create_app()
    with app.app_context():
        # 1. Asegurar que todas las tablas existan
        print("\n🔨 1. Verificando esquema en Neon...")
        db.create_all()
        inspector = inspect(engine)
        print(f"   ✅ Tablas detectadas: {inspector.get_table_names()}")

        def cargar(nombre_tabla, csv_filename, parse_dates=None, bool_cols=None, cols_filter=None):
            ruta_csv = os.path.join(PROCESSED_DIR, csv_filename)
            if not os.path.exists(ruta_csv):
                print(f"   ⚠️ No encontrado: {csv_filename}")
                return

            with engine.connect() as conn:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {nombre_tabla}")).scalar()
            
            if count > 0:
                print(f"   ℹ️  Tabla '{nombre_tabla}' ya contiene {count:,} registros. Omitiendo.")
                return

            print(f"   📥 Leyendo {csv_filename}...")
            df = pd.read_csv(ruta_csv, encoding="utf-8-sig", low_memory=False)

            if parse_dates:
                for col in parse_dates:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors="coerce")

            if bool_cols:
                for col in bool_cols:
                    if col in df.columns:
                        df[col] = df[col].astype(bool)

            # Filtrar columnas si la tabla requiere un subconjunto
            if cols_filter:
                db_cols = [c["name"] for c in inspector.get_columns(nombre_tabla) if c["name"] != "id"]
                valid_cols = [c for c in db_cols if c in df.columns]
                df = df[valid_cols]

            df = df.where(pd.notnull(df), None)

            t0 = time.time()
            total = len(df)
            print(f"   ⚡ Insertando {total:,} registros en '{nombre_tabla}'...")
            df.to_sql(nombre_tabla, con=engine, if_exists="append", index=False, chunksize=1000, method="multi")
            print(f"   ✅ '{nombre_tabla}' completada en {time.time() - t0:.2f}s.")

        # Cargar catálogos
        cargar("docentes", "catalogo_docentes_umsa.csv")
        cargar("materias", "catalogo_materias_umsa.csv")
        cargar("oferta_horarios", "oferta_horarios_umsa.csv")
        cargar("catalogo_modismos", "catalogo_modismos_umsa.csv")
        cargar("diccionario_jergas", "diccionario_jergas_y_modismos_umsa.csv")
        cargar("eventos_servicio", "eventos_servicio_log.csv", parse_dates=["fecha"])
        cargar("reacciones_granular", "dataset_reacciones_granular.csv", parse_dates=["fecha_mensaje"])

        # Cargar Menciones a Docentes (con filtro dinámico de columnas de la tabla)
        cargar(
            "menciones_docentes",
            "dataset_menciones_docentes.csv",
            parse_dates=["fecha"],
            bool_cols=["es_pregunta"],
            cols_filter=True
        )

        # Cargar Dataset Maestro (23,462 registros)
        bool_cols_master = [
            "es_respuesta", "padre_existe", "es_pregunta", "tiene_url",
            "tiene_imagen", "es_sticker", "es_gif", "entidad_heredada_hilo"
        ]
        cargar(
            "mensajes",
            "dataset_telegram_master.csv",
            parse_dates=["fecha"],
            bool_cols=bool_cols_master
        )

        # Resumen general
        print("\n" + "=" * 70)
        print("📊 AUDITORÍA GENERAL DE NEON POSTGRESQL:")
        print("=" * 70)
        with engine.connect() as conn:
            for t in inspector.get_table_names():
                c = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                print(f"  • {t:<25} : {c:>7,} registros")
        print("=" * 70)
        print("🎉 PROCESO FINALIZADO CON ÉXITO.")

if __name__ == "__main__":
    run_seed()
