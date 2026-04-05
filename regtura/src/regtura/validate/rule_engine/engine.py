"""Rule engine — executes validation rules against submission data."""

from __future__ import annotations

from regtura.common import (
    SubmissionData,
    ValidationReport,
    ValidationResult,
    ValidationRule,
    ValidationStatus,
)


class RuleEngine:
    """Framework-agnostic validation engine.

    The engine accepts a set of validation rules (from any regulatory taxonomy)
    and executes them against submission data. It is deliberately simple —
    all framework-specific logic lives in the taxonomy modules.

    Usage:
        from regtura.validate.taxonomies.finrep.rules import get_finrep_rules

        engine = RuleEngine()
        engine.load_rules(get_finrep_rules())
        report = engine.validate(submission_data)
    """

    def __init__(self) -> None:
        self._rules: list[ValidationRule] = []

    @property
    def rule_count(self) -> int:
        """Number of loaded rules."""
        return len(self._rules)

    def load_rules(self, rules: list[ValidationRule]) -> None:
        """Load a set of validation rules.

        Args:
            rules: List of ValidationRule objects, typically from a taxonomy module.
        """
        self._rules.extend(rules)

    def clear_rules(self) -> None:
        """Remove all loaded rules."""
        self._rules.clear()

    def validate(self, data: SubmissionData) -> ValidationReport:
        """Run all loaded rules against the submission data.

        Args:
            data: The regulatory submission to validate.

        Returns:
            A ValidationReport containing all results.
        """
        report = ValidationReport(framework=data.framework, period=data.period)

        for rule in self._rules:
            result = self._execute_rule(rule, data)
            report.results.append(result)

        return report

    def _execute_rule(self, rule: ValidationRule, data: SubmissionData) -> ValidationResult:
        """Execute a single validation rule.

        If the rule's check function raises an exception, the rule is marked
        as skipped with the error detail — we never silently swallow failures.
        """
        if rule.check is None:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.SKIPPED,
                detail=f"Rule {rule.rule_id} has no check function defined.",
            )

        try:
            return rule.check(data)
        except Exception as e:
            return ValidationResult(
                rule_id=rule.rule_id,
                status=ValidationStatus.SKIPPED,
                detail=f"Rule {rule.rule_id} raised an exception: {e}",
            )
