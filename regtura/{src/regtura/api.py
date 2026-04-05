"""Regtura API — FastAPI backend for the validation engine."""

from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from regtura.common import SubmissionData
from regtura.validate.rule_engine.engine import RuleEngine
from regtura.validate.taxonomies.finrep.taxonomy import FinrepTaxonomy


app = FastAPI(
    title="Regtura API",
    description="Open source regulatory reporting validation engine",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Available taxonomies
TAXONOMIES = {
    "finrep": FinrepTaxonomy,
}


class ValidationRequest(BaseModel):
    """Request body for validation."""
    framework: str
    period: str
    templates: dict[str, dict[str, float]]
    metadata: dict[str, Any] = {}


class ValidationResultOut(BaseModel):
    """Single validation result."""
    rule_id: str
    status: str
    detail: str
    expected: float | None = None
    actual: float | None = None
    delta: float | None = None


class RuleOut(BaseModel):
    """Validation rule info."""
    rule_id: str
    description: str
    severity: str
    rule_type: str
    template: str
    formula: str


class ValidationReportOut(BaseModel):
    """Complete validation report."""
    framework: str
    period: str
    summary: dict[str, int]
    passed: bool
    results: list[ValidationResultOut]


class TaxonomyInfoOut(BaseModel):
    """Taxonomy metadata."""
    name: str
    version: str
    description: str
    regulator: str
    jurisdiction: str
    rule_count: int
    templates: list[str]


@app.get("/")
def root():
    """Health check."""
    return {"name": "Regtura API", "version": "0.1.0", "status": "running"}


@app.get("/taxonomies", response_model=list[TaxonomyInfoOut])
def list_taxonomies():
    """List all available regulatory taxonomies."""
    return [tax.info() for tax in TAXONOMIES.values()]


@app.get("/taxonomies/{taxonomy_name}", response_model=TaxonomyInfoOut)
def get_taxonomy(taxonomy_name: str):
    """Get details about a specific taxonomy."""
    if taxonomy_name not in TAXONOMIES:
        raise HTTPException(status_code=404, detail=f"Taxonomy '{taxonomy_name}' not found.")
    return TAXONOMIES[taxonomy_name].info()


@app.get("/taxonomies/{taxonomy_name}/rules", response_model=list[RuleOut])
def get_rules(taxonomy_name: str):
    """List all validation rules for a taxonomy."""
    if taxonomy_name not in TAXONOMIES:
        raise HTTPException(status_code=404, detail=f"Taxonomy '{taxonomy_name}' not found.")
    
    rules = TAXONOMIES[taxonomy_name].get_rules()
    return [
        RuleOut(
            rule_id=r.rule_id,
            description=r.description,
            severity=r.severity.value,
            rule_type=r.rule_type.value,
            template=r.template,
            formula=r.formula,
        )
        for r in rules
    ]


@app.post("/validate/{taxonomy_name}", response_model=ValidationReportOut)
def validate(taxonomy_name: str, request: ValidationRequest):
    """Validate submission data against a taxonomy's rules."""
    if taxonomy_name not in TAXONOMIES:
        raise HTTPException(status_code=404, detail=f"Taxonomy '{taxonomy_name}' not found.")

    tax = TAXONOMIES[taxonomy_name]
    rules = tax.get_rules()

    data = SubmissionData(
        framework=request.framework,
        period=request.period,
        templates=request.templates,
        metadata=request.metadata,
    )

    engine = RuleEngine()
    engine.load_rules(rules)
    report = engine.validate(data)

    return ValidationReportOut(
        framework=report.framework,
        period=report.period,
        summary=report.summary,
        passed=report.passed,
        results=[
            ValidationResultOut(
                rule_id=r.rule_id,
                status=r.status.value,
                detail=r.detail,
                expected=r.expected,
                actual=r.actual,
                delta=r.delta,
            )
            for r in report.results
        ],
    )


@app.post("/validate/{taxonomy_name}/upload", response_model=ValidationReportOut)
async def validate_upload(taxonomy_name: str, file: UploadFile = File(...)):
    """Validate a JSON submission file uploaded by the user."""
    if taxonomy_name not in TAXONOMIES:
        raise HTTPException(status_code=404, detail=f"Taxonomy '{taxonomy_name}' not found.")

    try:
        content = await file.read()
        raw = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file.")

    request = ValidationRequest(
        framework=raw.get("framework", taxonomy_name),
        period=raw.get("period", "unknown"),
        templates=raw.get("templates", {}),
        metadata=raw.get("metadata", {}),
    )

    return validate(taxonomy_name, request)
