# ARCHITECTURE.md

# Drought Briefing Architecture

Version: 1.0

Status: Target Architecture

---

# Overview

The Drought Briefing platform is a fully static web application generated from automated daily data processing workflows.

The architecture follows a strict separation between:

1. Data Acquisition
2. Data Processing
3. Rule Evaluation
4. Static Content Generation
5. Website Publication

The frontend never performs scientific calculations.

All drought assessments are generated during the build process.

---

# High-Level Architecture

```text
External Data Sources
          │
          ▼
 GitHub Actions
          │
          ▼
 Data Download
          │
          ▼
 Data Validation
          │
          ▼
 Spatial Aggregation
          │
          ▼
 Rule Evaluation
          │
          ▼
 JSON Generation
          │
          ▼
 Static Website Generation
          │
          ▼
 GitHub Pages
```

---

# Repository Structure

```text
drought-briefing/

├── config/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── scripts/
│
├── site/
│
├── tests/
│
├── docs/
│
└── .github/
    └── workflows/
```

---

# Configuration Layer

All operational configuration shall be stored in YAML.

```text
config/

  sources.yaml

  regions.yaml

  rules.yaml

  messages.yaml

  translations.yaml

  site.yaml
```

Configuration must be editable by non-programmers.

No drought thresholds shall be hardcoded in Python.

---

# Configuration Responsibilities

## sources.yaml

Defines all data sources.

Example:

```yaml
sources:

  vhi:
    enabled: true

  groundwater:
    enabled: true

  precipitation:
    enabled: true
```

---

## regions.yaml

Defines aggregation regions.

Example:

```yaml
regions:

  national:
    enabled: true

  cantons:
    enabled: true

  warning_regions:
    enabled: true
```

---

## rules.yaml

Defines drought classifications.

Example:

```yaml
vhi:

  normal:
    min: 40

  watch:
    min: 30
    max: 39

  warning:
    min: 20
    max: 29

  severe:
    max: 19
```

---

## messages.yaml

Contains multilingual drought messages.

Example:

```yaml
messages:

  severe:

    de: Critical drought conditions.

    fr: Conditions de sécheresse critiques.

    it: Condizioni di siccità critiche.
```

---

# Data Layer

## Raw Data

Downloaded datasets.

Location:

```text
data/raw/
```

Purpose:

* temporary processing
* validation input

Raw data must never be consumed by the frontend.

---

## Processed Data

Location:

```text
data/processed/
```

Purpose:

* website input
* public API-like data products

---

# Processed Data Structure

```text
data/processed/

  national.json

  cantons/

      AG.json
      AI.json
      AR.json
      BE.json
      BL.json
      BS.json

  warning_regions/

      region_001.json
      region_002.json
```

---

# JSON Data Contract

All generated region files shall follow a common schema.

Example:

```json
{
  "region_id": "BE",
  "region_name": "Bern",

  "status": "warning",

  "indicators": {
    "vhi": 22,
    "precipitation": 35,
    "groundwater": 41
  },

  "messages": {
    "de": "Trockenheitssituation angespannt",
    "fr": "Situation de sécheresse tendue",
    "it": "Situazione di siccità tesa"
  },

  "updated_at": "2026-06-22T00:30:00Z"
}
```

This schema shall be considered stable.

Frontend components depend on it.

---

# Processing Layer

Location:

```text
scripts/
```

Modules:

```text
download.py

validate.py

aggregate.py

evaluate.py

generate_site.py
```

Each module shall have a single responsibility.

---

# Download Module

Purpose:

Download source datasets.

Responsibilities:

* download files
* verify availability
* store raw data

Output:

```text
data/raw/
```

---

# Validation Module

Purpose:

Verify downloaded datasets.

Checks:

* file exists
* schema validity
* geometry validity
* expected attributes

Failure:

Workflow stops.

---

# Aggregation Module

Purpose:

Generate regional statistics.

Input:

```text
data/raw/
```

Output:

```text
data/processed/
```

Aggregation logic shall remain equivalent to the current implementation.

---

# Evaluation Module

Purpose:

Apply drought rules.

Input:

```text
rules.yaml
```

Output:

Drought classifications.

No hardcoded thresholds allowed.

---

# Site Generation Module

Purpose:

Generate static website assets.

Input:

```text
data/processed/
config/
```

Output:

```text
site/
```

---

# Frontend Layer

Location:

```text
site/
```

Technology:

* HTML
* CSS
* Vanilla JavaScript

No frontend framework.

---

# Frontend Responsibilities

The frontend may:

* load JSON
* render pages
* switch languages
* display indicators
* display maps

The frontend may not:

* calculate drought classes
* evaluate thresholds
* perform aggregation

---

# Design System

Frontend shall use:

Swiss Confederation Design System

Objectives:

* responsive layout
* accessibility
* official visual identity
* multilingual navigation

Custom styling should be minimal.

---

# GitHub Actions Architecture

Workflow:

```text
.github/workflows/

  daily-update.yml
```

Execution:

1. Checkout repository
2. Install dependencies
3. Download datasets
4. Validate datasets
5. Aggregate indicators
6. Apply rules
7. Generate JSON
8. Generate website
9. Publish GitHub Pages

---

# Deployment Architecture

Deployment Target:

GitHub Pages

Published Content:

```text
site/
```

No runtime infrastructure required.

No server required.

No database required.

---

# Testing Architecture

Location:

```text
tests/
```

Required tests:

```text
test_download.py

test_validation.py

test_aggregation.py

test_rules.py

test_site_generation.py
```

Coverage focus:

* rule evaluation
* aggregation logic
* YAML validation
* JSON schema validation

---

# Extensibility Principles

Future contributors shall be able to:

* add indicators
* add regions
* add languages
* add briefing products

without modifying core architecture.

Changes should primarily occur in:

```text
config/
```

rather than:

```text
scripts/
```

---

# Architectural Constraints

Mandatory:

* static website
* GitHub Pages deployment
* GitHub Actions automation
* YAML-based configuration
* multilingual support
* open-source operation

Forbidden:

* backend services
* databases
* runtime APIs
* frontend drought calculations
* hardcoded drought thresholds

---

# Success Criteria

The architecture is considered successful when:

* outputs match the current Drought-Briefing implementation
* daily updates run automatically
* deployment is automatic
* non-programmers can maintain content
* scientific logic remains transparent
* operational costs remain effectively zero
* the entire platform can be hosted from a single GitHub repository

```
```
