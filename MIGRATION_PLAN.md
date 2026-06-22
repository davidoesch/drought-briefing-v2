# MIGRATION_PLAN.md

# Drought Briefing Migration Plan

Version: 1.0

Status: Execution Plan

---

# 1. Purpose

This document defines the step-by-step migration strategy for refactoring the existing Drought-Briefing application into a fully static, YAML-driven, GitHub Actions-based system.

The goal is to ensure:

* no loss of scientific functionality
* controlled incremental refactoring
* reproducible outputs at every stage
* minimal disruption to existing processing logic

---

# 2. Migration Principles

## 2.1 Preserve Outputs

At every migration step:

* outputs must match the current system
* deviations must be explicitly documented and approved

---

## 2.2 Incremental Refactoring

The system must not be rewritten in a single step.

Each phase must:

* introduce one architectural change at a time
* remain deployable
* remain testable

---

## 2.3 Dual System Validation

During migration:

* old logic and new logic may temporarily coexist
* outputs must be compared for equivalence

---

## 2.4 No Behavioural Changes Without Approval

Any change in:

* drought classification
* thresholds
* aggregation logic

must be explicitly reviewed.

---

# 3. Migration Phases Overview

```text id="migr0"
Phase 0: Code Audit & Baseline Capture
Phase 1: Data Pipeline Extraction
Phase 2: Aggregation Refactoring
Phase 3: Rule Engine Extraction (YAML)
Phase 4: JSON Contract Stabilisation
Phase 5: Static Site Generation
Phase 6: GitHub Actions Automation
Phase 7: Frontend Replacement (Static UI)
Phase 8: Full System Validation
```

---

# 4. Phase 0 — Code Audit & Baseline Capture

## Objective

Understand and freeze current system behaviour.

## Tasks

* Identify all data sources
* Document aggregation logic
* Document drought classification rules
* Capture current outputs as baseline datasets
* Create snapshot comparison fixtures

## Deliverables

* baseline JSON outputs
* system behaviour documentation
* list of all indicators and transformations

---

# 5. Phase 1 — Data Pipeline Extraction

## Objective

Separate data acquisition from processing logic.

## Tasks

* extract download logic into `scripts/download.py`
* ensure all sources are reproducible
* store raw data in `data/raw/`

## Output

* raw datasets only
* no transformations yet

## Acceptance Criteria

* identical raw data retrieved compared to current system

---

# 6. Phase 2 — Aggregation Refactoring

## Objective

Isolate spatial aggregation logic.

## Tasks

* move aggregation logic into `aggregate.py`
* ensure identical outputs as baseline
* write unit tests for aggregation consistency

## Output

```text id="agg02"
data/processed/
```

## Acceptance Criteria

* numerical equivalence with baseline outputs

---

# 7. Phase 3 — Rule Engine Extraction (YAML)

## Objective

Remove hardcoded drought logic.

## Tasks

* extract thresholds from code
* define `config/rules.yaml`
* implement YAML-driven evaluation engine
* map existing logic 1:1 into YAML

## Output

* rule-based classification identical to baseline

## Acceptance Criteria

* no hardcoded thresholds remain in code

---

# 8. Phase 4 — JSON Contract Stabilisation

## Objective

Define stable output schema.

## Tasks

* define region JSON schema
* enforce schema validation
* ensure backward compatibility

## Output Example

```json id="schema01"
{
  "region_id": "BE",
  "status": "warning",
  "indicators": {},
  "messages": {}
}
```

## Acceptance Criteria

* frontend can rely exclusively on JSON contract

---

# 9. Phase 5 — Static Site Generation

## Objective

Introduce static site build step.

## Tasks

* implement `generate_site.py`
* generate HTML + assets into `site/`
* ensure no runtime computation in frontend

## Output

* fully static website bundle

## Acceptance Criteria

* site works without backend

---

# 10. Phase 6 — GitHub Actions Automation

## Objective

Automate full pipeline.

## Tasks

* create `.github/workflows/daily-update.yml`
* implement full pipeline execution:

  * download
  * validate
  * aggregate
  * evaluate
  * generate site
* publish to GitHub Pages

## Acceptance Criteria

* daily automated execution works
* manual trigger works
* idempotent execution

---

# 11. Phase 7 — Frontend Replacement

## Objective

Replace any dynamic frontend logic with static rendering.

## Tasks

* implement vanilla JS frontend
* load JSON from `data/processed/`
* implement language switching
* apply Swiss Confederation Design System

## Restrictions

* no computation in frontend
* no API calls
* no backend dependencies

---

# 12. Phase 8 — Full System Validation

## Objective

Verify full equivalence with legacy system.

## Tasks

* compare outputs for multiple historical days
* validate all regions
* validate all indicators
* validate multilingual outputs

## Acceptance Criteria

* zero functional regression
* full automation working
* production deployment ready

---

# 13. Testing Strategy

## 13.1 Regression Tests

* compare old vs new outputs
* tolerance: exact match required for classifications

## 13.2 Schema Tests

* validate JSON structure
* validate YAML structure

## 13.3 Pipeline Tests

* ensure deterministic execution

---

# 14. Risk Management

## Risk 1: Hidden Business Logic in Legacy Code

Mitigation:

* full code audit in Phase 0
* extract implicit logic early

---

## Risk 2: Output Drift

Mitigation:

* strict regression testing
* snapshot comparison at each phase

---

## Risk 3: Over-Refactoring

Mitigation:

* enforce incremental phases
* forbid multi-phase changes in one commit

---

# 15. Definition of Done

The migration is complete when:

* all phases implemented
* outputs match legacy system
* YAML fully controls rules and messages
* GitHub Actions fully automate pipeline
* GitHub Pages hosts static site
* no backend services exist
* no database exists
* non-programmers can modify system behaviour safely
