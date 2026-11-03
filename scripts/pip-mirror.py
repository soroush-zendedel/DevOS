"""Run any pip command using the Iranian mirror, then official PyPI on failure."""
import os
import subprocess
import sys

default_mirrors = [
    "https://mirror.novin.cloud/artifactory/api/pypi/pypi/simple/",
    "https://mirror2.chabokan.net/pypi/simple/",
    "https://pypi.hyperclouds.ir/simple/",
]
configured_mirrors = os.environ.get("DEVOS_PYPI_MIRRORS")
if configured_mirrors:
    mirrors = [url.strip() for url in configured_mirrors.split(",") if url.strip()]
else:
    mirrors = [os.environ.get("DEVOS_PYPI_MIRROR", default_mirrors[0])]
    mirrors.extend(url for url in default_mirrors[1:] if url not in mirrors)
args = sys.argv[1:] or ["--help"]
indexes = [*mirrors, "https://pypi.org/simple"]
for index_number, index_url in enumerate(indexes):
    env = os.environ.copy()
    env["PIP_INDEX_URL"] = index_url
    env.pop("PIP_EXTRA_INDEX_URL", None)
    result = subprocess.run([sys.executable, "-m", "pip", *args], env=env, check=False)
    if result.returncode == 0:
        raise SystemExit(0)
    if index_number + 1 < len(indexes):
        print(f"PyPI index failed: {index_url}; trying {indexes[index_number + 1]}.", file=sys.stderr)
raise SystemExit(result.returncode)
