"""Regtura command-line interface."""

from __future__ import annotations

import json
import sys

import click

from regtura import __version__
from regtura.common import SubmissionData
from regtura.validate.rule_engine.engine import RuleEngine
from regtura.validate.taxonomies.finrep.taxonomy import FinrepTaxonomy


TAXONOMIES = {
    "finrep": FinrepTaxonomy,
    # Future:
    # "mas610": Mas610Taxonomy,
    # "fry9c": Fry9cTaxonomy,
}


@click.group()
@click.version_option(version=__version__, prog_name="regtura")
def main():
    """Regtura — Open source regulatory reporting suite."""
    pass


@main.command()
@click.option("--input", "-i", "input_file", required=True, help="Path to submission data (JSON).")
@click.option(
    "--taxonomy", "-t", required=True,
    type=click.Choice(list(TAXONOMIES.keys())),
    help="Regulatory taxonomy to validate against.",
)
@click.option("--output", "-o", "output_file", default=None, help="Output file path (JSON). Prints to stdout if omitted.")
def validate(input_file: str, taxonomy: str, output_file: str | None):
    """Validate a regulatory submission against a taxonomy's rules."""
    # Load taxonomy
    tax_class = TAXONOMIES[taxonomy]
    rules = tax_class.get_rules()

    click.echo(f"Loaded {len(rules)} validation rules from {tax_class.DESCRIPTION}.")

    # Load submission data
    try:
        with open(input_file) as f:
            raw = json.load(f)
    except FileNotFoundError:
        click.echo(f"Error: File not found: {input_file}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in {input_file}: {e}", err=True)
        sys.exit(1)

    data = SubmissionData(
        framework=raw.get("framework", taxonomy),
        period=raw.get("period", "unknown"),
        templates=raw.get("templates", {}),
        metadata=raw.get("metadata", {}),
    )

    # Run validation
    engine = RuleEngine()
    engine.load_rules(rules)
    report = engine.validate(data)

    # Format output
    output = {
        "framework": report.framework,
        "period": report.period,
        "summary": report.summary,
        "passed": report.passed,
        "results": [
            {
                "rule_id": r.rule_id,
                "status": r.status.value,
                "detail": r.detail,
                "expected": r.expected,
                "actual": r.actual,
                "delta": r.delta,
            }
            for r in report.results
        ],
    }

    output_json = json.dumps(output, indent=2)

    if output_file:
        with open(output_file, "w") as f:
            f.write(output_json)
        click.echo(f"Report written to {output_file}.")
    else:
        click.echo(output_json)

    # Print summary
    s = report.summary
    status_line = (
        f"\nSummary: {s['pass']} passed, {s['fail']} failed, "
        f"{s['warning']} warnings, {s['skipped']} skipped."
    )
    if report.passed:
        click.echo(click.style(status_line, fg="green"))
    else:
        click.echo(click.style(status_line, fg="red"))


@main.command()
@click.option(
    "--taxonomy", "-t", default=None,
    type=click.Choice(list(TAXONOMIES.keys())),
    help="Show info for a specific taxonomy.",
)
def info(taxonomy: str | None):
    """Show information about available taxonomies."""
    if taxonomy:
        tax_class = TAXONOMIES[taxonomy]
        info_data = tax_class.info()
        click.echo(json.dumps(info_data, indent=2))
    else:
        click.echo("Available taxonomies:\n")
        for name, tax_class in TAXONOMIES.items():
            info_data = tax_class.info()
            click.echo(f"  {name}")
            click.echo(f"    {info_data['description']}")
            click.echo(f"    Regulator: {info_data['regulator']}")
            click.echo(f"    Rules: {info_data['rule_count']}")
            click.echo()


if __name__ == "__main__":
    main()
