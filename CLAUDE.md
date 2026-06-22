# CLAUDE.md

## Project Context

This repository contains a refactoring of the existing Drought-Briefing application.

The goal is NOT to redesign the drought methodology.

The goal is to preserve the existing scientific and operational logic while improving maintainability, transparency and automation.

Whenever uncertainty exists, preserve existing functionality and outputs.

---

# Primary Design Principle

Preserve business logic.

Refactor architecture.

Do not change drought methodology unless explicitly instructed.

---

# Project Goals

The application shall:

* run fully on GitHub
* use GitHub Actions for automation
* use GitHub Pages for publication
* require no backend server
* require no database
* support open-source collaboration
* allow domain experts to modify rules without programming

---

# Architecture Principles

## Data First

Data processing and presentation must be separated.

Never calculate drought assessments inside the frontend.

Frontend consumes generated JSON only.

Correct:

Raw Data
→ Aggregation
→ Rule Evaluation
→ JSON
→ Static Website

Incorrect:

Raw Data
→ Frontend
→ Rule Evaluation in Browser

---

## Configuration First

All configurable behaviour must be stored in YAML.

Examples:

* thresholds
* drought categories
* messages
* translations
* region definitions
* briefing rules

Do not hardcode domain knowledge in Python or JavaScript.

---

## Static Site First

The final website must be fully static.

Allowed:

* HTML
* CSS
* Vanilla JavaScript
* JSON

Not allowed:

* Flask
* Django
* FastAPI
* Node.js backend
* Databases

---

## Simplicity First

Prefer simple solutions over complex frameworks.

Avoid unnecessary dependencies.

Avoid introducing build systems unless clearly justified.

---

# Technology Stack

## Backend Processing

Python

Preferred libraries:

* requests
* pandas
* geopandas
* shapely
* pyyaml

Avoid introducing large frameworks.

---

## Frontend

Use:

* HTML
* CSS
* Vanilla JavaScript

Do not introduce:

* React
* Angular
* Vue
* Svelte

unless explicitly requested.

---

# User Types

## Administrators

swisstopo and BAFU maintainers.

Expected skills:

* GitHub
* YAML

Do not assume programming knowledge.

---

## Domain Experts

Expected skills:

* editing YAML files
* creating pull requests

Do not require Python knowledge.

---

## Community Contributors

Public contributors may submit pull requests.

Code should therefore be understandable and documented.

---

# Configuration Structure

Target structure:

```text
config/

  sources.yaml

  rules.yaml

  messages.yaml

  translations.yaml

  regions.yaml
```

All configurable content should eventually reside here.

---

# Data Structure

Target structure:

```text
data/

  processed/

    national.json

    cantons/

    warning_regions/
```

Frontend shall only read processed outputs.

Never expose intermediate processing files.

---

# GitHub Actions

The system shall run automatically.

Typical workflow:

1. Download source datasets
2. Validate datasets
3. Aggregate indicators
4. Apply drought rules
5. Generate JSON outputs
6. Generate static website
7. Publish to GitHub Pages

Workflows must be idempotent.

Running the workflow twice with identical inputs should produce identical outputs.

---

# Multilingual Support

Supported languages:

* German
* French
* Italian

Language content must be stored in configuration files.

Avoid language-specific strings in source code.

---

# Swiss Confederation Design System

The frontend shall follow the Swiss Confederation Design System.

Objectives:

* accessibility
* responsive layout
* official visual appearance
* consistent navigation

Prefer using existing design system components.

Do not create a custom visual identity unless required.

---

# Documentation Requirements

Every major module shall contain:

* purpose
* inputs
* outputs

Every workflow shall contain:

* execution description
* dependencies
* expected outputs

Every configuration file shall contain examples and comments.

---

# Refactoring Rules

When refactoring:

1. Preserve outputs.
2. Preserve methodology.
3. Extract configuration.
4. Remove duplication.
5. Improve readability.
6. Improve testability.
7. Avoid behavioural changes.

If behaviour changes are necessary:

* document them
* justify them
* isolate them in a separate commit

---

# Testing Requirements

Create tests for:

* aggregation logic
* threshold evaluation
* YAML validation
* multilingual content loading

Tests should verify equivalence with existing outputs whenever possible.

---

# Definition of Success

The project is successful when:

* drought results match the current application
* daily execution is fully automated
* deployment is fully automated
* website is fully static
* no server infrastructure is required
* no database is required
* rules are editable via YAML
* texts are editable via YAML
* multilingual support is preserved
* GitHub Pages deployment works
* non-programmers can maintain operational content

---

# Decision Framework

When multiple implementations are possible:

Prefer, in order:

1. Simpler solution
2. More maintainable solution
3. More transparent solution
4. More configurable solution
5. More performant solution

Performance optimisation should never significantly reduce maintainability.
