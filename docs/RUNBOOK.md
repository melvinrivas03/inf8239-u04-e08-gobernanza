# Runbook de incidentes · Territorial Review DSS (sintético)

> Versión de política `u04-e08-1.0` (`configs/governance.yml`). Probado con el simulacro
> INC-2026-12-01 (`reports/lab13/INCIDENT_POSTMORTEM.md`). Los roles corresponden a
> `student_inputs/raci.csv`. Principio: **una puerta fallida produce REVIEW o STOP, nunca se oculta.**

## 1. Detección y clasificación
**Señales sin etiquetas** (cada corte quincenal, `src/inf8239_u04/monitoring.py`):
* **Contrato de calidad:** proporción de `previous_incidents == 0` por zona. Si aumenta más de 0.15
  respecto a la referencia, la zona queda en ALERTA. Con menos de 5 casos en la zona se marca SIN
  SOPORTE.
* **Contrato de datos:** el modelo no recibe identificadores directos, `case_id` ni el grupo
  protegido.
* **PSI** por variable contra la referencia de entrenamiento (5 cuantiles): REVISAR desde 0.10 y
  ALERTA desde 0.25. Con menos de 100 casos es INDICATIVO: en los meses limpios de prueba, con unos
  50 casos, el PSI llegó a 0.24 sin cambio real.

**Señales con etiquetas** (mensual, cuando termina la revisión humana): recall global, recall por
grupo y brechas de recall y FPR. Sólo se interpretan con 100 casos o más por ventana y al menos 5
positivos y 5 negativos por grupo.

| Severidad | Disparadores | Estado | Quién responde |
|---|---|---|---|
| **SEV-1** | Contrato de datos o de calidad violado; uso prohibido; brecha > 2 × tolerancia (> 0.32) con soporte | **STOP** del alcance afectado (segmento o sistema) | ML Engineer (R) · Institutional Owner (A) |
| **SEV-2** | Puerta de recall o de brecha fallida con soporte; PSI en ALERTA con n ≥ 100 | **REVIEW** con contención | ML Engineer (R) · Product Owner (A) |
| **SEV-3** | Señales indicativas sin soporte; PSI en REVISAR | **REVIEW** sin contención, con vigilancia reforzada | Data Scientist (R) · Product Owner (A) |

## 2. Autoridad de contención
* **STOP** lo declara el Institutional Owner, o el ML Engineer si el primero no está disponible en
  4 horas. Se informa al Institutional Owner, que debe ratificarlo o revocarlo en 24 horas.
* **Contención estándar:** los casos del alcance afectado salen del ranking y pasan a una cola
  manual por orden de llegada. Ningún caso se cierra ni se descarta por el sistema.
* **Fallback:** la regla transparente (`previous_incidents ≥ 3`) sólo se usa si la falla no afecta
  a `previous_incidents`. En el simulacro sí la afectaba y la regla tuvo el mismo recall que el
  modelo dañado (0.483). Por eso el fallback por defecto es la **cola manual**.

## 3. Preservación de evidencia
* Al declarar SEV-1 o SEV-2 se toma una instantánea en `reports/lab13/incident/`: deriva, calidad,
  métricas por ventana, desempeño y log de casos puntuados (sin el atributo protegido).
* Se genera `EVIDENCE_MANIFEST.json` con el SHA-256 de cada archivo. También se registran el hash
  del modelo, de los datos y de la política, y el commit (`trace_manifest`).
* Es de solo lectura y se conserva 36 meses (`retention.incident_evidence_months`).

## 4. Comunicación
* **Interna (día 0–1):** el Institutional Owner, el Product Owner, Data Engineering y el Data
  Protection Officer reciben la severidad, el alcance, la contención y la hora de la próxima
  actualización.
* **Personas afectadas (día 1):** el Product Owner (R) comunica, con el Institutional Owner (A), a
  los representantes de las zonas afectadas. Explica qué falló, que el sistema no cerró ningún
  caso, cómo se revisan sus casos y cómo apelar (5 días hábiles).
* **Registro:** se anota el incidente en el registro del sistema. En la administración pública, el
  Decreto 787-26 exige monitoreo y corrección de sesgos.

## 5. Rollback o línea base segura
1. Identificar el último estado sano: versión de ingesta, modelo y política (`trace_manifest`).
2. Revertir el componente defectuoso. En el simulacro fue la ingesta v2 → v1; el modelo no cambió y
   su hash se verificó.
3. Volver a puntuar el periodo afectado y repetir `classify`. **Criterio de salida:** sin SEV-1 ni
   SEV-2. Si queda SEV-3 por falta de soporte, se reanuda bajo LIMITAR, pero no se declara GO.
4. Revisar manualmente los casos afectados que fueron puntuados durante el incidente.

## 6. Postmortem, responsable y fecha
* Debe hacerse en 30 días como máximo. Lo hace el Product Owner (R) y lo aprueba el Institutional
  Owner (A). Es una revisión sin culpables.
* Incluye cronología, impacto por grupo, causa raíz, acciones correctivas con R, A y fecha límite,
  y lecciones aprendidas.
* Plantilla y ejemplo: `reports/lab13/INCIDENT_POSTMORTEM.md`, generado por
  `scripts/simulate_incident.py`.
* Se actualizan la Model Card, el Datasheet y la evaluación de impacto si cambian los límites o los
  riesgos.
