# Contributing to Bitaxe Gamma Monitor

Thank you for your interest in contributing to the Bitaxe Gamma Monitor! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Basic understanding of Bitcoin mining and Bitaxe devices (helpful but not required)

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/simple-monitor.git
   cd simple-monitor
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the setup script:**
   ```bash
   python setup.py
   ```

5. **Verify the installation:**
   ```bash
   pytest  # Run tests
   pylint src/  # Check code quality
   ```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only

# Run tests for specific modules
pytest tests/test_collector.py
pytest tests/test_cli_view.py
```

### Writing Tests
- All new functionality must include corresponding unit tests
- Maintain minimum 80% code coverage
- Use descriptive test names that explain what is being tested
- Follow the existing test structure and patterns
- Mock external dependencies (API calls, file operations)

### Test Categories
- **Unit tests:** Test individual functions and methods in isolation
- **Integration tests:** Test component interactions and workflows
- **Edge cases:** Test error handling and boundary conditions

## 📝 Code Style

### Python Style Guidelines
- Follow [PEP 8](https://pep8.org/) style guidelines
- Use meaningful variable and function names
- Write comprehensive docstrings for all public functions
- Keep functions focused and single-purpose
- Use type hints where appropriate

### Code Quality Tools
- **Pylint:** Code analysis and style checking
- **Coverage:** Test coverage measurement
- **CodeQL:** Security vulnerability analysis

### Pre-commit Checklist
Before submitting your changes:
```bash
# Run tests
pytest

# Check code quality
pylint src/

# Verify coverage
pytest --cov=src --cov-fail-under=80

# Check for security issues (if CodeQL CLI available)
codeql database analyze
```

## 🔧 Development Workflow

### Branch Naming
Use descriptive branch names that indicate the type of change:
- `feature/add-web-interface`
- `bugfix/fix-connection-timeout`
- `enhancement/improve-dashboard-layout`
- `docs/update-contributing-guide`

### Commit Messages
Use conventional commit format:
```
type(scope): description

Examples:
feat(collector): add support for new Bitaxe API endpoints
fix(viewer): resolve Unicode display issues on Windows
docs(readme): update installation instructions
test(collector): add unit tests for hostname caching
```

### Pull Request Process

1. **Create a feature branch** from the latest `main`
2. **Implement your changes** following the guidelines
3. **Add or update tests** for your changes
4. **Update documentation** if necessary
5. **Ensure all tests pass** and code quality checks succeed
6. **Submit a pull request** with a clear description

### Pull Request Template
Your PR description should include:
- **Summary:** What does this PR accomplish?
- **Motivation:** Why is this change needed?
- **Testing:** How was this tested?
- **Breaking Changes:** Are there any breaking changes?
- **Screenshots:** For UI changes (if applicable)

## 🎯 Types of Contributions

### Code Contributions
- Bug fixes
- New features
- Performance improvements
- Code refactoring
- Security enhancements

### Documentation
- README improvements
- Code documentation
- API documentation
- Usage examples
- Troubleshooting guides

### Testing
- Additional test cases
- Integration tests
- Performance tests
- Edge case testing

### Infrastructure
- CI/CD improvements
- Docker enhancements
- Dependency updates
- Security updates

## 🐛 Bug Reports

When reporting bugs, please include:
- **Environment details:** OS, Python version, installation method
- **Steps to reproduce:** Clear, step-by-step instructions
- **Expected behavior:** What should happen
- **Actual behavior:** What actually happens
- **Error messages:** Full error messages and stack traces
- **Configuration:** Relevant configuration details (sanitized)

## 💡 Feature Requests

For feature requests, please provide:
- **Use case:** Why is this feature needed?
- **Proposed solution:** How should it work?
- **Alternatives considered:** Other approaches you've considered
- **Additional context:** Any other relevant information

## 🔒 Security

If you discover a security vulnerability:
1. **Do not** open a public issue
2. **Email** the maintainers directly
3. **Provide** detailed information about the vulnerability
4. **Allow** reasonable time for the issue to be addressed

## 📚 Resources

### Documentation
- [README.md](README.md) - Main project documentation
- [Bitaxe Documentation](https://github.com/skot/bitaxe) - Hardware documentation
- [Rich Library](https://rich.readthedocs.io/) - Terminal interface library

### Community
- [GitHub Issues](https://github.com/mtab3000/simple-monitor/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/mtab3000/simple-monitor/discussions) - Community discussions

### Development Tools
- [pytest](https://docs.pytest.org/) - Testing framework
- [pylint](https://pylint.pycqa.org/) - Code analysis
- [Docker](https://docs.docker.com/) - Containerization

## 🏆 Recognition

Contributors will be recognized in:
- The project README
- Release notes for significant contributions
- GitHub contributor statistics

## 📜 Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct. By participating, you are expected to uphold this code.

## ❓ Questions

If you have questions about contributing:
1. Check the [README.md](README.md) for basic information
2. Search existing [issues](https://github.com/mtab3000/simple-monitor/issues)
3. Open a new issue with the "question" label
4. Join the community discussions

---

Thank you for contributing to the Bitaxe Gamma Monitor! Your contributions help make Bitcoin mining more accessible and transparent for everyone. ⚡