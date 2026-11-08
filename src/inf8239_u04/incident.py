"""Simulacro de incidente U04.E08 (reloj simulado, datos sintéticos).

Escenario: el 2026-12-01 la «ingesta v2» de las zonas Sur y Norte empieza a convertir el historial
ausente en ``previous_incidents = 0``. No hay cambio de modelo: el modelo v1.0 sigue intacto
(hash verificado), pero recibe datos degradados. Como Sur y Norte concentran más casos G1, el
defecto técnico se convierte en un daño desigual: se omiten casos reales de G1.

Fases (docs/RUNBOOK.md): detección → clasificación → contención → preservación de evidencia →
comunicación → rollback y verificación → postmortem.
"""
from __future__ import annotations

import json
import shutil
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .data import features, temporal_split
from .governance import sha256_file
from .monitoring import (
    classify,
    drift_report,
    model_features_ok,
    quality_report,
    window_metrics,
)

DEFECT_START = pd.Timestamp("2026-12-01")
DEFECT_ZONES = ("Sur", "Norte")
DETECTION_DAYS = 14         # primer corte quincenal tras el cambio
CLOCK0 = date(2026, 12, 15)  # corte quincenal de monitoreo (reloj simulado)


def inject_ingest_v2_defect(df: pd.DataFrame, start=DEFECT_START, zones=DEFECT_ZONES) -> pd.DataFrame:
    out = df.copy()
    mask = (out.received_date >= start) & out.zone.isin(zones)
    out.loc[mask, "previous_incidents"] = 0
    return out


def rule_baseline(df: pd.DataFrame) -> np.ndarray:
    """Línea base transparente de U04.E07 (fallback): previous_incidents ≥ 3.

    Depende de la MISMA variable dañada: en este incidente no es un refugio seguro."""
    return (df.previous_incidents >= 3).astype(int).to_numpy()


def _perf(df, pred):
    y, p = df.target.to_numpy(), np.asarray(pred)
    from .audit_extra import group_gaps
    g = group_gaps(df.target, p, df.protected_group)
    by = {grp: float(p[(df.protected_group == grp).to_numpy() & (y == 1)].mean()) for grp in sorted(df.protected_group.unique())}
    return {"n": len(df), "recall": float(p[y == 1].mean()), "recall_G1": by.get("G1"), "recall_G2": by.get("G2"),
            "recall_gap": g["recall_gap"], "fpr_gap": g["fpr_gap"], "selection_rate": float(p.mean())}


def run_drill(df: pd.DataFrame, model, cfg: dict, out_dir="reports/e08/incident",
              model_path="models/model.joblib") -> dict:
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    (out / "evidence").mkdir(parents=True)
    gates, mon = cfg["gates"], cfg["monitoring"]
    train, test = temporal_split(df)
    model_hash_before = sha256_file(model_path)
    stream = inject_ingest_v2_defect(test)

    # 1. Detección (sin etiquetas): primer lote semanal tras el cambio
    batch = stream[(stream.received_date >= DEFECT_START) & (stream.received_date < DEFECT_START + pd.to_timedelta(DETECTION_DAYS, unit="D"))]
    drift_b = drift_report(train, batch, mon["psi_review"], mon["psi_alert"])
    qual_b = quality_report(train, batch, mon["zero_history_delta_alert"])
    contract = model_features_ok(features(batch).columns)
    det = classify(drift_b, qual_b, None, gates, mon, contract_ok=contract)

    # 2. Ventana mensual con etiquetas (tras revisión humana): severidad confirmada
    dec = stream[stream.received_date >= DEFECT_START]
    pred_dec = model.predict(features(dec))
    drift_m = drift_report(train, dec, mon["psi_review"], mon["psi_alert"])
    qual_m = quality_report(train, dec, mon["zero_history_delta_alert"])
    perf_dec = _perf(dec, pred_dec)
    conf = classify(drift_m, qual_m, perf_dec, gates, mon, contract_ok=contract)
    windows = window_metrics(stream, model.predict(features(stream)), min_n=mon["min_window_cases_for_fairness"])

    # 3. Contención: los casos de zonas afectadas salen del ranking automático → cola manual
    affected = dec.zone.isin(DEFECT_ZONES)
    rule_dec = _perf(dec, rule_baseline(dec))

    # 4. Rollback: ingesta v2 → v1 (datos originales del mismo periodo); el modelo no cambia
    clean_dec = test[test.received_date >= DEFECT_START]
    perf_rollback = _perf(clean_dec, model.predict(features(clean_dec)))
    verify = classify(drift_report(train, clean_dec, mon["psi_review"], mon["psi_alert"]),
                      quality_report(train, clean_dec, mon["zero_history_delta_alert"]), perf_rollback, gates, mon)
    model_hash_after = sha256_file(model_path)

    # 5. Evidencia preservada
    ev = out / "evidence"
    drift_b.to_csv(ev / "drift_first_batch.csv", index=False)
    qual_b.to_csv(ev / "quality_first_batch.csv", index=False)
    drift_m.to_csv(ev / "drift_december.csv", index=False)
    qual_m.to_csv(ev / "quality_december.csv", index=False)
    windows.to_csv(ev / "window_metrics.csv", index=False)
    dec.assign(pred=pred_dec, routed_to_manual=affected.to_numpy())[
        ["case_id", "received_date", "zone", "previous_incidents", "pred", "routed_to_manual"]].to_csv(
        ev / "december_scored_cases.csv", index=False)  # sin atributo protegido: el log operativo no lo necesita
    perf = {"december_defective": perf_dec, "december_rule_fallback": rule_dec, "december_after_rollback": perf_rollback}
    (ev / "performance.json").write_text(json.dumps(perf, indent=2), encoding="utf-8")
    t = lambda d: (CLOCK0 + timedelta(days=d)).isoformat()
    timeline = [
        {"t": t(-14), "fase": "cambio", "evento": "Ingesta v2 activada en Sur y Norte (cambio no comunicado al equipo del modelo)"},
        {"t": t(0), "fase": "detección", "evento": f"Monitoreo quincenal sin etiquetas: {det['severity']} → {det['status']}", "motivos": det["reasons"]},
        {"t": t(0), "fase": "contención", "evento": f"STOP de segmento: el registro de cambios muestra que Norte y Sur comparten la ingesta v2, así que ambas salen del ranking ({int(affected.sum())} casos de diciembre); cola manual por orden de llegada. Este, Oeste siguen en REVIEW bajo LIMITAR"},
        {"t": t(0), "fase": "evidencia", "evento": "Instantánea de reportes, hashes y versión de modelo/política"},
        {"t": t(1), "fase": "comunicación", "evento": "Aviso interno al Institutional Owner y a Data Engineering; aviso a representantes afectados"},
        {"t": t(3), "fase": "rollback", "evento": "Ingesta revertida a v1; re-puntuación del periodo; verificación de puertas", "verificación": verify},
        {"t": t(26), "fase": "confirmación con etiquetas", "evento": f"Ventana de diciembre etiquetada: {conf['severity']} → {conf['status']}", "motivos": conf["reasons"]},
        {"t": t(30), "fase": "postmortem", "evento": "Revisión sin culpables y acciones correctivas con responsables"},
    ]
    result = {
        "scenario": "ingesta v2 convierte historial ausente en 0 (zonas Sur y Norte, desde 2026-12-01)",
        "clock": "simulado", "detection": det, "confirmation": conf, "rollback_verification": verify,
        "contract_ok": contract, "affected_cases": int(affected.sum()),
        "affected_G1_share": float(dec.loc[affected, "protected_group"].eq("G1").mean()),
        "model_sha256_before": model_hash_before, "model_sha256_after": model_hash_after,
        "model_unchanged": model_hash_before == model_hash_after, "performance": perf, "timeline": timeline,
    }
    (out / "incident_record.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    manifest = {p.relative_to(out).as_posix(): sha256_file(p) for p in sorted(out.rglob("*")) if p.is_file()}
    (out / "EVIDENCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    result["evidence_manifest"] = manifest
    return result
