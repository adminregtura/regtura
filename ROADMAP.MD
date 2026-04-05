# Regtura Roadmap

This roadmap outlines the planned development milestones for Regtura. Timelines are estimates and may shift based on community feedback and contributions.

---

## v0.1 — Foundation *(target: Month 2)*

The first public release. A working validation engine for core EBA FINREP templates.

- [ ] EBA FINREP taxonomy rule parser (v3.2)
- [ ] Deterministic validation engine for intra-template rules
- [ ] Support for F 01.01 (Balance Sheet), F 02.00 (P&L), F 04.01–04.04 (Loans breakdown)
- [ ] Inter-template validation rules between supported templates
- [ ] CLI interface for running validations
- [ ] JSON output format for validation results
- [ ] Synthetic sample data for testing and demos
- [ ] Unit test coverage for all implemented rules
- [ ] Documentation: installation, quickstart, architecture overview

## v0.2 — AI Agent Layer *(target: Month 3)*

Adding intelligence on top of the deterministic engine.

- [ ] AI agent framework for root cause analysis
- [ ] Anomaly detection module (period-over-period, ratio analysis)
- [ ] Configurable LLM provider (OpenAI, Anthropic, local models)
- [ ] Agent tools: query historical data, trace data lineage, generate explanations
- [ ] Prioritised findings with materiality-based triage
- [ ] Enhanced validation reports with AI insights
- [ ] Jupyter notebook tutorials

## v0.3 — MAS 610 *(target: Month 4)*

Expanding to Singapore — proving the multi-jurisdictional architecture.

- [ ] MAS 610 taxonomy parser and rule definitions
- [ ] Balance sheet schedule validation rules
- [ ] Profit and loss schedule validation rules
- [ ] Capital adequacy schedule validation rules
- [ ] Cross-schedule consistency checks within MAS 610
- [ ] Pluggable taxonomy architecture (any framework can be added as a module)
- [ ] Framework comparison tooling (map equivalent concepts across FINREP ↔ MAS 610)
- [ ] HTML and PDF report generation
- [ ] Basic web UI (Streamlit or FastAPI) for non-technical users

## v0.4 — FR Y-9C *(target: Month 5)*

Adding US Federal Reserve reporting — completing the three-jurisdiction foundation.

- [ ] FR Y-9C taxonomy parser and rule definitions
- [ ] Schedule HC-B (Securities) validation rules
- [ ] Schedule HC-K (Quarterly Averages) validation rules
- [ ] Schedule HC-R (Regulatory Capital) validation rules
- [ ] Inter-schedule consistency checks within FR Y-9C
- [ ] Cross-framework mapping (FINREP ↔ MAS 610 ↔ FR Y-9C equivalent fields)
- [ ] REST API mode for pipeline integration
- [ ] Structured logging and audit trails

## v0.5 — Enterprise Readiness *(target: Month 6)*

Making Regtura production-ready for institutional use.

- [ ] Custom rule definition support (user-defined rules in YAML/JSON)
- [ ] Performance optimisation for large submissions
- [ ] Configurable output formats and templates
- [ ] Integration examples with common data platforms (Snowflake, BigQuery, SQL Server)
- [ ] Security documentation and deployment guides
- [ ] Contributor toolkit and "good first issues" programme
- [ ] Project website with interactive documentation

---

## Beyond v0.5

Areas under consideration for future development. Community input welcome.

**Additional frameworks:**
- EBA COREP (EU capital requirements)
- APRA reporting (Australia)
- OSFI reporting (Canada)
- BOE statistical returns (UK)
- IFRS 9 expected credit loss reporting

**Additional modules:**
- Regtura Report — automated narrative generation for regulatory submissions
- Regtura Compute — regulatory calculation engine (RWA, capital ratios, liquidity metrics)
- Regtura Connect — pre-built integrations with source systems and submission gateways

**Platform capabilities:**
- Real-time validation during data entry
- Multi-entity consolidation support
- Managed cloud offering
- Regulatory change tracking and impact analysis

---

Want to influence the roadmap? Open an issue or join the discussion on GitHub.
