# Python Coding Agent Playbook

## Goal
Produce correct Python code with a tight generate → test → fix loop.

## Planner responsibilities
- Clarify inputs/outputs/constraints.
- Decide minimal viable artifact: snippet vs module vs CLI.
- Define success criteria (expected outputs, performance constraints, edge cases).

## Executor responsibilities
1) Plan implementation (outline functions/modules).
2) Implement minimal working code first.
3) Test using tools (python sandbox, unit tests, sample cases).
4) If failures: fix the smallest thing, re-run, repeat.
5) Polish: docstrings, type hints where useful, informative errors.

## Reviewer checklist
- Meets requirements + success criteria?
- Handles edge cases?
- No hidden dependencies (unless specified)?
- Readable structure + clear naming?
- No secrets/logging sensitive info?

## Finalizer format
- Final code block(s)
- Run instructions (commands / entrypoint)
- Short explanation + assumptions

## Example skeleton
```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

def solve(items: Iterable[int]) -> int:
    """Return <what it does>."""
    total = 0
    for x in items:
        total += x
    return total

if __name__ == "__main__":
    print(solve([1, 2, 3]))
```
