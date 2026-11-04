### Proposal: Implement Unit Tests

Ensure CLI commands are thoroughly tested with automated assertions.

### Solution:
1. Create `tests/` directory with:
   - `test_cli.py` for command testing
   - `test_utils.py` for helper functions
2. Use `pytest` with:
   - Fixture for temporary directories
   - Mocked environment variables
   - Assertion of CLI output
3. Add `pytest.ini` for configuration
4. Integrate with CI for automatic execution