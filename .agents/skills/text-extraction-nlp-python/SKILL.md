---
name: text-extraction-nlp-python
description: >-
  Guía y procedimientos para extracción de texto, minería de datos textuales,
  procesamiento de lenguaje natural (PLN), modelado de temas (LDA), cálculo
  de TF-IDF, análisis de sentimientos (NRC) y web scraping utilizando el
  ecosistema de librerías de Python (spaCy, NLTK, scikit-learn, Gensim,
  BeautifulSoup, NRCLex y Pandas). Usar cuando el usuario solicite implementar,
  refactorizar o ejecutar flujos de NLP en Python a partir de documentos, textos
  crudos o páginas web.
---

# Skill: Extracción de Texto y PLN en Python (Text Mining & NLP)

Esta skill proporciona un protocolo estructurado y modular para procesar datos textuales no estructurados y ejecutar tareas avanzadas de Minería de Texto en Python. Transforma las técnicas tradicionales de R (`tidytext`, `tm`, `syuzhet`, `topicmodels`) al ecosistema moderno y escalable de Python (`spaCy`, `NLTK`, `scikit-learn`, `Gensim`, `BeautifulSoup4`, `NRCLex`, `matplotlib`/`seaborn`).

---

## 🗂️ Arquitectura Modular de la Skill (Progressive Disclosure)

Para optimizar el uso de tokens y permitir consultas específicas bajo demanda, esta skill se organiza en módulos de referencia especializados:

*   **[Módulo 1: Tokenización y Preprocesamiento](./references/01_tokenization_preprocessing.md)**
    *   Tokenización por palabras, oraciones, caracteres y subpalabras.
    *   Filtrado avanzado de Stop Words y normalización morfológica (lematización vs. stemming).
*   **[Módulo 2: Lingüística Superficial y Ponderación TF-IDF](./references/02_shallow_linguistics_tfidf.md)**
    *   Conteos de frecuencias, n-gramas (bigramas, trigramas).
    *   Cálculo matemático manual vs. vectorización industrial con `TfidfVectorizer` de `scikit-learn`.
*   **[Módulo 3: Modelado de Temas (Topic Modeling LDA)](./references/03_topic_modeling_lda.md)**
    *   Construcción de matrices término-documento (DTM).
    *   Latent Dirichlet Allocation (LDA) con `scikit-learn` y `Gensim`.
    *   Extracción e interpretación de distribuciones $\beta$ (palabra-tema) y $\gamma$ (documento-tema).
*   **[Módulo 4: Reconocimiento de Entidades (NER), Georreferenciación y Sentimientos](./references/04_ner_geotagging_sentiments.md)**
    *   NER con `spaCy` (identificación de entidades geográficas `LOC`/`GPE`, personas, organizaciones).
    *   Georreferenciación cartográfica con `geopy` y `matplotlib`/`folium`.
    *   Análisis de sentimientos y emociones con léxico NRC (`NRCLex`), `VADER` y `TextBlob`.
*   **[Módulo 5: Adquisición Web (Web Crawling y Scraping Ético)](./references/05_web_scraping_crawling.md)**
    *   Extracción selectiva del DOM HTML con `BeautifulSoup` y `requests`.
    *   Rastreador recursivo (Crawler) con respeto a `robots.txt` y límites de cortesía.

---

## 🧭 Matriz de Selección de Librerías Python

| Tarea de PLN | Librería Python Recomendada | Alternativa / Complemento | Reemplazo de paquete R |
|---|---|---|---|
| **Tokenización y POS** | `spacy` (`es_core_news_sm`/`md`) | `nltk.tokenize` | `tidytext::unnest_tokens` |
| **Limpieza / Stopwords** | `nltk.corpus.stopwords` | Listas de `spacy` o `stopwords-iso` | `tidytext::get_stopwords` |
| **Lematización** | `spacy` (token.lemma_) | `nltk.stem.SnowballStemmer` | `hunspell` / `SnowballC` |
| **TF-IDF & N-gramas** | `sklearn.feature_extraction.text.TfidfVectorizer` | Implementación manual NumPy/Pandas | `tidytext::bind_tf_idf` |
| **Topic Modeling (LDA)** | `sklearn.decomposition.LatentDirichletAllocation` | `gensim.models.LdaModel` | `topicmodels::LDA` |
| **NER (Entidades)** | `spacy` (`doc.ents`) | `nltk.ne_chunk` | Extracción manual / `openNLP` |
| **Sentimientos (NRC)** | `nrclex` / `textblob` | `nltk.sentiment.vader` | `syuzhet::get_nrc_sentiment` |
| **Visualización** | `seaborn` / `matplotlib` | `pyLDAvis` / `folium` | `ggplot2` |
| **Web Scraping** | `beautifulsoup4` + `requests` | `Scrapy` / `playwright` | `rvest` / `httr` |

---

## ⚡ Protocolo de Ejecución de Tareas en 4 Pasos

Cuando se reciba una tarea de PLN en Python, seguir este flujo de trabajo:

1.  **Ingesta y Normalización:**
    *   Cargar texto o scrapear fuentes con `requests` + `BeautifulSoup`.
    *   Convertir a estructuras tabulares con `pandas.DataFrame`.
    *   Consultar [Módulo 1](./references/01_tokenization_preprocessing.md) y [Módulo 5](./references/05_web_scraping_crawling.md).
2.  **Filtrado y Vectorización:**
    *   Aplicar tokenización y remover palabras vacías con listas estándar o vocabulario personalizado.
    *   Generar matriz DTM / TF-IDF mediante `TfidfVectorizer` o `CountVectorizer`.
    *   Consultar [Módulo 2](./references/02_shallow_linguistics_tfidf.md).
3.  **Modelado y Extracción de Información:**
    *   Para descubrimiento de tópicos: ajustar `LatentDirichletAllocation` de scikit-learn o `gensim`.
    *   Para entidades y emociones: ejecutar pipeline de `spaCy` y clasificador `NRCLex`.
    *   Consultar [Módulo 3](./references/03_topic_modeling_lda.md) y [Módulo 4](./references/04_ner_geotagging_sentiments.md).
4.  **Validación y Exportación:**
    *   Exportar métricas y dataframes limpios a `.csv` o `.json`.
    *   Generar gráficos de distribución de tópicos o emociones guardándolos en `.png`.
