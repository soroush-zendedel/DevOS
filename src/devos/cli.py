from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from rich.table import Table
from rich.markup import escape


APP_ROOT = Path(__file__).resolve().parents[2]
console = Console()
active_status: Status | None = None
build_started_at: float | None = None
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
LIVE_BUILD_STAGE = re.compile(r"\blb\s+(bootstrap|chroot|binary|source)(?:_([a-z0-9_-]+))?\s+(\S+)", re.I)
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
    if active_status is not None:
        log_path = APP_ROOT / "build" / "devos-build.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        tail: deque[str] = deque(maxlen=24)
        recent_output: deque[str] = deque(maxlen=5)
        panel_lock = threading.RLock()
        started_at = build_started_at or time.monotonic()
        current_phase = "Preparing build"

        def elapsed_text() -> str:
            seconds = int(time.monotonic() - started_at)
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}:{seconds:02}"

        def progress_panel() -> Panel:
            # Reserve space for Rich's spinner and panel borders. Keeping five
            # fixed-height output rows makes the display steady as lines change.
            panel_width = max(40, console.size.width - 2)
            content_width = max(20, panel_width - 4)
            with panel_lock:
                output_rows = list(recent_output)
                phase = current_phase
            output_rows = [
                line if len(line) <= content_width else f"…{line[-(content_width - 1):]}"
                for line in output_rows
            ]
            output_rows.extend([""] * (5 - len(output_rows)))
            output_text = "\n".join(f"[dim]{escape(line)}[/dim]" if line else " " for line in output_rows)
            return Panel(
                f"[bold cyan]{escape(phase)}[/bold cyan]\n"
                f"[dim]Elapsed:[/dim] [white]{elapsed_text()}[/white]    "
                f"[dim]Remaining:[/dim] [yellow]Unknown[/yellow]\n"
                f"{output_text}",
                title="[bold blue]Building DevOS ISO[/bold blue]",
                border_style="cyan",
                width=panel_width,
            )

        class DynamicProgressPanel:
            def __rich_console__(self, render_console, options):
                # Rebuild on each Rich refresh so elapsed time advances even
                # while the subprocess is quiet.
                yield progress_panel()

        live_panel = DynamicProgressPanel()
        recent_output.append("Waiting for build output…")
        active_status.update(live_panel)
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                bufsize=1,
                env={**os.environ, "BUILDKIT_PROGRESS": "plain", "NO_COLOR": "1"},
            )
        except FileNotFoundError as exc:
            raise typer.BadParameter(f"Required command was not found: {command[0]}") from exc

        with log_path.open("a", encoding="utf-8", errors="replace") as log:
            log.write(f"\n$ {' '.join(command)}\n")
            assert process.stdout is not None
            for raw_line in process.stdout:
                log.write(raw_line)
                line = ANSI_ESCAPE.sub("", raw_line).replace("\r", "").strip()
                if line:
                    tail.append(line)
                    stage_match = LIVE_BUILD_STAGE.search(line)
                    if stage_match:
                        phase, component, action = stage_match.groups()
                        phase_names = {
                            "bootstrap": "Preparing Debian base",
                            "chroot": "Preparing system and packages",
                            "binary": "Building ISO",
                            "source": "Packaging source",
                        }
                        with panel_lock:
                            current_phase = f"{phase_names[phase.lower()]} · {component or 'general'} · {action}"
                    elif "Building DevOS ISO" in line or "[+] Building" in line:
                        with panel_lock:
                            current_phase = "Building Docker image"
                    elif "Created:" in line:
                        with panel_lock:
                            current_phase = "Finalizing ISO file"
                    with panel_lock:
                        recent_output.append(line)
                    active_status.update(live_panel)
            return_code = process.wait()

        if return_code:
            console.print(f"[bold red]FAIL: command exited with status {return_code}.[/bold red]")
            for line in tail:
                console.print(f"[red]{escape(line)}[/red]")
            console.print(f"Full build output: [cyan]{log_path}[/cyan]")
            raise typer.Exit(return_code)
        return

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
    command = [docker, "compose", "--progress", "plain", "--project-directory", str(APP_ROOT)]
    mirror_env = APP_ROOT / ".devos-mirrors.env"
    if mirror_env.is_file():
        command.extend(["--env-file", str(mirror_env)])
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


def ensure_docker_base_image() -> None:
    """Pull the Debian builder base from configured mirrors, then tag it locally."""
    docker = shutil.which("docker")
    if not docker:
        raise typer.BadParameter("Docker is required to pull the Debian builder base image.")
    env_file = APP_ROOT / ".devos-mirrors.env"
    values: dict[str, str] = {}
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    selected_country = values.get("DEVOS_MIRROR_COUNTRY", "iran")
    configured_candidates = values.get("DEVOS_DOCKER_BASE_IMAGES")
    if configured_candidates:
        candidates = configured_candidates.split(",")
    else:
        docker_mirrors = APP_ROOT / "config" / "mirrors" / selected_country / "docker.txt"
        candidates = [
            line.strip()
            for line in docker_mirrors.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    local_tag = "debian:trixie-slim"
    for candidate in (image.strip() for image in candidates if image.strip()):
        console.print(f"Trying Debian base image: [dim]{candidate}[/dim]")
        result = subprocess.run(
            [docker, "pull", "--quiet", candidate],
            cwd=APP_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            console.print(f"[yellow]Mirror unavailable; moving to the next configured source.[/yellow]")
            continue
        if candidate != local_tag:
            tagged = subprocess.run([docker, "tag", candidate, local_tag], cwd=APP_ROOT, check=False)
            if tagged.returncode:
                raise typer.BadParameter(f"Could not tag pulled base image {candidate} as {local_tag}.")
        console.print(f"Using Debian base image from [green]{candidate}[/green].")
        return
    raise typer.BadParameter("Could not pull the Debian base image from configured mirrors or official Docker Hub.")


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
    if expected is not None:
        console.print(
            f"[green]PASS[/green] Host ISO SHA-256 matches the builder checksum: [dim]{actual}[/dim]\n"
            f"      File: {iso}"
        )
    else:
        console.print(f"Host ISO SHA-256: [dim]{actual}[/dim]\nFile: {iso}")
    return actual


def ensure_project_ssh_key() -> Path:
    private_key = APP_ROOT / ".devos-ssh"
    public_key = APP_ROOT / ".devos-ssh.pub"
    if private_key.exists() != public_key.exists():
        raise typer.BadParameter(
            "Project SSH key pair is incomplete. Remove .devos-ssh and .devos-ssh.pub, then run devos build again."
        )
    if not private_key.exists():
        ssh_keygen = shutil.which("ssh-keygen")
        if not ssh_keygen:
            raise typer.BadParameter("OpenSSH ssh-keygen is required to create the project SSH key.")
        result = subprocess.run(
            [ssh_keygen, "-q", "-t", "ed25519", "-N", "", "-C", "devos-project", "-f", str(private_key)],
            cwd=APP_ROOT, capture_output=True, text=True, check=False,
        )
        if result.returncode:
            raise typer.BadParameter(result.stderr.strip() or "Could not create the project SSH key pair.")
        if os.name != "nt":
            private_key.chmod(0o600)
    return private_key


def container_build(*, build_image: bool = True) -> None:
    ensure_project_ssh_key()
    if build_image:
        ensure_docker_base_image()
    build_option = ("--build",) if build_image else ()
    run_compose("run", *build_option, "--rm", "builder", "./scripts/build-iso.sh")
    copied_iso_hash()


def container_verify() -> None:
    host_iso = APP_ROOT / "build" / "devos-amd64.iso"
    if not host_iso.is_file():
        raise typer.BadParameter(f"Windows host ISO does not exist: {host_iso}")
    console.print(
        f"Verifying Windows host ISO: [cyan]{host_iso}[/cyan]\n"
        "The container reads this same file through the /workspace/build bind mount."
    )
    copied_iso_hash(require_checksum_file=False)
    ensure_docker_base_image()
    run_compose(
        "run", "--build", "--rm", "builder",
        "./scripts/verify-iso.sh", "/workspace/build/devos-amd64.iso",
    )
    console.print(
        "[bold green]PASS: ISO verification completed.[/bold green] "
        "The host file's SHA-256 and BIOS/UEFI boot entries were checked."
    )


def run_powershell_script(script: str, *args: str) -> None:
    require_windows()
    powershell = shutil.which("pwsh") or shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise typer.BadParameter("PowerShell was not found. Install or enable Windows PowerShell.")
    path = APP_ROOT / "scripts" / "workflows" / "windows" / script
    run([powershell, "-NoProfile", "-File", str(path), *args])


@app.command()
def build(
    up: Annotated[
        bool,
        typer.Option("--up", help="Refresh the Debian builder image before building the ISO."),
    ] = False,
) -> None:
    """Build the ISO in the Debian container, keeping downloaded caches."""
    global active_status, build_started_at
    if up:
        ensure_docker_base_image()
    with console.status("[cyan]Building DevOS ISO…[/cyan]", spinner="dots") as status:
        active_status = status
        build_started_at = time.monotonic()
        try:
            if up:
                run_compose("build", "--no-cache", "builder")
            container_build(build_image=not up)
        finally:
            active_status = None
            build_started_at = None
    console.print(Panel.fit("[bold green]ISO build complete[/bold green]\nProject SSH key is ready.", border_style="green"))


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
    ensure_docker_base_image()
    run_compose("run", "--build", "--rm", "builder", *command)
    if purge:
        run_compose("down", "--volumes")


@app.command()
def verify() -> None:
    """Print the ISO SHA-256 and inspect its boot catalog in the Debian container."""
    container_verify()


@app.command()
def ssh(
    vm_name: Annotated[str | None, typer.Option(help="Hyper-V VM name; auto-select when only one VM is running.")] = None,
) -> None:
    """Find the running DevOS VM and connect using this project's SSH key."""
    require_windows()
    private_key = APP_ROOT / ".devos-ssh"
    public_key = APP_ROOT / ".devos-ssh.pub"
    if not private_key.is_file() or not public_key.is_file():
        raise typer.BadParameter("Project SSH key is missing. Run 'devos build' first.")
    if not shutil.which("ssh") or not shutil.which("ssh-keyscan"):
        raise typer.BadParameter("Windows OpenSSH Client (ssh and ssh-keyscan) is required.")
    script = APP_ROOT / "scripts" / "workflows" / "windows" / "Get-DevOSVmIp.ps1"
    powershell = shutil.which("pwsh") or shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise typer.BadParameter("PowerShell was not found. Install or enable Windows PowerShell.")
    args = [powershell, "-NoProfile", "-File", str(script), "-Quiet"]
    if vm_name:
        args.extend(["-VMName", vm_name])
    result = subprocess.run(args, cwd=APP_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "Could not find a running VM IP."
        raise typer.BadParameter(detail)
    try:
        guest = json.loads(result.stdout)
        ip = guest[0]["IPAddress"] if isinstance(guest, list) else guest["IPAddress"]
        guest_name = guest[0]["VMName"] if isinstance(guest, list) else guest["VMName"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise typer.BadParameter("Could not parse the Hyper-V guest address.") from exc

    known_hosts = APP_ROOT / ".devos-known-hosts"
    scan = subprocess.run(["ssh-keyscan", "-T", "5", ip], capture_output=True, text=True, check=False)
    if scan.returncode or not scan.stdout.strip():
        raise typer.BadParameter(f"SSH is not responding at {ip}. Confirm the DevOS ISO is booted and connected to a network.")
    scanned = APP_ROOT / ".devos-scanned-host-key"
    scanned.write_text(scan.stdout, encoding="utf-8")
    if known_hosts.exists():
        check = subprocess.run(
            [shutil.which("ssh-keygen") or "ssh-keygen", "-F", ip, "-f", str(known_hosts)],
            capture_output=True, text=True, check=False,
        )
        old_lines = [line.split() for line in check.stdout.splitlines() if line and not line.startswith("#")]
        new_lines = [line.split() for line in scan.stdout.splitlines() if line and not line.startswith("#")]
        if not old_lines:
            raise typer.BadParameter(f"Could not find a pinned host key for {ip}; remove .devos-known-hosts to trust this VM again.")
        if not any(len(old) >= 3 and len(new) >= 3 and old[-2:] == new[-2:] for old in old_lines for new in new_lines):
            raise typer.BadParameter(f"SSH host key changed for {ip}. Review the VM and remove .devos-known-hosts only if this change is expected.")
    else:
        host_key = next((line.split() for line in scan.stdout.splitlines() if line and not line.startswith("#")), [])
        if len(host_key) < 3:
            scanned.unlink(missing_ok=True)
            raise typer.BadParameter("Could not parse the SSH host key returned by the VM.")
        import base64
        import hashlib as hash_module

        fingerprint = base64.b64encode(hash_module.sha256(base64.b64decode(host_key[2])).digest()).decode().rstrip("=")
        console.print(Panel.fit(f"First connection to [bold]{guest_name}[/bold] at {ip}\nHost fingerprint: [yellow]SHA256:{fingerprint}[/yellow]", title="Trust this VM?", border_style="yellow"))
        if not typer.confirm("Save this host key and continue?", default=False):
            raise typer.Exit(1)
        known_hosts.write_text(scan.stdout, encoding="utf-8")
    scanned.unlink(missing_ok=True)
    table = Table.grid(padding=(0, 2))
    table.add_row("VM", guest_name)
    table.add_row("Address", ip)
    console.print(Panel(table, title="[bold cyan]Connecting to DevOS[/bold cyan]", border_style="cyan"))
    run([shutil.which("ssh") or "ssh", "-i", str(private_key), "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes",
         "-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={known_hosts}", f"user@{ip}"], cwd=APP_ROOT)


@app.command()
def logs(
    lines: Annotated[int, typer.Option(min=1, max=10000, help="Number of recent log lines.")] = 100,
) -> None:
    """Show detailed logs from the builder container, including past runs."""
    command = compose_base()
    result = subprocess.run(
        command + ["logs", "--no-color", "--tail", str(lines), "builder"],
        cwd=APP_ROOT, capture_output=True, text=True, check=False,
    )
    docker = shutil.which("docker") or "docker"
    containers = subprocess.run(
        [docker, "ps", "-a", "--filter", "name=devos-builder", "--format", "{{.ID}}"],
        cwd=APP_ROOT, capture_output=True, text=True, check=False,
    )
    output = result.stdout.strip()
    if output:
        console.print(Panel(output, title="[bold]Builder logs[/bold]", border_style="blue"))
    else:
        console.print("[dim]No retained builder logs. Use 'devos logs' immediately after a run to capture details.[/dim]")
    for container_id in containers.stdout.splitlines():
        inspect = subprocess.run(
            [docker, "inspect", "--format", "{{.State.Status}}: {{.State.Error}}", container_id],
            cwd=APP_ROOT, capture_output=True, text=True, check=False,
        )
        if inspect.stdout.strip():
            console.print(f"[dim]Container {container_id[:12]} · {inspect.stdout.strip()}[/dim]")
    if result.returncode:
        raise typer.Exit(result.returncode)


@app.command()
def deps() -> None:
    """Build the Debian builder image and refresh its required packages."""
    ensure_docker_base_image()
    run_compose("build", "--no-cache", "builder")


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
