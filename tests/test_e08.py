"""Pruebas del expediente U04.E08: inventario, trazabilidad, RACI estricto, monitoreo y simulacro."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from inf8239_u04.data import PROHIBITED, REQUIRED, features, load_data, temporal_split
from inf8239_u04.governance import (
    deployment_decision,
    governed_recommendation,
    load_config,
    sha256_file,
    trace_manifest,
    validate_raci,
)
from inf8239_u04.incident import DEFECT_ZONES, inject_ingest_v2_defect, run_drill
from inf8239_u04.monitoring import (
    classify,
    drift_report,
    model_features_ok,
    psi_numeric,
    quality_report,
)
from inf8239_u04.pipeline import run

ROOT = Path(__file__).resolve().parents[1]
DATA_SHA = "2af1858fe874f3914b0f9bfe068fd876cb716186694a6ece9a16e8c929128a01"
GATES = {"min_recall": .68, "max_recall_gap": .16, "max_fpr_gap": .16, "max_latency_ms": 500, "max_model_kb": 1024}
OK = ({"recall": .72}, {"recall_gap": .10, "fpr_gap": .10}, {"latency_ms": 1, "model_kb": 4})


@pytest.fixture(scope="module")
def cfg():
    return load_config(ROOT / "configs/governance.yml")


@pytest.fixture(scope="module")
def inventory():
    return pd.read_csv(ROOT / "docs/DATA_INVENTORY.csv")


# ------------------------------------------------------------------ inventario y retención
def test_inventory_covers_every_dataset_column(inventory):
    cols = set(pd.read_csv(ROOT / "data/territorial_risk_synthetic.csv", nrows=1).columns)
    assert cols == REQUIRED
    assert cols <= set(inventory.elemento)


def test_inventory_excludes_direct_identifiers(inventory):
    row = inventory[inventory.tipo == "identificadores directos"].iloc[0]
    assert {x.strip() for x in row.elemento.split(";")} == PROHIBITED
    assert row.uso == "excluido"


def test_model_features_are_inventoried_for_model_use(inventory):
    use = inventory.set_index("elemento").uso
    for f in features(load_data(ROOT / "data/territorial_risk_synthetic.csv")).columns:
        assert "modelo" in use[f], f
    assert use["protected_group"] == "auditoría"


def test_every_row_has_purpose_retention_and_norm_type(inventory, cfg):
    assert inventory[["finalidad", "retencion", "accion_al_vencer", "base_y_tipo_norma"]].notna().all().all()
    for key in inventory.retencion_clave:
        if key != "no_aplica":
            assert all(k in cfg["retention"] for k in key.split("+")), key
    assert inventory.base_y_tipo_norma.str.contains("obligación legal|marco voluntario|recomendación ética").all()


# ------------------------------------------------------------------ datasheet / model card trazables
def test_datasheet_hash_matches_data():
    assert sha256_file(ROOT / "data/territorial_risk_synthetic.csv") == DATA_SHA
    text = (ROOT / "docs/DATASHEET.md").read_text(encoding="utf-8")
    assert DATA_SHA in text
    for section in ["Motivación", "Composición", "recolección", "Preprocesamiento", "Usos", "Distribución", "Mantenimiento"]:
        assert section in text


def test_model_card_matches_current_versions():
    card = (ROOT / "docs/MODEL_CARD.md").read_text(encoding="utf-8")
    trace = trace_manifest(ROOT / "configs/governance.yml", ROOT / "data/territorial_risk_synthetic.csv")
    assert trace["data_sha256"] in card and trace["config_sha256"] in card and trace["policy_version"] in card


def test_trace_manifest_fields(cfg):
    t = trace_manifest(ROOT / "configs/governance.yml", ROOT / "data/territorial_risk_synthetic.csv", ROOT / "models/none")
    assert set(t) >= {"policy_version", "config_sha256", "data_sha256", "model_sha256", "code_commit", "generated_utc"}
    assert t["policy_version"] == cfg["policy_version"]


# ------------------------------------------------------------------ decisión gobernada
def test_decision_carries_version_policy_evidence_and_human_action():
    d = deployment_decision(*OK, GATES, evidence=["reports/e07/gates.csv"], trace={"policy_version": "x"},
                            human_decision={"decision": "LIMITAR"})
    assert d["status"] == "GO" and d["evidence"] and d["trace"] and d["human_action"] and d["human_decision"]


def test_contract_breach_is_stop():
    assert deployment_decision(*OK, GATES, contract_ok=False)["status"] == "STOP"


def test_gap_beyond_stop_factor_is_stop_and_gate_failure_is_review():
    gaps = {"recall_gap": .40, "fpr_gap": .10}
    assert deployment_decision(OK[0], gaps, OK[2], GATES, stop_factor=2.0)["status"] == "STOP"
    assert deployment_decision(OK[0], {"recall_gap": .20, "fpr_gap": .10}, OK[2], GATES, stop_factor=2.0)["status"] == "REVIEW"


def test_go_never_relaxes_human_policy():
    go = deployment_decision(*OK, GATES)
    assert governed_recommendation(go, "LIMITAR")["final"] == "LIMITAR"
    assert "REVISIÓN" in governed_recommendation({"status": "REVIEW"}, "DESPLEGAR")["final"]
    assert "NO UTILIZAR" in governed_recommendation({"status": "STOP"}, "DESPLEGAR")["final"]
    with pytest.raises(ValueError):
        governed_recommendation(go, "TAL VEZ")


def test_protected_attribute_cannot_be_a_feature():
    assert model_features_ok(["zone", "exposure"])
    assert not model_features_ok(["zone", "protected_group"])


# ------------------------------------------------------------------ RACI estricto
def test_project_raci_has_exactly_one_accountable_and_e08_activities():
    raci = pd.read_csv(ROOT / "student_inputs/raci.csv")
    assert validate_raci(raci, strict=True)
    acts = set(raci.activity)
    for a in ["Data inventory and retention", "Monitoring and drift", "Containment and STOP", "Rollback to safe state",
              "Appeals handling", "Communication to affected parties", "Model Card and Datasheet update",
              "Data pipeline change management"]:
        assert a in acts


@pytest.mark.parametrize("acc", ["Product Owner and Institutional Owner", "PO, IO", "PO/IO"])
def test_strict_raci_rejects_multiple_accountables(acc):
    with pytest.raises(ValueError):
        validate_raci(pd.DataFrame([{"activity": "x", "R": "ML", "A": acc, "C": "", "I": ""}]), strict=True)


def test_strict_raci_rejects_duplicated_activity():
    row = {"activity": "x", "R": "ML", "A": "PO", "C": "", "I": ""}
    with pytest.raises(ValueError):
        validate_raci(pd.DataFrame([row, row]), strict=True)


# ------------------------------------------------------------------ monitoreo
def test_psi_zero_for_identical_and_large_for_shift():
    x = np.random.default_rng(0).normal(size=500)
    assert psi_numeric(x, x) == pytest.approx(0, abs=1e-9)
    assert psi_numeric(x, x + 2) > 0.25


def test_small_windows_are_indicative_not_alerts():
    df = load_data(ROOT / "data/territorial_risk_synthetic.csv")
    train, test = temporal_split(df)
    rep = drift_report(train, test.head(50), .10, .25, min_n=100)
    assert (rep.nivel == "INDICATIVO").all()


def test_quality_contract_detects_injected_defect():
    df = load_data(ROOT / "data/territorial_risk_synthetic.csv")
    train, test = temporal_split(df)
    bad = inject_ingest_v2_defect(test)
    q = quality_report(train, bad[bad.received_date >= "2026-12-01"], .15).set_index("zone")
    assert set(q.index[q.nivel == "ALERTA"]) == set(DEFECT_ZONES)
    assert (quality_report(train, test, .15).nivel != "ALERTA").all()


def test_unsupported_performance_never_returns_go(cfg):
    empty = pd.DataFrame({"feature": [], "psi": [], "nivel": []})
    q = pd.DataFrame({"zone": [], "nivel": []})
    perf = {"n": 40, "recall": .9, "recall_gap": .0, "fpr_gap": .0}
    assert classify(empty, q, perf, GATES, cfg["monitoring"])["status"] == "REVIEW"


# ------------------------------------------------------------------ simulacro
@pytest.fixture(scope="module")
def drill(tmp_path_factory, cfg):
    df = load_data(ROOT / "data/territorial_risk_synthetic.csv")
    model_path = tmp_path_factory.mktemp("m") / "model.joblib"
    from inf8239_u04.model import build_model, fit_measure
    train, _ = temporal_split(df)
    model = build_model()
    fit_measure(model, features(train), train.target, output=model_path)
    out = tmp_path_factory.mktemp("incident")
    return run_drill(df, model, cfg, out_dir=out, model_path=model_path), out


def test_drill_detects_stop_and_rollback_clears_it(drill):
    r, _ = drill
    assert r["detection"]["status"] == "STOP" and "Norte" in r["detection"]["scope"]
    assert r["confirmation"]["severity"] == "SEV-1"
    assert r["rollback_verification"]["status"] in {"REVIEW", "GO"}
    assert r["rollback_verification"]["severity"] != "SEV-1"
    assert r["model_unchanged"]
    p = r["performance"]
    assert p["december_after_rollback"]["recall_G1"] > p["december_defective"]["recall_G1"]


def test_drill_evidence_hashes_match_and_log_has_no_protected_attribute(drill):
    _, out = drill
    manifest = json.loads((out / "EVIDENCE_MANIFEST.json").read_text())
    assert manifest and all(sha256_file(out / k) == v for k, v in manifest.items())
    log = pd.read_csv(out / "evidence/december_scored_cases.csv")
    assert "protected_group" not in log.columns and log.routed_to_manual.any()


def test_course_pipeline_still_reaches_gate_status(cfg):
    r = run(load_data(ROOT / "data/territorial_risk_synthetic.csv"), cfg["gates"])
    assert r["decision"]["status"] in {"GO", "REVIEW", "STOP"}


# ------------------------------------------------------------------ documentos
def test_docs_have_no_placeholders():
    for f in ["docs/RUNBOOK.md", "docs/HANDOFF.md", "docs/DATASHEET.md", "docs/MODEL_CARD.md",
              "reports/lab13/INCIDENT_POSTMORTEM.md"]:
        assert "REPLACE" not in (ROOT / f).read_text(encoding="utf-8"), f
