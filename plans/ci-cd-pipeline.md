### Proposal: Add CI/CD Pipeline

Implement automated testing and deployment workflows to ensure code quality and streamline releases.

### Solution:
1. Create `.github/workflows/ci.yml` with:
   - Python version matrix (3.10+)
   - Dependency installation
   - Linting (flake8)
   - Unit tests (pytest)
   - Documentation build (Sphinx)
2. Add `docker/build-and-push.yml` for container image publishing
3. Configure secrets for PyPI/Docker Hub access