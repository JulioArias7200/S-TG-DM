# -*- coding: utf-8 -*-
"""
02_pipeline_limpieza_multimodal.py
----------------------------------
Pipeline maestro de limpieza, enriquecimiento multimodal y vinculacion ontologica.
Genera los datasets analiticos en 'resultados/data/':
  1. dataset_telegram_master.csv
  2. dataset_menciones_docentes.csv
  3. dataset_reacciones_granular.csv
  4. eventos_servicio_log.csv
"""

import os
import re
import json
import csv
import hashlib
import unicodedata
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

# Configurar Tesseract si esta disponible
try:
    import pytesseract
    tesseract_exe = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_exe):
        pytesseract.pytesseract.tesseract_cmd = tesseract_exe
        TESSERACT_AVAILABLE = True
    else:
        TESSERACT_AVAILABLE = False
except ImportError:
    TESSERACT_AVAILABLE = False

EMOTION_TAXONOMY = {
    "humor_sarcasmo": ["😂", "🤣", "🤡", "😆", "😸", "🤪", "xd", "XD"],
    "frustracion_estres": ["😭", "😢", "💀", "💔", "😩", "😫", "🫠", "😓", "😵", "😞"],
    "enojo_indignacion": ["😡", "🤬", "👿", "🖕", "😠", "😤"],
    "aprobacion_apoyo": ["👍", "❤️", "👏", "💪", "🔥", "🙌", "💯", "👌", "🎉", "✨"],
    "sorpresa_duda": ["😱", "😮", "🤨", "🧐", "🫣", "🤔", "😐", "😶", "❓"],
    "saludo_agradecimiento": ["🙏", "👋", "🤝", "🫡"]
}

def map_emoji_to_emotion(emoji_str):
    if not emoji_str:
        return "sin_expresion"
    for cat, emojis in EMOTION_TAXONOMY.items():
        if any(e in emoji_str for e in emojis):
            return cat
    return "neutral_otro"

def extract_flat_text(raw_text):
    if isinstance(raw_text, str):
        return raw_text
    elif isinstance(raw_text, list):
        parts = []
        for item in raw_text:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", ""))
        return "".join(parts)
    return ""

def clean_text_for_nlp(text):
    if not text:
        return ""
    # Normalizacion Unicode NFKC
    norm = unicodedata.normalize("NFKC", text)
    # Reemplazar saltos de linea y tabulaciones por espacios limpios
    norm = re.sub(r"[\r\n\t]+", " ", norm)
    # Reducir espacios multiples
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm

def check_is_question(text):
    if not text:
        return False
    if "?" in text or "¿" in text:
        return True
    lower = text.lower()
    keywords = ["alguien sabe", "saben si", "quien sabe", "cuando es", "donde es", "hay cupos", "que docente", "cual docente", "conviene"]
    return any(k in lower for k in keywords)

def load_academic_catalog(data_dir):
    docentes = []
    docentes_csv = os.path.join(data_dir, "catalogo_docentes_umsa.csv")
    if os.path.exists(docentes_csv):
        with open(docentes_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    pat = re.compile(row["alias_regex"], re.IGNORECASE)
                    docentes.append((row["nombre_completo"], pat, row["materias_que_dicta"]))
                except re.error:
                    pass

    materias = []
    materias_csv = os.path.join(data_dir, "catalogo_materias_umsa.csv")
    if os.path.exists(materias_csv):
        with open(materias_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    pat = re.compile(row["alias_regex"], re.IGNORECASE)
                    materias.append((f"{row['codigo_materia']} - {row['nombre_materia']}", pat))
                except re.error:
                    pass

    return docentes, materias

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_root = os.path.dirname(script_dir)
    raw_dir = os.path.join(data_root, "raw")
    media_dir = os.path.join(data_root, "media")
    processed_dir = os.path.join(data_root, "processed")
    os.makedirs(processed_dir, exist_ok=True)
    data_dir = processed_dir

    json_path = os.path.join(raw_dir, "result.json")
    if not os.path.exists(json_path):
        json_path = os.path.join(data_root, "result.json")

    print(f"Cargando dataset origen: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_messages = data.get("messages", [])
    print(f"Total registros cargados: {len(all_messages)}")

    # 1. Separar mensajes de servicio de mensajes regulares
    service_events = []
    regular_messages = []
    for m in all_messages:
        if m.get("type") == "service":
            service_events.append(m)
        elif m.get("type") == "message":
            regular_messages.append(m)

    print(f"Mensajes de usuario: {len(regular_messages)} | Eventos de servicio: {len(service_events)}")

    # Guardar eventos de servicio
    service_csv = os.path.join(data_dir, "eventos_servicio_log.csv")
    with open(service_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "fecha", "actor", "actor_id", "accion"])
        for s in service_events:
            writer.writerow([
                s.get("id"),
                s.get("date"),
                s.get("actor", ""),
                s.get("actor_id", ""),
                s.get("action", "")
            ])
    print(f"Guardado log de servicio: {service_csv}")

    # Cargar catalogos academicos UMSA
    docentes_catalog, materias_catalog = load_academic_catalog(data_dir)
    print(f"Catalogos ontologicos cargados: {len(docentes_catalog)} docentes, {len(materias_catalog)} materias.")

    # Cargar o inicializar cache de OCR
    ocr_cache_path = os.path.join(data_dir, "ocr_cache.json")
    ocr_cache = {}
    if os.path.exists(ocr_cache_path):
        try:
            with open(ocr_cache_path, "r", encoding="utf-8") as f:
                ocr_cache = json.load(f)
            print(f"Cache de OCR cargada con {len(ocr_cache)} imagenes previas.")
        except Exception:
            ocr_cache = {}

    # Primer barrido: Indexacion de textos originales y padres para el grafo de conversacion
    id_to_text = {}
    for m in regular_messages:
        mid = m.get("id")
        raw = extract_flat_text(m.get("text"))
        id_to_text[mid] = clean_text_for_nlp(raw)

    # Identificar fotos de interes para OCR (priorizando imagenes sin texto de usuario o con preguntas)
    photos_to_ocr = []
    for m in regular_messages:
        if "photo" in m:
            photo_rel = m["photo"]
            photo_full = os.path.join(media_dir, photo_rel)
            if not os.path.exists(photo_full):
                photo_full = os.path.join(data_root, photo_rel)
            if os.path.exists(photo_full):
                # Generar hash rapido
                if photo_rel not in ocr_cache:
                    photos_to_ocr.append(photo_full)

    # Procesar OCR con concurrencia moderada (maximo 100 de las fotos mas relevantes para optimizar tiempo)
    if TESSERACT_AVAILABLE and photos_to_ocr:
        # Seleccionamos las primeras 120 imagenes unicas sin texto previo
        sample_ocr = photos_to_ocr[:120]
        print(f"Ejecutando OCR sobre {len(sample_ocr)} imagenes clave para enriquecer mensajes sin texto...")
        def process_single_ocr(img_path):
            try:
                rel = os.path.relpath(img_path, media_dir).replace("\\", "/")
                img = Image.open(img_path)
                txt = pytesseract.image_to_string(img, lang="spa")
                clean_ocr = clean_text_for_nlp(txt)
                return rel, clean_ocr
            except Exception:
                return rel, ""

        with ThreadPoolExecutor(max_workers=4) as executor:
            for rel_path, ocr_res in executor.map(process_single_ocr, sample_ocr):
                ocr_cache[rel_path] = ocr_res

        # Guardar cache de OCR
        with open(ocr_cache_path, "w", encoding="utf-8") as f:
            json.dump(ocr_cache, f, ensure_ascii=False, indent=2)
        print(f"Cache de OCR actualizada y guardada en {ocr_cache_path}")

    # Segundo barrido: Construccion del dataset maestro y granular
    master_rows = []
    menciones_rows = []
    reacciones_granulares = []

    # Mapas de entidades detectadas para propagacion en hilos
    id_to_docentes = {}
    id_to_materias = {}

    for m in regular_messages:
        mid = m.get("id")
        fecha = m.get("date", "")
        anio = fecha[:4] if len(fecha) >= 4 else ""
        mes = fecha[5:7] if len(fecha) >= 7 else ""
        dia = fecha[8:10] if len(fecha) >= 10 else ""
        hora = fecha[11:13] if len(fecha) >= 13 else ""

        usuario_id = m.get("from_id", "user_desconocido")
        usuario_nombre = m.get("from", "Usuario Desconocido") or "Usuario Desconocido"
        usuario_nombre_limpio = clean_text_for_nlp(usuario_nombre)

        reply_to_id = m.get("reply_to_message_id")
        es_respuesta = bool(reply_to_id)
        texto_padre = id_to_text.get(reply_to_id, "") if es_respuesta else ""
        padre_existe = reply_to_id in id_to_text if es_respuesta else False

        raw_text = extract_flat_text(m.get("text"))
        texto_limpio = clean_text_for_nlp(raw_text)
        longitud_caracteres = len(texto_limpio)
        conteo_palabras = len(texto_limpio.split()) if texto_limpio else 0
        es_pregunta = check_is_question(texto_limpio)

        # URLs y menciones
        tiene_url = "http://" in texto_limpio or "https://" in texto_limpio or "t.me/" in texto_limpio
        menciones = re.findall(r"@[\w_]+", raw_text)

        # Multimedia
        tiene_imagen = "photo" in m
        ruta_imagen = m.get("photo", "")
        texto_ocr_imagen = ocr_cache.get(ruta_imagen.replace("\\", "/"), "") if tiene_imagen else ""

        es_sticker = m.get("media_type") == "sticker" or "sticker_emoji" in m
        sticker_emoji = m.get("sticker_emoji", "")
        sticker_emocion = map_emoji_to_emotion(sticker_emoji) if es_sticker else "sin_sticker"

        es_gif = m.get("media_type") == "animation"
        archivo_adjunto = m.get("file", "") or m.get("photo", "")
        thumbnail_adjunto = m.get("thumbnail", "")

        gif_nombre_semantico = ""
        if es_gif and archivo_adjunto:
            base_fname = os.path.basename(archivo_adjunto)
            clean_fname = re.sub(r"\.(mp4|gif)", "", base_fname, flags=re.IGNORECASE)
            gif_nombre_semantico = clean_fname.replace("-", " ").replace("_", " ").strip()

        # Reacciones
        total_reacciones = 0
        reaccion_principal = ""
        reacciones_resumen_list = []
        if "reactions" in m and m["reactions"]:
            for r in m["reactions"]:
                cnt = r.get("count", 0)
                emj = r.get("emoji", "")
                total_reacciones += cnt
                if emj:
                    reacciones_resumen_list.append(f"{emj}: {cnt}")
                    # Guardar granular
                    reacciones_granulares.append({
                        "mensaje_id": mid,
                        "fecha_mensaje": fecha,
                        "emoji": emj,
                        "conteo": cnt,
                        "emocion_reaccion": map_emoji_to_emotion(emj)
                    })
            if m["reactions"]:
                best_r = max(m["reactions"], key=lambda x: x.get("count", 0))
                reaccion_principal = best_r.get("emoji", "")

        reacciones_resumen = ", ".join(reacciones_resumen_list)

        # Entity Linking Directo (Docentes y Materias)
        docentes_detectados = []
        for doc_nombre, pat, mat_dicta in docentes_catalog:
            if pat.search(texto_limpio):
                docentes_detectados.append(doc_nombre)

        materias_detectadas = []
        for mat_nombre, pat in materias_catalog:
            if pat.search(texto_limpio):
                materias_detectadas.append(mat_nombre)

        # Propagacion de Entidades por Hilo (si es respuesta y no menciono explicitamente un docente)
        heredado = False
        if es_respuesta and not docentes_detectados and reply_to_id in id_to_docentes:
            docentes_detectados = id_to_docentes[reply_to_id]
            heredado = True
        if es_respuesta and not materias_detectadas and reply_to_id in id_to_materias:
            materias_detectadas = id_to_materias[reply_to_id]

        # Guardar en mapa para respuestas siguientes
        if docentes_detectados:
            id_to_docentes[mid] = docentes_detectados
        if materias_detectadas:
            id_to_materias[mid] = materias_detectadas

        docentes_str = " ; ".join(docentes_detectados) if docentes_detectados else "Ninguno"
        materias_str = " ; ".join(materias_detectadas) if materias_detectadas else "Ninguna"

        # Construccion del Contenido Multimodal Unificado para NLP
        componentes = []
        if texto_limpio:
            componentes.append(texto_limpio)
        if texto_ocr_imagen:
            componentes.append(f"[IMAGEN_OCR: {texto_ocr_imagen}]")
        elif tiene_imagen:
            componentes.append("[IMAGEN_ADJUNTA]")
        if es_sticker and sticker_emoji:
            componentes.append(f"[STICKER: {sticker_emocion} ({sticker_emoji})]")
        if es_gif:
            gif_desc = f"[GIF_ANIMADO: {gif_nombre_semantico}]" if gif_nombre_semantico else "[ANIMACION_GIF]"
            componentes.append(gif_desc)
        if reacciones_resumen:
            componentes.append(f"[REACCIONES: {reacciones_resumen}]")

        contenido_multimodal_unificado = " ".join(componentes)

        row = {
            "mensaje_id": mid,
            "fecha": fecha,
            "anio": anio,
            "mes": mes,
            "dia": dia,
            "hora": hora,
            "usuario_id": usuario_id,
            "usuario_nombre": usuario_nombre_limpio,
            "es_respuesta": es_respuesta,
            "respuesta_a_id": reply_to_id if es_respuesta else "",
            "padre_existe": padre_existe,
            "texto_mensaje_padre": texto_padre,
            "texto_original": raw_text,
            "texto_limpio": texto_limpio,
            "longitud_caracteres": longitud_caracteres,
            "conteo_palabras": conteo_palabras,
            "es_pregunta": es_pregunta,
            "tiene_url": tiene_url,
            "menciones_usuarios": ", ".join(menciones),
            "tiene_imagen": tiene_imagen,
            "ruta_imagen": ruta_imagen,
            "imagen_texto_ocr": texto_ocr_imagen,
            "es_sticker": es_sticker,
            "sticker_emoji": sticker_emoji,
            "sticker_emocion": sticker_emocion,
            "es_gif": es_gif,
            "gif_nombre": gif_nombre_semantico,
            "archivo_adjunto": archivo_adjunto,
            "thumbnail_adjunto": thumbnail_adjunto,
            "total_reacciones": total_reacciones,
            "reaccion_principal": reaccion_principal,
            "reacciones_resumen": reacciones_resumen,
            "docente_mencionado": docentes_str,
            "materia_mencionada": materias_str,
            "entidad_heredada_hilo": heredado,
            "contenido_multimodal_unificado": contenido_multimodal_unificado
        }
        master_rows.append(row)

        if docentes_str != "Ninguno" or materias_str != "Ninguna":
            menciones_rows.append(row)

    print(f"Total filas procesadas para dataset maestro: {len(master_rows)}")
    print(f"Total mensajes vinculados a docentes o materias: {len(menciones_rows)}")
    print(f"Total reacciones registradas individualmente: {len(reacciones_granulares)}")

    # 1. Exportar dataset_telegram_master.csv
    master_csv = os.path.join(data_dir, "dataset_telegram_master.csv")
    if master_rows:
        fieldnames = list(master_rows[0].keys())
        with open(master_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(master_rows)
        print(f"Guardado Dataset Maestro: {master_csv}")

    # 2. Exportar dataset_menciones_docentes.csv
    menciones_csv = os.path.join(data_dir, "dataset_menciones_docentes.csv")
    if menciones_rows:
        with open(menciones_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(menciones_rows)
        print(f"Guardado Dataset Menciones Docentes: {menciones_csv}")

    # 3. Exportar dataset_reacciones_granular.csv
    reacciones_csv = os.path.join(data_dir, "dataset_reacciones_granular.csv")
    if reacciones_granulares:
        r_fieldnames = list(reacciones_granulares[0].keys())
        with open(reacciones_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=r_fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(reacciones_granulares)
        print(f"Guardado Dataset Reacciones Granular: {reacciones_csv}")

    # 4. Exportar catalogo_gifs_animaciones.csv
    gif_rows = [r for r in master_rows if r["es_gif"]]
    gif_csv = os.path.join(data_dir, "catalogo_gifs_animaciones.csv")
    if gif_rows:
        gif_fields = ["mensaje_id", "fecha", "usuario_nombre", "gif_nombre", "archivo_adjunto", "thumbnail_adjunto", "texto_limpio", "contenido_multimodal_unificado"]
        with open(gif_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=gif_fields, extrasaction="ignore", quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(gif_rows)
        print(f"Guardado Catalogo de GIFs/Animaciones ({len(gif_rows)} registros): {gif_csv}")

if __name__ == "__main__":
    main()
