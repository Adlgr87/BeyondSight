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

Simulador híbrido de dinámica social — Núcleo numérico + LLM como selector de régimen.

BeyondSight cierra la brecha entre los modelos matemáticos clásicos de formación de opinión y la flexibilidad contextual de los Modelos de Lenguaje de Gran Escala (LLMs).

## Fundamentos Teóricos e Investigación

El proyecto se inspira en modelos fundamentales de dinámica de opinión y en investigación de vanguardia:

- **Modelos de DeGroot y Friedkin-Johnsen:** Implementación base para la evolución de opiniones en redes sociales, considerando la influencia de vecinos y la resistencia al cambio (prejuicios).
- **Conexión Académica:** El enfoque de BeyondSight resuena con investigaciones recientes como *"Opinion Consensus Formation Among Networked Large Language Models"* (Enero 2026), explorando cómo los agentes inteligentes pueden alcanzar consensos o polarización en redes complejas.
- **Arquitectura Híbrida:** A diferencia de las simulaciones puramente numéricas, BeyondSight utiliza un LLM (como Llama 3) para analizar la trayectoria histórica y decidir qué régimen de transición (Lineal, Umbral, Backlash) es sociológicamente más coherente en cada paso.

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
├── archive/           # Versiones históricas y logs (ignorados por git)
├── tests/             # Pruebas unitarias del simulador
├── .gitignore         # Configuración de archivos ignorados
├── app.py             # Interfaz Streamlit
├── README.md          # Documentación y Meta-datos
├── requirements.txt   # Dependencias
└── simulator.py       # Núcleo del simulador y lógica LLM
```

## Licencia Ética

Este proyecto está bajo la **Prosperity Public License 3.0.0**.

- **Uso Comunal/Personal/Educativo:** Gratuito y libre.
- **Uso Corporativo:** Las empresas pueden probar el software por 30 días. Tras ese periodo, deben adquirir una licencia comercial.

Para consultas comerciales, contactar a [Adlgr87](https://github.com/Adlgr87) en GitHub.

---
*Desarrollado con un enfoque en la interpretabilidad de la IA y el estudio de sistemas sociales complejos.*
