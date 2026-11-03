from __future__ import annotations

import os
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


def require_linux() -> None:
    if sys.platform != "linux":
        raise typer.BadParameter("This command runs on the Debian builder (Linux).")


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


def run_builder_script(script: str, *args: str) -> None:
    require_linux()
    path = APP_ROOT / "scripts" / script
    command = [str(path), *args]
    if os.geteuid() != 0:
        sudo = shutil.which("sudo")
        if not sudo:
            raise typer.BadParameter("sudo is required; install it or run this command as root.")
        command.insert(0, sudo)
    run(command)


def run_powershell_script(script: str, *args: str) -> None:
    require_windows()
    powershell = shutil.which("pwsh") or shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise typer.BadParameter("PowerShell was not found. Install or enable Windows PowerShell.")
    path = APP_ROOT / "scripts" / "workflows" / "windows" / script
    run([powershell, "-NoProfile", "-File", str(path), *args])


@app.command()
def build() -> None:
    """Build the ISO from the current checkout, keeping downloaded caches."""
    require_linux()
    console.rule("Building DevOS ISO")
    run_builder_script("build-iso.sh")


@app.command()
def clean(
    purge: Annotated[
        bool,
        typer.Option(help="Also remove downloaded package and bootstrap caches."),
    ] = False,
) -> None:
    """Clean live-build output; preserve caches unless --purge is supplied."""
    require_linux()
    command = ["lb", "clean", "--purge"] if purge else ["lb", "clean"]
    console.rule("Cleaning live-build state")
    if os.geteuid() != 0:
        sudo = shutil.which("sudo")
        if not sudo:
            raise typer.BadParameter("sudo is required; install it or run this command as root.")
        command.insert(0, sudo)
    run(command)


@app.command()
def verify(
    iso: Annotated[
        Path,
        typer.Argument(help="ISO file to inspect."),
    ] = APP_ROOT / "build" / "devos-amd64.iso",
) -> None:
    """Print the ISO SHA-256 and inspect its boot catalog when xorriso is installed."""
    require_linux()
    iso_path = iso if iso.is_absolute() else Path.cwd() / iso
    run([str(APP_ROOT / "scripts" / "verify-iso.sh"), str(iso_path)])


@app.command()
def deps() -> None:
    """Install Debian packages needed by the image builder."""
    require_linux()
    run_builder_script("install-dependencies.sh")


@app.command()
def update() -> None:
    """Fast-forward the current Git branch from its configured upstream."""
    run(["git", "pull", "--ff-only"])


@app.command("update-build")
def update_build() -> None:
    """Update from Git, build, verify the ISO, and print builder IPs."""
    require_linux()
    script = APP_ROOT / "scripts" / "workflows" / "linux" / "update-build-iso.sh"
    run([str(script)])


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
