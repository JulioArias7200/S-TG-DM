# -*- coding: utf-8 -*-
"""
data/scripts/07_pipeline_nlp_avanzado.py
========================================
Pipeline Integral de Procesamiento de Lenguaje Natural (PLN):
1. TF-IDF Multidimensional (Docentes, Materias, Ciclos Académicos y Cohortes Temporales).
2. Topic Modeling con Latent Dirichlet Allocation (LDA k=4, Matrices Beta y Gamma).
3. Análisis Dual de Sentimientos y Emociones:
   a) Heurístico Nativo Context-Aware (SIN librerías externas):
      - Léxico propio UMSA/Bolivia (5 estados emocionales)
      - Ventana deslizante de 3 tokens con detección de inversores ("no es barco"),
        intensificadores ("recontra yuca") y atenuadores.
   b) Basado en Librerías: NRCLex para las 8 emociones de Plutchik adaptado al español.
4. Exportación estandarizada en data/processed/ lista para Neon Serverless PostgreSQL.
"""
import os
import sys
import json
import re
import unicodedata
from collections import Counter
import pandas as pd
import numpy as np

# Configuración de salida para Windows PowerShell
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import nltk
from nltk.corpus import stopwords
from nrclex import NRCLex

# Rutas base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed")

MASTER_CSV_PATH = os.path.join(DATA_PROCESSED, "dataset_telegram_master.csv")
MENCIONES_CSV_PATH = os.path.join(DATA_PROCESSED, "dataset_menciones_docentes.csv")
DOCENTES_CAT_PATH = os.path.join(DATA_PROCESSED, "catalogo_docentes_umsa.csv")
MATERIAS_CAT_PATH = os.path.join(DATA_PROCESSED, "catalogo_materias_umsa.csv")

# Archivos de salida
LEXICO_UMSA_PATH = os.path.join(DATA_PROCESSED, "lexico_emociones_umsa.json")
NRC_SPANISH_PATH = os.path.join(DATA_PROCESSED, "nrc_spanish_lexicon.json")
TFIDF_DOCENTES_PATH = os.path.join(DATA_PROCESSED, "tfidf_docentes_ranking.csv")
TFIDF_MATERIAS_PATH = os.path.join(DATA_PROCESSED, "tfidf_materias_ranking.csv")
TFIDF_CICLOS_PATH = os.path.join(DATA_PROCESSED, "tfidf_ciclos_academicos.csv")
TFIDF_CONSOLIDADO_PATH = os.path.join(DATA_PROCESSED, "tfidf_entidades_consolidado.csv")
LDA_TOPICOS_PATH = os.path.join(DATA_PROCESSED, "lda_topicos_vocabulario.csv")


def normalizar_texto(texto):
    """Limpia caracteres especiales, minúsculas y normaliza espacios."""
    if not isinstance(texto, str) or not texto.strip():
        return ""
    txt = texto.lower()
    # Eliminar URLs
    txt = re.sub(r'https?://\S+|www\.\S+', ' ', txt)
    # Conservar caracteres alfabéticos, tildes y eñes
    txt = re.sub(r'[^a-záéíóúñü\s]', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt


def construir_lexico_propio_umsa():
    """
    Construye y exporta el diccionario léxico contextual de emociones UMSA
    con pesos, polaridades e intensidades en 5 categorías académicas.
    """
    lexico = {
        "alivio_aprobacion": {
            "terminos": [
                "barco", "salvar", "salve", "salvó", "salvado", "salvando", "aprueba", "aprobé", "aprobado", 
                "aprobacion", "facil", "facilito", "facilita", "regalo", "regalado", "regala", "regalaba",
                "tranqui", "tranquilo", "tranquila", "tranquis", "accesible", "suave", "pichi", "pan comido",
                "llevadera", "llevadero", "chicha", "regalito", "relax", "alivio", "descanso", "pasamos"
            ],
            "peso_base": 1.2,
            "polaridad": 1.0
        },
        "frustracion_dificultad": {
            "terminos": [
                "fregado", "fregada", "friega", "fregar", "pesado", "pesada", "yuca", "complicado", "complicada",
                "dificil", "dificultad", "matador", "matadora", "filtro", "tirarse", "tiraron", "tire", "reprobar",
                "reprobado", "reprobada", "reprobo", "jalado", "jalada", "aplazado", "aplazada", "aplaza", "llanto",
                "llorar", "rip", "muerto", "morir", "masacre", "pesadilla", "desastre", "perdicion", "fui"
            ],
            "peso_base": 1.3,
            "polaridad": -1.0
        },
        "incertidumbre_ansiedad": {
            "terminos": [
                "parcial", "segundo parcial", "primer parcial", "final", "examen", "recuperatorio", "mesa", "2t",
                "segundo turno", "nota", "notas", "cuanto falta", "cuando salen", "actas", "kardex", "habilitado",
                "habilitada", "habilitacion", "alcanza", "reclamo", "asustado", "asustada", "miedo", "nervios",
                "duda", "preocupado", "preocupada", "rezar", "fe", "auxi", "auxiliar", "auxiliatura", "ponderacion"
            ],
            "peso_base": 1.0,
            "polaridad": -0.2
        },
        "conformidad_recomendacion": {
            "terminos": [
                "recomiendo", "recomendado", "recomendada", "conviene", "buen docente", "buena docente", "buen profe",
                "buena onda", "capo", "capa", "capisimo", "crack", "enseña bien", "explica bien", "legal",
                "justo", "justa", "amable", "comprensivo", "comprensiva", "puntual", "vale la pena", "excelente",
                "buenisimo", "buenisima", "sabe mucho", "dominio", "genio", "didactico", "didactica", "agradecido"
            ],
            "peso_base": 1.4,
            "polaridad": 1.0
        },
        "descontento_critica": {
            "terminos": [
                "no enseña", "no explica", "falton", "faltona", "no viene", "no asiste", "aburrido", "aburrida",
                "prepotente", "soberbio", "soberbia", "chanta", "injusto", "injusta", "anula", "abuso", "queja",
                "no te conviene", "peor", "asco", "rabia", "estafa", "pierde tiempo", "renegon", "renegona",
                "grita", "botado", "botada", "payaso", "circo", "desorden", "no sube notas"
            ],
            "peso_base": 1.5,
            "polaridad": -1.0
        }
    }

    with open(LEXICO_UMSA_PATH, "w", encoding="utf-8") as f:
        json.dump(lexico, f, ensure_ascii=False, indent=2)
    print(f"[*] Léxico propio UMSA generado: {LEXICO_UMSA_PATH}")
    return lexico


def construir_lexico_nrc_espanol(lexico_umsa):
    """
    Construye un léxico NRC estructurado en español compatible con NRCLex
    para capturar las 8 emociones de Plutchik + polaridades.
    """
    # Mapeo base de términos castellanos frecuentes hacia Plutchik 8
    nrc_base = {
        # Joy (alegría)
        "feliz": ["joy", "positive"], "felicidad": ["joy", "positive"], "alegre": ["joy", "positive"],
        "contento": ["joy", "positive"], "contenta": ["joy", "positive"], "aprobé": ["joy", "positive"],
        "aprobado": ["joy", "positive"], "éxito": ["joy", "positive"], "genial": ["joy", "positive"],
        "excelente": ["joy", "positive"], "celebrar": ["joy", "positive"], "salvé": ["joy", "positive"],
        # Trust (confianza)
        "recomiendo": ["trust", "positive"], "confianza": ["trust", "positive"], "bueno": ["trust", "positive"],
        "buena": ["trust", "positive"], "justo": ["trust", "positive"], "legal": ["trust", "positive"],
        "apoyo": ["trust", "positive"], "consejo": ["trust", "positive"], "seguro": ["trust", "positive"],
        "verdad": ["trust", "positive"], "amigo": ["trust", "positive"], "auxiliar": ["trust", "positive"],
        # Fear (miedo)
        "miedo": ["fear", "negative"], "asustado": ["fear", "negative"], "peligro": ["fear", "negative"],
        "reprobar": ["fear", "negative"], "matador": ["fear", "negative"], "amenaza": ["fear", "negative"],
        "grave": ["fear", "negative"], "nervios": ["fear", "negative"], "terror": ["fear", "negative"],
        # Sadness (tristeza)
        "triste": ["sadness", "negative"], "tristeza": ["sadness", "negative"], "pena": ["sadness", "negative"],
        "llanto": ["sadness", "negative"], "llorar": ["sadness", "negative"], "jalado": ["sadness", "negative"],
        "reprobé": ["sadness", "negative"], "perdido": ["sadness", "negative"], "decepcion": ["sadness", "negative"],
        "depresion": ["sadness", "negative"], "muerto": ["sadness", "negative"], "rip": ["sadness", "negative"],
        # Anger (ira)
        "ira": ["anger", "negative"], "rabia": ["anger", "negative"], "bronca": ["anger", "negative"],
        "odio": ["anger", "negative"], "molesto": ["anger", "negative"], "enojado": ["anger", "negative"],
        "injusto": ["anger", "negative"], "abuso": ["anger", "negative"], "estafa": ["anger", "negative"],
        "prepotente": ["anger", "negative"], "robo": ["anger", "negative"], "reniego": ["anger", "negative"],
        # Disgust (disgusto)
        "asco": ["disgust", "negative"], "desagradable": ["disgust", "negative"], "chanta": ["disgust", "negative"],
        "mentira": ["disgust", "negative"], "falso": ["disgust", "negative"], "horrible": ["disgust", "negative"],
        "pesadilla": ["disgust", "negative"], "pesado": ["disgust", "negative"], "sucio": ["disgust", "negative"],
        # Anticipation (anticipación)
        "espera": ["anticipation"], "esperando": ["anticipation"], "parcial": ["anticipation"],
        "examen": ["anticipation"], "futuro": ["anticipation"], "preparar": ["anticipation"],
        "estudiar": ["anticipation"], "horario": ["anticipation"], "inscripcion": ["anticipation"],
        "fecha": ["anticipation"], "mañana": ["anticipation"], "kardex": ["anticipation"],
        # Surprise (sorpresa)
        "sorpresa": ["surprise"], "inesperado": ["surprise"], "increible": ["surprise"],
        "asombro": ["surprise"], "milagro": ["surprise", "positive"], "apareció": ["surprise"]
    }

    # Integrar jergas UMSA al léxico NRC
    for termino in lexico_umsa["alivio_aprobacion"]["terminos"]:
        if termino not in nrc_base:
            nrc_base[termino] = ["joy", "trust", "positive"]
    for termino in lexico_umsa["conformidad_recomendacion"]["terminos"]:
        if termino not in nrc_base:
            nrc_base[termino] = ["trust", "positive"]
    for termino in lexico_umsa["frustracion_dificultad"]["terminos"]:
        if termino not in nrc_base:
            nrc_base[termino] = ["fear", "sadness", "negative"]
    for termino in lexico_umsa["descontento_critica"]["terminos"]:
        if termino not in nrc_base:
            nrc_base[termino] = ["anger", "disgust", "negative"]
    for termino in lexico_umsa["incertidumbre_ansiedad"]["terminos"]:
        if termino not in nrc_base:
            nrc_base[termino] = ["anticipation", "fear"]

    with open(NRC_SPANISH_PATH, "w", encoding="utf-8") as f:
        json.dump(nrc_base, f, ensure_ascii=False, indent=2)
    print(f"[*] Léxico NRC Español compilado: {NRC_SPANISH_PATH} ({len(nrc_base)} vocablos)")
    return nrc_base


class AnalizadorSentimientosUMSANativo:
    """
    Parser Context-Aware Heurístico (SIN librerías externas de inferencia).
    Implementa ventana deslizante hacia atrás de 3 tokens con detección de:
    - Inversores de polaridad ("no", "nunca", "jamas", "ni", "tampoco", "sin")
    - Intensificadores ("muy", "re", "contra", "super", "demasiado", "harto", "full", "bien")
    - Atenuadores ("poco", "medio", "algo", "apenas", "casi")
    """
    def __init__(self, lexico_umsa):
        self.lexico = lexico_umsa
        self.inversores = {"no", "nunca", "jamas", "jamás", "ni", "tampoco", "sin"}
        self.intensificadores = {
            "muy": 2.0, "re": 1.8, "contra": 1.8, "recontra": 2.2, "super": 1.8, "súper": 1.8,
            "demasiado": 2.0, "demas": 1.5, "harto": 1.8, "full": 1.7, "bien": 1.6, "bastante": 1.6,
            "ultra": 2.0, "totalmente": 1.8, "extremadamente": 2.2
        }
        self.atenuadores = {
            "poco": 0.5, "medio": 0.6, "algo": 0.6, "apenas": 0.5, "casi": 0.6, "relativamente": 0.7
        }

        # Índice plano de términos para búsqueda rápida
        self.terminos_index = {}
        for categoria, data in self.lexico.items():
            peso_cat = data["peso_base"]
            pol_cat = data["polaridad"]
            for term in data["terminos"]:
                self.terminos_index[term.lower()] = {
                    "categoria": categoria,
                    "peso": peso_cat,
                    "polaridad": pol_cat
                }

    def analizar(self, texto):
        """Retorna puntuación continua [-1.0, 1.0], categoría de sentimiento y emoción dominante."""
        if not isinstance(texto, str) or not texto.strip():
            return {
                "sentimiento": "neutral",
                "score": 0.0,
                "emocion": "neutral",
                "scores_emociones": {}
            }

        txt_clean = normalizar_texto(texto)
        tokens = txt_clean.split()
        if not tokens:
            return {
                "sentimiento": "neutral",
                "score": 0.0,
                "emocion": "neutral",
                "scores_emociones": {}
            }

        scores_emociones = {cat: 0.0 for cat in self.lexico.keys()}
        total_polaridad = 0.0
        conteo_matches = 0

        # Evaluar n-gramas de 1 y 2 palabras
        i = 0
        n_tokens = len(tokens)
        while i < n_tokens:
            match_found = False
            token_actual = tokens[i]
            bigrama = f"{tokens[i]} {tokens[i+1]}" if i + 1 < n_tokens else None

            termino_match = None
            salto = 1

            if bigrama and bigrama in self.terminos_index:
                termino_match = bigrama
                salto = 2
            elif token_actual in self.terminos_index:
                termino_match = token_actual
                salto = 1

            if termino_match:
                info = self.terminos_index[termino_match]
                cat = info["categoria"]
                base_peso = info["peso"]
                base_pol = info["polaridad"]

                # Analizar ventana deslizante de 3 tokens previos
                inicio_ventana = max(0, i - 3)
                ventana = tokens[inicio_ventana:i]

                es_invertido = False
                multiplicador = 1.0

                for w in ventana:
                    if w in self.inversores:
                        es_invertido = True
                    if w in self.intensificadores:
                        multiplicador *= self.intensificadores[w]
                    elif w in self.atenuadores:
                        multiplicador *= self.atenuadores[w]

                # Aplicar inversión contextual
                if es_invertido:
                    base_pol = -base_pol
                    # Reasignar emoción antagónica si fue negada
                    if cat == "alivio_aprobacion":
                        cat_ajustada = "frustracion_dificultad"
                    elif cat == "conformidad_recomendacion":
                        cat_ajustada = "descontento_critica"
                    elif cat == "frustracion_dificultad":
                        cat_ajustada = "alivio_aprobacion"
                    elif cat == "descontento_critica":
                        cat_ajustada = "conformidad_recomendacion"
                    else:
                        cat_ajustada = cat
                else:
                    cat_ajustada = cat

                impacto = base_peso * multiplicador
                scores_emociones[cat_ajustada] += impacto
                total_polaridad += (base_pol * impacto)
                conteo_matches += 1
                i += salto
            else:
                i += 1

        if conteo_matches == 0:
            return {
                "sentimiento": "neutral",
                "score": 0.0,
                "emocion": "neutral",
                "scores_emociones": scores_emociones
            }

        # Normalización matemática de polaridad en [-1.0, 1.0]
        score_normalizado = np.tanh(total_polaridad / (conteo_matches * 1.5))
        score_normalizado = round(float(score_normalizado), 4)

        if score_normalizado > 0.15:
            sentimiento = "positivo"
        elif score_normalizado < -0.15:
            sentimiento = "negativo"
        else:
            sentimiento = "neutral"

        # Emoción dominante propia
        max_emocion = max(scores_emociones, key=scores_emociones.get)
        if scores_emociones[max_emocion] <= 0:
            emocion_dominante = "neutral"
        else:
            emocion_dominante = max_emocion

        return {
            "sentimiento": sentimiento,
            "score": score_normalizado,
            "emocion": emocion_dominante,
            "scores_emociones": {k: round(v, 2) for k, v in scores_emociones.items()}
        }


def calcular_tfidf_multidimensional(df_master, df_menciones, stop_words_custom):
    """
    Calcula matrices TF-IDF agrupadas por:
    1. Docente (85 docentes)
    2. Materia (158 materias)
    3. Ciclo Académico (Básico, Intermedio, Superior)
    4. Cohorte Temporal (Años 2020 a 2026)
    """
    print("\n--- Ejecutando TF-IDF Multidimensional ---")
    tfidf_records = []

    # 1. TF-IDF por Docente
    print("[1/4] TF-IDF por Docente...")
    menciones_agrupadas = df_menciones.groupby("docente_mencionado")["contenido_multimodal_unificado"].apply(
        lambda s: " ".join([normalizar_texto(str(x)) for x in s if str(x).strip()])
    ).reset_index()

    if len(menciones_agrupadas) > 1:
        vec_docentes = TfidfVectorizer(
            stop_words=stop_words_custom,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.85
        )
        tfidf_mat = vec_docentes.fit_transform(menciones_agrupadas["contenido_multimodal_unificado"])
        vocab = np.array(vec_docentes.get_feature_names_out())

        docentes_tfidf_rows = []
        for idx, row in menciones_agrupadas.iterrows():
            docente_nom = row["docente_mencionado"]
            row_vector = tfidf_mat[idx].toarray().flatten()
            if row_vector.max() == 0:
                continue
            top_indices = row_vector.argsort()[:-16:-1]
            for rank, term_idx in enumerate(top_indices, 1):
                score = round(float(row_vector[term_idx]), 4)
                if score > 0:
                    rec = {
                        "entidad_tipo": "DOCENTE",
                        "entidad_id": docente_nom,
                        "termino": vocab[term_idx],
                        "score_tfidf": score,
                        "ranking_pos": rank
                    }
                    tfidf_records.append(rec)
                    docentes_tfidf_rows.append(rec)

        df_doc_tfidf = pd.DataFrame(docentes_tfidf_rows)
        df_doc_tfidf.to_csv(TFIDF_DOCENTES_PATH, index=False, encoding="utf-8-sig")
        print(f"    -> Exportado: {TFIDF_DOCENTES_PATH} ({len(df_doc_tfidf)} registros)")

    # 2. TF-IDF por Materia
    print("[2/4] TF-IDF por Materia...")
    materias_agrupadas = df_master.dropna(subset=["materia_mencionada"]).groupby("materia_mencionada")["contenido_multimodal_unificado"].apply(
        lambda s: " ".join([normalizar_texto(str(x)) for x in s if str(x).strip()])
    ).reset_index()

    if len(materias_agrupadas) > 1:
        vec_materias = TfidfVectorizer(
            stop_words=stop_words_custom,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.85
        )
        tfidf_mat_mat = vec_materias.fit_transform(materias_agrupadas["contenido_multimodal_unificado"])
        vocab_mat = np.array(vec_materias.get_feature_names_out())

        materias_tfidf_rows = []
        for idx, row in materias_agrupadas.iterrows():
            mat_nom = row["materia_mencionada"]
            row_vector = tfidf_mat_mat[idx].toarray().flatten()
            if row_vector.max() == 0:
                continue
            top_indices = row_vector.argsort()[:-16:-1]
            for rank, term_idx in enumerate(top_indices, 1):
                score = round(float(row_vector[term_idx]), 4)
                if score > 0:
                    rec = {
                        "entidad_tipo": "MATERIA",
                        "entidad_id": mat_nom,
                        "termino": vocab_mat[term_idx],
                        "score_tfidf": score,
                        "ranking_pos": rank
                    }
                    tfidf_records.append(rec)
                    materias_tfidf_rows.append(rec)

        df_mat_tfidf = pd.DataFrame(materias_tfidf_rows)
        df_mat_tfidf.to_csv(TFIDF_MATERIAS_PATH, index=False, encoding="utf-8-sig")
        print(f"    -> Exportado: {TFIDF_MATERIAS_PATH} ({len(df_mat_tfidf)} registros)")

    # 3. TF-IDF por Ciclo Académico (Básico, Intermedio, Superior)
    print("[3/4] TF-IDF por Ciclo Académico...")
    def determinar_ciclo(materia):
        if not isinstance(materia, str) or not materia:
            return "General"
        m = re.search(r'(\d{3})', materia)
        if m:
            num = int(m.group(1))
            if num <= 135:
                return "Ciclo Básico"
            elif num <= 166:
                return "Ciclo Intermedio"
            else:
                return "Ciclo Superior"
        return "Ciclo Básico"

    df_master["ciclo_academico"] = df_master["materia_mencionada"].apply(determinar_ciclo)
    ciclos_agrupados = df_master.groupby("ciclo_academico")["contenido_multimodal_unificado"].apply(
        lambda s: " ".join([normalizar_texto(str(x)) for x in s if str(x).strip()])
    ).reset_index()

    vec_ciclos = TfidfVectorizer(
        stop_words=stop_words_custom,
        ngram_range=(1, 2),
        min_df=1
    )
    tfidf_mat_ciclos = vec_ciclos.fit_transform(ciclos_agrupados["contenido_multimodal_unificado"])
    vocab_ciclos = np.array(vec_ciclos.get_feature_names_out())

    ciclos_tfidf_rows = []
    for idx, row in ciclos_agrupados.iterrows():
        ciclo_nom = row["ciclo_academico"]
        row_vector = tfidf_mat_ciclos[idx].toarray().flatten()
        top_indices = row_vector.argsort()[:-26:-1]
        for rank, term_idx in enumerate(top_indices, 1):
            score = round(float(row_vector[term_idx]), 4)
            if score > 0:
                rec = {
                    "entidad_tipo": "CICLO",
                    "entidad_id": ciclo_nom,
                    "termino": vocab_ciclos[term_idx],
                    "score_tfidf": score,
                    "ranking_pos": rank
                }
                tfidf_records.append(rec)
                ciclos_tfidf_rows.append(rec)

    df_ciclos_tfidf = pd.DataFrame(ciclos_tfidf_rows)
    df_ciclos_tfidf.to_csv(TFIDF_CICLOS_PATH, index=False, encoding="utf-8-sig")
    print(f"    -> Exportado: {TFIDF_CICLOS_PATH} ({len(df_ciclos_tfidf)} registros)")

    # 4. TF-IDF por Año (Temporal)
    print("[4/4] TF-IDF por Cohorte Temporal (Años)...")
    anios_agrupados = df_master.dropna(subset=["anio"]).groupby("anio")["contenido_multimodal_unificado"].apply(
        lambda s: " ".join([normalizar_texto(str(x)) for x in s if str(x).strip()])
    ).reset_index()

    if len(anios_agrupados) > 1:
        vec_anios = TfidfVectorizer(
            stop_words=stop_words_custom,
            ngram_range=(1, 2),
            min_df=1
        )
        tfidf_mat_anios = vec_anios.fit_transform(anios_agrupados["contenido_multimodal_unificado"])
        vocab_anios = np.array(vec_anios.get_feature_names_out())

        for idx, row in anios_agrupados.iterrows():
            anio_val = f"Año {int(row['anio'])}"
            row_vector = tfidf_mat_anios[idx].toarray().flatten()
            top_indices = row_vector.argsort()[:-21:-1]
            for rank, term_idx in enumerate(top_indices, 1):
                score = round(float(row_vector[term_idx]), 4)
                if score > 0:
                    tfidf_records.append({
                        "entidad_tipo": "TEMPORAL",
                        "entidad_id": anio_val,
                        "termino": vocab_anios[term_idx],
                        "score_tfidf": score,
                        "ranking_pos": rank
                    })

    # Guardar consolidado
    df_consolidado = pd.DataFrame(tfidf_records)
    df_consolidado.to_csv(TFIDF_CONSOLIDADO_PATH, index=False, encoding="utf-8-sig")
    print(f"[*] Matriz TF-IDF Consolidada guardada: {TFIDF_CONSOLIDADO_PATH} ({len(df_consolidado)} filas)")
    return df_consolidado


def ejecutar_topic_modeling_lda(df_master, stop_words_custom, k_topics=4):
    """
    Ajusta Latent Dirichlet Allocation (LDA) con k=4 sobre el corpus unificado.
    Extrae la Matriz Beta (vocabulario de temas) y Gamma (asignación por documento).
    """
    print(f"\n--- Ejecutando Topic Modeling LDA (k={k_topics}) ---")

    textos_corpus = df_master["contenido_multimodal_unificado"].fillna("").apply(normalizar_texto)

    # 1. Matriz de Conteo de Términos (CountVectorizer)
    tf_vectorizer = CountVectorizer(
        stop_words=stop_words_custom,
        ngram_range=(1, 2),
        min_df=5,
        max_df=0.60
    )
    dtm = tf_vectorizer.fit_transform(textos_corpus)
    vocab = np.array(tf_vectorizer.get_feature_names_out())
    print(f"[*] DTM construida: {dtm.shape[0]} documentos x {dtm.shape[1]} términos.")

    # 2. Ajustar Modelo LDA
    lda = LatentDirichletAllocation(
        n_components=k_topics,
        learning_method='batch',
        random_state=42,
        max_iter=40,
        n_jobs=-1
    )
    lda.fit(dtm)

    # 3. Matriz Beta: Distribución Término-Tema (Normalizada a probabilidades de Dirichlet)
    matriz_beta = lda.components_ / lda.components_.sum(axis=1)[:, np.newaxis]

    # Asignación de etiquetas conceptuales interpretables según el vocabulario
    etiquetas_topicos = {
        0: "Evaluaciones, Parciales y Exámenes",
        1: "Gestión Académica, Horarios e Inscripción",
        2: "Docencia, Criterios de Aprobación y Dificultad",
        3: "Auxiliaturas, Laboratorios y Consultas Prácticas"
    }

    lda_vocab_records = []
    print("\n=== TÓPICOS LDA DESCUBIERTOS (MATRIZ BETA) ===")
    for topic_idx in range(k_topics):
        topic_dist = matriz_beta[topic_idx]
        top_indices = topic_dist.argsort()[:-21:-1]
        top_words = vocab[top_indices]
        top_probs = topic_dist[top_indices]

        nombre_tema = etiquetas_topicos.get(topic_idx, f"Tema #{topic_idx + 1}")
        print(f"\n[{topic_idx}] {nombre_tema}:")
        for rank, (word, prob) in enumerate(zip(top_words, top_probs), 1):
            if rank <= 5:
                print(f"    - {word}: {prob:.4f}")
            lda_vocab_records.append({
                "topico_id": topic_idx,
                "nombre_etiqueta": nombre_tema,
                "termino": word,
                "beta_prob": round(float(prob), 5),
                "ranking_pos": rank
            })

    df_lda_vocab = pd.DataFrame(lda_vocab_records)
    df_lda_vocab.to_csv(LDA_TOPICOS_PATH, index=False, encoding="utf-8-sig")
    print(f"\n[*] Vocabulario Beta LDA guardado: {LDA_TOPICOS_PATH}")

    # 4. Matriz Gamma: Distribución Documento-Tema
    matriz_gamma = lda.transform(dtm)
    doc_topico_ids = matriz_gamma.argmax(axis=1)
    doc_topico_probs = matriz_gamma.max(axis=1)

    df_master["topico_lda_id"] = doc_topico_ids
    df_master["topico_lda_prob"] = np.round(doc_topico_probs, 4)

    return df_master, df_lda_vocab


def main():
    print("=" * 70)
    print("PIPELINE DE PLN AVANZADO: TF-IDF, TOPIC MODELING Y EMOCIONES DUALES")
    print("=" * 70)

    # 1. Cargar Datasets Maestros
    print(f"[*] Cargando: {MASTER_CSV_PATH}")
    df_master = pd.read_csv(MASTER_CSV_PATH, low_memory=False)
    print(f"    Total mensajes: {len(df_master)}")

    print(f"[*] Cargando: {MENCIONES_CSV_PATH}")
    df_menciones = pd.read_csv(MENCIONES_CSV_PATH, low_memory=False)
    print(f"    Total menciones a docentes: {len(df_menciones)}")

    # 2. Construir léxicos UMSA y NRC
    lexico_umsa = construir_lexico_propio_umsa()
    lexico_nrc = construir_lexico_nrc_espanol(lexico_umsa)

    # 3. Construir lista de Stop Words enriquecida
    nltk_stops = set(stopwords.words("spanish"))
    stops_telegram = {
        "hola", "buenas", "tardes", "dias", "noches", "alguien", "sabe", "grupo", "link",
        "porfa", "favor", "gracias", "muchas", "si", "no", "xd", "bro", "mano", "docente",
        "lic", "licen", "licenciado", "licenciada", "materia", "paralelo", "clase", "clases",
        "aula", "dia", "cada", "mas", "menos", "asi", "ahi", "aqui", "va", "van", "hacer",
        "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "en", "para", "por",
        "con", "sin", "sobre", "del", "al", "que", "se", "es", "son", "fue", "era", "ser"
    }
    stop_words_custom = sorted(list(nltk_stops.union(stops_telegram)))

    # 4. Inicializar Analizadores de Sentimientos
    analizador_nativo = AnalizadorSentimientosUMSANativo(lexico_umsa)
    nrc_analyzer = NRCLex(lexicon_file=NRC_SPANISH_PATH)

    print("\n--- Analizando Sentimientos y Emociones Duales en el Corpus ---")
    
    # Procesar Mensajes del Master
    n_total = len(df_master)
    sent_propios = []
    scores_propios = []
    emociones_propias = []
    nrc_emociones_top = []

    for idx, row in df_master.iterrows():
        txt = str(row["contenido_multimodal_unificado"]) if pd.notna(row["contenido_multimodal_unificado"]) else ""
        
        # a) Análisis Nativo UMSA (Context-Aware 3-tokens)
        res_nativo = analizador_nativo.analizar(txt)
        sent_propios.append(res_nativo["sentimiento"])
        scores_propios.append(res_nativo["score"])
        emociones_propias.append(res_nativo["emocion"])

        # b) Análisis con NRCLex (Léxico Plutchik en Español)
        tokens_txt = normalizar_texto(txt).split()
        if tokens_txt:
            nrc_analyzer.load_token_list(tokens_txt)
            top_emo = nrc_analyzer.top_emotions
            # Filtrar 'positive' y 'negative' de la emoción top para quedarnos con emoción afectiva Plutchik
            emociones_puras = [e for e, s in top_emo if e not in ("positive", "negative") and s > 0]
            if emociones_puras:
                nrc_emociones_top.append(emociones_puras[0])
            elif top_emo and top_emo[0][1] > 0:
                nrc_emociones_top.append(top_emo[0][0])
            else:
                nrc_emociones_top.append("none")
        else:
            nrc_emociones_top.append("none")

        if (idx + 1) % 5000 == 0 or (idx + 1) == n_total:
            print(f"    Procesados {idx + 1}/{n_total} mensajes ({((idx + 1)/n_total)*100:.1f}%)")

    # Asignar al DataFrame Master
    df_master["sentimiento_propio"] = sent_propios
    df_master["sentimiento_propio_score"] = scores_propios
    df_master["emocion_propia"] = emociones_propias
    df_master["nrc_emocion_top"] = nrc_emociones_top

    # 5. Topic Modeling LDA (k=4)
    df_master, df_lda_vocab = ejecutar_topic_modeling_lda(df_master, stop_words_custom, k_topics=4)

    # 6. TF-IDF Multidimensional
    df_tfidf_consolidado = calcular_tfidf_multidimensional(df_master, df_menciones, stop_words_custom)

    # 7. Sincronizar columnas nuevas a dataset_menciones_docentes.csv
    print("\n--- Sincronizando con dataset_menciones_docentes.csv ---")
    cols_enriquecidas = [
        "topico_lda_id", "topico_lda_prob", "sentimiento_propio",
        "sentimiento_propio_score", "emocion_propia", "nrc_emocion_top"
    ]
    df_menciones = df_menciones.drop(columns=[c for c in cols_enriquecidas if c in df_menciones.columns])
    df_menciones = df_menciones.merge(
        df_master[["mensaje_id"] + cols_enriquecidas],
        on="mensaje_id",
        how="left"
    )

    # 8. Guardar DataFrames Enriquecidos con formato UTF-8 con BOM
    print("\n--- Guardando Datasets Enriquecidos ---")
    df_master.to_csv(MASTER_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] Master actualizado: {MASTER_CSV_PATH} ({len(df_master)} filas, {len(df_master.columns)} columnas)")

    df_menciones.to_csv(MENCIONES_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] Menciones actualizado: {MENCIONES_CSV_PATH} ({len(df_menciones)} filas, {len(df_menciones.columns)} columnas)")

    # 9. Resumen Analítico Final
    print("\n" + "=" * 70)
    print("RESUMEN DE RESULTADOS NLP:")
    print("Distribución Sentimiento Propio:")
    print(df_master["sentimiento_propio"].value_counts())
    print("\nDistribución Emoción Propia (Léxico UMSA Context-Aware):")
    print(df_master["emocion_propia"].value_counts())
    print("\nDistribución Top Emociones NRC (Plutchik):")
    print(df_master["nrc_emocion_top"].value_counts().head(8))
    print("\nDistribución Tópicos LDA:")
    print(df_master["topico_lda_id"].value_counts())
    print("=" * 70)
    print("[SUCCESS] Pipeline NLP Completado Exitosamente.")


if __name__ == "__main__":
    main()
