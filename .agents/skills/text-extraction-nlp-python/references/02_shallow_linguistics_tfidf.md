# Módulo 2: Lingüística Superficial y Ponderación TF-IDF en Python

Este módulo aborda el cálculo de frecuencias léxicas (*Shallow Linguistics*), extracción de n-gramas y la ponderación matemática y vectorial mediante **TF-IDF** (Term Frequency - Inverse Document Frequency).

---

## 1. Lingüística Superficial: Conteo de Frecuencias y N-gramas

El enfoque superficial analiza patrones sintácticos observables sin inferencia contextual profunda.

```python
from collections import Counter
import pandas as pd
import nltk
from nltk.util import ngrams

textos = [
    "La política en Bolivia pone triste a la gente.",
    "El partido para el mundial una pena",
    "Las marchas son el pan de cada dia",
    "Están pensando subir el costo del pan",
    "Los transportistas amenazan cada dia"
]

# 1. Conteo de frecuencias superficiales con Collections
palabras_todas = [w.lower() for doc in textos for w in doc.split() if len(w) > 3]
frecuencias = Counter(palabras_todas)
df_freq = pd.DataFrame(frecuencias.most_common(5), columns=['palabra', 'frecuencia'])
print("Top 5 palabras más frecuentes:")
print(df_freq)

# 2. Extracción de Bigramas (n=2)
tokens_oracion = textos[0].lower().split()
bigramas = list(ngrams(tokens_oracion, 2))
print("\nBigramas extraídos:")
for b in bigramas:
    print(f"{b[0]} -> {b[1]}")
```

---

## 2. Fundamento Matemático de TF-IDF

En los documentos del proyecto, la fórmula definida es:

$$\text{TF}(t, d) = \frac{\text{Conteo de } t \text{ en } d}{\text{Total de palabras en } d}$$

$$\text{IDF}(t, D) = \log\left(\frac{|D|}{|\{d \in D : t \in d\}|}\right)$$

$$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \text{IDF}(t, D)$$

### Implementación Manual Exacta en Python
```python
import numpy as np
import pandas as pd

documentos = [
    "politica bolivia triste gente",
    "partido mundial pena",
    "marchas pan cada dia",
    "costo subir pan",
    "transportistas amenazan cada dia"
]

# Paso 1: Vocabulario único
vocab = sorted(list(set(w for doc in documentos for w in doc.split())))
N = len(documentos)

# Paso 2: Calcular IDF para cada término
idf_dict = {}
for term in vocab:
    n_docs_con_term = sum(1 for doc in documentos if term in doc.split())
    # logaritmo natural según el documento base
    idf_dict[term] = np.log(N / n_docs_con_term)

# Paso 3: Matriz TF-IDF
matriz_tfidf = []
for doc in documentos:
    words = doc.split()
    total_words = len(words)
    row = []
    for term in vocab:
        tf = words.count(term) / total_words if total_words > 0 else 0
        tfidf = tf * idf_dict[term]
        row.append(tfidf)
    matriz_tfidf.append(row)

df_tfidf_manual = pd.DataFrame(matriz_tfidf, columns=vocab, index=[f"doc{i+1}" for i in range(N)])
print("Matriz TF-IDF Manual (primeras 5 columnas):")
print(df_tfidf_manual.iloc[:, :5].round(4))
```

---

## 3. Implementación Industrial con `scikit-learn` (`TfidfVectorizer`)

En aplicaciones de producción, se utiliza `TfidfVectorizer` de scikit-learn, el cual incluye tokenización, eliminación de stopwords y normalización euclídea ($L2$) de manera optimizada en C.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

corpus = [
    "La política en Bolivia pone triste a la gente.",
    "El partido para el mundial una pena",
    "Las marchas son el pan de cada dia",
    "Están pensando subir el costo del pan",
    "Los transportistas amenazan cada dia",
    "Los transportistas quieren entran en paro por el problema del gas",
    "Estamos entrando en un frente frió",
    "Cada dia suben las cosas",
    "El pollo otra vez ha subido",
    "De todos modos subió el pasaje"
]

stop_words_es = [
    "la", "el", "en", "a", "para", "una", "las", "son", "de", "del",
    "los", "por", "un", "otra", "ha", "todos"
]

# Vectorizador con n-gramas (unigramas y bigramas)
vectorizer = TfidfVectorizer(
    stop_words=stop_words_es,
    ngram_range=(1, 1),
    sublinear_tf=False,
    norm='l2'
)

X_tfidf = vectorizer.fit_transform(corpus)
nombres_caracteristicas = vectorizer.get_feature_names_out()

df_tfidf_sklearn = pd.DataFrame(
    X_tfidf.toarray(),
    columns=nombres_caracteristicas,
    index=[f"doc{i+1}" for i in range(len(corpus))]
)

# Extraer los términos de mayor peso por documento (equivalente a bind_tf_idf de R)
print("\nTop términos de mayor ponderación en Documento 1:")
print(df_tfidf_sklearn.loc['doc1'].sort_values(ascending=False).head(4))
```

---

## 4. Visualización de Términos Relevantes con Seaborn

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Promedio de TF-IDF por término a través del corpus
promedio_tfidf = df_tfidf_sklearn.mean().sort_values(ascending=False).head(10)

plt.figure(figsize=(10, 5))
sns.barplot(x=promedio_tfidf.values, y=promedio_tfidf.index, palette="viridis")
plt.title("Términos con Mayor Importancia Global (TF-IDF Promedio)", fontsize=13)
plt.xlabel("Peso TF-IDF")
plt.ylabel("Términos")
plt.tight_layout()
plt.savefig("grafico_tfidf_python.png", dpi=300)
print("Gráfico guardado en 'grafico_tfidf_python.png'")
```
