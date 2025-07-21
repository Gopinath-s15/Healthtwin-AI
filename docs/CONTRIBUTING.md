# Contributing to HealthTwin AI

Thank you for your interest in contributing to HealthTwin AI! This document provides guidelines and information for contributors.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)
8. [Issue Reporting](#issue-reporting)

## Code of Conduct

### Our Pledge

We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- Git
- Basic understanding of FastAPI and React
- Familiarity with healthcare data privacy (HIPAA knowledge preferred)

### Development Setup

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR-USERNAME/Healthtwin-AI.git
   cd Healthtwin-AI
   
   # Add upstream remote for syncing
   git remote add upstream https://github.com/yourusername/Healthtwin-AI.git
   ```

2. **Set up development environment**
   ```bash
   # Backend setup
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   
   # Frontend setup
   cd frontend
   npm install
   cd ..
   ```

3. **Configure pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Run tests to ensure everything works**
   ```bash
   python test_enhanced_api.py
   cd frontend && npm test
   ```

## Development Workflow

### Branch Strategy

We use a simplified Git flow:

- **`main`**: Production-ready code
- **`develop`**: Integration branch for features
- **`feature/feature-name`**: Feature development
- **`bugfix/bug-description`**: Bug fixes
- **`hotfix/critical-fix`**: Critical production fixes

### Workflow Steps

1. **Create a feature branch**
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run backend tests
   python test_enhanced_api.py
   
   # Run frontend tests
   cd frontend && npm test
   
   # Run linting
   flake8 app/
   cd frontend && npm run lint
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new authentication feature"
   ```

5. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

### Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semi-colons, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

**Examples:**
```
feat(auth): add JWT token refresh functionality
fix(api): resolve patient timeline sorting issue
docs(readme): update installation instructions
test(auth): add unit tests for password validation
```

## Coding Standards

### Python (Backend)

**Style Guide:**
- Follow PEP 8
- Use type hints for function parameters and return values
- Maximum line length: 88 characters (Black formatter)
- Use meaningful variable and function names

**Code Quality Tools:**
```bash
# Install development dependencies
pip install black flake8 mypy pytest

# Format code
black app/

# Check style
flake8 app/

# Type checking
mypy app/

# Run tests
pytest
```

## Testing Guidelines

### Backend Testing

**Test Categories:**
- Unit tests for individual functions
- Integration tests for API endpoints
- Database tests for data operations
- Authentication and authorization tests

### Frontend Testing

**Test Categories:**
- Component rendering tests
- User interaction tests
- API integration tests
- Accessibility tests

### Test Coverage

Maintain minimum test coverage:
- Backend: 80%
- Frontend: 70%
- Critical paths: 95%

## Documentation

### Code Documentation

**Python:**
- Use docstrings for all functions, classes, and modules
- Follow Google or NumPy docstring format
- Include type hints

**JavaScript:**
- Use JSDoc comments for complex functions
- Document component props with PropTypes or TypeScript

### API Documentation

- Update OpenAPI/Swagger documentation for new endpoints
- Include request/response examples
- Document error codes and responses

### User Documentation

- Update README.md for new features
- Add setup instructions for new dependencies
- Include troubleshooting guides

## Pull Request Process

### Before Submitting

1. **Ensure your code follows our standards**
2. **Add tests for new functionality**
3. **Update documentation**
4. **Run the full test suite**
5. **Rebase your branch on the latest develop**

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Process

1. **Automated checks must pass**
2. **At least one code review required**
3. **Security review for sensitive changes**
4. **Documentation review if applicable**

## Issue Reporting

### Bug Reports

Use the bug report template on [GitHub Issues](https://github.com/yourusername/Healthtwin-AI/issues).

### Feature Requests

Use the feature request template on [GitHub Issues](https://github.com/yourusername/Healthtwin-AI/issues).

### Security Issues

**Do not create public issues for security vulnerabilities.**

Instead, email security@healthtwin-ai.com with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- Annual contributor appreciation

## Questions?

- **General questions**: [GitHub Discussions](https://github.com/yourusername/Healthtwin-AI/discussions)
- **Bug reports**: [GitHub Issues](https://github.com/yourusername/Healthtwin-AI/issues)
- **Security issues**: security@healthtwin-ai.com
- **Direct contact**: maintainers@healthtwin-ai.com

Thank you for contributing to HealthTwin AI! 🏥❤️
