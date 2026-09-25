"""Real-compiler tests: build generated projects with the Connect IQ SDK.

Skipped unless the SDK (`monkeyc`), a developer key, and a runnable `java`
are all available. CI has none of these, so this module skips cleanly there.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import pytest

from ciq_scaffold.cli import generate_project

TYPES = ["watchface", "datafield", "widget", "app"]

SDK_CFG = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Garmin"
    / "ConnectIQ"
    / "current-sdk.cfg"
)


def _sdk_dir() -> Optional[Path]:
    env = os.environ.get("CIQ_SDK")
    if env:
        return Path(env)
    try:
        text = SDK_CFG.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return Path(text) if text else None


def _developer_key() -> Path:
    env = os.environ.get("CIQ_DEVELOPER_KEY")
    if env:
        return Path(env)
    return Path.home() / ".garmin" / "developer_key.der"


def _java_ok() -> bool:
    if shutil.which("java") is None:
        return False
    try:
        proc = subprocess.run(["java", "-version"], capture_output=True, timeout=60)
    except OSError:
        return False
    return proc.returncode == 0


def _monkeyc_and_key() -> tuple[Path, Path]:
    sdk = _sdk_dir()
    if sdk is None:
        pytest.skip("no Connect IQ SDK found (CIQ_SDK or current-sdk.cfg)")
    assert sdk is not None  # narrow for type checkers
    monkeyc = sdk / "bin" / "monkeyc"
    if not monkeyc.is_file():
        pytest.skip(f"monkeyc not found at {monkeyc}")
    key = _developer_key()
    if not key.is_file():
        pytest.skip(f"developer key not found at {key}")
    if not _java_ok():
        pytest.skip("java is not runnable")
    return monkeyc, key


@pytest.mark.parametrize("app_type", TYPES)
def test_monkeyc_builds_generated_project(tmp_path: Path, app_type: str) -> None:
    monkeyc, key = _monkeyc_and_key()
    name = "HudTest"
    target = generate_project(
        name=name, app_type=app_type, out=tmp_path, devices=["instinct2"]
    )
    cmd = [
        str(monkeyc),
        "-d",
        "instinct2",
        "-f",
        "monkey.jungle",
        "-o",
        f"bin/{name}.prg",
        "-y",
        str(key),
        "-w",
    ]
    proc = subprocess.run(
        cmd, cwd=target, capture_output=True, text=True, timeout=180
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, f"monkeyc failed for {app_type}:\n{output}"
    assert "BUILD SUCCESSFUL" in output, (
        f"no BUILD SUCCESSFUL for {app_type}:\n{output}"
    )
    assert (target / "bin" / f"{name}.prg").is_file(), (
        f"missing .prg for {app_type}:\n{output}"
    )
