# -*- coding: utf-8 -*-
"""
03_entity_linking_docentes.py
-----------------------------
Modulo analitico para la agregacion y perfilado de entidades docentes y materias.
Genera reportes ejecutivos en 'resultados/data/':
  1. ranking_docentes_menciones.csv
  2. resumen_materias_menciones.csv
"""

import os
import csv
import pandas as pd

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_root = os.path.dirname(script_dir)
    processed_dir = os.path.join(data_root, "processed")
    data_dir = processed_dir if os.path.exists(processed_dir) else data_root
    menciones_csv = os.path.join(data_dir, "dataset_menciones_docentes.csv")

    if not os.path.exists(menciones_csv):
        print(f"Error: no se encontro {menciones_csv}")
        return

    print("Cargando dataset de menciones docentes...")
    df = pd.read_csv(menciones_csv)

    # 1. Ranking de Docentes
    doc_records = []
    df_doc = df[df["docente_mencionado"] != "Ninguno"]

    teacher_counts = {}
    teacher_reactions = {}
    teacher_questions = {}

    for _, row in df_doc.iterrows():
        docs = [d.strip() for d in str(row["docente_mencionado"]).split(";")]
        reacs = int(row.get("total_reacciones", 0)) if pd.notnull(row.get("total_reacciones")) else 0
        es_preg = bool(row.get("es_pregunta", False))
        for d in docs:
            teacher_counts[d] = teacher_counts.get(d, 0) + 1
            teacher_reactions[d] = teacher_reactions.get(d, 0) + reacs
            if es_preg:
                teacher_questions[d] = teacher_questions.get(d, 0) + 1

    for doc, cnt in sorted(teacher_counts.items(), key=lambda x: x[1], reverse=True):
        doc_records.append({
            "docente": doc,
            "total_menciones": cnt,
            "total_reacciones_recibidas": teacher_reactions.get(doc, 0),
            "consultas_estudiantiles": teacher_questions.get(doc, 0)
        })

    df_ranking_doc = pd.DataFrame(doc_records)
    ranking_doc_csv = os.path.join(data_dir, "ranking_docentes_menciones.csv")
    df_ranking_doc.to_csv(ranking_doc_csv, index=False, encoding="utf-8-sig")
    print(f"Guardado ranking de docentes: {ranking_doc_csv}")

    # 2. Ranking de Materias
    mat_records = []
    df_mat = df[df["materia_mencionada"] != "Ninguna"]
    mat_counts = {}
    mat_questions = {}

    for _, row in df_mat.iterrows():
        mats = [m.strip() for m in str(row["materia_mencionada"]).split(";")]
        es_preg = bool(row.get("es_pregunta", False))
        for m in mats:
            mat_counts[m] = mat_counts.get(m, 0) + 1
            if es_preg:
                mat_questions[m] = mat_questions.get(m, 0) + 1

    for m, cnt in sorted(mat_counts.items(), key=lambda x: x[1], reverse=True):
        mat_records.append({
            "materia": m,
            "total_menciones": cnt,
            "consultas_estudiantiles": mat_questions.get(m, 0)
        })

    df_ranking_mat = pd.DataFrame(mat_records)
    ranking_mat_csv = os.path.join(data_dir, "resumen_materias_menciones.csv")
    df_ranking_mat.to_csv(ranking_mat_csv, index=False, encoding="utf-8-sig")
    print(f"Guardado resumen de materias: {ranking_mat_csv}")

if __name__ == "__main__":
    main()
