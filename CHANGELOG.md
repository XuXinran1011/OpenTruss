# Changelog

All notable changes to OpenTruss will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive testing infrastructure (unit, integration, E2E, performance)
- GitHub Actions CI/CD workflows
- Prometheus metrics and Grafana monitoring
- Enhanced data validation with Pydantic validators and IFC constraints
- Example data for quick start and testing
- Architecture diagrams and ADR (Architecture Decision Records)
- Contributing guidelines and issue templates
- Unified setup scripts (Makefile, setup.sh, setup.ps1)

### Changed
- Improved README.md with table of contents and better documentation links
- Optimized requirements.txt structure with comments
- Enhanced API models with advanced validation

### Fixed
- Fixed commit message encoding issues (using English for all commits)

## [1.0.0] - 2025-01-01

### Added
- Initial release of OpenTruss
- Graph-First architecture with Memgraph LPG database
- HITL (Human-in-the-Loop) Workbench with three modes:
  - Trace Mode: Topology repair
  - Lift Mode: Batch Z-axis parameter setting
  - Classify Mode: Element classification
- GB50300-compliant hierarchy structure
- Inspection lot management with rule engine
- Approval workflow with state machine
- IFC export functionality
- RESTful API with FastAPI
- Next.js frontend with Canvas visualization
- Authentication and authorization (JWT)

### Technical Stack
- Backend: FastAPI, Memgraph, Pydantic, ifcopenshell
- Frontend: Next.js, React, TypeScript, D3.js, Canvas API
- Database: Memgraph (LPG graph database)
- Authentication: JWT with role-based access control

---

## Version History

- **1.0.0**: Initial release
- **Unreleased**: Development version with ongoing improvements

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

