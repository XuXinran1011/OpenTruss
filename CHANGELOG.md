# Changelog

All notable changes to OpenTruss will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Additional performance optimizations
- Enhanced monitoring capabilities
- Extended API documentation

## [1.0.0] - 2025-01-01

### Added
- Initial release of OpenTruss - Generative BIM Middleware platform
- Graph-First architecture with Memgraph LPG database and RDF semantic layer
- GB50300-compliant hierarchy structure (Project → Building → Division → SubDivision → Item → InspectionLot → Element)
- HITL (Human-in-the-Loop) Workbench with three modes:
  - Trace Mode: Topology repair and 2D geometry correction
  - Lift Mode: Batch Z-axis parameter setting for 3D conversion
  - Classify Mode: Element classification and hierarchy assignment
- Canvas visualization with D3.js for 2D topology rendering
- Inspection lot management with rule engine (level-based, zone-based, and custom strategies)
- Approval workflow with state machine (Draft → Submitted → Approved/Rejected)
- Role-based access control (Editor, Approver, PM roles)
- IFC 4.0 export functionality with lot-based export
- RESTful API with FastAPI
- Next.js frontend with TypeScript
- Authentication and authorization (JWT)
- MEP routing planning with obstacle avoidance
- MEP coordination with collision detection and 5-level priority system
- Hanger placement service with automated generation, rule-based adjustment, and integrated hangers
- Comprehensive validation system:
  - Semantic validation (Brick Schema-based)
  - Constructability validation (angle and Z-axis)
  - Topology validation (graph completeness)
  - Spatial validation (2.5D collision detection)
- Comprehensive testing infrastructure (unit, integration, E2E, performance)
- GitHub Actions CI/CD workflows
- Prometheus metrics and Grafana monitoring
- Example data for quick start and testing
- Architecture diagrams and ADR (Architecture Decision Records)
- Contributing guidelines and issue templates
- Unified setup scripts (Makefile, setup.sh, setup.ps1)

### Changed
- Improved README.md with table of contents and better documentation links
- Optimized requirements.txt structure with comments
- Enhanced API models with advanced validation
- Migrated from 2D geometry model to 3D native geometry model
- Reorganized documentation structure for better navigation

### Fixed
- Fixed commit message encoding issues (using UTF-8 encoding for Git)
- Fixed CoordinationService config access (using _config property)
- Improved error handling with custom exceptions (NotFoundError, ValidationError, LockedError, ConflictError)

### Technical Stack
- Backend: FastAPI, Memgraph, Pydantic, ifcopenshell
- Frontend: Next.js, React, TypeScript, D3.js, Canvas API
- Database: Memgraph (LPG graph database)
- Authentication: JWT with role-based access control

---

## Version History

- **1.0.0** (2025-01-01): Initial release - Complete OpenTruss platform with HITL Workbench, rule engine, approval workflow, and IFC export
- **Unreleased**: Development version with ongoing improvements

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

