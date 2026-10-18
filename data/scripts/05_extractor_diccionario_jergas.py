# -*- coding: utf-8 -*-
"""
05_extractor_diccionario_jergas.py
----------------------------------
Modulo de Data Mining y Lexicografia Computacional.
Extrae todas las jergas, modismos, abreviaciones y vocabulario no estandar
del dataset de Telegram (UMSA), asignando su significado real en contexto,
categoria ontologica, polaridad y ejemplos de uso.

Genera:
  resultados/data/diccionario_jergas_y_modismos_umsa.csv
"""

import os
import sys
import re
import csv
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Base de Conocimiento Lexicografica: Jergas, Modismos y Terminos Locales UMSA
BASE_JERGAS_SIGNIFICADOS = {
    # --- JERGA DE EVALUACION Y CARACTERIZACION DOCENTE ---
    "barco": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Docente extremadamente facil o permisivo que exige poco y regala notas o aprueba a casi todos.",
        "polaridad": 0.8,
        "regex": r"\b(barco[s]*)\b"
    },
    "fregado": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Docente estricto, severo o dificil de aprobar; materia con alta exigencia o complejidad.",
        "polaridad": -1.5,
        "regex": r"\b(fregad[oa]s*|frieg[aoe]n*)\b"
    },
    "capo": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Docente o estudiante con un dominio excepcional y brillante en su area o materia.",
        "polaridad": 2.0,
        "regex": r"\b(cap[oa]s*|cap[ií]sim[oa]s*)\b"
    },
    "crack": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Persona sumamente talentosa, agil y destacada en programacion o resolucion de problemas.",
        "polaridad": 2.0,
        "regex": r"\b(crack[s]*)\b"
    },
    "te aplaza": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Docente inflexible que reprueba sin dudar al estudiante que no cumple con el puntaje minimo.",
        "polaridad": -2.0,
        "regex": r"\b(aplaz[aoe]r*|aplazad[oa]s*|te\s+aplaza)\b"
    },
    "suave": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Docente tranquilo, tolerante y comprensivo; clase sin tensiones ni excesiva presion.",
        "polaridad": 1.0,
        "regex": r"\b(suave[s]*|suave\s+nom[aá]s)\b"
    },
    "buena onda": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Docente o companero amigable, simpatico, respetuoso y de trato accesible.",
        "polaridad": 1.5,
        "regex": r"\b(buena\s+onda)\b"
    },
    "falton": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Docente que se ausenta constantemente de clases o no asiste sin previo aviso.",
        "polaridad": -2.0,
        "regex": r"\b(falt[oó]n[a]*s*|no\s+asiste|no\s+viene|falta\s+mucho)\b"
    },
    "no sube notas": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Docente que retrasa indefinidamente la entrega y publicacion de actas de calificaciones en kardex.",
        "polaridad": -2.0,
        "regex": r"\b(no\s+sube\s+notas|tarda\s+en\s+subir|no\s+publica\s+notas)\b"
    },
    "prepotente": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Docente o autoridad con actitud arrogante, autoritaria y despectiva hacia los estudiantes.",
        "polaridad": -2.0,
        "regex": r"\b(prepotente[s]*|soberbi[oa]s*|reneg[oó]n[a]*s*)\b"
    },
    "llevadera": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Materia o clase que se cursa sin angustia, fluida y con dificultad moderada.",
        "polaridad": 1.2,
        "regex": r"\b(llevader[oa]s*)\b"
    },
    "pesado": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Materia con excesiva carga horaria, tareas saturadas o dificultad mental desgastante.",
        "polaridad": -1.2,
        "regex": r"\b(pesad[oa]s*)\b"
    },
    "matador": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Examen o docente de extrema rigurosidad que causa reprobacion masiva.",
        "polaridad": -2.0,
        "regex": r"\b(matador[a]*s*|masacre|colador)\b"
    },
    "filtro": {
        "categoria": "EVALUACION_DOCENTE",
        "significado": "Materia troncal disenada institucionalmente para depurar y seleccionar a los alumnos aptos.",
        "polaridad": -1.5,
        "regex": r"\b(filtro[s]*)\b"
    },

    # --- JERGA DE APROBACION Y RENDIMIENTO ESTUDIANTIL ---
    "facilito": {
        "categoria": "RENDIMIENTO_ESTUDIANTIL",
        "significado": "Contenido, examen o materia que requiere minimo esfuerzo para aprobar.",
        "polaridad": 1.5,
        "regex": r"\b(facilito[os]*|facil[es]*)\b"
    },
    "tirarse": {
        "categoria": "RENDIMIENTO_ESTUDIANTIL",
        "significado": "Modismo boliviano que significa reprobar o perder una materia academica.",
        "polaridad": -1.8,
        "regex": r"\b(tirar[s]*e*|tiraron|tirar[aá]n*)\b"
    },
    "pan comido / pichi": {
        "categoria": "RENDIMIENTO_ESTUDIANTIL",
        "significado": "Tarea o examen extremadamente sencillo; asunto resuelto sin ninguna complicacion.",
        "polaridad": 1.5,
        "regex": r"\b(pan\s+comido|pichi|mantequilla)\b"
    },
    "salvar": {
        "categoria": "RENDIMIENTO_ESTUDIANTIL",
        "significado": "Lograr la nota minima de aprobacion (51 puntos) in extremis en la etapa final del semestre.",
        "polaridad": 1.0,
        "regex": r"\b(salvar|salvarse|salvamos|salvo)\b"
    },
    "raspar": {
        "categoria": "RENDIMIENTO_ESTUDIANTIL",
        "significado": "Aprobar una materia con la calificacion justa e indispensable en el limite (51 sobre 100).",
        "polaridad": 0.5,
        "regex": r"\b(raspar|raspando|raspado)\b"
    },
    "chiste": {
        "categoria": "RENDIMIENTO_ESTUDIANTIL",
        "significado": "Algo tan sencillo o tan mal organizado que resulta ridiculo o ironico.",
        "polaridad": -0.5,
        "regex": r"\b(chiste[s]*|es\s+un\s+chiste)\b"
    },
    "es un lio": {
        "categoria": "RENDIMIENTO_ESTUDIANTIL",
        "significado": "Situacion confusa, caotica y desorganizada con choque de horarios o tramites.",
        "polaridad": -1.2,
        "regex": r"\b(es\s+un\s+l[ií]o|todo\s+un\s+l[ií]o)\b"
    },

    # --- TERMINOS INSTITUCIONALES Y ROLES DE LA UMSA ---
    "auxi": {
        "categoria": "TERMINOLOGIA_UMSA",
        "significado": "Auxiliar de docencia: Estudiante de cursos superiores becado y remunerado por concurso de meritos para dictar practicas y laboratorios.",
        "polaridad": 0.5,
        "regex": r"\b(auxi[s]*|auxiliar[es]*)\b"
    },
    "auxiliatura": {
        "categoria": "TERMINOLOGIA_UMSA",
        "significado": "Clase practica o de laboratorio complementaria a la catedra del docente, usualmente evaluada sobre 10-20 puntos.",
        "polaridad": 0.0,
        "regex": r"\b(auxiliatura[s]*)\b"
    },
    "kardex": {
        "categoria": "TERMINOLOGIA_UMSA",
        "significado": "Unidad administrativa de la Carrera encargada del historial academico, inscripciones, notas y convalidaciones.",
        "polaridad": 0.0,
        "regex": r"\b(kardex)\b"
    },
    "pensum": {
        "categoria": "TERMINOLOGIA_UMSA",
        "significado": "Plan oficial de estudios y malla curricular de la Carrera de Informatica (ej. Pensum 2023 vs Pensum Antiguo).",
        "polaridad": 0.0,
        "regex": r"\b(pensum)\b"
    },
    "temporada": {
        "categoria": "TERMINOLOGIA_UMSA",
        "significado": "Cursos intensivos y acelerados intersemestrales de verano (diciembre-enero) o invierno (junio-julio).",
        "polaridad": 0.0,
        "regex": r"\b(temporada|verano|invierno)\b"
    },
    "retiro y adicion": {
        "categoria": "TERMINOLOGIA_UMSA",
        "significado": "Periodo oficial en el que el estudiante puede anular la inscripcion de una materia o anadir una nueva con cupo.",
        "polaridad": 0.0,
        "regex": r"\b(retiro\s+y\s+adici[oó]n|adici[oó]n|retiro)\b"
    },
    "troncal": {
        "categoria": "TERMINOLOGIA_UMSA",
        "significado": "Materia obligatoria y columna vertebral de la carrera que abre prerrequisitos en semestres superiores.",
        "polaridad": 0.0,
        "regex": r"\b(troncal[es]*)\b"
    },
    "paralelo": {
        "categoria": "TERMINOLOGIA_UMSA",
        "significado": "Grupo o division de aula (A, B, C, D, etc.) asignado a un docente especifico para una materia.",
        "polaridad": 0.0,
        "regex": r"\b(paralelo[s]*)\b"
    },
    "lic / licen": {
        "categoria": "TERMINOLOGIA_UMSA",
        "significado": "Trato respetuoso abreviado para Licenciado/a (docente de la carrera).",
        "polaridad": 0.0,
        "regex": r"\b(lic|lics|licen|licenciad[oa]s*)\b"
    },

    # --- ABREVIACIONES DE CHAT Y COMUNIDAD TELEGRAM ---
    "xd / :v": {
        "categoria": "JERGA_CHAT_INTERNET",
        "significado": "Expresion de risa, humor, sarcasmo o burla ante una situacion absurda.",
        "polaridad": 0.0,
        "regex": r"\b(xd+|:v)\b"
    },
    "bro / mano": {
        "categoria": "JERGA_CHAT_INTERNET",
        "significado": "Vocativo coloquial de trato entre companeros ('hermano' / 'amigo').",
        "polaridad": 0.0,
        "regex": r"\b(bro[o]*|mano[s]*|we|wey)\b"
    },
    "porfa / plis": {
        "categoria": "JERGA_CHAT_INTERNET",
        "significado": "Abreviacion de cortesia de 'por favor' al solicitar ayuda o enlaces.",
        "polaridad": 0.0,
        "regex": r"\b(porfa|plis|xfa)\b"
    },
    "chapa cupo": {
        "categoria": "JERGA_CHAT_INTERNET",
        "significado": "Asegurar rapidamente un cupo de inscripcion en un paralelo deseado antes de que se agote.",
        "polaridad": 0.5,
        "regex": r"\b(chapa|chapar|chapo)\s+(cupo|aula)\b"
    }
}

def extraer_ejemplo_contexto(texto, regex_comp):
    m = regex_comp.search(texto)
    if not m:
        return ""
    start, end = m.span()
    antes = texto[:start].split()[-5:]
    despues = texto[end:].split()[:5]
    return f"... {' '.join(antes)} [{m.group(0)}] {' '.join(despues)} ..."

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_root = os.path.dirname(script_dir)
    processed_dir = os.path.join(data_root, "processed")
    data_dir = processed_dir if os.path.exists(processed_dir) else data_root
    master_csv = os.path.join(data_dir, "dataset_telegram_master.csv")

    print(f"Cargando dataset maestro para minerar jergas: {master_csv}...")
    with open(master_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        mensajes = [r for r in reader]

    total_mensajes = len(mensajes)
    print(f"Analizando {total_mensajes} mensajes con la Base de Conocimiento Lexicografica...")

    falso_caporales = re.compile(r"\bcaporales\b", re.IGNORECASE)

    diccionario_resultados = []

    for termino, meta in BASE_JERGAS_SIGNIFICADOS.items():
        patron = re.compile(meta["regex"], re.IGNORECASE)
        conteo = 0
        mensajes_con_termino = set()
        ejemplos = []

        for m in mensajes:
            txt = m.get("texto_limpio", "") or ""
            # Filtro caporales
            if termino == "capo" and falso_caporales.search(txt):
                if not re.search(r"\bcap[oa]s*\b", falso_caporales.sub("", txt), re.IGNORECASE):
                    continue

            matches = patron.findall(txt)
            if matches:
                conteo += len(matches)
                mensajes_con_termino.add(m.get("mensaje_id"))
                if len(ejemplos) < 3 and len(txt) > 15:
                    ej = extraer_ejemplo_contexto(txt, patron)
                    if ej and ej not in ejemplos:
                        ejemplos.append(ej)

        ejemplo_final = " ; ".join(ejemplos) if ejemplos else "Sin ejemplo especifico"

        diccionario_resultados.append({
            "termino_jerga": termino,
            "categoria": meta["categoria"],
            "significado_en_contexto_umsa": meta["significado"],
            "polaridad_base": meta["polaridad"],
            "total_ocurrencias": conteo,
            "mensajes_afectados": len(mensajes_con_termino),
            "ejemplo_real_del_chat": ejemplo_final
        })

    # Ordenar por categoria y luego por apariciones
    diccionario_resultados.sort(key=lambda x: (x["categoria"], -x["total_ocurrencias"]))

    # Guardar en CSV
    out_csv = os.path.join(data_dir, "diccionario_jergas_y_modismos_umsa.csv")
    fields = [
        "termino_jerga", "categoria", "significado_en_contexto_umsa", 
        "polaridad_base", "total_ocurrencias", "mensajes_afectados", "ejemplo_real_del_chat"
    ]
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(diccionario_resultados)

    print(f"\n[OK] Generado exitosamente el Diccionario de Jergas UMSA: {out_csv}")
    print(f"Total terminos documentados y explicados: {len(diccionario_resultados)}\n")

    # Resumen por categoria
    cat_counts = defaultdict(int)
    cat_terms = defaultdict(int)
    for d in diccionario_resultados:
        cat_counts[d["categoria"]] += d["total_ocurrencias"]
        cat_terms[d["categoria"]] += 1

    print("=========================================================================")
    print(" RESUMEN DEL DICCIONARIO DE JERGAS Y MODISMOS UMSA")
    print("=========================================================================")
    for cat in sorted(cat_terms.keys()):
        print(f" * {cat}: {cat_terms[cat]} terminos | {cat_counts[cat]} apariciones en el chat")
    print("=========================================================================\n")

if __name__ == "__main__":
    main()
