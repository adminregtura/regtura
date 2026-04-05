"""Submission history storage and variance analysis.

Stores validated submissions keyed by entity + reporting period,
enabling period-over-period variance analysis.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from regtura.common import SubmissionData, ValidationReport


@dataclass
class StoredSubmission:
    """A saved submission with its validation results."""

    submission_id: str
    entity: str
    period: str
    framework: str
    uploaded_at: str
    filename: str
    templates: dict[str, dict[str, float]]
    metadata: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, int] = field(default_factory=dict)
    passed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> StoredSubmission:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class VarianceItem:
    """A single cell's variance between two periods."""

    cell_ref: str
    label: str
    current_value: float
    previous_value: float
    absolute_change: float
    percentage_change: float | None

    @property
    def direction(self) -> str:
        if self.absolute_change > 0:
            return "increase"
        elif self.absolute_change < 0:
            return "decrease"
        return "unchanged"


class HistoryStore:
    """File-based storage for submission history.

    Stores submissions as JSON files in a configurable directory,
    organised by entity name.
    """

    def __init__(self, storage_dir: str | Path = "~/.regtura/history"):
        self._dir = Path(os.path.expanduser(str(storage_dir)))
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        data: SubmissionData,
        report: ValidationReport,
        filename: str = "",
    ) -> StoredSubmission:
        """Save a submission and its validation results."""
        entity = data.metadata.get("entity", "Unknown Entity")
        safe_entity = self._safe_name(entity)
        safe_period = self._safe_name(data.period)
        submission_id = f"{safe_entity}_{safe_period}"

        stored = StoredSubmission(
            submission_id=submission_id,
            entity=entity,
            period=data.period,
            framework=data.framework,
            uploaded_at=datetime.now().isoformat(),
            filename=filename,
            templates=data.templates,
            metadata=data.metadata,
            summary=report.summary,
            passed=report.passed,
        )

        entity_dir = self._dir / safe_entity
        entity_dir.mkdir(parents=True, exist_ok=True)

        filepath = entity_dir / f"{safe_period}.json"
        with open(filepath, "w") as f:
            json.dump(stored.to_dict(), f, indent=2, default=str)

        return stored

    def list_entities(self) -> list[str]:
        """List all entities that have stored submissions."""
        if not self._dir.exists():
            return []
        return sorted([
            d.name for d in self._dir.iterdir()
            if d.is_dir() and any(d.glob("*.json"))
        ])

    def list_submissions(self, entity: str | None = None) -> list[StoredSubmission]:
        """List stored submissions, optionally filtered by entity."""
        submissions = []
        search_dirs = []

        if entity:
            safe = self._safe_name(entity)
            entity_dir = self._dir / safe
            if entity_dir.exists():
                search_dirs.append(entity_dir)
        else:
            if self._dir.exists():
                search_dirs = [d for d in self._dir.iterdir() if d.is_dir()]

        for d in search_dirs:
            for f in sorted(d.glob("*.json")):
                try:
                    with open(f) as fh:
                        stored = StoredSubmission.from_dict(json.load(fh))
                        submissions.append(stored)
                except Exception:
                    continue

        return sorted(submissions, key=lambda s: s.period, reverse=True)

    def get_submission(self, entity: str, period: str) -> StoredSubmission | None:
        """Retrieve a specific submission."""
        safe_entity = self._safe_name(entity)
        safe_period = self._safe_name(period)
        filepath = self._dir / safe_entity / f"{safe_period}.json"

        if not filepath.exists():
            return None

        with open(filepath) as f:
            return StoredSubmission.from_dict(json.load(f))

    def delete_submission(self, entity: str, period: str) -> bool:
        """Delete a stored submission."""
        safe_entity = self._safe_name(entity)
        safe_period = self._safe_name(period)
        filepath = self._dir / safe_entity / f"{safe_period}.json"

        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def compute_variance(
        self,
        entity: str,
        current_period: str,
        previous_period: str,
        template: str = "F 01.01",
    ) -> list[VarianceItem]:
        """Compute period-over-period variance for an entity."""
        current = self.get_submission(entity, current_period)
        previous = self.get_submission(entity, previous_period)

        if current is None or previous is None:
            return []

        current_data = current.templates.get(template, {})
        previous_data = previous.templates.get(template, {})

        all_refs = sorted(set(list(current_data.keys()) + list(previous_data.keys())))

        variances = []
        for ref in all_refs:
            curr_val = current_data.get(ref)
            prev_val = previous_data.get(ref)

            if curr_val is None or prev_val is None:
                continue

            absolute = curr_val - prev_val
            pct = ((curr_val - prev_val) / abs(prev_val) * 100) if prev_val != 0 else None

            variances.append(VarianceItem(
                cell_ref=ref,
                label=CELL_LABELS.get(ref, ref),
                current_value=curr_val,
                previous_value=prev_val,
                absolute_change=absolute,
                percentage_change=round(pct, 2) if pct is not None else None,
            ))

        return variances

    @staticmethod
    def _safe_name(name: str) -> str:
        """Convert a name to a safe filename."""
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in name.strip()).lower()


# Human-readable labels for cell references
CELL_LABELS = {
    "r010c010": "Cash and central bank balances",
    "r020c010": "Financial assets held for trading",
    "r030c010": "Non-trading financial assets at FVPL",
    "r060c010": "Financial assets at FVOCI",
    "r100c010": "Financial assets at amortised cost",
    "r230c010": "Derivatives — Hedge accounting",
    "r240c010": "Fair value changes of hedged items",
    "r250c010": "Investments in subsidiaries",
    "r260c010": "Tangible assets",
    "r280c010": "Intangible assets",
    "r300c010": "Tax assets",
    "r340c010": "Other assets",
    "r370c010": "Non-current assets held for sale",
    "r380c010": "TOTAL ASSETS",
    "r390c010": "Financial liabilities held for trading",
    "r400c010": "Financial liabilities at FVPL",
    "r430c010": "Financial liabilities at amortised cost",
    "r500c010": "Derivatives — Hedge accounting (liabilities)",
    "r510c010": "Fair value changes of hedged items (liabilities)",
    "r520c010": "Provisions",
    "r540c010": "Tax liabilities",
    "r560c010": "Share capital repayable on demand",
    "r570c010": "Other liabilities",
    "r590c010": "Liabilities in disposal groups",
    "r600c010": "TOTAL LIABILITIES",
    "r610c010": "Total equity",
    "r620c010": "TOTAL EQUITY AND LIABILITIES",
}