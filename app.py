import json
from pathlib import Path

import pandas as pd
import streamlit as st

from inf8239_u04.data import features, load_data
from inf8239_u04.governance import (
    deployment_decision,
    governed_recommendation,
    load_config,
    trace_manifest,
)
from inf8239_u04.monitoring import model_features_ok
from inf8239_u04.pipeline import run

st.set_page_config(page_title="Governed Green DSS", layout="wide")
st.title("DSS territorial sintético · Gobernanza y Green AI")
st.warning("Demostración educativa con datos sintéticos. No autoriza decisiones automáticas ni representa estadísticas reales.")
cfg = load_config()
df = load_data()
result = run(df, cfg["gates"])
trace = trace_manifest()
decision = deployment_decision(result["metrics"], result["gaps"], result["resources"], cfg["gates"],
                               contract_ok=model_features_ok(features(df).columns),
                               stop_factor=cfg["monitoring"]["stop_factor"], trace=trace)
governed = governed_recommendation(decision, cfg["human_policy_decision"])

st.subheader("Propósito y autoridad")
st.write(cfg["purpose"])
st.write("Usos prohibidos:", ", ".join(cfg["prohibited_uses"]))
st.caption(governed["authority"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Accuracy", f"{result['metrics']['accuracy']:.3f}")
c2.metric("Recall", f"{result['metrics']['recall']:.3f}")
c3.metric("Puerta técnica", decision["status"])
c4.metric("Decisión gobernada", governed["final"])
if decision["status"] != "GO":
    st.error(f"Puertas fallidas: {decision['failed']}. Se requiere revisión humana antes de continuar.")

st.subheader("Métricas por grupo")
st.dataframe(result["by_group"], use_container_width=True)
st.subheader("Puertas de calidad")
st.json(decision["checks"])

st.subheader("Trazabilidad de la recomendación")
st.table(pd.DataFrame({"campo": list(trace), "valor": [str(v) for v in trace.values()]}))

rec = Path("reports/lab13/incident/incident_record.json")
st.subheader("Monitoreo y último simulacro")
if rec.exists():
    r = json.loads(rec.read_text(encoding="utf-8"))
    st.write(f"Escenario: {r['scenario']} (reloj simulado).")
    st.write(f"Detección: **{r['detection']['severity']} → {r['detection']['status']}** · "
             f"Tras rollback: **{r['rollback_verification']['status']}** · Modelo sin cambios: {r['model_unchanged']}")
    st.dataframe(pd.DataFrame(r["timeline"])[["t", "fase", "evento"]], use_container_width=True)
else:
    st.write("Aún no hay simulacro: ejecute `uv run python scripts/simulate_incident.py`.")

st.info("Acción humana: revisar cada caso priorizado y registrar la acción; apelación en 5 días hábiles; "
        "muestra aleatoria del 5 % de baja prioridad; STOP y rollback según docs/RUNBOOK.md.")
