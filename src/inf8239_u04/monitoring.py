"""Monitoreo operativo para U04.E08: deriva, calidad de datos, desempeño por ventana y severidad.

Dos niveles de señal, porque en producción las etiquetas llegan tarde:

* **Sin etiquetas (inmediata):** PSI de cada variable del modelo contra la referencia de
  entrenamiento y verificación de calidad (proporción de ``previous_incidents == 0`` por zona).
* **Con etiquetas (diferida, tras la revisión humana):** recall y brechas por grupo con soporte
  mínimo; una ventana sin soporte NO se declara «equitativa», se reporta como «sin soporte».

La severidad traduce señales en acciones del runbook. Nunca oculta una puerta fallida:
cualquier fallo produce REVIEW o STOP.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .audit_extra import group_gaps
from .data import features

NUMERIC = ["previous_incidents", "infrastructure_score", "exposure"]
CATEGORICAL = ["zone", "age_band"]
EPS = 1e-4


# ------------------------------------------------------------------ deriva
def psi_numeric(ref, cur, bins: int = 10) -> float:
    ref, cur = np.asarray(ref, float), np.asarray(cur, float)
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    r = np.histogram(ref, edges)[0] / len(ref)
    c = np.histogram(cur, edges)[0] / len(cur)
    r, c = np.clip(r, EPS, None), np.clip(c, EPS, None)
    return float(np.sum((c - r) * np.log(c / r)))


def psi_categorical(ref, cur) -> float:
    cats = sorted(set(ref) | set(cur))
    r = pd.Series(ref).value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    c = pd.Series(cur).value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    r, c = np.clip(r, EPS, None), np.clip(c, EPS, None)
    return float(np.sum((c - r) * np.log(c / r)))


def drift_report(ref: pd.DataFrame, cur: pd.DataFrame, psi_review: float, psi_alert: float,
                 min_n: int = 100, bins: int = 5) -> pd.DataFrame:
    """PSI por variable. Con menos de ``min_n`` casos el PSI es ruidoso (en los meses limpios de
    prueba, con ~50 casos, llega a 0.24 sin ningún cambio real): se reporta como INDICATIVO y no
    dispara alertas por sí solo."""
    rows = []
    for col in NUMERIC + CATEGORICAL:
        v = psi_numeric(ref[col], cur[col], bins) if col in NUMERIC else psi_categorical(ref[col], cur[col])
        if len(cur) < min_n:
            level = "INDICATIVO"
        else:
            level = "ALERTA" if v >= psi_alert else ("REVISAR" if v >= psi_review else "OK")
        rows.append({"feature": col, "psi": round(v, 4), "n": len(cur), "nivel": level})
    return pd.DataFrame(rows)


def quality_report(ref: pd.DataFrame, cur: pd.DataFrame, max_delta: float, min_zone_n: int = 5) -> pd.DataFrame:
    """Contrato de calidad: proporción de historial vacío (``previous_incidents == 0``) por zona.

    Es una señal nítida aun con pocos casos (pasar de ~5 % a 100 % no es ruido muestral)."""
    r = ref.assign(z=ref.previous_incidents.eq(0)).groupby("zone").z.mean()
    cg = cur.assign(z=cur.previous_incidents.eq(0)).groupby("zone").z
    out = pd.DataFrame({"ref_zero_share": r, "cur_zero_share": cg.mean(), "n": cg.size()}).fillna(0)
    out["delta"] = out.cur_zero_share - out.ref_zero_share
    out["nivel"] = np.select([out.n < min_zone_n, out.delta > max_delta], ["SIN SOPORTE", "ALERTA"], "OK")
    return out.round(4).reset_index(names="zone")


# ------------------------------------------------------------------ desempeño por ventana
def window_metrics(stream: pd.DataFrame, pred, freq: str = "MS", min_n: int = 100,
                   min_class: int = 5) -> pd.DataFrame:
    s = stream.assign(pred=np.asarray(pred), window=stream.received_date.dt.to_period("M").dt.start_time)
    rows = []
    for w, g in s.groupby("window"):
        y, p = g.target.to_numpy(), g.pred.to_numpy()
        rec = float(p[y == 1].mean()) if (y == 1).any() else np.nan
        per = {}
        support = len(g) >= min_n
        for grp, gg in g.groupby("protected_group"):
            pos, neg = int(gg.target.sum()), int((1 - gg.target).sum())
            support &= pos >= min_class and neg >= min_class
            per[f"recall_{grp}"] = float(gg.pred[gg.target == 1].mean()) if pos else np.nan
        gaps = group_gaps(g.target, g.pred, g.protected_group)
        rows.append({"window": w.date().isoformat(), "n": len(g), "recall": rec, **per,
                     "recall_gap": gaps["recall_gap"], "fpr_gap": gaps["fpr_gap"],
                     "soporte_equidad": "suficiente" if support else "insuficiente"})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ severidad
def classify(drift: pd.DataFrame, quality: pd.DataFrame, perf: dict | None, gates: dict, mon: dict,
             contract_ok: bool = True) -> dict:
    """Severidad, estado y alcance (ver docs/RUNBOOK.md §1).

    * SEV-1 → STOP del alcance afectado: contrato de datos violado (identificadores, atributo
      protegido como feature, o calidad en alerta en una zona) o brecha > ``stop_factor`` ×
      tolerancia con soporte suficiente.
    * SEV-2 → REVIEW + contención: puerta de desempeño/equidad fallida con soporte suficiente, o
      PSI en ALERTA con n ≥ mínimo.
    * SEV-3 → REVIEW sin contención: señales indicativas (soporte insuficiente) o PSI en REVISAR.
    """
    sev, reasons, scope = "OK", [], "sistema"
    def up(level, why):
        nonlocal sev
        sev = max(sev, level, key=_rank); reasons.append(why)
    if not contract_ok:
        up("SEV-1", "contrato de datos: identificador directo o atributo protegido como feature")
    bad_zones = quality.loc[quality.nivel == "ALERTA", "zone"].tolist()
    if bad_zones:
        up("SEV-1", f"contrato de calidad violado (historial vacío) en zonas {bad_zones}")
        if contract_ok:
            scope = bad_zones
    if (drift.nivel == "ALERTA").any():
        up("SEV-2", f"PSI en ALERTA: {drift.loc[drift.nivel == 'ALERTA', 'feature'].tolist()}")
    if (drift.nivel == "REVISAR").any():
        up("SEV-3", f"PSI en REVISAR: {drift.loc[drift.nivel == 'REVISAR', 'feature'].tolist()}")
    if (drift.nivel == "INDICATIVO").any() and (drift.psi >= mon["psi_alert"]).any():
        up("SEV-3", "PSI alto pero con n insuficiente (indicativo)")
    if perf is not None:
        supported = perf.get("n", 0) >= mon["min_window_cases_for_fairness"]
        tag = "" if supported else f" [n={perf.get('n')} < {mon['min_window_cases_for_fairness']}: indicativo]"
        if perf["recall"] < gates["min_recall"]:
            up("SEV-2" if supported else "SEV-3", f"recall {perf['recall']:.3f} < {gates['min_recall']}{tag}")
        for k, tol in (("recall_gap", gates["max_recall_gap"]), ("fpr_gap", gates["max_fpr_gap"])):
            if perf[k] > mon["stop_factor"] * tol and supported:
                up("SEV-1", f"{k} {perf[k]:.3f} > {mon['stop_factor']}×{tol}")
            elif perf[k] > tol:
                up("SEV-2" if supported else "SEV-3", f"{k} {perf[k]:.3f} > {tol}{tag}")
        if not supported:
            up("SEV-3", "ventana sin soporte suficiente: no puede declararse GO")
    status = {"OK": "GO", "SEV-3": "REVIEW", "SEV-2": "REVIEW", "SEV-1": "STOP"}[sev]
    return {"severity": sev, "status": status, "scope": scope if status == "STOP" else "sistema", "reasons": reasons}


def _rank(s: str) -> int:
    return {"OK": 0, "SEV-3": 1, "SEV-2": 2, "SEV-1": 3}[s]


def model_features_ok(columns) -> bool:
    """El modelo no puede recibir identificadores directos ni el atributo protegido."""
    banned = {"name", "document_number", "email", "phone", "protected_group", "case_id"}
    return not (banned & {str(c) for c in columns})


def score(model, df: pd.DataFrame):
    return model.predict(features(df))
