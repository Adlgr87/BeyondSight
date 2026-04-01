# BeyondSight

Simulador híbrido de dinámica social — Núcleo numérico + LLM como selector de régimen.

## Instalación

```bash
pip install -r requirements.txt
```

## Correr sin LLM (modo heurístico, no requiere Ollama)

```bash
python simulator.py
```

## Correr la interfaz Streamlit

```bash
streamlit run app.py
```

## Correr con LLM real (Ollama)

1. Instalar Ollama: https://ollama.ai
2. En una terminal: `ollama serve`
3. Descargar modelo: `ollama pull llama3:8b`
4. En la interfaz Streamlit, activar el toggle "Usar Ollama"

## Estructura

```
BeyondSight/
├── archive/           # Versiones históricas y logs (ignorados por git)
├── tests/             # Pruebas unitarias del simulador
├── .gitignore         # Configuración de archivos ignorados
├── app.py             # Interfaz Streamlit
├── README.md          # Documentación detallada
├── requirements.txt   # Dependencias del proyecto
└── simulator.py       # Núcleo del simulador
```

## Archivos en revisión

Los archivos `beyondsight_python_20260331_*.py` se mantienen como histórico de apoyo en la carpeta `archive/`.

## Añadir nuevas reglas

En `simulator.py`, define una función `regla_nueva(estado, params) -> dict`
y agrégala al diccionario `REGLAS["campana"]` con un ID entero.
El LLM la verá automáticamente si actualizas el prompt en `_construir_prompt`.

## Licencia

Este proyecto está bajo la **Prosperity Public License 3.0.0**.

- **Uso Comunal/Personal:** Gratuito y libre para individuos, estudiantes y organizaciones sin fines de lucro.
- **Uso Corporativo:** Las empresas pueden probar el software por 30 días. Tras ese periodo, deben adquirir una licencia comercial.

Para consultas sobre licencias comerciales, por favor contactar al autor [Adlgr87](https://github.com/Adlgr87) a través de GitHub.
