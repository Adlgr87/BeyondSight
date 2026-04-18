---
title: BeyondSight
emoji: 🌊
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
---

# BeyondSight

[![License: PPL 3.0](https://img.shields.io/badge/License-PROSPERITY_PUBLIC_V3.0-blue.svg)](https://prosperitylicense.com)
[![tests](https://github.com/Adlgr87/BeyondSight/actions/workflows/pytest.yml/badge.svg)](https://github.com/Adlgr87/BeyondSight/actions/workflows/pytest.yml)
[![docs](https://github.com/Adlgr87/BeyondSight/actions/workflows/mkdocs.yml/badge.svg)](https://github.com/Adlgr87/BeyondSight/actions/workflows/mkdocs.yml)

![BeyondSight Demo](docs/beyondsight_mockup.png)

Simulador híbrido de dinámica social — Núcleo numérico + LLM como selector de régimen.

BeyondSight cierra la brecha entre los modelos matemáticos clásicos de formación de opinión y la flexibilidad contextual de los Modelos de Lenguaje de Gran Escala (LLMs).

## Fundamentos Teóricos e Investigación

El proyecto se inspira en modelos fundamentales de dinámica de opinión y en investigación de vanguardia:

- **Modelos de DeGroot y Friedkin-Johnsen:** Implementación base para la evolución de opiniones en redes sociales, considerando la influencia de vecinos y la resistencia al cambio (prejuicios).
- **Hegselmann-Krause (2002) - Confianza Acotada:** El agente solo interactúa con grupos cuya opinión se encuentra dentro de un radio `ε`, propiciando polarización natural y formación de clusters.
- **Contagio Competitivo (Beutel et al., 2012):** Modela la propagación de dos narrativas rivales compitiendo simultáneamente en el sistema.
- **Umbral Heterogéneo (Granovetter, 1978):** Uso de una distribución normal de umbrales en la población en lugar de uno estático, propiciando fenómenos de cascadas sociales rápidas.
- **Redes Co-evolutivas y Homofilia (Axelrod, 1997):** La intensidad de la influencia varía según la similitud de las opiniones, lo que genera cámaras de eco (echo chambers) endógenas.
- **Ecuación Replicadora — EGT (Taylor & Jonker, 1978):** Modelo de teoría de juegos evolutiva de dos estrategias. Las frecuencias de la población evolucionan según el beneficio relativo, usando una matriz de pagos 2×2 configurable integrada mediante RK45.
- **Sesgo de Confirmación (Sunstein, 2009; Nickerson, 1998):** Un mecanismo transversal cognitivo que atenúa sistemáticamente el peso de la información contraria a la creencia actual del agente.
- **Señales de Alerta Temprana — EWS / Critical Slowing Down (Scheffer et al., 2009; Dakos et al., 2012):** La varianza, la autocorrelación lag-1 y la asimetría se calculan sobre una ventana deslizante de la opinión para detectar la proximidad a puntos de inflexión (bifurcaciones).
- **Análisis de Datos Topológicos — TDA / Homología Persistente (Carlsson, 2009; Perea & Harer, 2015):** Detección avanzada opcional de cambios topológicos en la serie temporal de opinión mediante embedding de Takens y distancia de Wasserstein entre diagramas de persistencia. Se activa cuando `ripser` y `persim` están instalados.
- **Conexión Académica:** El enfoque de BeyondSight resuena con investigaciones recientes como *"Opinion Consensus Formation Among Networked Large Language Models"* (Enero 2026), explorando cómo los agentes inteligentes pueden alcanzar consensos o polarización.
- **Arquitectura Híbrida:** A diferencia de simulaciones puramente numéricas, BeyondSight utiliza un LLM (como Llama 3) para analizar la trayectoria histórica y decidir qué régimen matemático de transición es sociológicamente más coherente en cada paso.

## Reglas de Transición

| ID | Nombre | Fundamento | Cuándo domina |
|---|---|---|---|
| 0 | Lineal | Friedkin-Johnsen | Condiciones moderadas |
| 1 | Umbral | Granovetter (simple) | Propaganda cruza punto crítico |
| 2 | Memoria | DeGroot con lag | Sistema estable, inercia |
| 3 | Backlash | Literatura de persuasión | Rechazo establecido + propaganda |
| 4 | Polarización | Cámara de eco | Tendencia ya iniciada |
| 5 | **HK** | Hegselmann-Krause (2002) | Grupos muy distantes entre sí |
| 6 | **Contagio competitivo** | Beutel et al. (2012) | Dos narrativas activas |
| 7 | **Umbral heterogéneo** | Granovetter (1978) | Cascadas sociales |
| 8 | **Homofilia** | Axelrod (1997) | Grupos convergen por similitud |
| 9 | **Replicador (EGT)** | Taylor & Jonker (1978) | Presión evolutiva entre estrategias de grupo |

**Mecanismos transversales:**
- **Sesgo de confirmación** — propaganda contraria llega atenuada según la posición actual.
- **Homofilia dinámica** — los pesos de influencia de los grupos se actualizan en cada paso según la similitud de opinión.
- **Rango bipolar `[-1, 1]`** — el rechazo activo tiene expresión directa y simétrica con el apoyo.
- **Narrativa B** — habilita el contagio competitivo entre dos narrativas simultáneas.

## Rangos de Opinión

| Situación | Rango | Por qué |
|---|---|---|
| Vacuna, política pública, producto nuevo | **[-1, 1] bipolar** | Rechazo activo ≠ indiferencia |
| Elecciones, referéndum | **[-1, 1] bipolar** | Votar en contra ≠ abstención |
| Probabilidad de adopción de tecnología | **[0, 1] probabilístico** | Tasa de adopción natural |
| Difusión de información / contagio | **[0, 1] probabilístico** | Modelos SIR en este rango |

## Arquitecto Social (Ingeniería Inversa)

BeyondSight Enterprise introduce al **Arquitecto Social**, nuestra funcionalidad de ingeniería inversa apoyada en un agente *LLM-in-the-loop*. En lugar de simplemente predecir el futuro de la red en base al estado actual, describes a la IA tu clima social deseado (ej. "Despolarizar la violencia y lograr un consenso social sólido en 20 iteraciones"). El agente iterará con los marcos matemáticos, simulará futuros hipotéticos, aprenderá de los escenarios de colapso y reajustará sus políticas hasta entregarte la `Matriz de Estrategia` exacta ("Receta Sociológica") requerida para alterar la dinámica sin margen de error analítico.

El Arquitecto Social opera en dos modos:

- **🌐 Modo Macro** — Diseñado para campañas políticas, opinión pública y redes sociales masivas. Las intervenciones se enmarcan como campañas mediáticas, discurso político, hashtags virales, cámaras de eco y polarización electoral.
- **🏢 Modo Corporativo** — Diseñado para RRHH, gestión del cambio organizacional y comunicación interna. Acepta un CSV de la red organizacional (`source`, `target`) para calcular centralidad de grado y betweenness mediante NetworkX, identificando líderes formales (grado alto) y líderes informales (betweenness alto). Las intervenciones se enmarcan como reuniones 1:1, comunicados internos, workshops y planes de acción 30-60-90 días alineados con OKRs.

El agente utiliza **validación de esquemas Pydantic** (`StrategyMatrix` / `Intervention`) para garantizar que cada cronograma de intervenciones generado sea estructuralmente correcto antes de ser ejecutado por el simulador.

## Proveedores LLM

| Proveedor | Descripción | Requiere key |
|---|---|---|
| `heurístico` | Sin LLM — lógica determinista, sin costo ni API key | No |
| `ollama` | LLM local con Ollama — privado, sin costo por llamada | No |
| `groq` | Groq Cloud — muy rápido, tier gratuito generoso | Sí |
| `openai` | OpenAI API — GPT-4o, GPT-4o-mini, etc. | Sí |
| `openrouter` | OpenRouter — acceso a cientos de modelos con una sola key | Sí |

## Modo Probabilístico

Activa **Simulación Múltiple** para correr N ejecuciones Monte Carlo con pequeñas perturbaciones en el estado inicial. Los resultados devuelven la distribución de la opinión final, la banda de confianza P10–P90 y la probabilidad de posición positiva — adecuado para análisis de escenarios y evaluación de riesgos.

## Señales de Alerta Temprana (EWS)

BeyondSight monitorea continuamente la serie temporal de opinión sobre una ventana deslizante y emite alertas cuando:
- **Varianza alta** — el sistema se está volviendo inestable.
- **Autocorrelación lag-1 alta** — Critical Slowing Down, proximidad a un punto de inflexión.
- **Asimetría alta** — fluctuaciones asimétricas, precursor de un cambio de régimen.

Cuando TDA está disponible, el detector de cambios topológicos mediante Homología Persistente también puede señalar transiciones estructurales de régimen.

## Visualización de Red Social

Tras cada simulación, BeyondSight genera un grafo interactivo de **Plotly** con una topología de red sintética coherente con el estado macroscópico final del simulador — la polarización de opinión, los niveles de confianza y la homofilia grupal quedan reflejados en los colores de los nodos y la densidad de conexiones.

## Internacionalización

La interfaz completa está disponible en **inglés** y **español** mediante el módulo `i18n.py`. El idioma puede cambiarse en cualquier momento desde la barra lateral.

## Instalación

```bash
pip install -r requirements.txt
```

> **Soporte TDA opcional:** `pip install ripser persim` habilita la detección topológica de cambios de régimen mediante Homología Persistente.

## Ejecución

### Modo Local (Streamlit)
```bash
streamlit run app.py
```

### Ejecución en Hugging Face Spaces
Este repositorio está listo para ser desplegado como un **Hugging Face Space**. Simplemente conecta este repo a un nuevo Space de tipo `Streamlit`.

## Estructura del Proyecto

```
BeyondSight/
├── docs/              # Fuentes de documentación MkDocs
├── tests/             # Pruebas unitarias e integración
├── .gitignore         # Configuración de archivos ignorados
├── app.py             # Interfaz Streamlit
├── i18n.py            # Internacionalización (inglés / español)
├── schemas.py         # Esquemas Pydantic para validación de StrategyMatrix
├── simulator.py       # Núcleo del simulador, todas las reglas, EWS, TDA y lógica LLM
├── social_architect.py# Agente Arquitecto Social (modo inverso)
├── visualizations.py  # Visualización de topología de red social con Plotly
├── mkdocs.yml         # Configuración de MkDocs
├── README.md          # Documentación (inglés)
├── README_ES.md       # Documentación (español)
└── requirements.txt   # Dependencias
```

## Seguridad

Las API keys se gestionan mediante variables de entorno. Copia `.env.example` a `.env` y rellena tus claves:

- `GROQ_API_KEY`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`

En Hugging Face Spaces puedes definirlas como **Secrets**.

## Licencia Ética

Este proyecto está bajo la **Prosperity Public License 3.0.0**.

- **Uso Comunal/Personal/Educativo:** Gratuito y libre.
- **Uso Corporativo:** Las empresas pueden probar el software por 30 días. Tras ese periodo, deben adquirir una licencia comercial.

Para consultas comerciales, contactar a [Adlgr87](https://github.com/Adlgr87) en GitHub.

---
*Desarrollado con un enfoque en la interpretabilidad de la IA y el estudio de sistemas sociales complejos.*
