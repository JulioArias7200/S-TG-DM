# Módulo 1: Tokenización y Preprocesamiento de Texto en Python

Este módulo cubre la tokenización en múltiples niveles de granularidad, normalización y eliminación de palabras vacías (*Stop Words*) usando las principales librerías de Python (`spaCy` y `NLTK`).

---

## 1. Niveles de Tokenización

### A. Tokenización por Palabras y Oraciones con spaCy
`spaCy` preserva contracciones, puntuación contextual y etiquetas morfológicas sin romper palabras complejas.

```python
import spacy

# Cargar modelo en español (sm: small, md: medium con vectores)
nlp = spacy.load("es_core_news_sm")

texto = (
    "La política en Bolivia pone triste a la gente. "
    "El partido para el mundial fue una pena. "
    "Las marchas son el pan de cada día."
)

doc = nlp(texto)

# 1. Tokenización por oraciones
print("=== ORACIONES ===")
for i, sent in enumerate(doc.sents, start=1):
    print(f"Oración {i}: {sent.text}")

# 2. Tokenización por palabras con información lingüística
print("\n=== PALABRAS Y POS TAGGING ===")
tokens_info = [(token.text, token.pos_, token.lemma_) for token in doc if not token.is_punct]
for t in tokens_info[:10]:
    print(t)
```

### B. Tokenización con NLTK
```python
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize

# Descargar recursos de NLTK si es la primera vez
nltk.download('punkt')
nltk.download('punkt_tab')

# Tokenización oracional
oraciones = sent_tokenize(texto, language='spanish')

# Tokenización de palabras
palabras = word_tokenize(texto, language='spanish')
print("Total palabras extraídas:", len(palabras))
```

### C. Tokenización por Caracteres y Subpalabras
*   **Por caracteres:** Útil para corrección ortográfica o modelos a nivel de glifo.
    ```python
    caracteres = [char for char in texto if char.strip()]
    ```
*   **Por subpalabras (Hugging Face / Tokenizers):** Esencial para modelos basados en Transformers (BERT/RoBERTa), mitigando el problema de palabras fuera de vocabulario (OOV).
    ```python
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("dccuchile/bert-base-spanish-wwm-cased")
    subtokens = tokenizer.tokenize("Los transportistas amenazan con paro indefinido")
    # Salida: ['Los', 'transport', '##istas', 'amenaz', '##an', 'con', 'paro', 'indefinido']
    ```

---

## 2. Limpieza de Ruido y Eliminación de Palabras Vacías (Stop Words)

En el documento original de R, se empleó el léxico Snowball con 308 palabras vacías mediante `anti_join()`. En Python, este proceso se realiza de manera vectorizada y eficiente.

### A. Filtrado con NLTK y Palabras Personalizadas
```python
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')
stop_words_es = set(stopwords.words('spanish'))

# Agregar palabras vacías de contexto local (Bolivia)
stop_words_es.update({"cada", "dia", "modo", "vez", "subir"})

palabras_crudas = ["la", "política", "en", "bolivia", "pone", "triste", "a", "la", "gente"]
palabras_limpias = [w for w in palabras_crudas if w.lower() not in stop_words_es]

print("Original:", palabras_crudas)
print("Filtrado:", palabras_limpias)
# Salida: ['política', 'bolivia', 'pone', 'triste', 'gente']
```

### B. Filtrado y Lematización nativa con spaCy
A diferencia de eliminar simplemente palabras, la lematización reduce flexiones verbales y de género a su forma canónica (e.g., `"amenazan"` $\to$ `"amenazar"`, `"subieron"` $\to$ `"subir"`).

```python
doc = nlp(texto)

tokens_filtrados = [
    token.lemma_.lower()
    for token in doc
    if not token.is_stop and not token.is_punct and not token.is_space
]
print("Tokens lematizados y sin stopwords:", tokens_filtrados)
```

---

## 3. Comparativa y Buenas Prácticas

1.  **¿Cuándo NO eliminar Stop Words?**
    *   En análisis de sentimientos donde negaciones como *"no"*, *"nunca"*, *"tampoco"* invierten la polaridad.
    *   En modelos de traducción o generación de texto donde la coherencia gramatical depende de los conectores.
2.  **Rendimiento:**
    *   Utilizar conjuntos (`set`) para las listas de stop words para obtener búsquedas en tiempo constante $O(1)$.
