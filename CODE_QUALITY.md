# Code Quality Expectations

## Overview
- Keep the project maintainable by following a consistent coding style, keeping functions small, and documenting intent when non-obvious decisions are made.
- Prioritize safety and robustness: guard external inputs, handle diffusion resource constraints, and keep promise of deterministic contracts.

## Python standards
- Target Python 3.10+ features such as structural pattern matching, `match/case`, and precise typing.
- Run formatting/linting before commits:
  ```bash
  ruff check src tests
  black src tests
  ```
- Favor dataclasses/Pydantic when modeling structured data rather than ad-hoc dictionaries.

## Testing & validation
- Add focused unit tests for prompt processing rules (validators, optimizers, explainers) and diffusion helpers.
- Protect generation tools with integration-style tests that mock `get_pipeline()` and assert metadata/result handling.
- Use `pytest` and `pytest-asyncio` when exercising FastMCP endpoints.

## Documentation and metadata
- Keep contracts/behavior docs synchronized with code changes (README translations already cover flow).
- Update `pyproject.toml` metadata if new dependencies or scripts are added.
 
## Review checklist
1. Did the change add/remove comments or logging without altering logic? Rerun formatting.
2. Do new endpoints/tools have schema updates reflected in `03-contracts/`?
3. Are quality thresholds (prompt rules, defaults) documented and enforced in validators/optimizers?
