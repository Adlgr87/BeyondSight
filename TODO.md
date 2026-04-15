# TODO - Realtime Serialization Pipeline (BeyondSight)

- [x] 1. Extender `schemas.py` con modelos Pydantic de visualización en tiempo real.
- [x] 2. Crear `realtime_bridge.py` con mapping de estado del simulador -> `VisualizationState`.
- [ ] 3. Extender `simulator.py` con generador de ticks serializables en tiempo real.
- [ ] 4. Mejorar `visualizations.py` para consumir payload técnico (event ticker / densidad).
- [ ] 5. Integrar en `app.py` la vista dual sincronizada por tick (técnica + cartoon).
- [ ] 6. Documentar payload/flujo en `docs/api.md` y actualizar `README_ES.md`.
- [ ] 7. Agregar pruebas en `tests/test_realtime_bridge.py`.
- [ ] 8. Ejecutar tests y ajustar errores.
