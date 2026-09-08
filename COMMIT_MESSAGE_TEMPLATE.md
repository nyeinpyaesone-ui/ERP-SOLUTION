# Professional Commit Guidelines for Modular ERP System

## Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types
- **feat**: New feature (triggers module activation in trigger_config.yaml)
- **fix**: Bug fix (compatible with existing modules)
- **docs**: Documentation only
- **style**: Formatting, missing semi-colons, etc. (no code change)
- **refactor**: Refactoring production code
- **test**: Adding tests, refactoring tests (no production code change)
- **chore**: Updating build tasks, package manager configs, etc.

## Scopes
- **core**: Module loader, base model, signals
- **inventory**: Inventory module
- **hr**: HR module
- **finance**: Finance module
- **sales**: Sales module
- **procurement**: Procurement module
- **manufacturing**: Manufacturing module
- **config**: Settings, URLs, WSGI/ASGI
- **deps**: Dependencies (requirements.txt)
- **ci**: CI/CD workflows
- **tests**: Test infrastructure

## Examples

### Feature with Trigger Configuration
```
feat(hr): add employee model with audit tracking

- Created Employee model extending BaseModel
- Added fields: employee_id, department, position, hire_date
- Integrated with module_loader for dynamic activation
- Updated trigger_config.yaml with hr module triggers

Closes #123
```

### Fix with Compatibility
```
fix(core): resolve module_loader singleton race condition

- Fixed thread-safe initialization in ModuleRegistry
- Added locking mechanism for concurrent access
- Maintained backward compatibility with existing modules

Fixes #456
```

### Chore with Build Script
```
chore(deps): update requirements with PyYAML compatibility

- Pinned PyYAML==6.0.1 to prevent wheel build errors
- Updated build-setup-test.sh with skip logic for pre-installed packages
- Added graceful error handling for dependency failures

Refs #789
```

## Pre-Commit Checklist
- [ ] Tests pass (60/60 minimum)
- [ ] Coverage >= 70%
- [ ] Pre-commit hooks pass (black, isort, flake8, mypy, bandit)
- [ ] trigger_config.yaml validated if modified
- [ ] Migration files created if models changed
- [ ] Documentation updated if API changed

## Branch Naming
- feature/<module>-<description>
- fix/<module>-<description>
- refactor/<module>-<description>
- chore/<description>

## Merge Requirements
- All tests passing
- Coverage requirement met
- At least 1 approval for production code
- Squash commits before merging to main
