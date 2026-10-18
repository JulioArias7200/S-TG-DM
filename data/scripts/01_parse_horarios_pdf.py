# -*- coding: utf-8 -*-
"""
01_parse_horarios_pdf.py
------------------------
Extractor y generador de la Base de Conocimiento de la Oferta Académica UMSA.
Lee el archivo 'horarios.pdf' y genera:
  1. resultados/data/catalogo_docentes_umsa.csv
  2. resultados/data/catalogo_materias_umsa.csv
  3. resultados/data/oferta_horarios_umsa.csv
"""

import os
import re
import csv
from collections import defaultdict
try:
    import pymupdf as fitz
except ImportError:
    import fitz

def extract_academic_data(pdf_path):
    doc = fitz.open(pdf_path)
    raw_lines = []
    for page in doc:
        text = page.get_text()
        for line in text.split("\n"):
            raw_lines.append(line.strip())

    headers_to_ignore = {
        "PARALELO", "DOCENTE", "HORARIO",
        "FACULTAD DE CIENCIAS PURAS Y NATURALES", "CARRERA DE INFORMATICA",
        "HORARIOS DE INSCRIPCION SEGUNDO 2026",
        "UNIVERSIDAD MAYOR DE SAN ANDRÉS", "UNIVERSIDAD MAYOR DE SAN ANDRS",
        "PENSUM 2023 AJUSTADO", "=== PAGE BREAK ==="
    }

    days_prefixes = ("LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO")

    def is_schedule(line):
        return any(line.startswith(d) for d in days_prefixes) or ("de " in line and " a " in line)

    def is_subject(line):
        return bool(re.match(r"^[A-Z]{3}-\d{3}\s*-", line))

    def is_paralelo(line):
        return len(line) == 1 and line.isupper() and line.isalpha()

    lines = []
    for l in raw_lines:
        if not l or l in headers_to_ignore:
            continue
        if re.match(r"^\d+\s*-\s*PLAN\s+2023\s+AJUSTADO$", l):
            continue
        lines.append(l)

    records = []
    current_sub_code = ""
    current_sub_name = ""
    current_paralelo = ""
    current_teacher = ""
    current_schedules = []

    def flush_record():
        nonlocal current_sub_code, current_sub_name, current_paralelo, current_teacher, current_schedules
        if current_sub_code and (current_teacher or current_paralelo):
            records.append({
                "codigo_materia": current_sub_code,
                "nombre_materia": current_sub_name,
                "paralelo": current_paralelo if current_paralelo else "A",
                "docente": current_teacher if current_teacher else "Sin Docente",
                "horarios": " // ".join(current_schedules)
            })
        current_teacher = ""
        current_schedules = []

    for line in lines:
        if is_subject(line):
            flush_record()
            m = re.match(r"^([A-Z]{3}-\d{3})\s*-\s*(.+)$", line)
            current_sub_code = m.group(1).strip()
            current_sub_name = m.group(2).strip()
            current_paralelo = ""
            current_teacher = ""
            current_schedules = []
        elif is_paralelo(line):
            flush_record()
            current_paralelo = line
        elif is_schedule(line):
            current_schedules.append(line)
        elif line == "Sin Docente":
            current_teacher = "Sin Docente"
        else:
            if line.isupper() and len(line) > 4 and not any(c.isdigit() for c in line):
                current_teacher = line
            else:
                if current_schedules:
                    current_schedules[-1] += " " + line
                else:
                    current_schedules.append(line)

    flush_record()
    return records

def build_teacher_regex(full_name):
    # Genera patrones flexibles para capturar menciones coloquiales en el chat
    parts = full_name.split()
    if len(parts) >= 2:
        # Apellido paterno y materno
        paterno = parts[-2]
        materno = parts[-1]
        primer_nombre = parts[0]
        # Ejemplos: "tarquino", "lic tarquino", "celia tarquino"
        # Ignorar apellidos extremadamente comunes solos para evitar falsos positivos
        patterns = [
            rf"\b(?:lic\.?|docente|ing\.?|profe|profesor|profesora)?\s*{re.escape(primer_nombre.lower())}\s+{re.escape(paterno.lower())}\b",
            rf"\b(?:lic\.?|docente|ing\.?|profe|profesor|profesora)\s+{re.escape(paterno.lower())}\b",
            rf"\b{re.escape(paterno.lower())}\s+{re.escape(materno.lower())}\b"
        ]
        if len(paterno) >= 5 and paterno not in ("FLORES", "QUISPE", "MAMANI", "ROJAS", "PEREZ", "LOPEZ"):
            patterns.append(rf"\b{re.escape(paterno.lower())}\b")
        if len(materno) >= 5 and materno not in ("FLORES", "QUISPE", "MAMANI", "ROJAS", "PEREZ", "LOPEZ"):
            patterns.append(rf"\b{re.escape(materno.lower())}\b")
        return "|".join(dict.fromkeys(patterns))
    return rf"\b{re.escape(full_name.lower())}\b"

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.dirname(script_dir)
    raw_dir = os.path.join(data_dir, "raw")
    processed_dir = os.path.join(data_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    pdf_path = os.path.join(raw_dir, "horarios.pdf")
    if not os.path.exists(pdf_path):
        # Fallback a raíz de data
        pdf_path = os.path.join(data_dir, "horarios.pdf")

    print(f"Leyendo archivo oficial de horarios: {pdf_path}")
    records = extract_academic_data(pdf_path)
    print(f"Total de registros de oferta extraídos: {len(records)}")

    # 1. Guardar oferta_horarios_umsa.csv
    oferta_csv = os.path.join(processed_dir, "oferta_horarios_umsa.csv")
    with open(oferta_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["codigo_materia", "nombre_materia", "paralelo", "docente", "horarios"])
        writer.writeheader()
        writer.writerows(records)
    print(f"Guardado: {oferta_csv}")

    # 2. Construir catálogo de docentes
    teacher_subjects = defaultdict(set)
    for r in records:
        if r["docente"] != "Sin Docente":
            teacher_subjects[r["docente"]].add(f"{r['codigo_materia']} - {r['nombre_materia']}")

    docentes_csv = os.path.join(processed_dir, "catalogo_docentes_umsa.csv")
    with open(docentes_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["docente_id", "nombre_completo", "materias_que_dicta", "alias_regex"])
        for idx, (docente, materias) in enumerate(sorted(teacher_subjects.items()), start=1):
            alias_pattern = build_teacher_regex(docente)
            writer.writerow([
                f"DOC_{idx:03d}",
                docente,
                " ; ".join(sorted(materias)),
                alias_pattern
            ])
    print(f"Guardado catálogo de docentes ({len(teacher_subjects)} docentes): {docentes_csv}")

    # 3. Construir catálogo de materias
    materia_data = defaultdict(lambda: {"nombre": "", "paralelos": set(), "docentes": set()})
    for r in records:
        materia_data[r["codigo_materia"]]["nombre"] = r["nombre_materia"]
        materia_data[r["codigo_materia"]]["paralelos"].add(r["paralelo"])
        if r["docente"] != "Sin Docente":
            materia_data[r["codigo_materia"]]["docentes"].add(r["docente"])

    materias_csv = os.path.join(processed_dir, "catalogo_materias_umsa.csv")
    with open(materias_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["codigo_materia", "nombre_materia", "paralelos_disponibles", "docentes_asignados", "alias_regex"])
        for codigo, data in sorted(materia_data.items()):
            # Generar alias para materias (sigla sin guión, con espacio, etc.)
            clean_code = codigo.replace("-", "").lower()
            regex_mat = rf"\b{re.escape(codigo.lower())}\b|\b{re.escape(clean_code)}\b|\b{re.escape(codigo.replace('-', ' ').lower())}\b"
            writer.writerow([
                codigo,
                data["nombre"],
                ", ".join(sorted(data["paralelos"])),
                " ; ".join(sorted(data["docentes"])) if data["docentes"] else "Sin Docente Asignado",
                regex_mat
            ])
    print(f"Guardado catálogo de materias ({len(materia_data)} materias): {materias_csv}")

if __name__ == "__main__":
    main()
