# Módulo 3: Modelado de Temas (Topic Modeling LDA) en Python

Este módulo explica cómo inferir temas latentes a partir de colecciones documentales no estructuradas utilizando **Latent Dirichlet Allocation (LDA)** tanto con `scikit-learn` como con `Gensim`.

---

## 1. Fundamentos Matemáticos de LDA

LDA es un modelo probabilístico generativo de tres niveles:
1.  Cada **documento** es modelado como una distribución multinomial de temas ($\theta_d \sim \text{Dirichlet}(\alpha)$).
2.  Cada **tema** es una distribución multinomial sobre palabras del vocabulario ($\phi_k \sim \text{Dirichlet}(\beta)$).
3.  La meta es estimar estas distribuciones ocultas a partir de las co-ocurrencias de términos observadas en la Matriz Documento-Término (DTM).

---

## 2. Implementación con `scikit-learn` (`LatentDirichletAllocation`)

Esta implementación sustituye la combinación de `tm` / `topicmodels::LDA` de R.

```python
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import pandas as pd
import numpy as np

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
    "los", "por", "un", "otra", "ha", "todos", "de", "se"
]

# Paso 1: Generar DTM (CountVectorizer)
tf_vectorizer = CountVectorizer(stop_words=stop_words_es, min_df=1)
tf_matrix = tf_vectorizer.fit_transform(corpus)
vocab = tf_vectorizer.get_feature_names_out()

# Paso 2: Ajustar Modelo LDA con k=4 tópicos
k_topics = 4
lda_model = LatentDirichletAllocation(
    n_components=k_topics,
    learning_method='batch', # Equivalente a Gibbs/Variacional
    random_state=42,
    max_iter=100
)
lda_model.fit(tf_matrix)

# Paso 3: Extraer Matriz Beta (Distribución Término-Tema)
# Equivalente a tidy(modelo_lda, matrix = "beta") en R
matriz_beta = lda_model.components_ / lda_model.components_.sum(axis=1)[:, np.newaxis]

print("=== PALABRAS MÁS IMPORTANTES POR TEMA (MATRIZ BETA) ===")
top_n = 5
for topic_idx, topic in enumerate(matriz_beta):
    top_indices = topic.argsort()[:-top_n - 1:-1]
    top_features = [vocab[i] for i in top_indices]
    top_probs = [topic[i] for i in top_indices]
    print(f"\nTema #{topic_idx + 1}:")
    for word, prob in zip(top_features, top_probs):
        print(f"  - {word}: {prob:.4f}")

# Paso 4: Extraer Matriz Gamma (Distribución Documento-Tema)
# Equivalente a tidy(modelo_lda, matrix = "gamma") en R
matriz_gamma = lda_model.transform(tf_matrix)
df_gamma = pd.DataFrame(matriz_gamma, columns=[f"Tema_{i+1}" for i in range(k_topics)])
df_gamma['Documento'] = [f"Doc_{i+1}" for i in range(len(corpus))]
print("\n=== DISTRIBUCIÓN DE TEMAS POR DOCUMENTO (MATRIZ GAMMA) ===")
print(df_gamma.head(5).round(3))
```

---

## 3. Implementación Alternativa con `Gensim`

`Gensim` es el estándar en PLN para cálculo de coherencia semántica ($C_v$) y visualizaciones interactivas con `pyLDAvis`.

```python
import gensim
from gensim import corpora
from gensim.models import LdaModel, CoherenceModel

# Tokenizar y limpiar
textos_tokenizados = [
    [w.lower() for w in doc.split() if len(w) > 3 and w.lower() not in stop_words_es]
    for doc in corpus
]

# Crear diccionario y corpus Gensim
diccionario = corpora.Dictionary(textos_tokenizados)
corpus_bow = [diccionario.doc2bow(text) for text in textos_tokenizados]

# Entrenar LDA
lda_gensim = LdaModel(
    corpus=corpus_bow,
    id2word=diccionario,
    num_topics=3,
    passes=20,
    random_state=100
)

# Imprimir tópicos
for idx, topic in lda_gensim.print_topics(-1):
    print(f"Tópico Gensim {idx + 1}: {topic}")

# Medir coherencia del modelo
coherence_model = CoherenceModel(
    model=lda_gensim,
    texts=textos_tokenizados,
    dictionary=diccionario,
    coherence='c_v'
)
print(f"\nCoherencia Semántica (C_v): {coherence_model.get_coherence():.4f}")
```

---

## 4. Visualización Facetada de Tópicos con Matplotlib y Seaborn

```python
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
axes = axes.flatten()

for topic_idx, ax in enumerate(axes):
    topic = matriz_beta[topic_idx]
    top_indices = topic.argsort()[:-6:-1]
    top_words = [vocab[i] for i in top_indices]
    top_weights = [topic[i] for i in top_indices]
    
    sns.barplot(x=top_weights, y=top_words, ax=ax, palette="mako")
    ax.set_title(f"Tópico {topic_idx + 1}", fontsize=11, fontweight='bold')
    ax.set_xlabel("Probabilidad Beta")

plt.tight_layout()
plt.savefig("grafico_lda_python.png", dpi=300)
print("Gráfico guardado en 'grafico_lda_python.png'")
```
