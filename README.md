# U04.E08 · Expediente de gobernanza y simulacro

**INF-8239 Ciencia de Datos II** · Unidad 04 · Ética y roles en Ciencia de Datos
Estudiante: Melvin H. Rivas Genao · Matrícula 100279298 · Docente: Edwin Ramón José Nolasco

Este expediente integra **LAB13** (DSS gobernado: inventario, Datasheet y Model Card, RACI, monitoreo,
runbook y simulacro) sobre el mismo sistema de U04.E07. El historial de Git conserva LAB11, LAB12 y
E07.

El sistema es un DSS sintético que **sugiere el orden de revisión humana** de casos territoriales. Los
datos son sintéticos y didácticos, y el sistema no autoriza decisiones automáticas.

## Decisión final: **LIMITAR** (se mantiene)

| Capa | Resultado | Fuente |
|---|---|---|
| Puerta técnica del curso | **GO**: recall 0.717; brechas de recall 0.138 y de FPR 0.125; 3.6 KB; menos de 1 ms | `reports/lab13/deployment_decision.json` |
| Incertidumbre (E07) | El IC 95 % de las brechas llega a 0.32 y 0.40 | `reports/e07/bootstrap_gaps_baseline.csv` |
| Simulacro | Un defecto de datos en dos zonas dejó el recall de G1 en 0.278; STOP de segmento y rollback | `reports/lab13/INCIDENT_POSTMORTEM.md` |
| **Decisión gobernada** | **LIMITAR**: un GO técnico no amplía la autoridad del sistema | `governed_recommendation` |

LIMITAR significa un piloto en el que el sistema sólo ordena. Todos los casos los revisa una persona,
que registra su acción. Hay apelación en 5 días hábiles y una muestra aleatoria del 5 % de los casos
de baja prioridad. El monitoreo es quincenal sin etiquetas y mensual con etiquetas, y existe una
condición de retiro.

No se elige DESPLEGAR porque los IC son amplios, las ventanas son pequeñas y el sistema depende de
una sola variable frágil. Tampoco NO UTILIZAR, porque el riesgo es controlable con supervisión humana
y la cola manual es un estado seguro probado.

## Inicio rápido

```bash
uv sync --frozen
uv run pytest -q                              # 49 pruebas (10 curso + 14 E07 + 25 E08)
uv run python scripts/lab13_governance.py     # decisión trazable + TRACE_MANIFEST.json
uv run python scripts/simulate_incident.py    # simulacro, evidencia con hashes y postmortem
uv run streamlit run app.py                   # aplicación (AppTest en tests/test_app.py)
```

## Mapa de la rúbrica

| Criterio | Artefactos editables | Pruebas |
|---|---|---|
| Inventario, minimización y retención | `docs/DATA_INVENTORY.csv` (14 elementos) y `configs/governance.yml` (`retention`) | `test_inventory_*`, `test_every_row_has_purpose_retention_and_norm_type` |
| Datasheet y Model Card trazables | `docs/DATASHEET.md` (Gebru et al.), `docs/MODEL_CARD.md` (hashes de datos, política y modelo) y `reports/lab13/TRACE_MANIFEST.json` | `test_datasheet_hash_matches_data`, `test_model_card_matches_current_versions` |
| RACI y traspaso entre roles | `student_inputs/raci.csv` (16 actividades, un único A en cada una) y `docs/HANDOFF.md` (T1–T5 con criterios y firmas) | `test_project_raci_*`, `test_strict_raci_*` |
| Monitoreo, runbook y simulacro | `src/inf8239_u04/monitoring.py`, `incident.py`, `docs/RUNBOOK.md`, `reports/lab13/incident/` (manifiesto SHA-256) y `INCIDENT_POSTMORTEM.md` | `test_quality_contract_*`, `test_drill_*`, `test_unsupported_performance_never_returns_go` |
| Pruebas, Git y calidad documental | 49 pruebas, `ruff`, etiqueta `u04-lab13` y `docs/AI_USE_DECLARATION.md` | `uv run pytest -q` |

`docs/NORMATIVE_MATRIX.csv` distingue **obligación legal** (condicionada a datos reales o a la
administración pública), **marco voluntario** y **recomendación ética** (N01–N20).

## Cambios respecto al proyecto base
* **`scripts/simulate_incident.py`.** Se corrigió un `SyntaxError` del original y ahora ejecuta el
  simulacro completo.
* **`scripts/lab13_governance.py`.** Valida el RACI en modo estricto y produce una decisión trazable.
* **`governance.py`.** Añade STOP, `trace_manifest` y `governed_recommendation`, y mantiene la
  compatibilidad con la prueba del curso.
* **Archivos nuevos.** `monitoring.py`, `incident.py` y `tests/test_e08.py`.
* **`app.py`.** Muestra la decisión gobernada, la trazabilidad y el simulacro.

## Uso de IA
Se usó Claude (Anthropic). Ver [`docs/AI_USE_DECLARATION.md`](docs/AI_USE_DECLARATION.md). Esa
declaración indica qué valores decidió el estudiante y cuáles propuso la IA para que el estudiante
los validara. El estudiante responde por las referencias, la interpretación normativa, el código y
las conclusiones.
