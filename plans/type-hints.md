### Proposal: Add Type Hints

Improve code maintainability with Python type annotations.

### Solution:
1. Add `from typing import` imports
2. Annotate:
   - Function parameters/returns
   - Class attributes
   - Complex data structures
3. Use `mypy` in CI for type checking
4. Add `pyright` configuration for IDE support