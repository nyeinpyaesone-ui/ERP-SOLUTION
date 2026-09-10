# Release Checklist - Modular ERP System

## Pre-Release Phase (T-7 Days)

### Code Freeze Preparation
- [ ] All feature branches merged or reverted
- [ ] No critical bugs open (P0/P1)
- [ ] Test coverage >= 70% overall, >= 80% per module
- [ ] All 60+ tests passing
- [ ] Pre-commit hooks passing on all files

### Documentation
- [ ] CHANGELOG.md updated with release notes
- [ ] API documentation current (drf-spectacular output)
- [ ] SYSTEM_REQUIREMENTS.md reviewed
- [ ] Deployment guide updated
- [ ] Migration guide for breaking changes

### Security Audit
- [ ] Bandit security scan passes
- [ ] Safety dependency check passes
- [ ] No hardcoded secrets in code
- [ ] Environment variables documented
- [ ] SSL/TLS configuration verified

## Release Phase (T-0)

### Final Verification
```bash
# Run complete test suite
./build-setup-test.sh --all

# Verify coverage
pytest --cov=src --cov-report=term-missing

# Run security scans
bandit -r src/
safety check

# Validate configuration
python -c "from core.module_loader import registry; print(registry.get_enabled_apps())"
```

### Version Bumping
- [ ] Update version in `trigger_config.yaml`
- [ ] Update version in Docker tags
- [ ] Create git tag: `git tag -a v1.x.0 -m "Release v1.x.0"`
- [ ] Push tag: `git push origin v1.x.0`

### Build & Deploy
- [ ] Docker image builds successfully
- [ ] CI/CD pipeline passes
- [ ] Staging deployment successful
- [ ] Smoke tests pass in staging
- [ ] Production deployment approved

## Post-Release Phase (T+1 Day)

### Monitoring
- [ ] Application logs reviewed (no errors)
- [ ] Performance metrics normal
- [ ] Database query performance acceptable
- [ ] Memory usage within limits
- [ ] Error tracking (Sentry) clean

### Communication
- [ ] Release announcement sent
- [ ] Stakeholders notified
- [ ] Support team briefed on changes
- [ ] Documentation published

### Rollback Plan (if needed)
- [ ] Rollback procedure tested
- [ ] Database migration rollback scripts ready
- [ ] Previous Docker image available
- [ ] Communication plan for rollback

## Module-Specific Checks

### Inventory Module
- [ ] Stock calculations accurate
- [ ] Warehouse operations functional
- [ ] Movement audit trail complete

### HR Module (when released)
- [ ] Employee data secure
- [ ] Payroll calculations verified
- [ ] Leave balances accurate

### Finance Module (when released)
- [ ] Transaction integrity maintained
- [ ] Financial reports accurate
- [ ] Currency conversions correct

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Release Manager | | | |
| Tech Lead | | | |
| QA Lead | | | |
| Security Officer | | | |

## Emergency Contacts
- On-call Engineer: _______________
- Product Owner: _______________
- Security Team: _______________
