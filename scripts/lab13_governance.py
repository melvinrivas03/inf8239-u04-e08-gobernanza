"""LAB13 / U04.E08 · Decisión de despliegue gobernada y trazable.

    uv run python scripts/lab13_governance.py

Valida el RACI en modo estricto (exactamente un Accountable), ejecuta el pipeline y escribe
reports/lab13/deployment_decision.json con versión, política, evidencia y acción humana.
La puerta automática nunca amplía la autoridad del sistema: prevalece la decisión humana LIMITAR.
"""
import json
from pathlib import Path

import pandas as pd

from inf8239_u04.data import features, load_data
from inf8239_u04.governance import (
                                    deployment_decision,
                                    governed_recommendation,
                                    load_config,
                                    trace_manifest,
                                    validate_raci,
)
from inf8239_u04.monitoring import model_features_ok
from inf8239_u04.pipeline import run

cfg = load_config()
validate_raci(pd.read_csv("student_inputs/raci.csv"), strict=True)
df = load_data()
result = run(df, cfg["gates"])
trace = trace_manifest()
evidence = ["reports/e07/gates.csv", "reports/e07/bootstrap_gaps_baseline.csv", "reports/lab13/fairness_by_group.csv",
            "reports/lab13/INCIDENT_POSTMORTEM.md", "docs/MODEL_CARD.md", "docs/DATASHEET.md", "docs/DATA_INVENTORY.csv"]
decision = deployment_decision(result["metrics"], result["gaps"], result["resources"], cfg["gates"],
                               contract_ok=model_features_ok(features(df).columns), stop_factor=cfg["monitoring"]["stop_factor"],
                               evidence=[e for e in evidence if Path(e).exists()], trace=trace,
                               human_decision={"decision": cfg["human_policy_decision"], "by": "Institutional Owner (estudiante en el rol)",
                                               "record": "student_inputs/lab12_decision.yml"})
decision["human_action"] = ("Revisar cada caso priorizado; el DSS no decide. Apelación en 5 días hábiles; "
                            "muestra aleatoria del 5 % de casos de baja prioridad; monitoreo mensual (docs/RUNBOOK.md).")
governed = governed_recommendation(decision, cfg["human_policy_decision"])
out = Path("reports/lab13")
out.mkdir(parents=True, exist_ok=True)
(out / "deployment_decision.json").write_text(json.dumps(
    {"metrics": result["metrics"], "gaps": result["gaps"], "resources": result["resources"], "decision": decision,
     "governed_recommendation": governed}, indent=2, ensure_ascii=False), encoding="utf-8")
result["by_group"].to_csv(out / "fairness_by_group.csv")
(out / "TRACE_MANIFEST.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")
print(decision["status"], "→", governed["final"])
