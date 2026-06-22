# Product Requirements Document (PRD)

## Project

Drought Briefing Refactoring and Operationalisation

Version: 1.0

Status: Draft

Project Owners: swisstopo, BAFU

Repository: Refactoring of the existing Drought-Briefing application

---

# 1. Executive Summary

The existing Drought-Briefing application shall be refactored into a fully static, open-source web application that can be automatically operated via GitHub Actions and published through GitHub Pages.

The scientific methodology, data sources, aggregation logic, multilingual support and drought assessment rules shall remain functionally equivalent to the current implementation.

The primary objective is to separate:

* data processing
* business rules
* editorial content
* presentation layer

This separation shall allow non-programmers to maintain thresholds, texts, translations and briefing rules without modifying application code.

---

# 2. Background

The current Drought-Briefing application contains domain logic, configuration and presentation components that are tightly coupled.

This increases maintenance complexity and creates dependencies on software developers for routine content updates.

The new architecture shall:

* preserve existing functionality
* improve maintainability
* reduce operational complexity
* support community contributions
* eliminate server-side infrastructure

---

# 3. Objectives

## Primary Objectives

* Preserve all existing drought briefing functionality.
* Preserve all existing data sources.
* Preserve all existing aggregation methods.
* Preserve all existing multilingual capabilities.
* Enable fully automated daily updates.
* Publish as a static website via GitHub Pages.
* Move all configurable rules to YAML files.
* Allow domain experts to update rules without programming.
* Support open-source community contributions.

## Secondary Objectives

* Improve transparency of drought assessment logic.
* Improve maintainability.
* Simplify deployment and operations.
* Align visual design with the Swiss Confederation Design System.

---

# 4. Out of Scope

The following capabilities are explicitly excluded:

* AI-generated narratives
* Large language model integration
* User authentication
* Database infrastructure
* Server-side APIs
* Historical archives
* Real-time processing
* User-generated content

---

# 5. User Roles

## System Administrators

Organisation:

* swisstopo
* BAFU

Responsibilities:

* manage repository
* approve pull requests
* maintain workflows
* manage releases

Required skills:

* GitHub
* YAML

No Python knowledge required.

---

## Domain Editors

Responsibilities:

* modify drought rules
* update multilingual texts
* maintain configuration files

Required skills:

* YAML editing
* GitHub pull requests

No programming knowledge required.

---

## Community Contributors

Responsibilities:

* report issues
* propose improvements
* submit pull requests

---

# 6. Functional Requirements

## FR-01 Daily Data Acquisition

The system shall automatically download all existing data sources currently used by the Drought-Briefing application.

Acceptance Criteria:

* Daily execution via GitHub Actions.
* Automatic failure reporting.
* No manual intervention required.

---

## FR-02 Data Validation

The system shall validate downloaded datasets before processing.

Acceptance Criteria:

* Missing datasets detected.
* Invalid files detected.
* Workflow fails gracefully.

---

## FR-03 Spatial Aggregation

The system shall aggregate drought indicators using the same methodology as the current application.

Supported regions:

* Switzerland
* Cantons
* Existing warning regions

Acceptance Criteria:

* Numerical results match current implementation.

---

## FR-04 Rule-Based Assessment

The system shall evaluate drought conditions using configurable YAML rule definitions.

Acceptance Criteria:

* No hardcoded thresholds.
* Rule modifications require no code changes.

---

## FR-05 Multilingual Support

The system shall support:

* German
* French
* Italian

Acceptance Criteria:

* All texts configurable via YAML.
* Language switch available in UI.

---

## FR-06 Static Website Generation

The system shall generate a fully static website.

Acceptance Criteria:

* No backend required.
* No database required.
* Deployable via GitHub Pages.

---

## FR-07 Community Contribution Support

The system shall support GitHub-based collaboration.

Acceptance Criteria:

* Pull request workflow.
* Public issue tracking.
* Open-source documentation.

---

# 7. Non-Functional Requirements

## NFR-01 Simplicity

The architecture shall favour simplicity over technical sophistication.

Target:

* understandable by non-specialist maintainers

---

## NFR-02 Maintainability

Configuration shall be separated from code.

Target:

* all thresholds configurable
* all texts configurable

---

## NFR-03 Reproducibility

Given identical inputs, the system shall generate identical outputs.

---

## NFR-04 Cost

Operational cost shall be effectively zero.

Target platform:

* GitHub Actions
* GitHub Pages

---

## NFR-05 Accessibility

The generated website shall follow accessibility best practices and comply with the Swiss Confederation Design System guidelines.

---

# 8. Technical Architecture

## Data Processing Layer

Responsibilities:

* data download
* validation
* aggregation
* rule evaluation

Technology:

* Python

Output:

JSON

---

## Configuration Layer

Responsibilities:

* data source definitions
* thresholds
* assessment rules
* multilingual texts

Technology:

YAML

---

## Presentation Layer

Responsibilities:

* rendering
* navigation
* language selection

Technology:

* HTML
* CSS
* Vanilla JavaScript

---

## Deployment Layer

Technology:

* GitHub Actions
* GitHub Pages

---

# 9. Repository Structure

```text
drought-briefing/

config/
  sources.yaml
  rules.yaml
  messages.yaml
  regions.yaml

scripts/
  download.py
  validate.py
  aggregate.py
  evaluate.py
  generate_site.py

data/
  processed/

site/
  index.html
  region.html
  assets/

.github/
  workflows/

docs/
```

# 10. Configuration Principles

All configurable behaviour shall be stored in YAML.

Examples:

* thresholds
* classifications
* multilingual texts
* region definitions
* briefing templates

Python code shall not contain domain-specific drought thresholds.

---

# 11. User Stories

## US-01 Domain Expert

As a domain expert,

I want to change drought thresholds in YAML,

so that I can update drought classifications without programming.

---

## US-02 Domain Expert

As a domain expert,

I want to update multilingual texts,

so that briefing content can evolve independently of software releases.

---

## US-03 Administrator

As an administrator,

I want daily updates to run automatically,

so that no manual processing is required.

---

## US-04 Public User

As a public user,

I want to access drought briefings through a standard web browser,

so that no specialised software is required.

---

# 12. Definition of Done

The project is considered complete when:

* Existing functionality is preserved.
* Existing data sources are preserved.
* Existing aggregation logic is preserved.
* Existing multilingual functionality is preserved.
* GitHub Actions perform daily updates.
* GitHub Pages hosts the website.
* No server infrastructure is required.
* No database is required.
* Rules are fully YAML-based.
* Texts are fully YAML-based.
* The Swiss Confederation Design System is implemented.
* Non-programmers can maintain operational content.
* Public contributions via pull requests are supported.

---

# 13. Future Enhancements

Potential future enhancements:

* Additional environmental indicators
* Additional hazard types
* Interactive configuration editor
* Automated QA dashboards
* Extended regional products
* STAC-compatible exports

These enhancements are outside the scope of Version 1.0.
