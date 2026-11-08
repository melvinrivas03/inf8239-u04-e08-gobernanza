# ruff: noqa: ISC004  (concatenación implícita intencional en las líneas largas del postmortem)
"""U04.E08 · Simulacro de incidente (corrige el script del curso, que no compilaba).

    uv run python scripts/simulate_incident.py

El original tenía un f-string con saltos de línea literales (``SyntaxError: unterminated
f-string literal``) y dejaba comunicación y acciones correctivas como REPLACE. Esta versión
ejecuta el simulacro completo (src/inf8239_u04/incident.py), preserva evidencia con hashes en
reports/lab13/incident/ y escribe reports/lab13/INCIDENT_POSTMORTEM.md a partir de los resultados.
"""
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from inf8239_u04.data import load_data
from inf8239_u04.governance import load_config, trace_manifest
from inf8239_u04.incident import CLOCK0, run_drill
from inf8239_u04.pipeline import run

OUT = Path("reports/lab13")
cfg = load_config()
df = load_data()
model = run(df, cfg["gates"])["model"]  # modelo v1.0 en producción (models/model.joblib)
r = run_drill(df, model, cfg, out_dir=OUT / "incident")
trace = trace_manifest()
P = r["performance"]
d, c, v = r["detection"], r["confirmation"], r["rollback_verification"]
due = lambda n: (CLOCK0 + timedelta(days=n)).isoformat()
fmt = lambda x: f"{x:.3f}"

lines = [
    "# Postmortem del simulacro · INC-2026-12-01 (U04.E08)",
    "",
    f"> Simulacro con datos sintéticos y reloj simulado. Generado {datetime.now(UTC).isoformat(timespec='seconds')} "
    f"con commit `{trace['code_commit']}`, política `{trace['policy_version']}`, datos `{trace['data_sha256'][:12]}…`, "
    f"modelo `{r['model_sha256_before'][:12]}…`. Revisión sin culpables.",
    "",
    "## 1. Resumen",
    f"- **Escenario:** {r['scenario']}.",
    f"- **Detección:** {d['severity']} → **{d['status']}** (alcance {d['scope']}). {'; '.join(d['reasons'])}.",
    f"- **Confirmación con etiquetas:** {c['severity']} → **{c['status']}**. {'; '.join(c['reasons'])}.",
    f"- **Casos afectados:** {r['affected_cases']} en diciembre; {r['affected_G1_share']:.0%} pertenecen a G1.",
    f"- **Modelo sin cambios:** {r['model_unchanged']} (hash antes = hash después). La falla está en los datos, no en el modelo.",
    "",
    "## 2. Impacto (mismos casos de diciembre, n = 46: indicativo)",
    "",
    "| Escenario | Recall | Recall G1 | Recall G2 | Brecha recall | Brecha FPR |",
    "|---|---|---|---|---|---|",
]
for name, key in [("Ingesta v2 defectuosa", "december_defective"), ("Fallback regla (≥ 3 incidentes)", "december_rule_fallback"),
                  ("Tras rollback a ingesta v1", "december_after_rollback")]:
    p = P[key]
    lines.append(f"| {name} | {fmt(p['recall'])} | {fmt(p['recall_G1'])} | {fmt(p['recall_G2'])} | {fmt(p['recall_gap'])} | {fmt(p['fpr_gap'])} |")
lines += [
    "",
    "La comparación es pareada (mismos casos, sólo cambia la ingesta), por lo que atribuye la caída de recall en G1 "
    "al defecto. La regla transparente de U04.E07 **no es un refugio seguro** aquí: usa la misma variable dañada.",
    "",
    "## 3. Cronología (reloj simulado)",
    "",
    "| Fecha | Fase | Evento |",
    "|---|---|---|",
] + [f"| {e['t']} | {e['fase']} | {e['evento']} |" for e in r["timeline"]] + [
    "",
    "## 4. Contención, evidencia y rollback",
    "- **Contención:** STOP de segmento (Norte y Sur, ingesta v2): sus casos salen del ranking y pasan a cola manual por orden de llegada; "
    "Este y Oeste siguen en REVIEW bajo LIMITAR. No se usó la regla como fallback porque depende de la misma variable.",
    "- **Evidencia:** `reports/lab13/incident/` con `EVIDENCE_MANIFEST.json` (SHA-256 de cada archivo). El log operativo no contiene el atributo protegido.",
    f"- **Rollback:** ingesta v2 → v1 y re-puntuación del periodo. Verificación: {v['severity']} → **{v['status']}**. {'; '.join(v['reasons'])}. "
    "Se reanuda la priorización bajo LIMITAR, pero no se declara GO hasta tener una ventana con ≥ 100 casos y soporte por grupo. "
    "Aun con datos limpios, diciembre muestra brechas por encima de 0.16 con sólo 46 casos: puede ser ruido muestral (U04.E07 ya "
    "reportó IC amplios), pero no se descarta; queda como acción 8.",
    "",
    "## 5. Comunicación",
    "- **Interna (día 0–1):** Institutional Owner (A del incidente), Product Owner, Data Engineering y Legal/Protección de datos: severidad, alcance, contención y próxima actualización.",
    "- **Personas afectadas (día 1):** representantes de las zonas Norte y Sur: qué falló, que ningún caso fue cerrado por el sistema, que los casos de diciembre se revisan manualmente y cómo apelar (5 días hábiles).",
    "- **Registro institucional:** anotación del incidente en el registro del sistema (Decreto 787-26, monitoreo y corrección de sesgos; aplicable si el sistema fuera de la administración pública).",
    "",
    "## 6. Causa raíz",
    "Un cambio de ingesta (v2) convirtió valores ausentes en 0 sin comunicarse al equipo del modelo. No existía un contrato de datos "
    "que exigiera aviso de cambios ni una prueba de completitud por zona antes de puntuar.",
    "",
    "## 7. Acciones correctivas",
    "",
    "| # | Acción | Responsable (R) | Rinde cuentas (A) | Fecha límite |",
    "|---|---|---|---|---|",
    f"| 1 | Re-revisión manual de los {r['affected_cases']} casos de diciembre de Norte/Sur | Reviewer Analyst | Product Owner | {due(3)} |",
    f"| 2 | Contrato de datos: ausente ≠ 0; `previous_incidents` nulo bloquea la puntuación del caso | Data Engineer | Product Owner | {due(10)} |",
    f"| 3 | Prueba de completitud por zona antes de puntuar (`quality_report`) en el pipeline | ML Engineer | Product Owner | {due(10)} |",
    f"| 4 | Gestión de cambios: todo cambio de ingesta requiere aviso y aprobación del ML Engineer (actividad RACI nueva) | Product Owner | Institutional Owner | {due(14)} |",
    f"| 5 | Fallback que no dependa de `previous_incidents` (cola manual) documentado en el runbook | ML Engineer | Product Owner | {due(14)} |",
    f"| 6 | Actualizar Model Card y Datasheet (limitación y dependencia de la variable) | Data Scientist | Product Owner | {due(21)} |",
    f"| 7 | Revisar en la EIED la dependencia del historial como factor de daño desigual | Product Owner | Institutional Owner | {due(30)} |",
    f"| 8 | Evaluar la ventana acumulada diciembre–enero (≥ 100 casos) y aplicar la regla de retiro de U04.E07 si la brecha persiste | Data Scientist | Product Owner | {due(45)} |",
    "",
    "## 8. Lecciones",
    "- La señal sin etiquetas (contrato de calidad) detectó el problema 26 días antes que las métricas con etiquetas.",
    "- El PSI con ~50 casos es ruidoso (hasta 0.24 en meses limpios): se reporta como indicativo y no decide por sí solo.",
    "- Un defecto técnico aparentemente neutral (por zona) produjo daño desigual por grupo: monitorear por grupo es obligatorio.",
]
path = OUT / "INCIDENT_POSTMORTEM.md"
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(path, json.dumps({"detection": d["status"], "confirmation": c["status"], "after_rollback": v["status"]}))
