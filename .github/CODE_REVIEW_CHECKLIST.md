# Code Review Checklist - Modular ERP System

## Pre-Review Requirements
- [ ] All tests pass (60/60 minimum)
- [ ] Test coverage >= 70% (module-specific >= 80%)
- [ ] Pre-commit hooks pass locally
- [ ] Migration files created for model changes
- [ ] Documentation updated for API changes

## Code Quality

### Architecture & Design
- [ ] Follows modular architecture pattern
- [ ] New modules use `BaseModel` for audit tracking
- [ ] Dynamic module activation via `trigger_config.yaml`
- [ ] Proper separation of concerns (models, views, serializers)
- [ ] No circular imports between modules

### Code Style
- [ ] PEP 8 compliant (black formatted)
- [ ] Type hints on all function signatures
- [ ] Comprehensive docstrings (Google style)
- [ ] Meaningful variable/function names
- [ ] No hardcoded values (use settings)

### Testing
- [ ] Unit tests for new models
- [ ] Serializer validation tests
- [ ] ViewSet CRUD operation tests
- [ ] Edge cases covered
- [ ] Fixtures properly defined

## Security
- [ ] No sensitive data in logs
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (use ORM)
- [ ] XSS protection (DRF serializers)
- [ ] Authentication/authorization checks
- [ ] Bandit security scan passes

## Performance
- [ ] Database queries optimized (select_related/prefetch_related)
- [ ] No N+1 query problems
- [ ] Pagination on list endpoints
- [ ] Indexes on frequently queried fields
- [ ] Caching strategy documented

## Module-Specific Checks

### Inventory Module
- [ ] Stock movements are atomic
- [ ] Negative stock prevention
- [ ] Warehouse capacity checks
- [ ] Audit trail completeness

### HR Module (when implemented)
- [ ] Employee data privacy
- [ ] Payroll calculation accuracy
- [ ] Leave balance validation

### Finance Module (when implemented)
- [ ] Decimal precision (use Decimal, not float)
- [ ] Currency handling
- [ ] Transaction integrity
- [ ] Audit compliance

## Documentation
- [ ] API endpoints documented
- [ ] Model relationships explained
- [ ] Business logic comments
- [ ] Changelog updated
- [ ] README sections updated if needed

## Deployment Readiness
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Docker build succeeds
- [ ] CI/CD pipeline passes
- [ ] Rollback plan documented

## Sign-off
Reviewer: _______________  
Date: _______________  
Approval: [ ] Approved  [ ] Changes Requested  [ ] Comment Only
