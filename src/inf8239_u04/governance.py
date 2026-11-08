import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import yaml


def load_config(path="configs/governance.yml"):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ RACI
MULTI_ROLE_MARKERS = (",", ";", "/", " and ", " y ", "+")


def validate_raci(df, strict: bool = False):
    """Base del curso: cada actividad necesita R y A.

    ``strict=True`` (U04.E08) exige además EXACTAMENTE un Accountable por actividad (sin
    «X and Y», comas ni barras) y actividades no duplicadas.
    """
    required = {"activity", "R", "A", "C", "I"}
    if required - set(df.columns):
        raise ValueError("RACI columns missing")
    if df[["R", "A"]].fillna("").apply(lambda s: s.str.strip().eq("")).any().any():
        raise ValueError("Every activity needs R and A")
    if strict:
        if df.activity.duplicated().any():
            raise ValueError("Duplicated RACI activity")
        bad = [a for a, acc in zip(df.activity, df.A.astype(str))
               if any(m in f" {acc.lower()} " for m in MULTI_ROLE_MARKERS)]
        if bad:
            raise ValueError(f"Exactly one Accountable required: {bad}")
    return True


# ------------------------------------------------------------------ trazabilidad
def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:  # noqa: BLE001 - fuera de un repositorio
        return "sin-git"


def trace_manifest(config_path="configs/governance.yml", data_path="data/territorial_risk_synthetic.csv",
                   model_path="models/model.joblib") -> dict:
    """Versión, política y evidencia que acompañan cada recomendación (LAB13: Trazabilidad)."""
    cfg = load_config(config_path)
    return {
        "system_name": cfg["system_name"],
        "policy_version": cfg.get("policy_version", "sin-versión"),
        "config_sha256": sha256_file(config_path),
        "data_sha256": sha256_file(data_path),
        "model_sha256": sha256_file(model_path) if Path(model_path).exists() else None,
        "code_commit": git_commit(),
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }


# ------------------------------------------------------------------ decisión gobernada
def deployment_decision(metrics, gaps, resources, gates, contract_ok: bool = True, stop_factor: float | None = None,
                        evidence=None, trace=None, human_decision=None):
    """GO si todas las puertas pasan; REVIEW si alguna falla; STOP si falla el contrato de datos
    (privacidad / columnas) o una brecha supera ``stop_factor`` veces su tolerancia.

    Los argumentos extra son opcionales: sin ellos la función se comporta como la del curso.
    """
    checks = {
        "recall": metrics["recall"] >= gates["min_recall"],
        "recall_gap": gaps["recall_gap"] <= gates["max_recall_gap"],
        "fpr_gap": gaps["fpr_gap"] <= gates["max_fpr_gap"],
        "latency": resources["latency_ms"] <= gates["max_latency_ms"],
        "model_size": resources["model_kb"] <= gates["max_model_kb"],
    }
    if not contract_ok:
        checks["data_contract"] = False
    failed = [k for k, v in checks.items() if not v]
    severe = (not contract_ok) or (stop_factor is not None and (
        gaps["recall_gap"] > stop_factor * gates["max_recall_gap"] or gaps["fpr_gap"] > stop_factor * gates["max_fpr_gap"]))
    status = "STOP" if severe else ("REVIEW" if failed else "GO")
    out = {"status": status, "checks": checks, "failed": failed, "human_action": "Document review and final decision"}
    if evidence is not None:
        out["evidence"] = evidence
    if trace is not None:
        out["trace"] = trace
    if human_decision is not None:
        out["human_decision"] = human_decision
    return out


def governed_recommendation(gate_decision: dict, policy_decision: str) -> dict:
    """Combina la puerta automática con la decisión humana vigente (LIMITAR de U04.E07).

    La puerta nunca puede AMPLIAR la autoridad del sistema: si la política humana es más restrictiva,
    prevalece la política. Un STOP o REVIEW de la puerta siempre prevalece sobre la política.
    """
    order = {"DESPLEGAR": 0, "MODIFICAR": 1, "LIMITAR": 2, "NO UTILIZAR": 3}
    gate = gate_decision["status"]
    if gate == "STOP":
        final = "NO UTILIZAR (suspendido hasta cerrar el incidente)"
    elif gate == "REVIEW":
        final = "REVISIÓN HUMANA OBLIGATORIA antes de continuar"
    else:  # GO técnico: aplica la política humana tal cual (nunca se relaja automáticamente)
        if policy_decision not in order:
            raise ValueError(f"Unknown policy decision: {policy_decision}")
        final = policy_decision
    return {"gate_status": gate, "policy_decision": policy_decision, "final": final,
            "authority": "El DSS sólo prioriza revisión; no declara emergencias, culpabilidad, elegibilidad ni interviene."}
