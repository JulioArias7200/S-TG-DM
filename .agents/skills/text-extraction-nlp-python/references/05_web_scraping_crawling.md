# Módulo 5: Adquisición Web (Web Crawling y Scraping Ético) en Python

Este módulo detalla las técnicas de recolección automatizada de texto desde páginas web utilizando `requests`, `BeautifulSoup4` y el parser ético `urllib.robotparser`.

---

## 1. Web Crawling vs. Web Scraping

*   **Web Crawling (Rastreo):** Proceso automatizado donde un bot inicia en una semilla de URLs (*seed*), extrae hipervínculos `<a href="...">` y navega en profundidad o amplitud para catalogar la estructura del sitio.
*   **Web Scraping (Raspado):** Extracción selectiva y parsing de información estructurada específica (e.g. títulos, artículos, fechas, precios) desde el código HTML de páginas ya identificadas.

---

## 2. Scraping Básico con `requests` y `BeautifulSoup`

```python
import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://es.wikipedia.org/wiki/Miner%C3%ADa_de_textos"

headers = {
    "User-Agent": "InvestigacionAcademicaBot/1.0 (contacto@universidad.edu.bo)"
}

response = requests.get(url, headers=headers, timeout=10)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 1. Extraer título principal (h1)
    titulo = soup.find('h1').get_text(strip=True)
    
    # 2. Extraer párrafos de texto
    parrafos = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 50]
    
    print(f"Título del documento: {titulo}")
    print(f"Total de párrafos sustantivos: {len(parrafos)}")
    print("\nPrimer párrafo extraído:")
    print(parrafos[0][:200] + "...")
else:
    print(f"Error en la petición: {response.status_code}")
```

---

## 3. Crawler Web Ético con `urllib.robotparser` y Límite de Profundidad

Un crawler ético **debe**:
1.  Verificar y acatar las directivas de `robots.txt` del dominio.
2.  Implementar pausas de cortesía (`time.sleep`) para no saturar los servidores.
3.  Evitar bucles infinitos rastreando un conjunto acotado de enlaces visitados (`visited_urls`).

```python
import time
from urllib.parse import urljoin, urlparse
import urllib.robotparser
import requests
from bs4 import BeautifulSoup

def verificar_robot_txt(base_url, user_agent="*"):
    """Comprueba si el rastreador tiene autorización de explorar la URL."""
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urljoin(base_url, "/robots.txt"))
    try:
        rp.read()
        return rp
    except Exception:
        return None

def crawler_etico(url_semilla, max_paginas=5, retraso_seg=1.0):
    dominio_base = f"{urlparse(url_semilla).scheme}://{urlparse(url_semilla).netloc}"
    rp = verificar_robot_txt(dominio_base)
    
    cola_visitas = [url_semilla]
    urls_visitadas = set()
    documentos_recolectados = []
    
    headers = {"User-Agent": "EticoAcademicoNLP/1.0"}
    
    while cola_visitas and len(urls_visitadas) < max_paginas:
        url_actual = cola_visitas.pop(0)
        
        if url_actual in urls_visitadas:
            continue
            
        # Comprobar robots.txt
        if rp and not rp.can_fetch("EticoAcademicoNLP/1.0", url_actual):
            print(f"[RECHAZADO POR ROBOTS.TXT] {url_actual}")
            continue
            
        try:
            print(f"Rastreando ({len(urls_visitadas) + 1}/{max_paginas}): {url_actual}")
            res = requests.get(url_actual, headers=headers, timeout=8)
            time.sleep(retraso_seg) # Pausa de cortesía
            
            if res.status_code == 200:
                urls_visitadas.add(url_actual)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Extraer texto de párrafos
                texto_pagina = " ".join([p.get_text() for p in soup.find_all('p')])
                documentos_recolectados.append({
                    "url": url_actual,
                    "longitud_texto": len(texto_pagina),
                    "texto_resumen": texto_pagina[:150]
                })
                
                # Descubrir nuevos hipervínculos internos
                for a_tag in soup.find_all('a', href=True):
                    enlace_absoluto = urljoin(url_actual, a_tag['href'])
                    # Filtrar únicamente enlaces del mismo dominio
                    if urlparse(enlace_absoluto).netloc == urlparse(url_semilla).netloc:
                        if enlace_absoluto not in urls_visitadas and enlace_absoluto not in cola_visitas:
                            cola_visitas.append(enlace_absoluto)
                            
        except Exception as e:
            print(f"Fallo al rastrear {url_actual}: {e}")
            
    return documentos_recolectados

# Ejemplo de ejecución demostrativa
# corpus_web = crawler_etico("https://example.com", max_paginas=3)
```

---

## 4. Pipeline Completo: De la Web a TF-IDF y LDA

Una vez recolectados los textos con el crawler, se integran directamente con los módulos previos:
```python
# texts = [doc['texto'] for doc in corpus_web]
# Matriz TF-IDF -> Ver Módulo 2
# Tópicos LDA  -> Ver Módulo 3
```
