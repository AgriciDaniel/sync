## Summary

## Verification

- [ ] `python -m compileall scripts sync_brain tests`
- [ ] `ruff check .`
- [ ] `mypy .`
- [ ] `python -m pytest -q`
- [ ] `python tests/test_pipeline.py`
- [ ] `python scripts/build_demo_vault.py --verify-determinism`
- [ ] `python scripts/audit_brain.py --require market-ready --json`

## Release Risk

- [ ] No credentials or client PII added
- [ ] Raw-source immutability preserved
- [ ] Report sources cite raw files or source notes
- [ ] Any new `.raw` material is a reviewed fixture or remains outside release artifacts
- [ ] No authorization boundary was widened
