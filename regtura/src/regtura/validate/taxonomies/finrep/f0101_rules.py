"""EBA FINREP validation rules for F 01.01 (Balance Sheet).

These rules implement the published EBA validation checks for the
FINREP Balance Sheet template. Each rule is a pure function that takes
SubmissionData and returns a ValidationResult.

Reference: EBA FINREP Taxonomy v3.2 validation rules.
"""

from __future__ import annotations

from regtura.common import (
    RuleType,
    Severity,
    SubmissionData,
    ValidationResult,
    ValidationRule,
    ValidationStatus,
)

TEMPLATE = "F 01.01"


def _fmt(value: float | None) -> str:
    """Format a number for display."""
    if value is None:
        return "N/A"
    return f"{value:,.0f}"


# ---------------------------------------------------------------------------
# Rule: v0100_m — Total Assets must equal sum of asset line items
# ---------------------------------------------------------------------------
def _check_total_assets(data: SubmissionData) -> ValidationResult:
    """Total Assets (r380,c010) = Cash (r010,c010) + Financial assets HfT (r020,c010)
    + ... + Other assets (r370,c010).

    For this initial implementation we check the major asset categories.
    Full coverage of all sub-rows will be added as we expand.
    """
    asset_rows = [
        "r010c010",  # Cash, cash balances at central banks
        "r020c010",  # Financial assets held for trading
        "r030c010",  # Non-trading financial assets (FVPL)
        "r060c010",  # Financial assets at FVOCI
        "r100c010",  # Financial assets at amortised cost
        "r230c010",  # Derivatives — hedge accounting
        "r240c010",  # Fair value changes of hedged items
        "r250c010",  # Investments in subsidiaries
        "r260c010",  # Tangible assets
        "r280c010",  # Intangible assets
        "r300c010",  # Tax assets
        "r340c010",  # Other assets
        "r370c010",  # Non-current assets held for sale
    ]

    total_assets = data.get_cell(TEMPLATE, "r380c010")
    if total_assets is None:
        return ValidationResult(
            rule_id="v0100_m",
            status=ValidationStatus.SKIPPED,
            detail="Total Assets (r380,c010) is missing from submission.",
        )

    component_sum = 0.0
    missing_rows = []
    for row in asset_rows:
        val = data.get_cell(TEMPLATE, row)
        if val is not None:
            component_sum += val
        else:
            missing_rows.append(row)

    if missing_rows:
        return ValidationResult(
            rule_id="v0100_m",
            status=ValidationStatus.WARNING,
            detail=(
                f"Partial check: sum of available components = {_fmt(component_sum)} "
                f"vs Total Assets = {_fmt(total_assets)}. "
                f"Missing rows: {', '.join(missing_rows)}."
            ),
            expected=total_assets,
            actual=component_sum,
            delta=total_assets - component_sum,
        )

    delta = total_assets - component_sum
    if abs(delta) < 0.01:  # Allow for floating point rounding
        return ValidationResult(
            rule_id="v0100_m",
            status=ValidationStatus.PASS,
            detail=f"Total Assets ({_fmt(total_assets)}) reconciles with component sum.",
            expected=total_assets,
            actual=component_sum,
            delta=0.0,
        )

    return ValidationResult(
        rule_id="v0100_m",
        status=ValidationStatus.FAIL,
        detail=(
            f"Total Assets mismatch: reported {_fmt(total_assets)} "
            f"but sum of components = {_fmt(component_sum)}. "
            f"Delta: {_fmt(delta)}."
        ),
        expected=total_assets,
        actual=component_sum,
        delta=delta,
    )


# ---------------------------------------------------------------------------
# Rule: v0101_m — Total Liabilities must equal sum of liability line items
# ---------------------------------------------------------------------------
def _check_total_liabilities(data: SubmissionData) -> ValidationResult:
    """Total Liabilities (r600,c010) = sum of liability line items."""
    liability_rows = [
        "r390c010",  # Financial liabilities held for trading
        "r400c010",  # Financial liabilities designated at FVPL
        "r430c010",  # Financial liabilities at amortised cost
        "r500c010",  # Derivatives — hedge accounting
        "r510c010",  # Fair value changes of hedged items
        "r520c010",  # Provisions
        "r540c010",  # Tax liabilities
        "r560c010",  # Share capital repayable on demand
        "r570c010",  # Other liabilities
        "r590c010",  # Liabilities in disposal groups
    ]

    total_liab = data.get_cell(TEMPLATE, "r600c010")
    if total_liab is None:
        return ValidationResult(
            rule_id="v0101_m",
            status=ValidationStatus.SKIPPED,
            detail="Total Liabilities (r600,c010) is missing from submission.",
        )

    component_sum = 0.0
    missing = []
    for row in liability_rows:
        val = data.get_cell(TEMPLATE, row)
        if val is not None:
            component_sum += val
        else:
            missing.append(row)

    if missing:
        return ValidationResult(
            rule_id="v0101_m",
            status=ValidationStatus.WARNING,
            detail=(
                f"Partial check: sum of available components = {_fmt(component_sum)} "
                f"vs Total Liabilities = {_fmt(total_liab)}. "
                f"Missing rows: {', '.join(missing)}."
            ),
            expected=total_liab,
            actual=component_sum,
            delta=total_liab - component_sum,
        )

    delta = total_liab - component_sum
    if abs(delta) < 0.01:
        return ValidationResult(
            rule_id="v0101_m",
            status=ValidationStatus.PASS,
            detail=f"Total Liabilities ({_fmt(total_liab)}) reconciles with component sum.",
            expected=total_liab,
            actual=component_sum,
            delta=0.0,
        )

    return ValidationResult(
        rule_id="v0101_m",
        status=ValidationStatus.FAIL,
        detail=(
            f"Total Liabilities mismatch: reported {_fmt(total_liab)} "
            f"but sum of components = {_fmt(component_sum)}. Delta: {_fmt(delta)}."
        ),
        expected=total_liab,
        actual=component_sum,
        delta=delta,
    )


# ---------------------------------------------------------------------------
# Rule: v0102_m — Total Equity + Liabilities = Equity + Total Liabilities
# ---------------------------------------------------------------------------
def _check_equity_plus_liabilities(data: SubmissionData) -> ValidationResult:
    """Total Equity and Liabilities (r620,c010) = Equity (r610,c010) + Liabilities (r600,c010)."""
    total = data.get_cell(TEMPLATE, "r620c010")
    equity = data.get_cell(TEMPLATE, "r610c010")
    liabilities = data.get_cell(TEMPLATE, "r600c010")

    if any(v is None for v in [total, equity, liabilities]):
        missing = [
            ref for ref, val in [
                ("r620c010", total), ("r610c010", equity), ("r600c010", liabilities)
            ] if val is None
        ]
        return ValidationResult(
            rule_id="v0102_m",
            status=ValidationStatus.SKIPPED,
            detail=f"Missing cells: {', '.join(missing)}.",
        )

    expected = equity + liabilities
    delta = total - expected

    if abs(delta) < 0.01:
        return ValidationResult(
            rule_id="v0102_m",
            status=ValidationStatus.PASS,
            detail=(
                f"Equity + Liabilities reconciles: {_fmt(equity)} + {_fmt(liabilities)} "
                f"= {_fmt(total)}."
            ),
            expected=expected,
            actual=total,
            delta=0.0,
        )

    return ValidationResult(
        rule_id="v0102_m",
        status=ValidationStatus.FAIL,
        detail=(
            f"Equity + Liabilities mismatch: {_fmt(equity)} + {_fmt(liabilities)} "
            f"= {_fmt(expected)} but reported {_fmt(total)}. Delta: {_fmt(delta)}."
        ),
        expected=expected,
        actual=total,
        delta=delta,
    )


# ---------------------------------------------------------------------------
# Rule: v0103_m — Balance sheet must balance
# ---------------------------------------------------------------------------
def _check_balance_sheet_balances(data: SubmissionData) -> ValidationResult:
    """Total Assets (r380,c010) must equal Total Equity + Liabilities (r620,c010)."""
    assets = data.get_cell(TEMPLATE, "r380c010")
    eq_liab = data.get_cell(TEMPLATE, "r620c010")

    if assets is None or eq_liab is None:
        return ValidationResult(
            rule_id="v0103_m",
            status=ValidationStatus.SKIPPED,
            detail="Missing Total Assets or Total Equity + Liabilities.",
        )

    delta = assets - eq_liab
    if abs(delta) < 0.01:
        return ValidationResult(
            rule_id="v0103_m",
            status=ValidationStatus.PASS,
            detail=f"Balance sheet balances: Assets = Equity + Liabilities = {_fmt(assets)}.",
            expected=assets,
            actual=eq_liab,
            delta=0.0,
        )

    return ValidationResult(
        rule_id="v0103_m",
        status=ValidationStatus.FAIL,
        detail=(
            f"Balance sheet imbalance: Total Assets = {_fmt(assets)}, "
            f"Total Equity + Liabilities = {_fmt(eq_liab)}. Gap: {_fmt(delta)}."
        ),
        expected=assets,
        actual=eq_liab,
        delta=delta,
    )


# ---------------------------------------------------------------------------
# Rule: v0104_m — Sign convention: provisions must be negative or zero
# ---------------------------------------------------------------------------
def _check_provisions_sign(data: SubmissionData) -> ValidationResult:
    """Provisions (r520,c010) must be reported as a negative value or zero."""
    provisions = data.get_cell(TEMPLATE, "r520c010")

    if provisions is None:
        return ValidationResult(
            rule_id="v0104_m",
            status=ValidationStatus.SKIPPED,
            detail="Provisions (r520,c010) not present in submission.",
        )

    if provisions <= 0:
        return ValidationResult(
            rule_id="v0104_m",
            status=ValidationStatus.PASS,
            detail=f"Provisions sign convention correct: {_fmt(provisions)}.",
        )

    return ValidationResult(
        rule_id="v0104_m",
        status=ValidationStatus.FAIL,
        detail=(
            f"Sign convention violation: Provisions (r520,c010) = {_fmt(provisions)}. "
            f"Expected negative or zero."
        ),
        actual=provisions,
    )


# ---------------------------------------------------------------------------
# Public API: get all F 01.01 rules
# ---------------------------------------------------------------------------
def get_f0101_rules() -> list[ValidationRule]:
    """Return all validation rules for FINREP F 01.01 (Balance Sheet)."""
    return [
        ValidationRule(
            rule_id="v0100_m",
            description="Total Assets (r380) = Sum of asset line items",
            severity=Severity.ERROR,
            rule_type=RuleType.INTRA,
            template=TEMPLATE,
            formula="r380c010 == SUM(r010c010:r370c010)",
            check=_check_total_assets,
        ),
        ValidationRule(
            rule_id="v0101_m",
            description="Total Liabilities (r600) = Sum of liability line items",
            severity=Severity.ERROR,
            rule_type=RuleType.INTRA,
            template=TEMPLATE,
            formula="r600c010 == SUM(r390c010:r590c010)",
            check=_check_total_liabilities,
        ),
        ValidationRule(
            rule_id="v0102_m",
            description="Total Equity + Liabilities (r620) = Equity (r610) + Liabilities (r600)",
            severity=Severity.ERROR,
            rule_type=RuleType.INTRA,
            template=TEMPLATE,
            formula="r620c010 == r610c010 + r600c010",
            check=_check_equity_plus_liabilities,
        ),
        ValidationRule(
            rule_id="v0103_m",
            description="Balance sheet must balance: Total Assets = Total Equity + Liabilities",
            severity=Severity.ERROR,
            rule_type=RuleType.INTRA,
            template=TEMPLATE,
            formula="r380c010 == r620c010",
            check=_check_balance_sheet_balances,
        ),
        ValidationRule(
            rule_id="v0104_m",
            description="Sign convention: Provisions must be negative or zero",
            severity=Severity.WARNING,
            rule_type=RuleType.QUALITY,
            template=TEMPLATE,
            formula="r520c010 <= 0",
            check=_check_provisions_sign,
        ),
    ]
