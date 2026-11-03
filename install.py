"""Install DevOS into the active virtual environment using configured mirrors."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
MIRROR_ROOT = ROOT / "config" / "mirrors"

if __name__ == "__main__":
    countries = sorted(
        path.name
        for path in MIRROR_ROOT.iterdir()
        if path.is_dir() and (path / "pypi.txt").is_file()
    )
    parser = argparse.ArgumentParser(description="Install DevOS using a regional package mirror list.")
    parser.add_argument("country", choices=countries, help="country whose PyPI mirror list to use")
    args = parser.parse_args()

    if sys.prefix == sys.base_prefix:
        print("Activate the project virtual environment first, then run python install.py.", file=sys.stderr)
        raise SystemExit(2)

    mirror_file = MIRROR_ROOT / args.country / "pypi.txt"
    mirrors = [
        line.strip()
        for line in mirror_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not mirrors:
        print(f"No PyPI mirrors configured in {mirror_file}.", file=sys.stderr)
        raise SystemExit(2)

    debian_mirrors_file = MIRROR_ROOT / args.country / "debian.txt"
    docker_file = MIRROR_ROOT / args.country / "docker.txt"
    docker_images = [
        line.strip()
        for line in docker_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not docker_images:
        print(f"No Docker images configured in {docker_file}.", file=sys.stderr)
        raise SystemExit(2)
    debian_mirrors = [
        line.strip()
        for line in debian_mirrors_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    debian_pairs = [line.split("|", 1) for line in debian_mirrors if "|" in line]
    if len(debian_pairs) != len(debian_mirrors) or not debian_pairs:
        print(f"Invalid Debian mirror list in {debian_mirrors_file}.", file=sys.stderr)
        raise SystemExit(2)

    installer = ROOT / "scripts" / "pip-mirror.py"
    env = os.environ.copy()
    env["DEVOS_PYPI_MIRRORS"] = ",".join(mirrors)
    result = subprocess.run(
        [sys.executable, str(installer), "install", "--editable", str(ROOT)],
        cwd=ROOT,
        env=env,
        check=False,
    )
    if result.returncode == 0:
        selected_env = {
            "DEVOS_MIRROR_COUNTRY": args.country,
            "DEVOS_PYPI_MIRRORS": ",".join(mirrors),
            "DEVOS_DEBIAN_MIRRORS": ",".join(debian_mirrors),
            "DEVOS_DOCKER_BASE_IMAGES": ",".join(docker_images),
            "DEVOS_DEBIAN_MIRROR": debian_pairs[0][0],
            "DEVOS_SECURITY_MIRROR": debian_pairs[0][1],
        }
        env_path = ROOT / ".devos-mirrors.env"
        env_path.write_text("".join(f"{key}={value}\n" for key, value in selected_env.items()), encoding="utf-8")
    raise SystemExit(result.returncode)
