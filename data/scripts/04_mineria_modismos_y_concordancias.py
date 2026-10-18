# -*- coding: utf-8 -*-
"""
04_mineria_modismos_y_concordancias.py
--------------------------------------
Modulo de Data Mining para la extraccion, indexacion y catalogacion de modismos,
jerga estudiantil y calificadores academicos sobre el dataset de Telegram UMSA.

Genera en 'resultados/data/':
  1. dataset_modismos_mensajes.csv   (Tabla relacional: cada aparicion de un modismo con su contexto KWIC)
  2. catalogo_modismos_umsa.csv      (Diccionario consolidado de jerga con frecuencias, polaridad y categoria)
"""

import os
import sys
import re
import csv
from collections import defaultdict, Counter

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Catalogo Maestro de Patrones Lexicos y Modismos Universitarios (UMSA)
CATALOGO_PATRONES_MODISMOS = [
    # 1. FACILIDAD Y APROBACION
    {"patron": r"\b(facilito[os]*|facil[es]*)\b", "nombre": "facil / facilito", "categoria": "FACILIDAD_APROBACION", "polaridad": 1.5},
    {"patron": r"\b(accesibl[es]*)\b", "nombre": "accesible", "categoria": "FACILIDAD_APROBACION", "polaridad": 1.2},
    {"patron": r"\b(suave[s]*|suave\s+nom[aá]s)\b", "nombre": "suave / suave nomas", "categoria": "FACILIDAD_APROBACION", "polaridad": 1.0},
    {"patron": r"\b(tranqui[s]*|tranquil[oa]s*|tranquilamente)\b", "nombre": "tranqui / tranquilo", "categoria": "FACILIDAD_APROBACION", "polaridad": 1.0},
    {"patron": r"\b(barco[s]*)\b", "nombre": "barco (pasa facil)", "categoria": "FACILIDAD_APROBACION", "polaridad": 0.8},
    {"patron": r"\b(regala\s+nota[s]*|regalaba\s+nota[s]*|regalad[oa]s*)\b", "nombre": "regala notas / regalado", "categoria": "FACILIDAD_APROBACION", "polaridad": 1.5},
    {"patron": r"\b(aprobaci[oó]n\s+segura|hace\s+pasar)\b", "nombre": "aprobacion segura / hace pasar", "categoria": "FACILIDAD_APROBACION", "polaridad": 1.5},
    {"patron": r"\b(mantequilla|pan\s+comido|pichi)\b", "nombre": "pichi / pan comido", "categoria": "FACILIDAD_APROBACION", "polaridad": 1.5},

    # 2. DIFICULTAD, FILTRO Y EXIGENCIA
    {"patron": r"\b(fregad[oa]s*|frieg[aoe]n*)\b", "nombre": "fregado / friega", "categoria": "DIFICULTAD_EXIGENCIA", "polaridad": -1.5},
    {"patron": r"\b(pesad[oa]s*)\b", "nombre": "pesado / materia pesada", "categoria": "DIFICULTAD_EXIGENCIA", "polaridad": -1.2},
    {"patron": r"\b(exigent[es]*)\b", "nombre": "exigente", "categoria": "DIFICULTAD_EXIGENCIA", "polaridad": -0.8},
    {"patron": r"\b(estrict[oa]s*)\b", "nombre": "estricto / estricta", "categoria": "DIFICULTAD_EXIGENCIA", "polaridad": -0.8},
    {"patron": r"\b(matador[a]*s*|masacre|colador)\b", "nombre": "matador / masacre / colador", "categoria": "DIFICULTAD_EXIGENCIA", "polaridad": -2.0},
    {"patron": r"\b(filtro[s]*)\b", "nombre": "filtro (materia colador)", "categoria": "DIFICULTAD_EXIGENCIA", "polaridad": -1.5},
    {"patron": r"\b(yuca[s]*)\b", "nombre": "yuca (dificil)", "categoria": "DIFICULTAD_EXIGENCIA", "polaridad": -1.5},
    {"patron": r"\b(complicad[oa]s*)\b", "nombre": "complicado", "categoria": "DIFICULTAD_EXIGENCIA", "polaridad": -1.0},

    # 3. REPROBACION, FRUSTRACION Y SANCION
    {"patron": r"\b(tirar[s]*e*|tiraron|tirar[aá]n*)\b", "nombre": "tirarse (reprobar)", "categoria": "REPROBACION_SANCION", "polaridad": -1.8},
    {"patron": r"\b(aplaz[aoe]r*|aplazad[oa]s*|te\s+aplaza)\b", "nombre": "aplazar / te aplaza", "categoria": "REPROBACION_SANCION", "polaridad": -2.0},
    {"patron": r"\b(reprob[aoe]r*|reprobad[oa]s*)\b", "nombre": "reprobar / reprobado", "categoria": "REPROBACION_SANCION", "polaridad": -1.5},
    {"patron": r"\b(abandon[aoe]r*|abandon[oó])\b", "nombre": "abandonar materia", "categoria": "REPROBACION_SANCION", "polaridad": -1.2},
    {"patron": r"\b(llorar|llorando|lloren)\b", "nombre": "llorar (frustracion)", "categoria": "REPROBACION_SANCION", "polaridad": -1.0},
    {"patron": r"\b(morir|muerto|rip)\b", "nombre": "morir / rip", "categoria": "REPROBACION_SANCION", "polaridad": -1.2},

    # 4. CALIDAD DOCENTE Y RECONOCIMIENTO POSITIVO
    {"patron": r"\b(cap[oa]s*|cap[ií]sim[oa]s*)\b", "nombre": "capo / capisimo", "categoria": "CALIDAD_DOCENTE", "polaridad": 2.0},
    {"patron": r"\b(crack[s]*)\b", "nombre": "crack (excelente)", "categoria": "CALIDAD_DOCENTE", "polaridad": 2.0},
    {"patron": r"\b(buen\s+docente|buen\s+tipo|buen\s+profe|buena\s+licen*)\b", "nombre": "buen docente / buen profe", "categoria": "CALIDAD_DOCENTE", "polaridad": 1.8},
    {"patron": r"\b(buena\s+onda)\b", "nombre": "buena onda", "categoria": "CALIDAD_DOCENTE", "polaridad": 1.5},
    {"patron": r"\b(se\s+aprende\s+bien|aprendes\s+bien|ense[ñn]a\s+bien)\b", "nombre": "enseña / aprende bien", "categoria": "CALIDAD_DOCENTE", "polaridad": 2.0},
    {"patron": r"\b(recomiend[oa]|recomendad[oa]|conviene)\b", "nombre": "recomiendo / conviene", "categoria": "CALIDAD_DOCENTE", "polaridad": 1.5},
    {"patron": r"\b(comprensiv[oa]s*|amable[s]*)\b", "nombre": "comprensivo / amable", "categoria": "CALIDAD_DOCENTE", "polaridad": 1.2},

    # 5. DEFICIENCIA DOCENTE, MAL TRATO Y DESAPROBACION
    {"patron": r"\b(no\s+ense[ñn]a|no\s+se\s+entiende|no\s+explica)\b", "nombre": "no enseña / no explica", "categoria": "DEFICIENCIA_DOCENTE", "polaridad": -2.2},
    {"patron": r"\b(falt[oó]n[a]*s*|no\s+asiste|no\s+viene|falta\s+mucho)\b", "nombre": "falton / no asiste", "categoria": "DEFICIENCIA_DOCENTE", "polaridad": -2.0},
    {"patron": r"\b(no\s+sube\s+notas|tarda\s+en\s+subir|no\s+publica\s+notas)\b", "nombre": "no sube notas / tarda", "categoria": "DEFICIENCIA_DOCENTE", "polaridad": -2.0},
    {"patron": r"\b(prepotente[s]*|soberbi[oa]s*|reneg[oó]n[a]*s*)\b", "nombre": "prepotente / soberbio", "categoria": "DEFICIENCIA_DOCENTE", "polaridad": -2.0},
    {"patron": r"\b(mala\s+reputaci[oó]n|p[eé]sim[oa]s*|no\s+te\s+conviene)\b", "nombre": "mala reputacion / no te conviene", "categoria": "DEFICIENCIA_DOCENTE", "polaridad": -2.2},
    {"patron": r"\b(aburrid[oa]s*|ense[ñn]anza\s+antigua|metodolog[ií]a\s+antigua)\b", "nombre": "aburrido / didactica antigua", "categoria": "DEFICIENCIA_DOCENTE", "polaridad": -1.2},

    # 6. SARCASMO E IRONIA
    {"patron": r"\b(chiste[s]*|es\s+un\s+chiste)\b", "nombre": "chiste (ironia)", "categoria": "SARCASMO_IRONIA", "polaridad": -1.0},
    {"patron": r"\b(payas[oa]s*|circo)\b", "nombre": "payaso / circo", "categoria": "SARCASMO_IRONIA", "polaridad": -1.5}
]

EMOJIS_SARCASMO = set(["💀", "🤡", "⚰️", "😭", "🤣", "😂", "xd", "XD", ":v", "🤡"])

def extraer_kwic(texto, span_inicio, span_fin, ventana_palabras=6):
    """Extrae palabras previas y posteriores para concordancia KWIC."""
    antes = texto[:span_inicio].strip().split()
    despues = texto[span_fin:].strip().split()
    kwic_antes = " ".join(antes[-ventana_palabras:]) if antes else ""
    kwic_despues = " ".join(despues[:ventana_palabras]) if despues else ""
    target = texto[span_inicio:span_fin]
    return f"... {kwic_antes} [{target}] {kwic_despues} ..."

def minar_modismos(data_dir):
    master_path = os.path.join(data_dir, "dataset_telegram_master.csv")
    if not os.path.exists(master_path):
        print(f"Error: no existe {master_path}")
        return

    print(f"Cargando dataset maestro: {master_path}...")
    registros = []
    with open(master_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            registros.append(r)

    print(f"Total registros cargados para mineria: {len(registros)}")

    # Compilar expresiones regulares con control de falsos positivos
    compiled_catalog = []
    for elem in CATALOGO_PATRONES_MODISMOS:
        compiled_catalog.append({
            "regex": re.compile(elem["patron"], re.IGNORECASE),
            "nombre": elem["nombre"],
            "categoria": elem["categoria"],
            "polaridad": elem["polaridad"]
        })

    apariciones_modismos = []
    stats_catalogo = defaultdict(lambda: {
        "categoria": "",
        "polaridad_base": 0.0,
        "conteo_total": 0,
        "mensajes_unicos": set(),
        "con_docente_vinculado": 0,
        "con_materia_vinculada": 0,
        "con_sarcasmo_multimodal": 0,
        "ejemplo_destacado": ""
    })

    # Regla de falso positivo conocida: descartar "caporales"
    regex_falso_caporales = re.compile(r"\bcaporales\b", re.IGNORECASE)

    for r in registros:
        mid = r.get("mensaje_id")
        fecha = r.get("fecha")
        usuario = r.get("usuario_nombre")
        docente = r.get("docente_mencionado", "Ninguno")
        materia = r.get("materia_mencionada", "Ninguna")
        texto = r.get("texto_limpio", "") or ""
        multimodal = r.get("contenido_multimodal_unificado", "") or ""
        reacciones = r.get("reacciones_resumen", "")

        # Verificar emojis o stickers de sarcasmo
        tiene_sarcasmo = any(e in multimodal for e in EMOJIS_SARCASMO)

        tiene_docente = docente != "Ninguno"
        tiene_materia = materia != "Ninguna"

        # Evaluar patrones
        for item in compiled_catalog:
            # Control específico para "capo": si dice "caporales", ignorar
            if item["nombre"] == "capo / capisimo" and regex_falso_caporales.search(texto):
                # Validar si también tiene capo independiente
                if not re.search(r"\bcap[oa]s*\b", regex_falso_caporales.sub("", texto), re.IGNORECASE):
                    continue

            for m in item["regex"].finditer(texto):
                termino_exacto = m.group(0)
                kwic = extraer_kwic(texto, m.start(), m.end())

                # Polaridad contextual (inversion si hay sarcasmo)
                pol_final = item["polaridad"]
                if tiene_sarcasmo and item["polaridad"] > 0 and item["categoria"] in ["FACILIDAD_APROBACION", "SARCASMO_IRONIA"]:
                    pol_final = -1.2 * item["polaridad"] # Inversión por sarcasmo

                apariciones_modismos.append({
                    "mensaje_id": mid,
                    "fecha": fecha,
                    "usuario_nombre": usuario,
                    "modismo_nombre": item["nombre"],
                    "termino_exacto": termino_exacto,
                    "categoria": item["categoria"],
                    "polaridad_asignada": round(pol_final, 2),
                    "es_sarcasmo_potencial": tiene_sarcasmo,
                    "docente_mencionado": docente,
                    "materia_mencionada": materia,
                    "contexto_kwic": kwic,
                    "reacciones": reacciones,
                    "texto_completo": texto
                })

                # Stats agregadas
                s = stats_catalogo[item["nombre"]]
                s["categoria"] = item["categoria"]
                s["polaridad_base"] = item["polaridad"]
                s["conteo_total"] += 1
                s["mensajes_unicos"].add(mid)
                if tiene_docente:
                    s["con_docente_vinculado"] += 1
                if tiene_materia:
                    s["con_materia_vinculada"] += 1
                if tiene_sarcasmo:
                    s["con_sarcasmo_multimodal"] += 1
                if not s["ejemplo_destacado"] and len(texto) > 15:
                    s["ejemplo_destacado"] = kwic

    print(f"\n=================================================================")
    print(f" RESUMEN DE MINERIA DE MODISMOS:")
    print(f" Total ocurrencias de modismos detectadas: {len(apariciones_modismos)}")
    print(f" Modismos unicos catalogados: {len(stats_catalogo)}")
    print(f"=================================================================\n")

    # 1. Exportar dataset relacional de modismos por mensaje
    out_mensajes_csv = os.path.join(data_dir, "dataset_modismos_mensajes.csv")
    if apariciones_modismos:
        fields = list(apariciones_modismos[0].keys())
        with open(out_mensajes_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(apariciones_modismos)
        print(f"[OK] Guardado dataset de ocurrencias con KWIC: {out_mensajes_csv} ({len(apariciones_modismos)} filas)")

    # 2. Exportar catálogo consolidado
    out_catalogo_csv = os.path.join(data_dir, "catalogo_modismos_umsa.csv")
    catalogo_rows = []
    for mod_nombre, s in sorted(stats_catalogo.items(), key=lambda x: x[1]["conteo_total"], reverse=True):
        catalogo_rows.append({
            "modismo_nombre": mod_nombre,
            "categoria": s["categoria"],
            "polaridad_base": s["polaridad_base"],
            "total_ocurrencias": s["conteo_total"],
            "mensajes_unicos": len(s["mensajes_unicos"]),
            "menciones_con_docente": s["con_docente_vinculado"],
            "menciones_con_materia": s["con_materia_vinculada"],
            "menciones_con_sarcasmo": s["con_sarcasmo_multimodal"],
            "ejemplo_kwic": s["ejemplo_destacado"]
        })

    if catalogo_rows:
        fields_cat = list(catalogo_rows[0].keys())
        with open(out_catalogo_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields_cat, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(catalogo_rows)
        print(f"[OK] Guardado catalogo ontologico de jerga: {out_catalogo_csv} ({len(catalogo_rows)} modismos)")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_root = os.path.dirname(script_dir)
    processed_dir = os.path.join(data_root, "processed")
    data_dir = processed_dir if os.path.exists(processed_dir) else data_root
    minar_modismos(data_dir)
