"""Tests for FINREP F 01.01 validation rules."""

from regtura.common import SubmissionData, ValidationStatus
from regtura.validate.rule_engine.engine import RuleEngine
from regtura.validate.taxonomies.finrep.f0101_rules import get_f0101_rules


def _make_submission(**overrides) -> SubmissionData:
    """Create a valid baseline submission, with optional overrides."""
    base = {
        "r010c010": 5200000,
        "r020c010": 12800000,
        "r030c010": 3400000,
        "r060c010": 8900000,
        "r100c010": 82500000,
        "r230c010": 1200000,
        "r240c010": 500000,
        "r250c010": 4500000,
        "r260c010": 7800000,
        "r280c010": 3200000,
        "r300c010": 1900000,
        "r340c010": 2600000,
        "r370c010": 500000,
        # Total assets = sum of above = 135,000,000
        "r380c010": 135000000,
        "r390c010": 8500000,
        "r400c010": 5200000,
        "r430c010": 78000000,
        "r500c010": 900000,
        "r510c010": 300000,
        "r520c010": -4500000,
        "r540c010": 2100000,
        "r560c010": 0,
        "r570c010": 6800000,
        "r590c010": 1200000,
        # Total liabilities = sum of above = 98,500,000
        "r600c010": 98500000,
        "r610c010": 36500000,
        # Total equity + liabilities = 98,500,000 + 36,500,000 = 135,000,000
        "r620c010": 135000000,
    }
    base.update(overrides)
    return SubmissionData(
        framework="finrep",
        period="2024-Q4",
        templates={"F 01.01": base},
    )


class TestRuleEngine:
    """Tests for the core rule engine."""

    def test_engine_loads_rules(self):
        engine = RuleEngine()
        rules = get_f0101_rules()
        engine.load_rules(rules)
        assert engine.rule_count == 5

    def test_engine_clears_rules(self):
        engine = RuleEngine()
        engine.load_rules(get_f0101_rules())
        engine.clear_rules()
        assert engine.rule_count == 0

    def test_engine_returns_report(self):
        engine = RuleEngine()
        engine.load_rules(get_f0101_rules())
        data = _make_submission()
        report = engine.validate(data)
        assert report.framework == "finrep"
        assert report.period == "2024-Q4"
        assert len(report.results) == 5


class TestValidSubmission:
    """Tests that a fully valid submission passes all rules."""

    def test_all_rules_pass(self):
        engine = RuleEngine()
        engine.load_rules(get_f0101_rules())
        data = _make_submission()
        report = engine.validate(data)
        assert report.passed is True
        assert report.summary["fail"] == 0

    def test_total_assets_passes(self):
        data = _make_submission()
        rules = get_f0101_rules()
        result = rules[0].check(data)  # v0100_m
        assert result.status == ValidationStatus.PASS

    def test_balance_sheet_balances(self):
        data = _make_submission()
        rules = get_f0101_rules()
        result = rules[3].check(data)  # v0103_m
        assert result.status == ValidationStatus.PASS

    def test_provisions_sign_correct(self):
        data = _make_submission()
        rules = get_f0101_rules()
        result = rules[4].check(data)  # v0104_m
        assert result.status == ValidationStatus.PASS


class TestFailingSubmission:
    """Tests that invalid data is correctly caught."""

    def test_total_assets_mismatch(self):
        # Total assets doesn't match sum of components
        data = _make_submission(**{"r380c010": 999999999})
        rules = get_f0101_rules()
        result = rules[0].check(data)
        assert result.status == ValidationStatus.FAIL
        assert result.delta is not None
        assert result.delta != 0

    def test_balance_sheet_imbalance(self):
        # Assets != Equity + Liabilities
        data = _make_submission(**{"r620c010": 100000000})
        rules = get_f0101_rules()
        result = rules[3].check(data)
        assert result.status == ValidationStatus.FAIL

    def test_provisions_wrong_sign(self):
        # Provisions reported as positive (wrong)
        data = _make_submission(**{"r520c010": 4500000})
        rules = get_f0101_rules()
        result = rules[4].check(data)
        assert result.status == ValidationStatus.FAIL

    def test_equity_plus_liabilities_mismatch(self):
        # r620 != r610 + r600
        data = _make_submission(**{"r620c010": 999999})
        rules = get_f0101_rules()
        result = rules[2].check(data)
        assert result.status == ValidationStatus.FAIL


class TestEdgeCases:
    """Tests for missing data and edge cases."""

    def test_missing_total_assets_skips(self):
        data = SubmissionData(
            framework="finrep",
            period="2024-Q4",
            templates={"F 01.01": {"r010c010": 100}},
        )
        rules = get_f0101_rules()
        result = rules[0].check(data)
        assert result.status == ValidationStatus.SKIPPED

    def test_missing_template_skips(self):
        data = SubmissionData(framework="finrep", period="2024-Q4", templates={})
        rules = get_f0101_rules()
        result = rules[0].check(data)
        assert result.status == ValidationStatus.SKIPPED

    def test_partial_data_warns(self):
        # Has total assets but missing some component rows
        data = SubmissionData(
            framework="finrep",
            period="2024-Q4",
            templates={
                "F 01.01": {
                    "r010c010": 5200000,
                    "r380c010": 135000000,
                }
            },
        )
        rules = get_f0101_rules()
        result = rules[0].check(data)
        assert result.status == ValidationStatus.WARNING

    def test_zero_provisions_passes(self):
        data = _make_submission(**{"r520c010": 0})
        rules = get_f0101_rules()
        result = rules[4].check(data)
        assert result.status == ValidationStatus.PASS

    def test_report_summary_counts(self):
        engine = RuleEngine()
        engine.load_rules(get_f0101_rules())
        # Create data where some rules pass and some fail
        data = _make_submission(**{"r380c010": 999, "r520c010": 100})
        report = engine.validate(data)
        assert report.summary["fail"] > 0
        assert report.passed is False
