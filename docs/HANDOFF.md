# Traspaso entre roles · Territorial Review DSS (sintético)

> Cada traspaso tiene entregables verificables y un criterio de aceptación. Quien recibe puede
> **rechazar** el traspaso; si lo rechaza, el sistema no avanza de etapa. Los roles corresponden a
> `student_inputs/raci.csv`, validado en modo estricto (exactamente un Accountable por actividad).
> En este expediente individual, el estudiante asume todos los roles. Las firmas registran qué
> evidencia revisó en cada rol.

## T1 · Data Engineer → Data Scientist (datos listos para modelar)
| Entregable | Criterio de aceptación | Evidencia |
|---|---|---|
| Datos versionados | El SHA-256 coincide con el Datasheet | `tests/test_e08.py::test_datasheet_hash_matches_data` |
| Contrato de esquema | Sin identificadores directos y `target` binario | `tests/test_privacy.py`, `tests/test_data.py` |
| Inventario y retención | Cada columna tiene finalidad, uso, minimización y retención | `docs/DATA_INVENTORY.csv`, `tests/test_e08.py` |
| Aviso de cambios en la ingesta | Todo cambio de ingesta se anuncia antes de producción (actividad nueva tras el simulacro) | `student_inputs/raci.csv` («Data pipeline change management») |

## T2 · Data Scientist → ML Engineer (modelo listo para operar)
| Entregable | Criterio de aceptación | Evidencia |
|---|---|---|
| Modelo serializado y hash | El hash coincide con la Model Card | `docs/MODEL_CARD.md`, `reports/lab13/TRACE_MANIFEST.json` |
| Auditoría de equidad | Puertas evaluadas con IC 95 %; grupos sin soporte declarados | `reports/e07/` |
| Atributo protegido | No es feature ni se usa al decidir | `monitoring.model_features_ok`, `tests/test_e08.py` |
| Límites | Usos fuera de alcance y condición de retiro documentados | `docs/MODEL_CARD.md` |

## T3 · ML Engineer → Product Owner (sistema listo para el piloto)
| Entregable | Criterio de aceptación | Evidencia |
|---|---|---|
| Decisión trazable | El JSON incluye estado, puertas, versión, hashes, evidencia y acción humana | `reports/lab13/deployment_decision.json` |
| Monitoreo | Umbrales de calidad, PSI y desempeño configurados, con soporte mínimo | `configs/governance.yml`, `src/inf8239_u04/monitoring.py` |
| Runbook probado | Simulacro ejecutado con detección, STOP, rollback y postmortem | `reports/lab13/INCIDENT_POSTMORTEM.md` |
| Aplicación | Muestra la advertencia de datos sintéticos, la decisión gobernada y la acción humana | `app.py`, `tests/test_app.py` |

## T4 · Product Owner → Institutional Owner (autorización)
| Entregable | Criterio de aceptación | Evidencia |
|---|---|---|
| Recomendación final | Una puerta técnica GO no amplía la decisión humana (LIMITAR) | `governed_recommendation`, `tests/test_e08.py` |
| Normativa | Cada exigencia está clasificada como obligación legal, marco voluntario o recomendación ética | `docs/NORMATIVE_MATRIX.csv` |
| EIED y registro | Si lo opera una entidad pública: evaluación previa y registro (Decreto 787-26) | `docs/NORMATIVE_MATRIX.csv` (N04, N14) |

## T5 · Operación diaria (Reviewer Analyst ↔ Product Owner)
* Cada caso priorizado lo revisa una persona, que **registra su acción**: confirmar, descartar o
  escalar.
* Se revisa además una muestra aleatoria del 5 % de los casos de baja prioridad.
* Las apelaciones (5 días hábiles) las atiende un revisor distinto del original.

## Registro de firmas
| Traspaso | Entrega | Recibe | Fecha | Resultado |
|---|---|---|---|---|
| T1 | Data Engineer | Data Scientist | 08-11-2026 | Aceptado |
| T2 | Data Scientist | ML Engineer | 08-11-2026 | Aceptado |
| T3 | ML Engineer | Product Owner | 08-11-2026 | Aceptado tras el simulacro, con acciones correctivas 2 a 5 pendientes |
| T4 | Product Owner | Institutional Owner | 08-11-2026 | **LIMITAR**: piloto acotado; no desplegar sin restricciones |

Firmado en todos los roles: Melvin H. Rivas Genao (100279298), estudiante. El ejercicio es
individual.
