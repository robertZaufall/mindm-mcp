# mindm-mcp Project Guidelines

## Build & Development Commands
```bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/                 # Run all tests
pytest tests/test_client.py   # Run specific test file
pytest tests/test_client.py::test_create_session  # Run specific test

# Format code
black mindm_mcp/ tests/

# Lint code
flake8 mindm_mcp/ tests/

# Build package
make build                    # Clean, update version, build package

# Generate code documentation
make llms                     # Generate consolidated documentation
```

## Code Style Guidelines
- **Imports**: Standard library → third-party → local modules, alphabetized within groups
- **Typing**: Use type hints for all function parameters and return values
- **Documentation**: Docstrings for all public modules, classes, methods (Google style)
- **Naming**: `snake_case` for variables/functions, `PascalCase` for classes
- **Error Handling**: Raise explicit exceptions with descriptive messages
- **Async**: Use async/await pattern consistently, provide sync wrappers where needed
- **Formatting**: Black with default settings (line length 88, double quotes)