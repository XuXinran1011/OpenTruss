# OpenTruss v1.0.0 Release Notes

**Release Date**: January 1, 2025

## Overview

OpenTruss v1.0.0 is the first stable release of the Generative BIM Middleware platform. This release provides a complete solution for CAD-to-BIM reverse engineering through a graph-first architecture with human-in-the-loop workflows.

## Key Features

### Core Architecture
- **Graph-First Design**: Memgraph LPG database with RDF semantic layer
- **GB50300 Compliance**: Strict adherence to Chinese national standard for construction quality acceptance
- **Dual-Mode Architecture**: High-performance runtime (LPG) + semantic standardization (RDF)

### HITL Workbench
- **Trace Mode**: Topology repair and 2D geometry correction
- **Lift Mode**: Batch Z-axis parameter setting for 3D conversion
- **Classify Mode**: Element classification and hierarchy assignment
- **Canvas Visualization**: D3.js-powered 2D topology rendering

### Inspection Lot Management
- **Rule Engine**: Automated lot assignment with configurable rules
- **Flexible Strategy**: Support for level-based, zone-based, and custom lot creation
- **Batch Operations**: Efficient handling of large-scale projects

### Approval Workflow
- **State Machine**: Complete workflow from Draft → Submitted → Approved/Rejected
- **Role-Based Access**: Editor, Approver, and PM roles
- **Batch Approval**: Support for bulk approval operations
- **History Tracking**: Complete audit trail of approval decisions

### IFC Export
- **Standards Compliant**: Full IFC 4.0 export support
- **Lot-Based Export**: Export inspection lots as separate IFC files
- **Geometry Conversion**: Accurate 2D-to-3D geometry transformation

### MEP Routing & Coordination
- **Routing Planning**: 2D routing with obstacle avoidance
- **Coordination**: 3D space arrangement with collision detection
- **Priority System**: Configurable 5-level priority for MEP systems
- **Constraint Validation**: Angle, bend radius, and slope validation

### Validation & Quality
- **Semantic Validation**: Brick Schema-based semantic checks
- **Constructability Validation**: Angle and Z-axis validation
- **Topology Validation**: Graph completeness and connectivity checks
- **Spatial Validation**: 2.5D bounding box collision detection

### Hanger Placement
- **Automated Generation**: Intelligent hanger placement for MEP elements
- **Rule-Based Adjustment**: Joint detection and mandatory hanger placement
- **Integrated Hangers**: Support for shared hangers across multiple elements
- **Spatial Grouping**: Smart grouping based on proximity and alignment

## System Requirements

### Backend
- Python 3.10+
- Memgraph 2.10+
- Docker 20.10+ (recommended for Memgraph)

### Frontend
- Node.js 18.0+
- Modern browser with ES6+ support

### Production Deployment
- Docker and Docker Compose
- Minimum 4GB RAM
- Minimum 20GB disk space

## Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/XuXinran1011/OpenTruss.git
cd OpenTruss

# Using Makefile (recommended)
make setup
make dev

# Or using Docker Compose
docker-compose up -d
```

### Detailed Installation

See [Development Guide](docs/development/DEVELOPMENT.md) for detailed installation instructions.

## Documentation

- [Product Requirements Document](docs/references/PRD.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [API Documentation](docs/api/index.md)
- [User Manual](docs/guides/USER_MANUAL.md)
- [Deployment Guide](docs/deployment/DEPLOYMENT.md)

## Breaking Changes

This is the initial release, so there are no breaking changes from previous versions.

## Security

- JWT-based authentication
- Role-based access control (RBAC)
- Secure password hashing with bcrypt
- CORS configuration for production environments

**Important**: Before deploying to production, ensure you:
- Generate strong JWT secrets (use `openssl rand -hex 32`)
- Configure appropriate CORS origins (NOT `*`)
- Use HTTPS in production
- Review security best practices in [Deployment Guide](docs/deployment/DEPLOYMENT.md) and [Security Checklist](SECURITY_CHECKLIST.md)

## Performance

- API response times: < 200ms (p95)
- Graph query performance: < 100ms for typical queries
- Frontend render performance: 60 FPS for canvas interactions
- Supports projects with 10,000+ elements

## Known Limitations

- IFC export requires ifcopenshell (may have platform-specific limitations)
- Large projects (>50,000 elements) may require performance tuning
- MEP routing currently supports 2D routing only (3D routing in roadmap)

## Upgrading

This is the initial release. Future upgrade guides will be provided for subsequent versions.

## Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: Report issues on [GitHub Issues](https://github.com/XuXinran1011/OpenTruss/issues)
- **Contributions**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## Credits

OpenTruss is developed with:
- FastAPI for backend framework
- Memgraph for graph database
- Next.js for frontend framework
- D3.js for data visualization
- ifcopenshell for IFC processing

See [LICENSE](LICENSE) for license information.

---

**Full Changelog**: See [CHANGELOG.md](CHANGELOG.md)
