# Declaración de uso de IA · U04.E08

**Estudiante:** Melvin H. Rivas Genao · Matrícula 100279298 · U04.E08 · 8 de noviembre de 2026.

**Herramienta:** Claude (Anthropic), modelo Claude Opus 5.5, en la aplicación Claude con un entorno
de ejecución en la nube. Los commits del repositorio la identifican como coautora.

**Finalidad:** estructura del expediente, código de monitoreo y del simulacro, pruebas, búsqueda y
verificación de fuentes (Ley 172-13, Gebru et al.) y borradores de redacción.

## Valores: quién los decidió

| Valor | Origen | Dónde |
|---|---|---|
| Daño prioritario (falso negativo), tolerancia 0.16 y decisión **LIMITAR** | Estudiante, en U04.E07; se mantiene | `student_inputs/lab12_decision.yml`, `configs/governance.yml` |
| Retención: 12 meses activos + 12 de bloqueo; log de predicciones y auditoría 24 meses; evidencia 36 meses | Propuesto por la IA. **Lo valida el estudiante** | `configs/governance.yml` (`retention`) |
| STOP si la brecha supera 2 × la tolerancia; severidades SEV-1 a SEV-3 | Propuesto por la IA. **Lo valida el estudiante** | `configs/governance.yml`, `docs/RUNBOOK.md` |
| Umbrales de PSI (0.10 y 0.25) | Convención de la industria, no norma | `configs/governance.yml` |
| Umbral de calidad (+0.15 de historial vacío) y mínimo de 100 casos | La IA lo propuso. El mínimo de 100 casos viene de la regla de retiro de U04.E07 | `configs/governance.yml` |
| Escenario del simulacro (ingesta v2 en Norte y Sur) | Propuesto por la IA como caso realista | `src/inf8239_u04/incident.py` |

La IA **no inventó evidencia**. Todas las cifras salen de ejecutar el código sobre los datos del
curso. El defecto del simulacro se inyecta de forma explícita y determinista, y se declara como
simulación.

## Fragmentos afectados

| Archivo | Aporte de la IA | Revisión humana |
|---|---|---|
| `src/inf8239_u04/monitoring.py`, `src/inf8239_u04/incident.py` | Código nuevo: PSI, contrato de calidad, métricas por ventana, severidad y simulacro | Ejecución, lectura y pruebas |
| `src/inf8239_u04/governance.py` | RACI estricto, `trace_manifest`, estado STOP y `governed_recommendation`; se mantiene compatible con el curso | Pruebas del curso y nuevas |
| `scripts/simulate_incident.py`, `scripts/lab13_governance.py` | Corrección y ampliación | Ejecutados sin errores |
| `tests/test_e08.py` | 25 pruebas nuevas | 49 de 49 en verde |
| `docs/DATA_INVENTORY.csv`, `DATASHEET.md`, `RUNBOOK.md`, `HANDOFF.md`, `MODEL_CARD.md`, `NORMATIVE_MATRIX.csv` (N14–N20), `student_inputs/raci.csv` | Borradores a partir de la evidencia | Cifras contrastadas con `reports/lab13/` |

## Prompts relevantes
1. Enunciado del Ejercicio 08 (propósito, mandato, uso responsable de IA y rúbrica) y la guía de
   LAB13.
2. Instrucción de continuar sobre el repositorio de U04.E07 para conservar la continuidad de la
   decisión LIMITAR.

## Verificaciones
* `uv run pytest -q`: 49 pruebas en verde (10 del curso, 14 de E07 y 25 de E08).
* `ruff check` sin errores en los archivos nuevos o modificados.
* `scripts/lab13_governance.py` produce GO en la puerta técnica y LIMITAR como decisión gobernada.
  `scripts/simulate_incident.py` produce STOP, después STOP confirmado y REVIEW tras el rollback.
* Hashes: los de datos, política y modelo de la Model Card coinciden con `TRACE_MANIFEST.json`
  (lo comprueba una prueba). El hash del modelo se mantuvo estable en dos ejecuciones.
* El PSI se calibró con los meses limpios: llega a 0.24 con unos 50 casos sin cambio real. Por eso
  se marca como indicativo.
* Ley 172-13: arts. 5, 6, 13 y 15, consultados en el texto publicado (bdi.com.do) el 08-11-2026.
  Gebru et al. (2021): DOI 10.1145/3458723, verificado.

## Errores detectados y correcciones
1. **`scripts/simulate_incident.py` del curso no compilaba.** Tenía un f-string con saltos de línea
   literales (`SyntaxError: unterminated f-string literal`) y dejaba la comunicación y las acciones
   como REPLACE. Se reescribió para ejecutar el simulacro y generar el postmortem desde los
   resultados.
2. **La puerta del curso sólo devolvía GO o REVIEW y no dejaba traza.** Se añadieron STOP, versión,
   política, evidencia y acción humana. La prueba del curso sigue pasando: una puerta fallida da
   REVIEW.
3. **El validador RACI del curso aceptaba «A and B» como Accountable.** Se añadió el modo estricto.
4. **Primer diseño del monitoreo.** El PSI se calculaba sobre lotes semanales de unos 10 casos y daba
   ALERTA en todas las variables, incluso en las no alteradas. También daba falsos STOP en el mes
   limpio. Se cambió a cortes quincenales, PSI indicativo con menos de 100 casos y contrato de
   calidad como señal principal.
5. **Supuesto falso de fallback seguro.** Se esperaba que la regla transparente de U04.E07 sirviera
   de respaldo. El simulacro mostró que falla igual (recall de G1 0.278), porque usa la misma
   variable. El estado seguro pasó a ser la cola manual.
6. **Hallazgo no resuelto.** Aun con datos limpios, diciembre (46 casos) muestra brechas por encima
   de 0.16. No se oculta: queda como acción correctiva 8.
7. **Limitación de fuentes.** El texto oficial del Decreto 787-26 sigue sin consultarse directamente,
   como en U04.E07.

*La clasificación normativa es académica y no constituye asesoría legal.*

---

## Anexo · Declaración de U04.E07 (se conserva sin cambios)

**Estudiante:** Melvin H. Rivas Genao · Matrícula 100279298 · U04.E07 · 8 de noviembre de 2026.

**Herramienta:** Claude (Anthropic), modelo Claude Opus 5.5, en la aplicación Claude con un entorno de
ejecución en la nube. Los commits del repositorio la identifican como coautora.

**Finalidad:** estructura del expediente, código de auditoría extendida, pruebas, búsqueda y
verificación de fuentes normativas y bibliográficas, y borradores de redacción.

## Lo que decidió el estudiante, no la IA

La IA presentó la evidencia y opciones con sus consecuencias. El estudiante eligió:
* el **daño prioritario**: falso negativo;
* la **métrica principal**: recall por grupo y brecha de recall;
* la **tolerancia**: 0.16 sobre la estimación puntual, con monitoreo del IC 95 %;
* la **decisión final**: LIMITAR.

Esos valores están en `student_inputs/lab12_decision.yml`.

## Fragmentos afectados

| Archivo | Aporte de la IA | Revisión humana |
|---|---|---|
| `src/inf8239_u04/audit_extra.py`, `scripts/e07_audit.py` | Código nuevo: IC por bootstrap, soporte mínimo, 7 candidatos, puertas con IC, figura y resumen NIST | Ejecución, lectura y pruebas |
| `tests/test_e07.py` | 14 pruebas nuevas | Ejecutadas: 24 de 24 pasan |
| `student_inputs/*.yml`, `*.csv` | Borradores de redacción a partir del caso y la evidencia; R09–R11 y su puntuación propuestos por la IA | Validados por el estudiante; R01–R08 conservan la probabilidad e impacto de la plantilla del curso |
| `docs/NORMATIVE_MATRIX.csv` | Clasificación en obligación legal, marco voluntario y recomendación ética, con fuentes | Revisión de la interpretación normativa por el estudiante |
| `reports/lab11/DECISION_RECORD.md`, `docs/MODEL_CARD.md` | Redacción a partir de `reports/e07/` | Cifras contrastadas con los CSV |

## Prompts relevantes

1. Enunciado del Ejercicio 07 (propósito, mandato y rúbrica) junto con las guías de LAB11 y LAB12.
2. Entrega del proyecto base `INF8239_U04_Gobernanza_DSS_Proyecto_Base_uv.zip`.
3. Elección de daño, tolerancia y decisión entre opciones presentadas con su evidencia.

## Verificaciones

* `uv run pytest -q`: 24 pruebas en verde (10 del curso y 14 nuevas).
* `scripts/lab11_impact.py`, `scripts/validate_lab12_decision.py` y `scripts/e07_audit.py` se
  ejecutan sin errores.
* Las cifras de los documentos provienen de `reports/e07/*.csv` y `*.json`.
* Las fuentes normativas se buscaron en la web, con fecha de consulta 8 de noviembre de 2026:
  * Ley 172-13 y artículos 39, 44 y 70 de la Constitución: fuentes oficiales y jurisprudencia del TC.
  * Decreto 498-23 (ENIA): PDF oficial de OGTIC.
  * Decreto 787-26: nota de la Presidencia y reseñas de prensa y de un despacho jurídico.

## Errores detectados y correcciones

1. **Script del curso con error de sintaxis.** `scripts/lab11_impact.py` tenía una cadena con saltos
   de línea literales (`SyntaxError`) y, además, sobrescribía `DECISION_RECORD.md` en cada ejecución.
   Se corrigió para crearlo sólo si no existe.
2. **Dependencia faltante.** Para generar la figura se añadió `matplotlib` a `pyproject.toml` y
   `uv.lock`.
3. **Lectura engañosa de las puertas.** La logística «cumple» sobre la estimación puntual, pero el IC
   95 % de las brechas llega a 0.32 y 0.40. Se añadió la puerta conservadora con el límite superior y
   se reporta que, con estos datos, ningún candidato la cumple.
4. **Hipótesis del proxy territorial.** Se esperaba que quitar `zone` mejorara la equidad. Mejoró la
   brecha de recall, pero triplicó la de FPR (0.327). Se documentó como compromiso, no como solución.
5. **Limitación de fuentes.** El texto oficial del Decreto 787-26 no pudo descargarse del portal de
   la Presidencia (error del sitio). Su descripción se apoya en fuentes secundarias concordantes y
   **debe verificarse contra el texto oficial** antes de citarlo en un trabajo final.

*La clasificación normativa es académica y no constituye asesoría legal.*
