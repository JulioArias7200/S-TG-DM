# Módulo 4: Reconocimiento de Entidades (NER), Georreferenciación y Análisis de Sentimientos en Python

Este módulo reemplaza los scripts originales de R basados en `maps` y `syuzhet` utilizando las librerías líderes de Python para NER (`spaCy`), geolocalización (`geopy`, `folium`, `matplotlib`) y análisis de emociones con léxico NRC (`NRCLex`).

---

## 1. Reconocimiento de Entidades Nombradas (NER) con spaCy

En lugar de extraer entidades manualmente como en el documento de R, `spaCy` detecta automáticamente ubicaciones (`LOC`/`GPE`), personas (`PER`) y organizaciones (`ORG`).

```python
import spacy

nlp = spacy.load("es_core_news_sm")

frase = "Voy a Madrid mañana, la oficina central está en Nueva York y luego visitaré La Paz y Buenos Aires."
doc = nlp(frase)

entidades_geograficas = []
print("=== ENTIDADES DETECTADAS AUTOMÁTICAMENTE ===")
for ent in doc.ents:
    print(f"Texto: {ent.text:15} | Etiqueta: {ent.label_:8} | Explicación: {spacy.explain(ent.label_)}")
    if ent.label_ in ["LOC", "GPE"]:
        entidades_geograficas.append(ent.text)

print("\nLugares Geográficos Extraídos:", entidades_geograficas)
```

---

## 2. Georreferenciación y Mapeo Cartográfico

### A. Geocodificación Automática con `geopy`
```python
from geopy.geocoders import Nominatim
import pandas as pd

geolocator = Nominatim(user_agent="text_mining_bolivia_app")

datos_mapa = []
for lugar in entidades_geograficas:
    try:
        location = geolocator.geocode(lugar, timeout=5)
        if location:
            datos_mapa.append({
                "lugar": lugar,
                "lat": location.latitude,
                "lon": location.longitude
            })
    except Exception as e:
        print(f"Error geocodificando {lugar}: {e}")

df_lugares = pd.DataFrame(datos_mapa)
print(df_lugares)
```

### B. Visualización Cartográfica con Matplotlib
```python
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
# Gráfico de dispersión de coordenadas
plt.scatter(df_lugares['lon'], df_lugares['lat'], color='crimson', s=120, edgecolors='black', zorder=5)

for _, row in df_lugares.iterrows():
    plt.annotate(
        row['lugar'],
        (row['lon'], row['lat']),
        textcoords="offset points",
        xytext=(0, 10),
        ha='center',
        fontweight='bold',
        fontsize=10
    )

plt.title("Lugares Geográficos Identificados en el Texto (Python)", fontsize=13)
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("mapa_lugares_python.png", dpi=300)
print("Mapa guardado en 'mapa_lugares_python.png'")
```

---

## 3. Análisis de Sentimientos y Emociones NRC en Python

En R, el paquete `syuzhet` utilizaba el NRC Emotion Lexicon de Saif Mohammad. En Python, la librería equivalente directa es `nrclex`, complementada por `textblob` o `nltk.sentiment.vader`.

### A. Detección de las 8 Emociones NRC con `NRCLex`
El léxico NRC evalúa:
1. *fear* (miedo)
2. *anger* (ira)
3. *anticip* / *anticipation* (anticipación)
4. *trust* (confianza)
5. *surprise* (sorpresa)
6. *sadness* (tristeza)
7. *disgust* (disgusto)
8. *joy* (alegría)
y las 2 polaridades: *positive* y *negative*.

```python
from nrclex import NRCLex
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

texto_es = "Estoy muy feliz y contento hoy, pero también un poco cansado y triste por algunos problemas."

# Instanciar analizador NRC
emotion_analyzer = NRCLex(texto_es)

# 1. Obtener frecuencias brutas de emociones
frecuencias_emociones = emotion_analyzer.raw_emotion_scores
print("Puntajes de emociones NRC:", frecuencias_emociones)

# 2. Convertir a DataFrame ordenado
df_emociones = pd.DataFrame(list(frecuencias_emociones.items()), columns=['Emocion', 'Frecuencia'])
df_emociones = df_emociones.sort_values(by='Frecuencia', ascending=False)

# 3. Graficado de barras estilizado
plt.figure(figsize=(9, 4.5))
sns.barplot(x='Frecuencia', y='Emocion', data=df_emociones, palette="Set3")
plt.title("Distribución de Emociones y Sentimientos (NRC Lexicon en Python)", fontsize=12)
plt.xlabel("Frecuencia")
plt.ylabel("Emoción")
plt.tight_layout()
plt.savefig("grafico_sentimientos_nrc_python.png", dpi=300)
print("Gráfico guardado en 'grafico_sentimientos_nrc_python.png'")
```

### B. Análisis de Polaridad y Subjetividad con `TextBlob`
```python
from textblob import TextBlob

blob = TextBlob(texto_es)
# Polaridad: [-1.0 (muy negativo) a 1.0 (muy positivo)]
# Subjetividad: [0.0 (muy objetivo) a 1.0 (muy subjetivo)]
print(f"Polaridad: {blob.sentiment.polarity:.2f}")
print(f"Subjetividad: {blob.sentiment.subjectivity:.2f}")
```
