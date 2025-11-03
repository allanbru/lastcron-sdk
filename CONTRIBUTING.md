# Contributing to LastCron

Thank you for your interest in contributing to LastCron! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your changes
5. Make your changes
6. Test your changes
7. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

### Installation

1. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/lastcron-sdk.git
cd lastcron-sdk
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode with dev dependencies:
```bash
pip install -e ".[dev]"
```

This will install:
- The lastcron package in editable mode
- All development dependencies (pytest, black, mypy, ruff, etc.)

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes**: Fix issues in the codebase
- **New features**: Add new functionality to the SDK
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Examples**: Create example flows and use cases
- **Performance improvements**: Optimize existing code

### Workflow

1. **Check existing issues**: Before starting work, check if there's an existing issue for what you want to do
2. **Create an issue**: If no issue exists, create one describing your proposed changes
3. **Discuss**: Wait for feedback from maintainers before starting significant work
4. **Branch**: Create a feature branch from `main`
5. **Develop**: Make your changes following our coding standards
6. **Test**: Ensure all tests pass and add new tests for your changes
7. **Commit**: Write clear, descriptive commit messages
8. **Push**: Push your changes to your fork
9. **Pull Request**: Open a PR with a clear description of your changes

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: Maximum 100 characters
- **Formatting**: Use `black` for code formatting
- **Linting**: Use `ruff` for linting
- **Type hints**: Use type hints where appropriate
- **Docstrings**: Use Google-style docstrings for all public functions and classes

### Code Formatting

Before committing, format your code:

```bash
# Format code with black
black lastcron/

# Check with ruff
ruff check lastcron/

# Type check with mypy
mypy lastcron/
```

### Docstring Example

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description of the function.

    Longer description if needed, explaining what the function does,
    any important details, and usage examples.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
        TypeError: When param1 is not a string

    Example:
        >>> my_function("test", 42)
        True
    """
    pass
```

## Testing

### Running Tests

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=lastcron --cov-report=html

# Run specific test file
pytest tests/test_flow.py

# Run specific test
pytest tests/test_flow.py::test_flow_decorator
```

### Writing Tests

- Write tests for all new features and bug fixes
- Aim for high test coverage (>80%)
- Use descriptive test names that explain what is being tested
- Use pytest fixtures for common setup
- Test both success and failure cases
- Test edge cases and error handling

### Test Example

```python
import pytest
from lastcron import flow

def test_flow_decorator_basic():
    """Test that the flow decorator works with a basic function."""
    @flow
    def my_flow(**params):
        return "success"
    
    assert callable(my_flow)
    assert hasattr(my_flow, 'submit')

def test_flow_decorator_with_invalid_params():
    """Test that flow decorator handles invalid parameters correctly."""
    with pytest.raises(TypeError):
        @flow
        def my_flow(invalid_param):
            pass
```

## Pull Request Process

### Before Submitting

1. **Update documentation**: Update README.md and docstrings as needed
2. **Add tests**: Ensure your changes are tested
3. **Run tests**: All tests must pass
4. **Format code**: Run black and ruff
5. **Update changelog**: Add a note about your changes (if applicable)

### PR Description

Your pull request should include:

- **Title**: Clear, concise description of the change
- **Description**: Detailed explanation of what changed and why
- **Related Issues**: Link to related issues (e.g., "Fixes #123")
- **Testing**: Describe how you tested your changes
- **Breaking Changes**: Note any breaking changes

### PR Template

```markdown
## Description
Brief description of the changes

## Related Issues
Fixes #(issue number)

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe the tests you ran and how to reproduce them

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

## Reporting Bugs

### Before Reporting

- Check if the bug has already been reported
- Verify the bug exists in the latest version
- Collect information about your environment

### Bug Report Template

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. ...
2. ...

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.0]
- LastCron version: [e.g., 0.1.0]

**Additional context**
Any other context about the problem.
```

## Suggesting Enhancements

We welcome suggestions for new features and improvements!

### Enhancement Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots about the feature request.
```

## Questions?

If you have questions about contributing, feel free to:

- Open an issue with the "question" label
- Reach out to the maintainers

## License

By contributing to LastCron, you agree that your contributions will be licensed under the Elastic License 2.0.

Thank you for contributing to LastCron! 🎉

