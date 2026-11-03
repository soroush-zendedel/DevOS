from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console


APP_ROOT = Path(__file__).resolve().parents[2]
console = Console()
app = typer.Typer(
    name="devos",
    help="Build, inspect, and test the DevOS live image.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,
)


def require_windows() -> None:
    if sys.platform != "win32":
        raise typer.BadParameter("This command runs on the Windows Hyper-V host.")


def run(command: list[str], *, cwd: Path = APP_ROOT) -> None:
    try:
        result = subprocess.run(command, cwd=cwd, check=False)
    except FileNotFoundError as exc:
        raise typer.BadParameter(f"Required command was not found: {command[0]}") from exc
    if result.returncode:
        raise typer.Exit(result.returncode)


def compose_base() -> list[str]:
    docker = shutil.which("docker")
    if not docker:
        raise typer.BadParameter("Docker is required. Install Docker Desktop or Docker Engine with the Compose plugin.")
    command = [docker, "compose", "--project-directory", str(APP_ROOT)]
    try:
        daemon = subprocess.run(
            [docker, "info", "--format", "{{.ServerVersion}}"],
            cwd=APP_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise typer.BadParameter(f"Could not start Docker: {exc}") from exc
    if daemon.returncode:
        detail = daemon.stderr.strip() or "Docker Engine did not respond."
        raise typer.BadParameter(f"Docker Engine is unavailable. Start Docker Desktop/Engine and retry. {detail}")
    compose_version = subprocess.run(
        [docker, "compose", "version"], cwd=APP_ROOT, capture_output=True, text=True, check=False
    )
    if compose_version.returncode:
        raise typer.BadParameter("Docker Compose v2 is required. Install/enable the Compose plugin and retry.")
    run(command + ["config", "--quiet"])
    return command


def run_compose(*args: str) -> None:
    command = compose_base()
    run(command + list(args))


def copied_iso_hash(*, require_checksum_file: bool = True) -> str:
    iso = APP_ROOT / "build" / "devos-amd64.iso"
    checksum_file = APP_ROOT / "build" / "devos-amd64.iso.sha256"
    if not iso.is_file():
        raise typer.BadParameter(f"ISO does not exist: {iso}")
    expected = None
    if checksum_file.is_file():
        try:
            expected = checksum_file.read_text(encoding="ascii").split()[0].upper()
        except (OSError, IndexError, UnicodeError) as exc:
            raise typer.BadParameter(f"Could not read the container's ISO checksum: {exc}") from exc
    elif require_checksum_file:
        raise typer.BadParameter("The container did not create build/devos-amd64.iso.sha256.")
    digest = hashlib.sha256()
    with iso.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest().upper()
    if expected is not None and actual != expected:
        raise typer.BadParameter(f"ISO copy hash mismatch: container={expected}, host={actual}")
    label = "ISO copy verified" if expected is not None else "ISO SHA-256"
    console.print(f"{label}: {iso} [dim]{actual}[/dim]")
    return actual


def container_build() -> None:
    run_compose("run", "--build", "--rm", "builder", "./scripts/build-iso.sh")
    copied_iso_hash()


def container_verify() -> None:
    copied_iso_hash(require_checksum_file=False)
    run_compose(
        "run", "--build", "--rm", "builder",
        "./scripts/verify-iso.sh", "/workspace/build/devos-amd64.iso",
    )


def run_powershell_script(script: str, *args: str) -> None:
    require_windows()
    powershell = shutil.which("pwsh") or shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise typer.BadParameter("PowerShell was not found. Install or enable Windows PowerShell.")
    path = APP_ROOT / "scripts" / "workflows" / "windows" / script
    run([powershell, "-NoProfile", "-File", str(path), *args])


@app.command()
def build() -> None:
    """Build the ISO in the Debian container, keeping downloaded caches."""
    console.rule("Building DevOS ISO with Docker Compose")
    container_build()


@app.command()
def clean(
    purge: Annotated[
        bool,
        typer.Option(help="Also remove downloaded package and bootstrap caches."),
    ] = False,
) -> None:
    """Clean containerized live-build output; preserve caches unless --purge is supplied."""
    command = ["lb", "clean", "--purge"] if purge else ["lb", "clean"]
    console.rule("Cleaning live-build state")
    run_compose("run", "--build", "--rm", "builder", *command)
    if purge:
        run_compose("down", "--volumes")


@app.command()
def verify() -> None:
    """Print the ISO SHA-256 and inspect its boot catalog in the Debian container."""
    container_verify()


@app.command()
def deps() -> None:
    """Build the Debian builder image and refresh its required packages."""
    run_compose("build", "--pull", "--no-cache", "builder")


@app.command()
def update() -> None:
    """Fast-forward the current Git branch from its configured upstream."""
    run(["git", "pull", "--ff-only"])


@app.command("update-build")
def update_build() -> None:
    """Fast-forward from Git, build the ISO in Docker, and verify it."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=APP_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise typer.BadParameter(result.stderr.strip() or "Could not inspect the Git working tree.")
    if result.stdout.strip():
        raise typer.BadParameter("Tracked local changes exist. Commit or stash them before update-build.")
    run(["git", "pull", "--ff-only"])
    console.print("Building repository revision:", end=" ")
    run(["git", "log", "-1", "--format=%h %s"])
    container_build()
    container_verify()
    console.print("DevOS build and ISO verification completed.")


@app.command("vm-ip")
def vm_ip(
    vm_name: Annotated[str | None, typer.Option(help="Hyper-V VM name; auto-select when only one is running.")] = None,
) -> None:
    """Find the IPv4 address of a running Hyper-V guest."""
    args: list[str] = []
    if vm_name:
        args.extend(["-VMName", vm_name])
    run_powershell_script("Get-DevOSVmIp.ps1", *args)


@app.command("copy-iso")
def copy_iso(
    builder_host: Annotated[str, typer.Option(envvar="DEVOS_BUILDER_HOST", help="Builder IP or DNS name.")],
    builder_user: Annotated[str, typer.Option(envvar="DEVOS_BUILDER_USER", help="SSH account on the builder.")],
    remote_iso_path: Annotated[str, typer.Option(envvar="DEVOS_REMOTE_ISO_PATH", help="Absolute ISO path on the builder.")],
    destination_directory: Annotated[Path, typer.Option(help="Local directory for the verified ISO.")],
    identity_file: Annotated[Path | None, typer.Option(help="Optional private key path; never stored by DevOS.")] = None,
) -> None:
    """Copy an ISO over SSH and compare its SHA-256 before accepting the copy."""
    args = [
        "-BuilderHost", builder_host,
        "-BuilderUser", builder_user,
        "-RemoteIsoPath", remote_iso_path,
        "-DestinationDirectory", str(destination_directory),
    ]
    if identity_file:
        args.extend(["-IdentityFile", str(identity_file)])
    run_powershell_script("Copy-DevOSIso.ps1", *args)


@app.command("attach-iso")
def attach_iso(
    vm_name: Annotated[str, typer.Option(help="Hyper-V VM name.")],
    iso_path: Annotated[Path, typer.Option(help="ISO already copied to the Windows host.")],
    what_if: Annotated[bool, typer.Option(help="Preview the Hyper-V changes without applying them.")] = False,
) -> None:
    """Attach an ISO only when the named Hyper-V VM is already Off."""
    args = ["-VMName", vm_name, "-IsoPath", str(iso_path)]
    if what_if:
        args.append("-WhatIf")
    run_powershell_script("Set-DevOSVmIso.ps1", *args)


@app.command()
def status() -> None:
    """Show the Git checkout status."""
    run(["git", "status", "-sb"])


def main() -> None:
    app()


if __name__ == "__main__":
    main()
