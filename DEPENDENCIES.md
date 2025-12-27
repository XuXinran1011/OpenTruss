# OpenTruss Dependencies

This document lists the major dependencies used in OpenTruss and their purposes.

## Backend Dependencies

### Core Framework
- **FastAPI** (≥0.104.0): Modern, fast web framework for building APIs
- **Uvicorn** (≥0.24.0): ASGI server for FastAPI
- **Pydantic** (≥2.0.0): Data validation using Python type annotations
- **Pydantic Settings** (≥2.0.0): Settings management for Pydantic

### Database
- **neo4j** (≥5.0.0): Python driver for Neo4j/Memgraph (uses Bolt protocol)

### Authentication & Security
- **PyJWT** (≥2.8.0): JSON Web Token implementation
- **python-jose** (≥3.3.0): JWT and JWS implementation with cryptography support
- **bcrypt** (≥4.0.0): Password hashing library

### Data Processing
- **ifcopenshell** (≥0.7.0): IFC file processing library
- **brickschema** (≥0.7.0): Brick Schema ontology processing
- **rdflib** (≥6.0.0): RDF processing library

### Utilities
- **requests** (≥2.31.0): HTTP library for API calls
- **python-dotenv** (≥1.0.0): Environment variable management
- **networkx** (≥3.0): Graph algorithms (optional, for routing)

### Monitoring
- **prometheus-client** (≥0.19.0): Prometheus metrics exporter

## Frontend Dependencies

### Core Framework
- **Next.js** (^14.0.0): React framework with SSR support
- **React** (^18.0.0): UI library
- **React DOM** (^18.0.0): React DOM renderer

### State Management & Data Fetching
- **Zustand** (^4.5.0): Lightweight state management
- **@tanstack/react-query** (^5.17.0): Data fetching and caching

### Visualization
- **d3** (^7.9.0): Data visualization library
- **@types/d3** (^7.4.3): TypeScript types for D3

### Utilities
- **clsx** (^2.1.0): Conditional class names
- **tailwind-merge** (^2.2.0): Merge Tailwind CSS classes
- **rbush** (^3.0.1): High-performance 2D spatial indexing

### Development & Testing
- **@playwright/test** (^1.40.0): E2E testing framework
- **@testing-library/react** (^14.1.2): React testing utilities
- **@testing-library/jest-dom** (^6.1.5): Custom Jest matchers
- **Jest** (^29.7.0): JavaScript testing framework
- **ESLint** (^8.57.1): Code linting
- **TypeScript** (^5.x): Type safety

## License Compatibility

All dependencies used in OpenTruss are compatible with the MIT license:

- **MIT License**: FastAPI, Uvicorn, Pydantic, React, Next.js, Zustand, and most dependencies
- **Apache 2.0**: Some dependencies (compatible with MIT)
- **BSD License**: Various utilities (compatible with MIT)

### License Audit

To audit licenses:
```bash
# Python dependencies
pip-licenses --with-urls --format=json > licenses.json

# npm dependencies
npm license-checker --json > npm-licenses.json
```

## Version Requirements

### Minimum Versions
- Python: 3.10+
- Node.js: 18.0+
- Memgraph: 2.10+
- Docker: 20.10+ (optional)

### Version Pinning Strategy

**Development**:
- Use version ranges (e.g., `>=0.104.0`) for flexibility
- Regularly update to latest compatible versions

**Production**:
- Consider pinning exact versions for reproducibility
- Create `requirements-lock.txt` for production deployments
- Use `package-lock.json` (already committed for npm)

## Security

- All dependencies are regularly audited for security vulnerabilities
- Use `pip-audit` and `npm audit` to check for known vulnerabilities
- Update dependencies promptly when security patches are released

## Updating Dependencies

### Python
```bash
cd backend
pip install --upgrade -r requirements.txt
pip freeze > requirements-lock.txt  # Optional: for production
```

### Node.js
```bash
cd frontend
npm update
npm audit fix  # Fix security vulnerabilities
```

## Dependency Size

Approximate sizes:
- Backend (Python dependencies): ~200MB (with ifcopenshell)
- Frontend (node_modules): ~500MB (development), ~50MB (production build)

## Optional Dependencies

Some dependencies are optional and can be excluded if not needed:
- `networkx`: Only needed for advanced routing algorithms
- `brickschema`: Can be excluded if not using Brick Schema validation

