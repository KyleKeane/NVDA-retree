## Summary

<!-- What does this change do? One to three bullets. -->

## Why

<!-- The problem this solves, or the behaviour it enables. Link issues. -->

## Test plan

<!-- Mark off what you verified. Add rows as needed. -->

- [ ] `pytest` is green
- [ ] `ruff check .` and `ruff format --check .` are clean
- [ ] `python tools/build_addon.py` builds the `.nvda-addon` successfully
- [ ] Manually smoke-tested inside NVDA (if the change touches plugin.py, navigator.py, walker.py, identity.py, or ui/ — see the checklist in CONTRIBUTING.md)

## Notes for reviewers

<!-- Anything subtle, anything you'd like a second pair of eyes on,
     screenshots, gesture traces, etc. -->
