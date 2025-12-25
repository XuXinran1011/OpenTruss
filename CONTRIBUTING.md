# Contributing to OpenTruss

Thank you for your interest in contributing to OpenTruss! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- Python 3.10+ installed
- Node.js 18.0+ installed
- Docker 20.10+ (optional, for running Memgraph)
- Git 2.30+ installed

### Development Environment Setup

1. **Fork and Clone the Repository**

   ```bash
   git clone https://github.com/your-username/OpenTruss.git
   cd OpenTruss
   ```

2. **Set Up Backend Environment**

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Set Up Frontend Environment**

   ```bash
   cd frontend
   npm install
   ```

4. **Start Memgraph Database**

   ```bash
   # Using Docker Compose (recommended)
   docker-compose up -d memgraph
   
   # Or using Docker directly
   docker run -it -p 7687:7687 memgraph/memgraph:latest
   ```

5. **Configure Environment Variables**

   Create `backend/.env` file (see `docs/DEVELOPMENT.md` for details)

For detailed setup instructions, please refer to [Development Environment Guide](docs/DEVELOPMENT.md).

## Development Workflow

### Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical production fixes

### Creating a Branch

```bash
# Create a new branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b bugfix/issue-number-description
```

### Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(workbench): Add trace mode topology repair

fix(api): Resolve memory leak in element service

docs(readme): Update installation instructions
```

### Making Changes

1. **Write Code**: Follow the code style guidelines (see below)
2. **Write Tests**: Ensure your code has adequate test coverage
3. **Run Tests**: Verify all tests pass locally
4. **Update Documentation**: Update relevant documentation if needed

## Code Style Guidelines

### Python Code Style

- Follow **PEP 8** style guide
- Use type hints for function signatures
- Keep functions focused and small
- Write docstrings for public APIs

For detailed Python guidelines, see [Coding Standards - Python](docs/CODING_STANDARDS.md#2-python-代码规范).

### TypeScript/React Code Style

- Follow ESLint configuration (run `npm run lint` to check)
- Use TypeScript for type safety
- Follow React best practices
- Use functional components with hooks

For detailed frontend guidelines, see [Coding Standards - Frontend](docs/CODING_STANDARDS.md#3-前端代码规范).

### Code Formatting

**Python**:
```bash
# Recommended: Use black and isort (if configured)
black .
isort .
```

**TypeScript/JavaScript**:
```bash
# Format and lint
cd frontend
npm run lint
```

## Testing Requirements

### Running Tests

**Backend Tests**:
```bash
cd backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html  # With coverage
```

**Frontend Tests**:
```bash
cd frontend
npm test                    # Unit tests
npm run test:coverage       # With coverage
npm run test:e2e           # E2E tests with Playwright
```

### Test Coverage

- **Unit Tests**: Aim for ≥80% coverage
- **Integration Tests**: Cover critical workflows
- **E2E Tests**: Cover user-facing features

For detailed testing guidelines, see [Testing Strategy](docs/TESTING.md).

### Test Requirements Before PR

Before submitting a PR, ensure:

- [ ] All existing tests pass
- [ ] New tests are added for new features
- [ ] Test coverage is maintained or improved
- [ ] E2E tests pass (if applicable)

## Submitting Changes

### Pull Request Process

1. **Push Your Changes**

   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**

   - Go to the GitHub repository
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template

3. **PR Checklist**

   - [ ] Code follows style guidelines
   - [ ] Tests pass locally
   - [ ] Documentation is updated
   - [ ] Commit messages follow conventions
   - [ ] Branch is up to date with base branch

4. **Review Process**

   - Maintainers will review your PR
   - Address any requested changes
   - PRs require at least one approval before merging

### PR Template

When creating a PR, please include:

- **Description**: What changes are made and why
- **Related Issue**: Link to related issues (if any)
- **Testing**: How the changes were tested
- **Screenshots**: If UI changes are involved

## Reporting Issues

### Bug Reports

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.yml) when reporting bugs. Include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment information (OS, Python version, etc.)
- Error messages or logs

### Feature Requests

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.yml) for new features. Include:

- Use case and motivation
- Proposed solution
- Alternatives considered
- Additional context

### Security Issues

**Do NOT** open public issues for security vulnerabilities. Instead, please email security concerns to: support@opentruss.com

## Documentation

When contributing, please also:

- Update relevant documentation files
- Add comments for complex logic
- Update API documentation if endpoints change
- Keep CHANGELOG.md updated (for maintainers)

## Getting Help

If you need help:

- Check existing documentation in `docs/`
- Search existing issues and discussions
- Ask questions in GitHub Discussions (if enabled)
- Contact maintainers for clarification

## Recognition

Contributors will be recognized in:

- CONTRIBUTORS.md file (if maintained)
- Release notes for significant contributions
- Project documentation

---

Thank you for contributing to OpenTruss! 🎉

