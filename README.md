# Regtura

**The open source regulatory reporting suite.**

Regtura helps financial institutions automate regulatory reporting — from data validation to submission-ready outputs. Built for risk and compliance teams who are tired of complex automation tools. My ambition is to build incrementally and quickly to capture the latest technology trends and directly apply them to the regulatory compliance domain.

---

## Why Regtura?

Regulatory reporting is one of the most resource-intensive functions in financial institutions. Every quarter, teams spend weeks manually validating data, chasing discrepancies, and formatting reports — all under tight deadlines with zero tolerance for errors.

Existing solutions are expensive, rigid, and opaque. Regtura takes a different approach:

- **Open source** — inspect every rule, audit every check, understand exactly what's happening to your data. No black boxes.
- **AI-augmented** — deterministic rule engines for accuracy, AI agents for root cause analysis and intelligent triage. The right tool for each job.
- **Multi-jurisdictional** — built from the ground up to support regulatory frameworks across the EU, US, and Asia-Pacific.
- **Modular** — start with what you need today, expand as your requirements grow.
- **Community-driven** — built by practitioners, for practitioners.

---

## Modules

Regtura is designed as a suite of modules that work together or independently.

### Regtura Validate *(active development)*

Automated validation engine for regulatory templates across multiple jurisdictions. Runs published validation rules against your submission data and uses AI to analyse failures, detect anomalies, and prioritise findings.

**Supported frameworks:**

| Framework | Jurisdiction | Regulator | Templates | Status |
|-----------|-------------|-----------|-----------|--------|
| EBA FINREP | European Union | EBA / ECB | F 01.01, F 02.00, F 04.01–04.04 | In progress |
| MAS 610 | Singapore | MAS | Balance sheet, P&L, capital adequacy | Planned |
| FR Y-9C | United States | Federal Reserve | HC-B, HC-K, HC-R | Planned |

**Features:**
- Intra-template and inter-template validation rules
- Period-over-period anomaly detection
- AI-powered root cause analysis for validation failures
- Cross-framework consistency checks
- Structured validation reports (JSON, HTML)

### Regtura Report *(planned)*

Automated generation of submission-ready regulatory reports, including narrative commentary sections.

### Regtura Compute *(planned)*

Risk calculation engine for standard regulatory computations (RWA, capital ratios, liquidity metrics).

---

## Quick start

> **Note:** Regtura is in early development. The API and interfaces may change between releases.

### Requirements

- Python 3.10 or higher
- pip

### Installation

```bash
pip install regtura
```

### Basic usage

```python
from regtura.validate import RuleEngine, Taxonomy

# Load a regulatory taxonomy
taxonomy = Taxonomy.load("finrep_v3.2")  # or "mas610", "fry9c"

# Run validation
engine = RuleEngine(taxonomy)
results = engine.validate("path/to/your/data.csv")

# View results
for result in results:
    print(f"{result.rule_id}: {result.status} — {result.detail}")
```

### CLI

```bash
# Validate against different frameworks
regtura validate --input data.csv --taxonomy finrep_v3.2 --output report.json
regtura validate --input data.csv --taxonomy mas610 --output report.json
regtura validate --input data.csv --taxonomy fry9c --output report.json
```

---

## Architecture

```
regtura/
├── validate/          # Validation engine (active)
│   ├── taxonomies/    # Framework-specific rule definitions
│   │   ├── finrep/    # EBA FINREP (EU)
│   │   ├── mas610/    # MAS 610 (Singapore)
│   │   └── fry9c/     # FR Y-9C (US)
│   ├── rule_parser/   # Parses taxonomy rules into executable checks
│   ├── rule_engine/   # Runs validation checks against data
│   ├── ai_agent/      # Root cause analysis & anomaly detection
│   └── reporter/      # Generates validation reports
├── report/            # Report generation (planned)
├── compute/           # Risk calculations (planned)
└── common/            # Shared utilities, data models, config
```

The validation engine follows a clear separation of concerns:

1. **Deterministic rule engine** — executes every published validation rule with full traceability. No AI here — just precise, auditable arithmetic.
2. **AI agent layer** — wraps around the rule engine to provide root cause analysis, anomaly detection, and intelligent triage. The AI never modifies validation results — it analyses and explains them.
3. **Reporter** — transforms results into structured, actionable reports.

Each regulatory framework is implemented as a pluggable taxonomy module. The rule engine is framework-agnostic — it executes whatever rules the taxonomy provides. This means adding a new jurisdiction is a matter of defining its rules, not rewriting the engine.

---

## Roadmap

See our full [roadmap](ROADMAP.md) for details. High-level milestones:

- **v0.1** — Core FINREP validation engine with EBA rules
- **v0.2** — AI agent layer for root cause analysis and anomaly detection
- **v0.3** — MAS 610 support and cross-framework architecture
- **v0.4** — FR Y-9C support, web UI, and reporting module
- **v0.5** — Enterprise features (API mode, structured logging, custom rules)

---

## Contributing

Regtura is in its early stages and contributions are welcome. Whether you're a developer, a risk analyst, or a regulatory reporting specialist — there's a place for you.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ways to contribute:**
- Report bugs or suggest features via [GitHub Issues](../../issues)
- Submit pull requests for bug fixes or new features
- Add validation rules for additional regulatory frameworks
- Improve documentation or write tutorials
- Share your experience with regulatory reporting to help shape the roadmap

---

## Who is this for?

- **Risk and compliance teams** at banks, investment firms, and insurance companies who want to automate and improve their validation processes
- **RegTech companies** looking for an open source foundation to build upon
- **Consultants and auditors** who need transparent, auditable validation tools
- **Developers** building regulatory reporting pipelines who need a reliable validation layer

---

## Licence

Regtura is licensed under the [GNU Affero General Public License v3.0](LICENSE). This means you can freely use, modify, and distribute Regtura, but any modifications to the code — including when deployed as a service — must be released under the same licence.

For commercial licensing enquiries, please [get in touch](mailto:admin@regtura-ai.com).

---

## Acknowledgements

Regtura uses publicly available regulatory taxonomies and validation rules published by the European Banking Authority (EBA), the Monetary Authority of Singapore (MAS), and the Federal Reserve. This project is not affiliated with or endorsed by any regulatory authority.

---

<p align="center">
  <strong>Regtura</strong> — Regulatory reporting, forged in the open.
</p>
