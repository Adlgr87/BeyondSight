# BeyondSight Recovery Checkpoint

## Estado actual
- [x] Confirmado: `simulator.py` en `main` está truncado/incompleto (solo imports, sin implementación funcional).
- [x] Confirmado: hay incompatibilidad entre tests y APIs actuales (`tests/test_social_architect.py` usa firmas antiguas).
- [x] Confirmado: `requirements.txt` ya incluye `networkx` y `python-dotenv`.

## Plan de remediación (bloqueantes primero)
- [ ] Reimplementar `simulator.py` completo y funcional, con API compatible para:
  - [ ] `social_architect.py` (`simular`, `simular_multiples`, `resumen_historial`, `get_graph_metrics`, `DEFAULT_PAYOFF_MATRIX`)
  - [ ] `tests/test_simulator.py` (`calcular_efecto_grupos`, firma legacy de `simular`)
- [ ] Revisar y corregir `app.py` para que arranque limpio sin imports inválidos.
- [ ] Ejecutar pruebas y corregir fallos de integración.
- [ ] Revisar docs/licencia para inconsistencias observables (AGPL vs LICENSE) y registrar estado.
- [ ] Entregar estado final con evidencia de ejecución.

## Progreso detallado
- [x] Checkpoint reabierto.
- [x] Diagnóstico inicial realizado.
- [ ] Implementación en curso.
