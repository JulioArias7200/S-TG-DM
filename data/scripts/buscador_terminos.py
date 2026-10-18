# -*- coding: utf-8 -*-
"""
buscador_terminos.py
--------------------
Herramienta de exploracion y mineria lexica sobre el dataset de Telegram UMSA.
Permite:
  1. Buscar terminos especificos o patrones regex en el dataset maestro y de menciones.
  2. Descubrir nuevas variantes de jerga (co-ocurrencias con emojis de sarcasmo 💀, 🤡, 😭).
  3. Analizar concordancias en contexto (KWIC - Key Word in Context).

Uso:
  python buscador_terminos.py --buscar "facil" "regal" "chiste" "pichi" "mantequilla"
  python buscador_terminos.py --descubrir_sarcasmo
  python buscador_terminos.py --top_adjetivos
"""

import os
import sys
import re
import csv
import argparse
from collections import Counter

# Asegurar salida utf-8 en terminal de Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def cargar_textos(data_dir, solo_menciones=False):
    archivo = "dataset_menciones_docentes.csv" if solo_menciones else "dataset_telegram_master.csv"
    ruta = os.path.join(data_dir, archivo)
    if not os.path.exists(ruta):
        # Fallback al master
        ruta = os.path.join(data_dir, "dataset_telegram_master.csv")
    
    registros = []
    with open(ruta, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            registros.append(row)
    return registros, os.path.basename(ruta)

def buscar_terminos(registros, patrones, max_ejemplos=5):
    print(f"\n=======================================================")
    print(f" RESULTADOS DE BUSQUEDA PARA: {patrones}")
    print(f"=======================================================")
    
    hallazgos_totales = 0
    por_patron = Counter()
    
    ejemplos_por_patron = {p: [] for p in patrones}
    
    compiled_pats = [(p, re.compile(r"\b" + re.escape(p) if not p.endswith("*") else r"\b" + re.escape(p[:-1]) + r"\w*", re.IGNORECASE)) for p in patrones]

    for r in registros:
        texto = r.get("texto_limpio", "") or ""
        multimodal = r.get("contenido_multimodal_unificado", "") or ""
        docente = r.get("docente_mencionado", "")
        materia = r.get("materia_mencionada", "")
        mid = r.get("mensaje_id", "")
        fecha = r.get("fecha", "")[:10]

        texto_evaluar = f"{texto} {multimodal}"
        
        for p, regex in compiled_pats:
            matches = regex.findall(texto)
            if matches:
                por_patron[p] += len(matches)
                hallazgos_totales += len(matches)
                if len(ejemplos_por_patron[p]) < max_ejemplos:
                    ejemplos_por_patron[p].append({
                        "id": mid,
                        "fecha": fecha,
                        "texto": texto,
                        "docente": docente,
                        "materia": materia,
                        "coincidencias": matches
                    })

    for p in patrones:
        cnt = por_patron[p]
        print(f"\n[+] Patron: '{p}' -> {cnt} ocurrencias encontradas.")
        for idx, ej in enumerate(ejemplos_por_patron[p], 1):
            doc_str = f" | Docente: {ej['docente']}" if ej['docente'] != "Ninguno" else ""
            mat_str = f" | Materia: {ej['materia']}" if ej['materia'] != "Ninguna" else ""
            print(f"   {idx}. [ID {ej['id']} - {ej['fecha']}{doc_str}{mat_str}]")
            print(f"      \"{ej['texto']}\"")

    print(f"\n-------------------------------------------------------")
    print(f"Total coincidencias acumuladas: {hallazgos_totales}")
    print(f"-------------------------------------------------------\n")

def descubrir_sarcasmo_y_facilidad(registros):
    print(f"\n=======================================================")
    print(f" MINERIA DE DESCUBRIMIENTO: PALABRAS CLAVE ASOCIADAS A SARCASMO Y EXAMENES")
    print(f"=======================================================")
    
    # Emojis asociados a sarcasmo / burla / sufrimiento estudiantil
    sarcasm_emojis = ["💀", "🤡", "⚰️", "😭", "🤣", "😂", "xd", "XD"]
    
    # Palabras stopword basicas en espanol
    stopwords = set([
        "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para", "con", "no", 
        "una", "su", "al", "lo", "como", "mas", "pero", "sus", "le", "ya", "o", "este", "si", "porque", "esta", 
        "son", "entre", "esta", "cuando", "muy", "sin", "sobre", "tambien", "me", "hasta", "hay", "donde", "quien",
        "desde", "todo", "nos", "durante", "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante",
        "ellos", "e", "esto", "mi", "antes", "algunos", "que", "unos", "yo", "otro", "otras", "otra", "el", "tanto",
        "esa", "estos", "mucho", "quienes", "nada", "muchos", "cual", "poco", "ella", "estar", "estas", "algunas",
        "algo", "nosotros", "mi", "mis", "tu", "te", "ti", "tu", "tus", "ellas", "nosotras", "vosostros", "vosostras",
        "mio", "mia", "mios", "mias", "tuyo", "tuya", "tuyos", "tuyas", "suyo", "suya", "suyos", "suyas", "nuestro",
        "nuestra", "nuestros", "nuestras", "vuestro", "vuestra", "vuestros", "vuestras", "esos", "esas", "es", "alguien"
    ])

    vocab_sarcasmo = Counter()
    vocab_facilidad = Counter()

    patron_facil_raiz = re.compile(r"\b(facil\w*|regal\w*|chiste\w*|pichi\w*|mantequilla\w*|pan comido|suave\w*|tranqui\w*|accesibl\w*|barco\w*)\b", re.IGNORECASE)

    mensajes_sarcasmo_detectados = []

    for r in registros:
        txt = r.get("texto_limpio", "") or ""
        multi = r.get("contenido_multimodal_unificado", "") or ""
        lower = txt.lower()

        # Chequear emojis de sarcasmo en el texto o stickers
        tiene_emoji_sarcasmo = any(e in multi for e in sarcasm_emojis)
        matches_facil = patron_facil_raiz.findall(lower)

        if matches_facil:
            for mf in matches_facil:
                vocab_facilidad[mf.lower()] += 1

            if tiene_emoji_sarcasmo:
                mensajes_sarcasmo_detectados.append({
                    "id": r.get("mensaje_id"),
                    "texto": txt,
                    "multi": multi,
                    "docente": r.get("docente_mencionado"),
                    "materia": r.get("materia_mencionada")
                })

        if tiene_emoji_sarcasmo:
            words = re.findall(r"[a-záéíóúñ]{4,}", lower)
            for w in words:
                if w not in stopwords:
                    vocab_sarcasmo[w] += 1

    print("\n[+] Top variantes de expresiones de 'FACILIDAD / REGALADO / TRANQUILO' encontradas en el corpus:")
    for w, c in vocab_facilidad.most_common(20):
        print(f"    - '{w}': {c} veces")

    print(f"\n[+] Total mensajes detectados con posible SARCASMO (Palabra de facilidad + Emoji 💀/🤡/😭/🤣): {len(mensajes_sarcasmo_detectados)}")
    print("    Ejemplos reales del dataset:")
    for idx, m in enumerate(mensajes_sarcasmo_detectados[:8], 1):
        doc = f" [Docente: {m['docente']}]" if m['docente'] != "Ninguno" else ""
        print(f"    {idx}. ID {m['id']}{doc}: \"{m['texto']}\"")
        if "[STICKER:" in m['multi'] or "[REACCIONES:" in m['multi']:
            print(f"       -> Multimodal: {m['multi']}")

    print("\n[+] Palabras más frecuentes en mensajes que contienen 💀 o 🤡 (Jerga de sufrimiento/ironía):")
    for w, c in vocab_sarcasmo.most_common(20):
        print(f"    - '{w}': {c} veces")

def main():
    parser = argparse.ArgumentParser(description="Buscador y explorador de terminos especiales y jerga UMSA.")
    parser.add_argument("--buscar", nargs="+", help="Lista de palabras o raices con comodin * (ej. facil* regal* pichi*)")
    parser.add_argument("--descubrir_sarcasmo", action="store_true", help="Descubrir co-ocurrencias de facilidad con emojis de burla/muerte.")
    parser.add_argument("--solo_menciones", action="store_true", help="Buscar solo en mensajes vinculados a docentes/materias.")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_root = os.path.dirname(script_dir)
    processed_dir = os.path.join(data_root, "processed")
    data_dir = processed_dir if os.path.exists(processed_dir) else data_root

    registros, nom_archivo = cargar_textos(data_dir, solo_menciones=args.solo_menciones)
    print(f"Cargados {len(registros)} registros desde {nom_archivo}")

    if args.buscar:
        buscar_terminos(registros, args.buscar)
    
    if args.descubrir_sarcasmo or not args.buscar:
        descubrir_sarcasmo_y_facilidad(registros)

if __name__ == "__main__":
    main()
