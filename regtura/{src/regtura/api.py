"""Regtura API — FastAPI backend with history storage and variance analysis."""

from __future__ import annotations

import io
import json
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from regtura.common import SubmissionData
from regtura.validate.rule_engine.engine import RuleEngine
from regtura.validate.taxonomies.finrep.taxonomy import FinrepTaxonomy
from regtura.validate.excel_parser import parse_excel
from regtura.validate.history import HistoryStore, CELL_LABELS

app = FastAPI(title="Regtura API", description="Open source regulatory reporting validation engine", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

TAXONOMIES = {"finrep": FinrepTaxonomy}
history = HistoryStore()

# Human-readable rule descriptions
RULE_EXPLANATIONS = {
    "v0100_m": {
        "name": "Total Assets reconciliation",
        "what": "Checks that the reported Total Assets figure equals the sum of all individual asset line items.",
        "why": "If Total Assets doesn't match the sum of its components, there may be a data entry error, a missing line item, or a mapping issue from the source system.",
        "fix": "Review each asset line item and verify the amounts match your source data. Check for any items that may have been omitted or double-counted.",
    },
    "v0101_m": {
        "name": "Total Liabilities reconciliation",
        "what": "Checks that the reported Total Liabilities figure equals the sum of all individual liability line items.",
        "why": "A mismatch indicates that liability components don't add up to the reported total, which could signal missing entries or incorrect aggregation.",
        "fix": "Compare each liability line item against your general ledger. Look for items mapped to the wrong row or missing from the breakdown.",
    },
    "v0102_m": {
        "name": "Equity plus Liabilities consistency",
        "what": "Checks that Total Equity + Total Liabilities equals the reported Total Equity and Liabilities figure.",
        "why": "This is a basic arithmetic check. A failure here usually means the equity or liabilities total was entered incorrectly.",
        "fix": "Verify the Total Equity and Total Liabilities figures independently, then confirm their sum matches the combined total.",
    },
    "v0103_m": {
        "name": "Balance sheet balance",
        "what": "Checks that Total Assets equals Total Equity and Liabilities — the fundamental accounting equation.",
        "why": "An unbalanced balance sheet is a critical error that will be rejected by the regulator. It means the asset side and the funding side of the balance sheet don't match.",
        "fix": "This is usually caused by an error in one of the other checks. Fix any failures in v0100_m, v0101_m, or v0102_m first, as those typically resolve this issue.",
    },
    "v0104_m": {
        "name": "Provisions sign convention",
        "what": "Checks that Provisions are reported as a negative value (or zero), following the EBA sign convention.",
        "why": "The EBA requires provisions to be reported with a negative sign because they represent a reduction in the carrying value of assets. A positive value suggests the sign was omitted.",
        "fix": "Ensure provisions are entered as a negative number. For example, enter -4,500,000 instead of 4,500,000.",
    },
}


class ValidationRequest(BaseModel):
    framework: str
    period: str
    templates: dict[str, dict[str, float]]
    metadata: dict[str, Any] = {}


class RuleExplanation(BaseModel):
    rule_id: str
    name: str
    description: str
    what: str
    why: str
    fix: str
    severity: str
    rule_type: str
    template: str
    formula: str


class ValidationResultOut(BaseModel):
    rule_id: str
    rule_name: str
    status: str
    severity: str
    detail: str
    what: str
    why: str
    fix: str
    expected: float | None = None
    actual: float | None = None
    delta: float | None = None


class ValidationReportOut(BaseModel):
    framework: str
    framework_name: str
    period: str
    entity: str
    currency: str
    submitted_at: str
    summary: dict[str, int]
    passed: bool
    templates_found: list[str]
    results: list[ValidationResultOut]


class StoredSubmissionOut(BaseModel):
    submission_id: str
    entity: str
    period: str
    framework: str
    uploaded_at: str
    filename: str
    summary: dict[str, int]
    passed: bool


class VarianceItemOut(BaseModel):
    cell_ref: str
    label: str
    current_value: float
    previous_value: float
    absolute_change: float
    percentage_change: float | None
    direction: str


class VarianceReportOut(BaseModel):
    entity: str
    current_period: str
    previous_period: str
    template: str
    items: list[VarianceItemOut]
    material_changes: list[VarianceItemOut]


def _build_result(r, rules_map) -> ValidationResultOut:
    rule = rules_map.get(r.rule_id)
    expl = RULE_EXPLANATIONS.get(r.rule_id, {})
    return ValidationResultOut(
        rule_id=r.rule_id,
        rule_name=expl.get("name", rule.description if rule else r.rule_id),
        status=r.status.value,
        severity=rule.severity.value if rule else "error",
        detail=r.detail,
        what=expl.get("what", ""),
        why=expl.get("why", ""),
        fix=expl.get("fix", ""),
        expected=r.expected,
        actual=r.actual,
        delta=r.delta,
    )


def _run_validation(taxonomy_name: str, data: SubmissionData, filename: str = "") -> ValidationReportOut:
    tax = TAXONOMIES[taxonomy_name]
    rules = tax.get_rules()
    rules_map = {r.rule_id: r for r in rules}

    engine = RuleEngine()
    engine.load_rules(rules)
    report = engine.validate(data)

    # Save to history
    stored = history.save(data, report, filename=filename)

    from datetime import datetime

    return ValidationReportOut(
        framework=report.framework,
        framework_name=tax.DESCRIPTION,
        period=data.period,
        entity=data.metadata.get("entity", "Unknown Entity"),
        currency=data.metadata.get("currency", "EUR"),
        submitted_at=datetime.now().isoformat(),
        summary=report.summary,
        passed=report.passed,
        templates_found=list(data.templates.keys()),
        results=[_build_result(r, rules_map) for r in report.results],
    )


@app.get("/")
def root():
    return {"name": "Regtura API", "version": "0.1.0", "status": "running"}


@app.get("/taxonomies/{taxonomy_name}/rules", response_model=list[RuleExplanation])
def get_rules(taxonomy_name: str):
    if taxonomy_name not in TAXONOMIES:
        raise HTTPException(status_code=404, detail=f"Taxonomy '{taxonomy_name}' not found.")
    rules = TAXONOMIES[taxonomy_name].get_rules()
    result = []
    for r in rules:
        expl = RULE_EXPLANATIONS.get(r.rule_id, {})
        result.append(RuleExplanation(
            rule_id=r.rule_id,
            name=expl.get("name", r.description),
            description=r.description,
            what=expl.get("what", ""),
            why=expl.get("why", ""),
            fix=expl.get("fix", ""),
            severity=r.severity.value,
            rule_type=r.rule_type.value,
            template=r.template,
            formula=r.formula,
        ))
    return result


@app.post("/validate/{taxonomy_name}", response_model=ValidationReportOut)
def validate_json(taxonomy_name: str, request: ValidationRequest):
    if taxonomy_name not in TAXONOMIES:
        raise HTTPException(status_code=404, detail=f"Taxonomy '{taxonomy_name}' not found.")
    data = SubmissionData(
        framework=request.framework, period=request.period,
        templates=request.templates, metadata=request.metadata,
    )
    return _run_validation(taxonomy_name, data)


@app.post("/validate/{taxonomy_name}/upload", response_model=ValidationReportOut)
async def validate_upload(taxonomy_name: str, file: UploadFile = File(...), period: str = Form(default="unknown")):
    if taxonomy_name not in TAXONOMIES:
        raise HTTPException(status_code=404, detail=f"Taxonomy '{taxonomy_name}' not found.")
    content = await file.read()
    filename = (file.filename or "").lower().strip()

    # Detect file type by content bytes first, then fall back to filename
    is_excel = (
        content[:4] == b"PK\x03\x04"  # ZIP/XLSX magic bytes
        or filename.endswith(".xlsx")
        or filename.endswith(".xls")
    )
    is_json = (
        not is_excel
        and (filename.endswith(".json") or content[:1] in (b"{", b"["))
    )

    if is_excel:
        try:
            data = parse_excel(file_obj=io.BytesIO(content), framework=taxonomy_name, period=period)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse Excel: {e}")
    elif is_json:
        try:
            raw = json.loads(content)
            data = SubmissionData(
                framework=raw.get("framework", taxonomy_name), period=raw.get("period", period),
                templates=raw.get("templates", {}), metadata=raw.get("metadata", {}),
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Invalid JSON file.")
    else:
        raise HTTPException(status_code=400, detail="Upload .xlsx or .json files only.")

    return _run_validation(taxonomy_name, data, filename=filename)


# --- History endpoints ---

@app.get("/history", response_model=list[StoredSubmissionOut])
def list_history(entity: str | None = Query(default=None)):
    submissions = history.list_submissions(entity=entity)
    return [
        StoredSubmissionOut(
            submission_id=s.submission_id, entity=s.entity, period=s.period,
            framework=s.framework, uploaded_at=s.uploaded_at, filename=s.filename,
            summary=s.summary, passed=s.passed,
        )
        for s in submissions
    ]


@app.get("/history/entities", response_model=list[str])
def list_entities():
    return history.list_entities()


@app.delete("/history/{entity}/{period}")
def delete_submission(entity: str, period: str):
    if history.delete_submission(entity, period):
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Submission not found.")


# --- Variance endpoint ---

@app.get("/variance/{entity}", response_model=VarianceReportOut)
def get_variance(
    entity: str,
    current: str = Query(..., description="Current period (e.g. 2024-Q4)"),
    previous: str = Query(..., description="Previous period (e.g. 2024-Q3)"),
    template: str = Query(default="F 01.01"),
    threshold: float = Query(default=10.0, description="Material change threshold (%)"),
):
    items = history.compute_variance(entity, current, previous, template)
    if not items:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find submissions for '{entity}' in periods '{current}' and/or '{previous}'.",
        )

    variance_items = [
        VarianceItemOut(
            cell_ref=v.cell_ref, label=v.label,
            current_value=v.current_value, previous_value=v.previous_value,
            absolute_change=v.absolute_change,
            percentage_change=v.percentage_change, direction=v.direction,
        )
        for v in items
    ]

    material = [v for v in variance_items if v.percentage_change is not None and abs(v.percentage_change) >= threshold]

    return VarianceReportOut(
        entity=entity, current_period=current, previous_period=previous,
        template=template, items=variance_items, material_changes=material,
    )