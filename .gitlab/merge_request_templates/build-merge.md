# Auto-build merge request

## Summary

- Buildroom ID: `BR-...`

## Scope

<!-- Describe the bounded change. Do not include secrets. -->

## Buildroom evidence

- [ ] `request.json` exists and matches the approved request
- [ ] `contract.json` defines acceptance criteria and verification requirements
- [ ] `plan.json` / implementation plan exists
- [ ] coder receipt exists
- [ ] artifact manifest or diff evidence exists
- [ ] QA report exists
- [ ] trust report exists
- [ ] retention decision exists
- [ ] operator summary exists

## Verification

```text
# command -> result
```

## Risk and rollback

- Risk level:
- Production impact:
- Rollback path:

## Required checks / approvals

- [ ] buildroom validation
- [ ] tests/lint/build as applicable
- [ ] independent QA
- [ ] trust state is not `investigate`
- [ ] human approval for production-impacting changes

/label ~"auto-build" ~"stage:review" ~"trust:pending"
