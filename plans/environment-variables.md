### Proposal: Document Environment Variables

Clarify required and optional environment variables for configuration.

### Solution:
1. Create `docs/environment-variables.md` with:
   - `DEVOS_MIRROR_COUNTRY` (required)
   - `DEVOS_DEBIAN_MIRRORS` (required)
   - `CI_REGISTRY_USER` (optional for CI)
   - `CI_REGISTRY_PASSWORD` (optional for CI)
2. Add comments in `Dockerfile` and `scripts/build-iso.sh` referencing the documentation
3. Include in README.md as configuration prerequisites