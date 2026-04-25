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

En el corazón de BeyondSight se encuentra el **Arquitecto Social** — un agente LLM de ingeniería inversa que calcula la secuencia precisa de intervenciones matemáticas necesarias para llevar cualquier red social hacia el resultado deseado. En lugar de predecir hacia dónde *irá* una red, el Arquitecto Social determina exactamente *cómo llegar* adonde quieres ir.

## ¿Por Qué BeyondSight?

¿Te has preguntado qué podría desencadenar una huelga masiva, o cómo un escándalo podría hundir la aprobación de un político? BeyondSight te permite simular estas dinámicas de una manera fundamentada en matemáticas pero impulsada por la intuición de la IA. No se trata solo de predecir el caos—es ayudarte a entender e incluso dirigir las mareas sociales.

## Escenarios en Acción

Vamos a sumergirnos en algunos escenarios hipotéticos donde BeyondSight brilla. Cubriremos tanto el **Modo Simulación** (predicción hacia adelante) como el **Arquitecto Social** (ingeniería inversa).

### Escenario 1: La Huelga Laboral Inminente

Imagina un piso de fábrica donde los trabajadores están cada vez más frustrados con las decisiones de la gerencia. Opinión inicial: neutral (0.5), pero la propaganda de los sindicatos empuja hacia el disentimiento (-0.3 en rango bipolar).

- **Modo Simulación:** Ejecuta una simulación de 50 pasos con HK (confianza acotada) como régimen. El selector LLM podría cambiar a "contagio_competitivo" cuando dos narrativas (sindicato vs. empresa) compiten. Observa cómo se forman clusters, y las señales EWS advierten de puntos de inflexión inminentes. Resultado: La polarización aumenta, prediciendo el estallido de una huelga.

- **Arquitecto Social:** Entrada: "Prevenir la huelga fomentando el consenso." El ingeniero inverso genera un horario de intervenciones: Comienza con homofilia para construir cohesión grupal, luego cambia a memoria para estabilidad. Salida: Un plan por fases con nodos objetivo (e.g., trabajadores influyentes) para redirigir la energía hacia la negociación.

### Escenario 2: La Caída del Político Corrupto

Un candidato comienza con alta aprobación (0.8), pero las acusaciones de corrupción se filtran como propaganda negativa (-0.6).

- **Modo Simulación:** Usa umbral_heterogeneo para cascadas. El sistema podría detectar alta varianza vía EWS, indicando desaceleración crítica. A medida que se cruzan umbrales, las opiniones avalanchan hacia el rechazo, simulando una caída rápida en desgracia.

- **Arquitecto Social:** Meta: "Estabilizar el apoyo a pesar del escándalo." Modo inverso: Prueba iterativamente regímenes como backlash (reforzar oposición) o polarización para profundizar divisiones. Resultado: Una estrategia que enfatiza el sesgo de confirmación para mantener lealistas, con targeting corporativo de donantes clave.

### Escenario 3: El Movimiento de Protesta Viral

Una protesta impulsada por redes sociales comienza pequeña (opinión 0.6 en apoyo), amplificada por cámaras de eco.

- **Modo Simulación:** Hegselmann-Krause crea clusters naturales. El contagio competitivo modela hashtags rivales. TDA detecta cambios topológicos a medida que el movimiento gana impulso, pronosticando escalada.

- **Arquitecto Social:** Objetivo: "Amplificar el movimiento a nivel nacional." Genera intervenciones: Impulsa con contagio_competitivo para propagación narrativa, targetea influencers macro. Salida: Cronograma de "eventos virales" como temas trending, con narrativas sociológicas generadas por LLM.

Estos son solo inicios—mezcla parámetros, rangos y LLMs para explorar. BeyondSight convierte modelos abstractos en insights tangibles.

## Fundamentos Teóricos e Investigación

El proyecto se inspira en modelos fundamentales de dinámica de opinión y en investigación de vanguardia:

- **Modelos de DeGroot y Friedkin-Johnsen:** Implementación base para la evolución de opiniones en redes sociales, considerando la influencia de vecinos y la resistencia al cambio (prejuicios).
- **Hegselmann-Krause (2002) - Confianza Acotada:** El agente solo interactúa con grupos cuya opinión se encuentra dentro de un radio `ε`, propiciando polarización natural y formación de clusters.
- **Contagio Competitivo (Beutel et al., 2012):** Modela la propagación de dos narrativas rivales compitiendo simultáneamente en el sistema.
- **Umbral Heterogéneo (Granovetter, 1978):** Uso de una distribución normal de umbrales en la población en lugar de uno estático, propiciando fenómenos de cascadas sociales rápidas.
- **Redes Co-evolutivas y Homofilia (Axelrod, 1997):** La intensidad de la influencia varía según la similitud de las opiniones, lo que genera cámaras de eco (echo chambers) endógenas.
- **Sesgo de Confirmación:** Un mecanismo transversal cognitivo que atenúa sistemáticamente el peso de la información contraria a la creencia actual del agente.
- **Dinámica de Energía de Langevin:** Ecuaciones diferenciales estocásticas de inspiración física donde los agentes se mueven a través de un paisaje de energía social configurable con atractores y repulsores — el núcleo de simulación más reciente de BeyondSight.
- **Conexión Académica:** El enfoque de BeyondSight resuena con investigaciones recientes como *"Opinion Consensus Formation Among Networked Large Language Models"* (Enero 2026), explorando cómo agentes inteligentes forman opiniones en redes.
- **Arquitectura Híbrida:** A diferencia de simulaciones puramente numéricas, BeyondSight utiliza un LLM (como Llama 3) para analizar la trayectoria histórica y decidir qué régimen matemático es sociológicamente apropiado.

## Motor de Paisaje Energético

El **Motor de Paisaje Energético** de BeyondSight modela la dinámica social como un sistema físico donde la opinión de cada agente evoluciona según una ecuación diferencial estocástica de Langevin:

```
x_i(t+η) = x_i(t) − η·∇U(x_i) + η·λ·(x̄_vecinos − x_i) + √(2η·T)·ε
```

| Término | Significado |
|---|---|
| `∇U(x)` | Gradiente del paisaje de energía social (atractores/repulsores) |
| `λ` (`lambda_social`) | Balance: 0 = solo paisaje, 1 = solo influencia de red social |
| `T` (`temperature`) | Ruido / libre albedrío — mayor = comportamiento individual más caótico |
| `ε ~ N(0,1)` | Término estocástico (integración Euler-Maruyama) |

Los **Atractores** modelan fuerzas de cohesión social (puntos de consenso, identidades faccionales, posiciones oficiales). Los **Repulsores** modelan fuerzas de división social (aversión a la moderación, dinámicas anti-consenso). Todos los parámetros se validan mediante esquemas Pydantic v2 `EnergyConfig` antes de ejecutar cualquier simulación.

### Arquetipos Sociales Pre-construidos

El **Arquitecto Programático** (`programmatic_architect.py`) incluye 8 arquetipos validados que cubren los escenarios sociológicos más comunes:

| Clave del arquetipo | Descripción |
|---|---|
| `polarizacion_extrema` | Dos bandos irreconciliables. El centro es tierra de nadie. |
| `polarizacion_moderada` | Dos grupos, pero con diálogo posible en el centro. |
| `consenso_moderado` | La sociedad tiende a acuerdos. El centro atrae a todos. |
| `consenso_forzado` | Presión institucional fuerte hacia una sola posición. |
| `fragmentacion_3_grupos` | Tres facciones que coexisten sin fusionarse. |
| `fragmentacion_4_grupos` | Cuatro comunidades tribales con alta segmentación. |
| `caos_social` | Sin estructura clara. Cada agente actúa por impulso propio. |
| `radicalizacion_progresiva` | Los agentes empiezan al centro y son jalados hacia los extremos. |

**Pipeline de resolución** — para cualquier objetivo en texto libre, el motor intenta en orden:
1. **Coincidencia exacta de arquetipo** (instantáneo, sin llamada API)
2. **Caché RAM** (submilisegundo, mismo proceso)
3. **Caché SQLite** (`LandscapeCache`) — persiste entre sesiones de Streamlit y reinicios de contenedor
4. **Generación LLM one-shot** (Groq / OpenAI / OpenRouter / Ollama) con validación Pydantic
5. **Fallback** a `caos_social` si el LLM falla o devuelve una configuración inválida

## Arquitecto Social (Ingeniería Inversa)

BeyondSight Enterprise introduce al **Arquitecto Social**, un potente agente de ingeniería inversa apoyado en un bucle *LLM-in-the-loop*. En lugar de simplemente predecir el futuro de la red, tú defines el resultado sociológico que deseas (p. ej., *"Lograr un consenso moderado y eliminar la polarización en 20 iteraciones"*), y el Arquitecto Social trabaja hacia atrás para encontrar la estrategia exacta que te lleva allí.

### Cómo Funciona

1. **Definición del objetivo:** Describes en lenguaje natural el estado final deseado — consenso, polarización, propagación viral, contención de crisis, alineación cultural, etc.
2. **Bucle de simulación iterativo:** El agente LLM propone una `StrategyMatrix` — un calendario de intervenciones matemáticas por fases (HK, contagio, homofilia, umbrales…). El simulador ejecuta el calendario y puntúa el resultado.
3. **Autocrítica y refinamiento:** Si la puntuación no alcanza el objetivo, el agente recibe feedback estructurado (nivel de polarización, delta de opinión, varianza) y propone una estrategia mejorada. Se ejecutan automáticamente hasta `N` rondas de refinamiento.
4. **Generación de narrativa:** Una vez hallada la estrategia óptima, una segunda llamada al LLM traduce los parámetros matemáticos a un informe sociológico o ejecutivo legible — campañas, palancas de política, acciones organizacionales — adaptado al modo operativo elegido.

### Modos Operativos

| Modo | Dominio | Vocabulario |
|---|---|---|
| **Macro** | Política, redes sociales masivas, polarización pública | Campañas mediáticas, hashtags virales, cámaras de eco, polarización electoral, nodos influyentes |
| **Corporativo** | RRHH, cambio organizacional, liderazgo interno | Sesiones 1:1, reuniones interdepartamentales, comunicación top-down, planes 30-60-90 días, alineación con OKRs |

En el **Modo Corporativo**, el Arquitecto Social identifica a los líderes informales (alta centralidad de intermediación) como objetivos prioritarios de intervención, generando planes de acción específicos para la organización en lugar de estrategias mediáticas.

### Salida Clave: `StrategyMatrix`

El Arquitecto Social devuelve una `StrategyMatrix` validada — un calendario de intervenciones estructurado que indica, para cada ventana temporal: el régimen matemático, sus parámetros de ajuste, los nodos objetivo (opcional) y una justificación en lenguaje natural para esa fase. Este calendario puede exportarse, reproducirse en el simulador o usarse como hoja de ruta para una campaña real.

> **Ejemplo de objetivo →** *"Estabilizar la aprobación de los empleados durante una reestructuración organizacional."*
> **Salida →** Un plan de 3 fases: primero cohesión basada en homofilia entre líderes de equipo, luego un régimen de memoria para estabilizar, y finalmente un impulso de comunicación top-down focalizado — con una narrativa de RRHH completa que explica cada fase en lenguaje consultivo.

## Instalación

```bash
pip install -r requirements.txt
```

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
├── tests/                     # Pruebas unitarias e integración
│   ├── test_energy_core.py    # Suite de pruebas del motor energético (42 tests)
│   ├── test_simulator.py      # Pruebas del núcleo simulador
│   ├── test_social_architect.py
│   └── test_visualizations.py
├── docs/                      # Fuentes de documentación MkDocs
├── .gitignore
├── app.py                     # Interfaz Streamlit
├── cache_manager.py           # Caché RAM + SQLite para paisajes sociales
├── energy_engine.py           # Motor de dinámica de Langevin (SocialEnergyEngine)
├── energy_runner.py           # Orquestador de simulaciones Langevin
├── energy_schemas.py          # Esquemas Pydantic v2 para EnergyConfig
├── i18n.py                    # Ayudantes de internacionalización
├── programmatic_architect.py  # Arquitecto Programático (arquetipos + caché + LLM)
├── README.md                  # Documentación (inglés)
├── README_ES.md               # Documentación (español)
├── requirements.txt           # Dependencias
├── schemas.py                 # Esquemas Pydantic para StrategyMatrix
├── simulator.py               # Núcleo del simulador y lógica LLM
├── social_architect.py        # Agente de ingeniería inversa Arquitecto Social
└── visualizations.py          # Ayudantes de visualización de red
```

## Licencia Ética

Este proyecto está bajo la **Prosperity Public License 3.0.0**.

- **Uso Comunal/Personal/Educativo:** Gratuito y libre.
- **Uso Corporativo:** Las empresas pueden probar el software por 30 días. Tras ese periodo, deben adquirir una licencia comercial.

Para consultas comerciales, contactar a [Adlgr87](https://github.com/Adlgr87) on GitHub.

---
*Desarrollado con un enfoque en la interpretabilidad de la IA y el estudio de sistemas sociales complejos.*