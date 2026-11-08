# Datasheet · `territorial_risk_synthetic.csv`

> Sigue las preguntas de *Datasheets for Datasets* (Gebru et al., 2021). Completa la ficha breve
> `docs/DATASET_CARD.md` del curso. Inventario por columna, minimización y retención:
> `docs/DATA_INVENTORY.csv`.

| Campo | Valor |
|---|---|
| Archivo | `data/territorial_risk_synthetic.csv` |
| SHA-256 | `2af1858fe874f3914b0f9bfe068fd876cb716186694a6ece9a16e8c929128a01` (verificado por `tests/test_e08.py`) |
| Versión | v1.0, provista por el curso en `INF8239_U04_Gobernanza_DSS_Proyecto_Base_uv.zip` |
| Filas × columnas | 640 × 9, sin valores faltantes; `case_id` único |
| Periodo | 01-01-2026 a 27-12-2026 (fechas sintéticas) |
| Responsable de la ficha | Data Scientist (R) · Product Owner (A), según `student_inputs/raci.csv` |

## 1. Motivación
* **Para qué se creó:** practicar contratos de datos, evaluación temporal, auditoría por subgrupos
  y gobernanza de un sistema de apoyo a la decisión (DSS) en la Unidad 04.
* **Quién lo creó:** el equipo docente del curso, con una semilla educativa fija. El estudiante no
  conoce el generador; las afirmaciones sobre su proceso se limitan a lo que declara el curso.
* **Financiamiento:** no aplica.

## 2. Composición
* **Instancias:** casos territoriales **sintéticos**. No representan personas, lugares, tasas ni
  estadísticas oficiales de la República Dominicana.
* **Columnas:** `case_id` (seudónimo `CASE-0001`…), `received_date`, `zone` (Sur 164, Este 164,
  Oeste 157, Norte 155), `protected_group` (G1 396, G2 244), `age_band` (18-29 148, 30-44 163,
  45-59 150, 60+ 179), `previous_incidents` (0–9, mediana 3), `infrastructure_score` y `exposure`
  (índices 0–1) y `target` (1 = riesgo confirmado por revisión humana).
* **Etiqueta:** tasa positiva 0.552; G1 0.497 y G2 0.639. Las tasas base distintas impiden igualar a
  la vez todas las tasas de error (ver Model Card).
* **Datos sensibles:** `protected_group` se trata como dato sensible y, si representara origen
  étnico, como especialmente protegido (Ley 172-13, art. 6). Sólo se usa para auditar.
* **Identificadores directos:** ninguno. `validate_schema` rechaza `name`, `document_number`,
  `email` y `phone`.
* **Relación zona–grupo:** débil (G1 entre 59 % y 64 % según zona), pero suficiente para que un
  defecto por zona produzca daño desigual por grupo (simulacro, §6 del runbook).

## 3. Proceso de recolección
Generación sintética. No hubo consentimiento ni recolección de personas porque no existen sujetos.
**Si el sistema se usara con datos reales**, habría que documentar la fuente de cada campo, la base
legal del tratamiento, el aviso a los titulares y quién produce la etiqueta.

## 4. Preprocesamiento
* Se ordena por `received_date` y se aplica un corte temporal 75/25: entrenamiento hasta el
  24-09-2026 (480 casos) y prueba desde el 25-09-2026 (160 casos).
* El modelo aplica *one-hot* a `zone` y `age_band` y estandariza las tres variables numéricas.
* No se limpian ni imputan valores: no hay faltantes. **Lección del simulacro:** en producción,
  «ausente» no puede convertirse en 0 (acción correctiva 2 del postmortem).

## 5. Usos
* **Permitido:** docencia; prácticas de auditoría, monitoreo y simulacro.
* **Prohibido:** perfilamiento operativo, inferencias sobre poblaciones reales, intervención
  automática, decisiones de elegibilidad y declaración de emergencias (`configs/governance.yml`).
* **Riesgo de uso indebido:** presentar resultados sintéticos como evidencia sobre territorios
  reales. Toda salida lleva la advertencia «sintético» (prueba `test_app`).

## 6. Distribución
Se distribuye con el proyecto del curso. Este repositorio lo versiona para reproducibilidad; la
integridad se comprueba con el hash SHA-256.

## 7. Mantenimiento
* Un cambio en el archivo cambia el hash y hace fallar `tests/test_e08.py`. Eso obliga a actualizar
  esta ficha, la Model Card y la evaluación de impacto antes de volver a desplegar.
* Retención si los datos fueran reales: 12 meses activos, luego 12 meses bloqueados (Ley 172-13,
  art. 15) y después supresión (`configs/governance.yml`, sección `retention`).
