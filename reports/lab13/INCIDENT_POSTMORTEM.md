# Postmortem del simulacro · INC-2026-12-01 (U04.E08)

> Simulacro con datos sintéticos y reloj simulado. Generado 2026-11-08T23:22:24+00:00 con commit `d2a226b`, política `u04-e08-1.0`, datos `2af1858fe874…`, modelo `2b33ffa636a5…`. Revisión sin culpables.

## 1. Resumen
- **Escenario:** ingesta v2 convierte historial ausente en 0 (zonas Sur y Norte, desde 2026-12-01).
- **Detección:** SEV-1 → **STOP** (alcance ['Norte']). contrato de calidad violado (historial vacío) en zonas ['Norte']; PSI alto pero con n insuficiente (indicativo).
- **Confirmación con etiquetas:** SEV-1 → **STOP**. contrato de calidad violado (historial vacío) en zonas ['Norte', 'Sur']; PSI alto pero con n insuficiente (indicativo); recall 0.483 < 0.68 [n=46 < 100: indicativo]; recall_gap 0.540 > 0.16 [n=46 < 100: indicativo]; ventana sin soporte suficiente: no puede declararse GO.
- **Casos afectados:** 23 en diciembre; 78% pertenecen a G1.
- **Modelo sin cambios:** True (hash antes = hash después). La falla está en los datos, no en el modelo.

## 2. Impacto (mismos casos de diciembre, n = 46: indicativo)

| Escenario | Recall | Recall G1 | Recall G2 | Brecha recall | Brecha FPR |
|---|---|---|---|---|---|
| Ingesta v2 defectuosa | 0.483 | 0.278 | 0.818 | 0.540 | 0.117 |
| Fallback regla (≥ 3 incidentes) | 0.483 | 0.278 | 0.818 | 0.540 | 0.050 |
| Tras rollback a ingesta v1 | 0.793 | 0.667 | 1.000 | 0.333 | 0.433 |

La comparación es pareada (mismos casos, sólo cambia la ingesta), por lo que atribuye la caída de recall en G1 al defecto. La regla transparente de U04.E07 **no es un refugio seguro** aquí: usa la misma variable dañada.

## 3. Cronología (reloj simulado)

| Fecha | Fase | Evento |
|---|---|---|
| 2026-12-01 | cambio | Ingesta v2 activada en Sur y Norte (cambio no comunicado al equipo del modelo) |
| 2026-12-15 | detección | Monitoreo quincenal sin etiquetas: SEV-1 → STOP |
| 2026-12-15 | contención | STOP de segmento: el registro de cambios muestra que Norte y Sur comparten la ingesta v2, así que ambas salen del ranking (23 casos de diciembre); cola manual por orden de llegada. Este, Oeste siguen en REVIEW bajo LIMITAR |
| 2026-12-15 | evidencia | Instantánea de reportes, hashes y versión de modelo/política |
| 2026-12-16 | comunicación | Aviso interno al Institutional Owner y a Data Engineering; aviso a representantes afectados |
| 2026-12-18 | rollback | Ingesta revertida a v1; re-puntuación del periodo; verificación de puertas |
| 2027-01-10 | confirmación con etiquetas | Ventana de diciembre etiquetada: SEV-1 → STOP |
| 2027-01-14 | postmortem | Revisión sin culpables y acciones correctivas con responsables |

## 4. Contención, evidencia y rollback
- **Contención:** STOP de segmento (Norte y Sur, ingesta v2): sus casos salen del ranking y pasan a cola manual por orden de llegada; Este y Oeste siguen en REVIEW bajo LIMITAR. No se usó la regla como fallback porque depende de la misma variable.
- **Evidencia:** `reports/lab13/incident/` con `EVIDENCE_MANIFEST.json` (SHA-256 de cada archivo). El log operativo no contiene el atributo protegido.
- **Rollback:** ingesta v2 → v1 y re-puntuación del periodo. Verificación: SEV-3 → **REVIEW**. recall_gap 0.333 > 0.16 [n=46 < 100: indicativo]; fpr_gap 0.433 > 0.16 [n=46 < 100: indicativo]; ventana sin soporte suficiente: no puede declararse GO. Se reanuda la priorización bajo LIMITAR, pero no se declara GO hasta tener una ventana con ≥ 100 casos y soporte por grupo. Aun con datos limpios, diciembre muestra brechas por encima de 0.16 con sólo 46 casos: puede ser ruido muestral (U04.E07 ya reportó IC amplios), pero no se descarta; queda como acción 8.

## 5. Comunicación
- **Interna (día 0–1):** Institutional Owner (A del incidente), Product Owner, Data Engineering y Legal/Protección de datos: severidad, alcance, contención y próxima actualización.
- **Personas afectadas (día 1):** representantes de las zonas Norte y Sur: qué falló, que ningún caso fue cerrado por el sistema, que los casos de diciembre se revisan manualmente y cómo apelar (5 días hábiles).
- **Registro institucional:** anotación del incidente en el registro del sistema (Decreto 787-26, monitoreo y corrección de sesgos; aplicable si el sistema fuera de la administración pública).

## 6. Causa raíz
Un cambio de ingesta (v2) convirtió valores ausentes en 0 sin comunicarse al equipo del modelo. No existía un contrato de datos que exigiera aviso de cambios ni una prueba de completitud por zona antes de puntuar.

## 7. Acciones correctivas

| # | Acción | Responsable (R) | Rinde cuentas (A) | Fecha límite |
|---|---|---|---|---|
| 1 | Re-revisión manual de los 23 casos de diciembre de Norte/Sur | Reviewer Analyst | Product Owner | 2026-12-18 |
| 2 | Contrato de datos: ausente ≠ 0; `previous_incidents` nulo bloquea la puntuación del caso | Data Engineer | Product Owner | 2026-12-25 |
| 3 | Prueba de completitud por zona antes de puntuar (`quality_report`) en el pipeline | ML Engineer | Product Owner | 2026-12-25 |
| 4 | Gestión de cambios: todo cambio de ingesta requiere aviso y aprobación del ML Engineer (actividad RACI nueva) | Product Owner | Institutional Owner | 2026-12-29 |
| 5 | Fallback que no dependa de `previous_incidents` (cola manual) documentado en el runbook | ML Engineer | Product Owner | 2026-12-29 |
| 6 | Actualizar Model Card y Datasheet (limitación y dependencia de la variable) | Data Scientist | Product Owner | 2027-01-05 |
| 7 | Revisar en la EIED la dependencia del historial como factor de daño desigual | Product Owner | Institutional Owner | 2027-01-14 |
| 8 | Evaluar la ventana acumulada diciembre–enero (≥ 100 casos) y aplicar la regla de retiro de U04.E07 si la brecha persiste | Data Scientist | Product Owner | 2027-01-29 |

## 8. Lecciones
- La señal sin etiquetas (contrato de calidad) detectó el problema 26 días antes que las métricas con etiquetas.
- El PSI con ~50 casos es ruidoso (hasta 0.24 en meses limpios): se reporta como indicativo y no decide por sí solo.
- Un defecto técnico aparentemente neutral (por zona) produjo daño desigual por grupo: monitorear por grupo es obligatorio.
