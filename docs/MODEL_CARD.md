# Model Card · Territorial Review DSS (sintético) · regresión logística del curso

> Completada en U04.E07 (LAB11–LAB12) y ampliada en U04.E08 (LAB13) con versiones, monitoreo y
> simulacro. Datasheet: `docs/DATASHEET.md`.

## Versions and traceability
| Elemento | Versión / SHA-256 |
|---|---|
| Política | `u04-e08-1.0` (`configs/governance.yml`, `b9f59e1a999eca2ca28212b1f9b6a3bbc01af104469608c9cd9315a0b462f3ea`) |
| Datos | `2af1858fe874f3914b0f9bfe068fd876cb716186694a6ece9a16e8c929128a01` |
| Modelo v1.0 | `models/model.joblib`, `2b33ffa636a5e025b6931403dcadc8013b2ecf1d4e24b3e133b4c3580eae5f42` (reproducible con `uv.lock`; el archivo no se versiona en Git) |
| Código | etiqueta `u04-lab13` |
| Decisión | `reports/lab13/deployment_decision.json`: puerta técnica **GO** → decisión gobernada **LIMITAR** |

Cada decisión lleva el manifiesto `trace_manifest()` con estas versiones, más el commit y la hora.
`tests/test_e08.py` falla si los datos o la política cambian sin actualizar esta ficha.

## Intended use
Sugerir el **orden de revisión humana** de casos territoriales sintéticos. Es apoyo a la decisión: un
analista revisa y firma cada caso, y ningún caso se descarta. Decisión vigente: **LIMITAR**, es decir,
piloto acotado (ver `reports/lab11/DECISION_RECORD.md`).

## Out-of-scope use
* Intervención automática, decisión de elegibilidad y declaración de emergencia
  (`configs/governance.yml`).
* Usar el grupo protegido para decidir; perfilar personas o zonas.
* Usar el sistema con datos reales sin una nueva evaluación de impacto. Si lo opera una entidad
  pública, eso incluye la evaluación de impacto ético y de derechos del Decreto 787-26.

## Data and split
* `data/territorial_risk_synthetic.csv`: 640 casos sintéticos, con una tasa positiva de 0.552.
* Grupos: G1 con 396 casos (tasa base 0.497) y G2 con 244 (tasa base 0.639).
* **Corte temporal**: entrenamiento hasta el 24-09-2026 (480 casos) y prueba desde el 25-09-2026
  (160 casos: 101 de G1 y 59 de G2).
* Variables del modelo: `zone`, `age_band`, `previous_incidents`, `infrastructure_score` y
  `exposure`.
* `protected_group` se **excluye del modelo** y sólo se usa para auditar.

## Global and subgroup evaluation (prueba)
| Métrica | Global | G1 | G2 | Brecha [IC 95 %] |
|---|---|---|---|---|
| Recall | 0.717 | 0.653 | 0.791 | 0.138 [0.010, 0.318] |
| FPR | 0.279 | 0.250 | 0.375 | 0.125 [0.006, 0.398] |
| Tasa de selección | 0.531 | 0.446 | 0.678 | 0.232 |
| Accuracy | 0.719 | 0.703 | 0.746 | — |

La auditoría interseccional (grupo × banda de edad) está en `reports/e07/intersectional_baseline.csv`.
4 de las 8 intersecciones no tienen soporte suficiente (n < 20, o menos de 5 positivos o negativos):
se reportan, pero no se interpretan como brechas. La comparación con otros 6 candidatos está en
`reports/e07/candidates.csv`.

## Green AI evidence
* Logística: 3.6 KB, entrenamiento en unos 0.02 s, unos 0.02 ms por caso.
* El árbol ocupa el doble (7.9 KB), no mejora el recall y falla las dos puertas de brecha.
* ExponentiatedGradient ocupa 135 KB y empeora la brecha de FPR.

Se elige la opción suficiente.

## Limitations, human oversight and appeal
* Datos sintéticos: sin validez externa.
* Muestra de prueba pequeña: los intervalos son amplios.
* Tasas base distintas: las tasas de error no pueden igualarse todas a la vez.
* Una brecha no prueba discriminación causal.
* Supervisión humana en todos los casos, con revisión aleatoria del 5 % de los casos de baja prioridad.
* Apelación ante un revisor distinto en 5 días hábiles.
* Condición de retiro definida en el registro de decisión.

## Monitoring and incident drill (U04.E08)
* **Monitoreo:** cada 15 días, contrato de calidad por zona y PSI, sin necesidad de etiquetas.
  Cada mes, recall y brechas por grupo, sólo con 100 casos o más (`docs/RUNBOOK.md`).
* **Simulacro INC-2026-12-01:** la ingesta v2 de Norte y Sur convirtió el historial ausente en 0.
  * **Impacto:** el recall de G1 bajó de 0.667 a 0.278 en los mismos 46 casos de diciembre, y el
    78 % de los casos afectados era de G1.
  * **Detección:** el contrato de calidad lo detectó en el primer corte quincenal (SEV-1 → STOP de
    segmento).
  * **Rollback:** se revirtió la ingesta y se verificó REVIEW, porque con 46 casos no puede
    declararse GO. El modelo no cambió (mismo hash).
* **Nueva limitación:** el modelo y la regla de respaldo dependen de `previous_incidents`. Un
  defecto en esa variable afecta a ambos, así que el estado seguro es la cola manual.

## Owner and review date
Institutional Owner (A) y Data Scientist (R de validación del modelo). Expediente preparado por
Melvin H. Rivas Genao el 8 de noviembre de 2026. La próxima revisión es al cerrar la primera ventana
mensual del piloto con 100 casos o más, o antes si cualquier cambio de datos o de política altera los hashes.
