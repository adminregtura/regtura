"""EBA FINREP taxonomy — aggregates all FINREP validation rules.

Usage:
    from regtura.validate.taxonomies.finrep.taxonomy import FinrepTaxonomy

    rules = FinrepTaxonomy.get_rules()
"""

from __future__ import annotations

from regtura.common import ValidationRule
from regtura.validate.taxonomies.finrep.f0101_rules import get_f0101_rules


class FinrepTaxonomy:
    """EBA FINREP taxonomy definition.

    Aggregates validation rules from all supported FINREP templates.
    New templates are added by importing their rule functions here.
    """

    NAME = "finrep"
    VERSION = "3.2"
    DESCRIPTION = "EBA FINREP — Financial Reporting Framework"
    REGULATOR = "European Banking Authority (EBA)"
    JURISDICTION = "European Union"

    @classmethod
    def get_rules(cls) -> list[ValidationRule]:
        """Return all validation rules across all supported FINREP templates."""
        rules: list[ValidationRule] = []

        # F 01.01 — Balance Sheet
        rules.extend(get_f0101_rules())

        # Future templates will be added here:
        # rules.extend(get_f0200_rules())  # P&L
        # rules.extend(get_f0401_rules())  # Loans breakdown

        return rules

    @classmethod
    def info(cls) -> dict:
        """Return metadata about this taxonomy."""
        rules = cls.get_rules()
        return {
            "name": cls.NAME,
            "version": cls.VERSION,
            "description": cls.DESCRIPTION,
            "regulator": cls.REGULATOR,
            "jurisdiction": cls.JURISDICTION,
            "rule_count": len(rules),
            "templates": sorted(set(r.template for r in rules)),
        }
