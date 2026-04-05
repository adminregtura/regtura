"""Core data models used across Regtura modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Validation rule severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleType(str, Enum):
    """Categories of validation rules."""

    INTRA = "intra"          # Within a single template
    INTER = "inter"          # Across templates
    ANOMALY = "anomaly"      # Statistical / period-over-period
    QUALITY = "quality"      # Data quality checks (signs, nil reporting)


class ValidationStatus(str, Enum):
    """Result of a single validation check."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationRule:
    """A single validation rule definition.

    Attributes:
        rule_id: Unique identifier (e.g. 'v0100_m' for EBA rules).
        description: Human-readable explanation of what the rule checks.
        severity: Whether a failure is an error, warning, or informational.
        rule_type: Category of the rule (intra-template, inter-template, etc.).
        template: Which template(s) this rule applies to.
        formula: Human-readable formula string for documentation.
        check: Callable that takes submission data and returns a ValidationResult.
    """

    rule_id: str
    description: str
    severity: Severity
    rule_type: RuleType
    template: str
    formula: str
    check: Any = None  # Callable[[SubmissionData], ValidationResult]


@dataclass
class ValidationResult:
    """The outcome of running a single validation rule.

    Attributes:
        rule_id: Which rule produced this result.
        status: Pass, fail, warning, or skipped.
        detail: Human-readable explanation of the result.
        expected: The expected value (if applicable).
        actual: The actual value found (if applicable).
        delta: The difference between expected and actual (if applicable).
    """

    rule_id: str
    status: ValidationStatus
    detail: str
    expected: float | None = None
    actual: float | None = None
    delta: float | None = None


@dataclass
class SubmissionData:
    """Container for regulatory submission data.

    Holds the data for one or more templates, keyed by template name.
    Each template's data is a dictionary mapping cell references to values.

    Example:
        data = SubmissionData(
            framework="finrep",
            period="2024-Q4",
            templates={
                "F 01.01": {"r010c010": 15200000, "r380c010": 145000000, ...},
                "F 02.00": {"r010c010": 3200000, ...},
            }
        )
    """

    framework: str
    period: str
    templates: dict[str, dict[str, float]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_cell(self, template: str, cell_ref: str) -> float | None:
        """Retrieve a single cell value.

        Args:
            template: Template name (e.g. 'F 01.01').
            cell_ref: Cell reference (e.g. 'r380c010').

        Returns:
            The cell value, or None if not found.
        """
        tpl = self.templates.get(template)
        if tpl is None:
            return None
        return tpl.get(cell_ref)

    def has_template(self, template: str) -> bool:
        """Check whether data exists for a given template."""
        return template in self.templates


@dataclass
class ValidationReport:
    """Complete validation report for a submission.

    Attributes:
        framework: Which regulatory framework was validated.
        period: Reporting period.
        results: List of individual validation results.
        summary: Aggregate statistics.
    """

    framework: str
    period: str
    results: list[ValidationResult] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        """Count results by status."""
        counts = {"pass": 0, "fail": 0, "warning": 0, "skipped": 0}
        for r in self.results:
            counts[r.status.value] = counts.get(r.status.value, 0) + 1
        return counts

    @property
    def passed(self) -> bool:
        """True if no errors (warnings are acceptable)."""
        return self.summary.get("fail", 0) == 0
