# -*- coding: utf-8 -*-
"""
06_analisis_multimodal_imagenes_sentimiento.py
----------------------------------------------
Pipeline maestro de procesamiento integral de imagenes, stickers y GIFs:
  1. OCR total sobre fotos unicas (mediante hash MD5 y multithreading).
  2. Clasificacion de Intencion Multimodal (Problema de Sistema, Comunicado Oficial, Meme/Satira, etc.).
  3. Evaluacion de Sentimiento, Emocion y Polaridad Visual (-2.0 a +2.0).
  4. Generacion de 'catalogo_multimodal_imagenes_stickers.csv'.
  5. Sincronizacion de columnas multimodales en 'dataset_telegram_master.csv'.
  6. Eliminacion de archivos obsoletos superados por este catalogo.
"""

import os
import sys
import re
import csv
import json
import hashlib
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Configurar Tesseract
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

# Reglas de Intencion y Emocion Multimodal
REGLAS_INTENCION_TEXTO = [
    # Problemas de Sistema / Kardex Error
    {
        "intencion": "PROBLEMA_SISTEMA_ERROR",
        "emocion": "FRUSTRACION_ESTRES",
        "polaridad": -1.5,
        "regex": r"(ha superado el n[uú]mero m[aá]ximo|no se hizo el dep[oó]sito|error|sistema ca[ií]do|no puedo ingresar|bloqueado|sin docente)"
    },
    # Comprobantes Transaccionales
    {
        "intencion": "COMPROBANTE_TRANSACCIONAL",
        "emocion": "NEUTRAL_OPERATIVO",
        "polaridad": 0.0,
        "regex": r"(banco uni[oó]n|cpt|c[oó]digo cpt|uninet|transacci[oó]n|comprobante|dep[oó]sito bancario|65\s*bs)"
    },
    # Comunicados Oficiales
    {
        "intencion": "AVISO_KARDEX_COMUNICADO",
        "emocion": "NEUTRAL_INFORMATIVO",
        "polaridad": 0.2,
        "regex": r"(comunicado|carrera de inform[aá]tica|direcci[oó]n|la coordinaci[oó]n|cronograma|ampliaci[oó]n|kardex acad[eé]mico|hcu|resoluci[oó]n)"
    },
    # Horarios y Oferta
    {
        "intencion": "HORARIO_OFERTA_AULAS",
        "emocion": "NEUTRAL_LOGISTICO",
        "polaridad": 0.0,
        "regex": r"(horario|temporada verano|temporada invierno|paralelo|aula|inf-\d+|mat-\d+|est-\d+|fis-\d+)"
    },
    # Eventos Sociales y Culturales
    {
        "intencion": "EVENTO_CULTURAL_SOCIAL",
        "emocion": "APROBACION_CELEBRACION",
        "polaridad": 1.5,
        "regex": r"(caporales|entrada universitaria|concurso|fiesta|elecci[oó]n|chacha|warmi|premiaci[oó]n|fraternidad)"
    }
]

EMOTION_TAXONOMY = {
    "humor_sarcasmo": ["😂", "🤣", "🤡", "😆", "😸", "🤪", "xd", "XD", ":v"],
    "frustracion_estres": ["😭", "😢", "💀", "💔", "😩", "😫", "🫠", "😓", "😵", "😞", "⚰️"],
    "enojo_indignacion": ["😡", "🤬", "👿", "🖕", "😠", "😤"],
    "aprobacion_apoyo": ["👍", "❤️", "👏", "💪", "🔥", "🙌", "💯", "👌", "🎉", "✨", "🫡"],
    "sorpresa_duda": ["😱", "😮", "🤨", "🧐", "🫣", "🤔", "😐", "😶", "❓"],
    "saludo_agradecimiento": ["🙏", "👋", "🤝"]
}

POLARIDAD_EMOCIONES = {
    "humor_sarcasmo": 0.5,
    "frustracion_estres": -1.8,
    "enojo_indignacion": -2.0,
    "aprobacion_apoyo": 1.5,
    "sorpresa_duda": -0.2,
    "saludo_agradecimiento": 1.0,
    "NEUTRAL_INFORMATIVO": 0.0,
    "NEUTRAL_OPERATIVO": 0.0,
    "NEUTRAL_LOGISTICO": 0.0
}

def clean_ocr(text):
    if not text:
        return ""
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def clasificar_multimodal(texto_ocr, texto_msg, sticker_emoji, sticker_emocion, es_gif, gif_nombre, reacciones):
    # 1. Si es Sticker
    if sticker_emoji or (sticker_emocion and sticker_emocion != "sin_sticker"):
        emocion = sticker_emocion if sticker_emocion != "sin_sticker" else "humor_sarcasmo"
        pol = POLARIDAD_EMOCIONES.get(emocion, 0.0)
        
        # Inversión si convive con texto que aparenta facilidad
        if any(w in texto_msg.lower() for w in ["facil", "regalado", "chiste"]) and emocion in ["humor_sarcasmo", "frustracion_estres"]:
            pol = -1.5
            intencion = "MEME_HUMOR_SATIRA"
        elif emocion == "humor_sarcasmo":
            intencion = "REACCION_BURLESCA"
        elif emocion == "frustracion_estres":
            intencion = "QUEJA_DESESPERACION"
        elif emocion == "aprobacion_apoyo":
            intencion = "APOYO_CELEBRACION"
        else:
            intencion = "REACCION_EXPRESIVA"
            
        return intencion, emocion.upper(), pol

    # 2. Si es GIF / Animación
    if es_gif:
        nombre = gif_nombre.lower() if gif_nombre else ""
        if any(w in nombre for w in ["laugh", "meme", "joke", "cry", "dance", "fail", "cat", "dog"]):
            return "MEME_HUMOR_SATIRA", "HUMOR_SARCASMO", 0.8
        elif any(w in nombre for w in ["angry", "rage", "fight", "no"]):
            return "REACCION_ENOJO", "ENOJO_INDIGNACION", -1.5
        elif any(w in nombre for w in ["cry", "sad", "die", "dead", "tired"]):
            return "QUEJA_DESESPERACION", "FRUSTRACION_ESTRES", -1.5
        return "ANIMACION_INTERACCION", "HUMOR_SARCASMO", 0.5

    # 3. Si es Imagen con Texto OCR
    texto_evaluar = f"{texto_ocr} {texto_msg}".strip().lower()
    if texto_evaluar:
        for regla in REGLAS_INTENCION_TEXTO:
            if re.search(regla["regex"], texto_evaluar, re.IGNORECASE):
                # Chequear si tiene reacciones que modulen la polaridad
                pol = regla["polaridad"]
                if "🤣" in reacciones or "😂" in reacciones:
                    emocion = "HUMOR_SARCASMO"
                    intencion = "MEME_HUMOR_SATIRA"
                else:
                    emocion = regla["emocion"]
                    intencion = regla["intencion"]
                return intencion, emocion, pol

    # 4. Imagen sin texto detectable (Meme, foto de pizarra o captura generica)
    if any(e in reacciones for e in ["🤣", "😂", "🤡"]):
        return "MEME_HUMOR_SATIRA", "HUMOR_SARCASMO", 0.8
    elif any(e in reacciones for e in ["😭", "💀", "💔"]):
        return "QUEJA_DESESPERACION", "FRUSTRACION_ESTRES", -1.5
    elif any(e in reacciones for e in ["👍", "❤️", "🔥"]):
        return "APROBACION_CELEBRACION", "APROBACION_APOYO", 1.2

    if texto_ocr:
        return "CAPTURA_DOCUMENTAL_OTRO", "NEUTRAL_INFORMATIVO", 0.0
    else:
        return "IMAGEN_FOTOGRAFICA_GENERAL", "NEUTRAL_VISUAL", 0.0

def procesar_ocr_masivo(workspace_dir, photos_to_process, ocr_cache, ocr_cache_path):
    if not TESSERACT_AVAILABLE:
        print("[!] Tesseract OCR no está disponible. Se conservará la caché existente.")
        return ocr_cache

    total = len(photos_to_process)
    print(f"\n[+] Iniciando OCR masivo sobre {total} imagenes unicas pendientes...")
    print("    Utilizando ThreadPoolExecutor (8 hilos en paralelo)...")

    t0 = time.time()
    completados = 0

    def worker_ocr(item):
        rel_path, abs_path = item
        try:
            img = Image.open(abs_path)
            # Timeout preventivo por imagen
            txt = pytesseract.image_to_string(img, lang="spa", timeout=8)
            clean_txt = clean_ocr(txt)
            return rel_path, clean_txt
        except Exception:
            return rel_path, ""

    with ThreadPoolExecutor(max_workers=8) as executor:
        for rel_path, clean_txt in executor.map(worker_ocr, photos_to_process):
            ocr_cache[rel_path] = clean_txt
            completados += 1
            if completados % 200 == 0 or completados == total:
                elapsed = time.time() - t0
                pct = (completados / total) * 100
                print(f"    -> Progreso OCR: {completados}/{total} ({pct:.1f}%) | Tiempo transcurrido: {elapsed:.1f}s")
                # Guardado intermedio de seguridad
                with open(ocr_cache_path, "w", encoding="utf-8") as f:
                    json.dump(ocr_cache, f, ensure_ascii=False, indent=2)

    total_time = time.time() - t0
    print(f"[OK] OCR masivo completado en {total_time:.1f} segundos ({total_time/max(total,1):.2f} s/foto).")
    return ocr_cache

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_root = os.path.dirname(script_dir)
    media_dir = os.path.join(data_root, "media")
    photos_dir = os.path.join(media_dir, "photos")
    processed_dir = os.path.join(data_root, "processed")
    data_dir = processed_dir if os.path.exists(processed_dir) else data_root

    master_csv = os.path.join(data_dir, "dataset_telegram_master.csv")
    ocr_cache_path = os.path.join(data_dir, "ocr_cache.json")

    print("=========================================================================")
    print(" PIPELINE MULTIMODAL DE SENTIMIENTO E INTENCION (FOTOS, STICKERS, GIFS)")
    print("=========================================================================")

    # 1. Cargar cache OCR existente
    ocr_cache = {}
    if os.path.exists(ocr_cache_path):
        with open(ocr_cache_path, "r", encoding="utf-8") as f:
            ocr_cache = json.load(f)
    print(f"[i] Cache OCR inicial: {len(ocr_cache)} imagenes ya procesadas.")

    # 2. Cargar Dataset Maestro
    with open(master_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        master_rows = list(reader)

    # 3. Mapear imagenes unicas por hash MD5
    md5_to_cached = {}
    for rel_path, txt in ocr_cache.items():
        abs_p = os.path.join(media_dir, rel_path.replace("/", os.sep))
        if not os.path.exists(abs_p):
            abs_p = os.path.join(data_root, rel_path.replace("/", os.sep))
        if os.path.exists(abs_p):
            try:
                with open(abs_p, "rb") as fp:
                    h = hashlib.md5(fp.read()).hexdigest()
                    md5_to_cached[h] = txt
            except Exception:
                pass

    photos_to_process = []
    seen_hashes_to_process = set()

    for r in master_rows:
        if r.get("tiene_imagen") in ["True", "1", True]:
            rel_p = r.get("ruta_imagen", "").replace("\\", "/")
            if rel_p:
                norm_rel = rel_p.replace("/", os.sep)
                abs_p = os.path.join(media_dir, norm_rel)
                if not os.path.exists(abs_p):
                    abs_p = os.path.join(data_root, norm_rel)
                if os.path.exists(abs_p):
                    # Chequear si ya está en cache
                    if rel_p not in ocr_cache:
                        with open(abs_p, "rb") as fp:
                            h = hashlib.md5(fp.read()).hexdigest()
                        if h in md5_to_cached:
                            # Reutilizar texto del hash duplicado
                            ocr_cache[rel_p] = md5_to_cached[h]
                        elif h not in seen_hashes_to_process:
                            seen_hashes_to_process.add(h)
                            photos_to_process.append((rel_p, abs_p))

    # 4. Ejecutar OCR masivo sobre pendientes
    if photos_to_process:
        ocr_cache = procesar_ocr_masivo(media_dir, photos_to_process, ocr_cache, ocr_cache_path)
    else:
        print("[OK] Todas las imagenes ya cuentan con texto OCR en caché.")

    # Guardar cache consolidada definitiva
    with open(ocr_cache_path, "w", encoding="utf-8") as f:
        json.dump(ocr_cache, f, ensure_ascii=False, indent=2)

    # 5. Generar Catálogo Multimodal de Imágenes, Stickers y GIFs
    multimodal_catalog_rows = []
    
    print("\n[+] Construyendo Catálogo Multimodal con Intención y Sentimiento...")

    for r in master_rows:
        mid = r.get("mensaje_id")
        fecha = r.get("fecha")
        usuario = r.get("usuario_nombre")
        docente = r.get("docente_mencionado", "Ninguno")
        materia = r.get("materia_mencionada", "Ninguna")
        reacciones = r.get("reacciones_resumen", "")
        texto_msg = r.get("texto_limpio", "")

        tiene_img = r.get("tiene_imagen") in ["True", "1", True]
        es_stk = r.get("es_sticker") in ["True", "1", True]
        es_gif = r.get("es_gif") in ["True", "1", True]

        if not (tiene_img or es_stk or es_gif):
            continue

        ruta_img = r.get("ruta_imagen", "").replace("\\", "/")
        texto_ocr = ocr_cache.get(ruta_img, "") if tiene_img else ""

        stk_emoji = r.get("sticker_emoji", "")
        stk_emo = r.get("sticker_emocion", "")
        gif_nom = r.get("gif_nombre", "")
        archivo_adj = r.get("archivo_adjunto", "")

        if tiene_img:
            tipo_medio = "FOTO_IMAGEN"
            recurso_path = ruta_img
        elif es_stk:
            tipo_medio = "STICKER"
            recurso_path = f"sticker_{stk_emoji}"
        elif es_gif:
            tipo_medio = "ANIMACION_GIF"
            recurso_path = archivo_adj
        else:
            tipo_medio = "OTRO"
            recurso_path = ""

        # Clasificación de Intención y Sentimiento
        intencion, emocion, polaridad = clasificar_multimodal(
            texto_ocr=texto_ocr,
            texto_msg=texto_msg,
            sticker_emoji=stk_emoji,
            sticker_emocion=stk_emo,
            es_gif=es_gif,
            gif_nombre=gif_nom,
            reacciones=reacciones
        )

        # Actualizar datos en fila maestra
        r["imagen_texto_ocr"] = texto_ocr
        r["multimodal_intencion"] = intencion
        r["multimodal_emocion"] = emocion
        r["multimodal_polaridad"] = polaridad

        # Construir fila para catálogo multimodal
        multimodal_catalog_rows.append({
            "mensaje_id": mid,
            "fecha": fecha,
            "usuario_nombre": usuario,
            "tipo_medio": tipo_medio,
            "recurso_path": recurso_path,
            "intencion_multimodal": intencion,
            "emocion_visual": emocion,
            "polaridad_score": round(polaridad, 2),
            "docente_asociado": docente,
            "materia_asociada": materia,
            "texto_ocr_extraido": texto_ocr,
            "texto_mensaje_acompanante": texto_msg,
            "reacciones_sociales": reacciones
        })

    # 6. Exportar catalogo_multimodal_imagenes_stickers.csv
    out_multimodal_csv = os.path.join(data_dir, "catalogo_multimodal_imagenes_stickers.csv")
    if multimodal_catalog_rows:
        fields = list(multimodal_catalog_rows[0].keys())
        with open(out_multimodal_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(multimodal_catalog_rows)
        print(f"[OK] Guardado Catálogo Multimodal Unificado: {out_multimodal_csv} ({len(multimodal_catalog_rows)} registros)")

    # 7. Actualizar dataset_telegram_master.csv
    if master_rows:
        master_fields = list(master_rows[0].keys())
        with open(master_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=master_fields, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(master_rows)
        print(f"[OK] Actualizado Dataset Maestro con OCR total y métricas multimodales: {master_csv}")

    # 8. Limpiar archivos obsoletos
    archivos_obsoletos = [
        os.path.join(data_dir, "catalogo_gifs_animaciones.csv") # Superado completamente por el catalogo multimodal
    ]
    for obs in archivos_obsoletos:
        if os.path.exists(obs):
            try:
                os.remove(obs)
                print(f"[OK] Archivo obsoleto eliminado: {obs}")
            except Exception as e:
                print(f"[!] No se pudo eliminar {obs}: {e}")

    # 9. Resumen Analitico de Intenciones y Emociones
    intenciones_stat = defaultdict(int)
    emociones_stat = defaultdict(int)
    for row in multimodal_catalog_rows:
        intenciones_stat[row["intencion_multimodal"]] += 1
        emociones_stat[row["emocion_visual"]] += 1

    print("\n=========================================================================")
    print(" RESUMEN ANALITICO MULTIMODAL (FOTOS + STICKERS + GIFS)")
    print("=========================================================================")
    print("\n--- DISTRIBUCION DE INTENCIONES MULTIMODALES ---")
    for k, v in sorted(intenciones_stat.items(), key=lambda x: x[1], reverse=True):
        print(f"  * {k}: {v} elementos")

    print("\n--- DISTRIBUCION DE EMOCIONES VISUALES ---")
    for k, v in sorted(emociones_stat.items(), key=lambda x: x[1], reverse=True):
        print(f"  * {k}: {v} elementos")
    print("=========================================================================\n")

if __name__ == "__main__":
    main()
