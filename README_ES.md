---
title: BeyondSight
emoji: 🌊
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
---

# BeyondSight: Ingeniería de Estrategia para Dinámicas Sociales

[![License: PPL 3.0](https://img.shields.io/badge/License-PROSPERITY_PUBLIC_V3.0-blue.svg)](https://prosperitylicense.com)
[![tests](https://github.com/Adlgr87/BeyondSight/actions/workflows/pytest.yml/badge.svg)](https://github.com/Adlgr87/BeyondSight/actions/workflows/pytest.yml)
[![docs](https://github.com/Adlgr87/BeyondSight/actions/workflows/mkdocs.yml/badge.svg)](https://github.com/Adlgr87/BeyondSight/actions/workflows/mkdocs.yml)

![BeyondSight Demo](docs/beyondsight_mockup.png)

**BeyondSight** es una plataforma técnica de **Simulación Social Inversa**.  
En lugar de limitarse a pronosticar resultados, calcula la ruta de intervención necesaria para alcanzar un estado social objetivo.

En la práctica: defines una meta (por ejemplo, reducir polarización, aumentar consenso o activar adopción controlada) y BeyondSight busca la estrategia de intervención más coherente usando simulación + razonamiento con IA.

Combina:
- **Modelos matemáticos de dinámica social** (DeGroot, Hegselmann-Krause, Axelrod y cascadas por umbrales).
- **Analítica de grafos** (detección de centralidad y nodos puente).
- **Búsqueda estratégica guiada por LLM** para mejorar decisiones de forma iterativa.

El resultado no es solo una gráfica, sino un **itinerario accionable de estrategia** basado en dinámica formal.

---

## ⚡ El Arquitecto Social (Capacidad Principal)

La capacidad central de BeyondSight es el **Arquitecto Social**.  
En lugar de ajustar parámetros manualmente para ver qué sucede, tú defines el objetivo:

> *"Lograr un consenso moderado y eliminar la polarización en 20 iteraciones, partiendo de una red altamente fragmentada."*

El Arquitecto Social utiliza una arquitectura **LLM-in-the-loop** para:
1. **Analizar** topología de red, estructura de grupos y estados iniciales de opinión.
2. **Simular** rutas candidatas de intervención en múltiples regímenes sociológicos.
3. **Optimizar** una `Matriz de Estrategia` (intervenciones temporales + cronograma paramétrico).
4. **Devolver** un plan de intervención claro e interpretable para analistas, investigadores y equipos de decisión.

---

## 🧭 Cómo Funciona BeyondSight (en 4 pasos)

1. **Definir estado objetivo**  
   Ejemplo: “Lograr consenso moderado en ≤20 iteraciones sin polarización extrema.”

2. **Ejecutar búsqueda inversa**  
   El Arquitecto Social explora secuencias de intervención y evalúa la calidad de trayectoria en cada ciclo.

3. **Validar con simulación híbrida**  
   Los modelos numéricos + métricas de grafos verifican estabilidad, realismo y coherencia sociológica.

4. **Exportar estrategia**  
   La salida incluye el itinerario recomendado de intervención y su justificación.

---

## 🔬 Arquitectura de Simulación Híbrida

BeyondSight cierra la brecha entre la investigación clásica y la IA moderna:

-   **Núcleo Numérico:** Implementa modelos de vanguardia como DeGroot (influencia), Hegselmann-Krause (formación de clusters) y Axelrod (homofilia).
-   **Selector de Régimen LLM:** Un "cerebro heurístico" que analiza trayectorias históricas y selecciona dinámicamente el régimen de transición sociológicamente más coherente en cada paso.
-   **Inteligencia de Grafos:** Métricas integradas de NetworkX (Centralidad de Grado/Betweenness) para identificar nodos puente y líderes informales para intervenciones dirigidas.

---

## 📖 Fundamentos Teóricos

El sistema se basa en décadas de investigación revisada por pares:

-   **Hegselmann-Krause (2002):** Confianza acotada para formación de clusters y polarización.
-   **Contagio Competitivo (Beutel et al., 2012):** Propagación de narrativas rivales duales.
-   **Umbral Heterogéneo (Granovetter, 1978):** Distribución normal de umbrales para modelar cascadas.
-   **Sesgo de Confirmación:** Mecanismos de exposición selectiva como filtros transversales.

---

## 🚀 Comenzando (Fácil para no técnicos)

### 1) Ruta más rápida (recomendada)

#### Windows
Haz doble clic en `start.bat` desde la carpeta del proyecto.

O ejecuta:
```bash
start.bat
```

#### macOS / Linux
```bash
chmod +x start.sh
./start.sh
```

Estos scripts hacen automáticamente:
1. Crear entorno virtual local (`.venv`) si no existe.
2. Instalar/actualizar dependencias desde `requirements.txt`.
3. Crear `.env` desde `.env.example` si falta.
4. Iniciar Streamlit en `http://localhost:8501`.

---

### 2) Instalación manual (usuarios avanzados)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

---

### 3) API keys (solo si usas proveedores LLM en la nube)

Crea `.env` desde `.env.example` y completa el proveedor que usarás:

- `GROQ_API_KEY`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- `OLLAMA_HOST` (para Ollama local, por defecto: `http://localhost:11434`)

Si eliges `ollama` en la interfaz, no necesitas llaves cloud.

---

### 4) Despliegue en Hugging Face Spaces (ruta simple)

1. Crea un **Streamlit Space** nuevo.
2. Conecta este repositorio.
3. En Settings → **Variables and secrets**, agrega tus API keys.
4. Publica.

`app.py` ya está configurado como entrypoint de Streamlit.

---

### Solución de problemas

- **No se reconoce `streamlit`**  
  Ejecuta usando `start.bat` / `start.sh`, o activa correctamente el entorno virtual.

- **El proveedor pide API key**  
  Agrega la llave en `.env` y reinicia la app.

- **Puerto ocupado**  
  Ejecuta:
  ```bash
  streamlit run app.py --server.port 8502
  ```

- **Problemas de red/proxy instalando paquetes**  
  Configura proxy de pip y vuelve a ejecutar:
  ```bash
  pip install -r requirements.txt
  ```

### Avanzado: Análisis de Estrategia vía Gemini-CLI
Para interacción directa con los modelos Gemini de Google desde tu terminal — útil para profundizar en las estrategias generadas o realizar auditorías manuales:
```bash
npm install -g @google/gemini-cli
gemini
```

---

## 🔐 Seguridad y Gestión de APIs

BeyondSight soporta Groq, OpenAI y OpenRouter. Configura tus llaves en un archivo `.env` o en variables de entorno:
- `GROQ_API_KEY`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`

---

## 📜 Licencia

BeyondSight se distribuye bajo la **Prosperity Public License 3.0.0**.
- **No Comercial:** Gratuito para individuos, investigadores y fines educativos.
- **Comercial:** Prueba de 30 días para empresas, seguida del requisito de una licencia comercial.

Contacta a [Adlgr87](https://github.com/Adlgr87) para licencias comerciales.

---
*Diseñando el futuro de los sistemas sociales mediante la interpretabilidad impulsada por IA.*
