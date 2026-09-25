"""CLI for ciq-scaffold: generate a starter Garmin Connect IQ project skeleton.

Emits ONLY the official Connect IQ SDK project structure. Requires the
official SDK (monkeyc / simulator) to build; this tool never downloads
or bundles the SDK.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import uuid
import zlib
from pathlib import Path

from ciq_scaffold import __version__

VALID_TYPES = ("watchface", "datafield", "widget", "app")

# --type flag -> manifest iq:application type attribute.
MANIFEST_TYPES = {
    "watchface": "watchface",
    "datafield": "datafield",
    "widget": "widget",
    "app": "watch-app",
}

# --type flag -> Monkey C view base class.
VIEW_BASES = {
    "watchface": "WatchUi.WatchFace",
    "datafield": "WatchUi.DataField",
    "widget": "WatchUi.View",
    "app": "WatchUi.View",
}

# --device flag -> manifest iq:product id. Small curated subset of the
# Instinct 2 family (see README). Names follow the Connect IQ SDK's
# devices.xml product ids; verify against your installed SDK before
# building, and file an issue if you need more targets added.
SUPPORTED_DEVICES = (
    "instinct2",
    "instinct2s",
    "instinct2x",
)

# Target used when --device is omitted (same as 0.1.0 bootstrap behavior).
DEFAULT_DEVICES = ("instinct2",)

_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*$")

# 62x62 placeholder launcher icon (matches the Instinct 2 launcher icon
# size so monkeyc does not need to scale it). Generated with stdlib only.
_ICON_SIZE = 62


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def launcher_icon_png(size: int = _ICON_SIZE) -> bytes:
    """Return a valid `size` x `size` RGB PNG (dark bg, light centre square)."""
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    raw = bytearray()
    margin = size // 3
    for y in range(size):
        raw.append(0)  # filter byte: none
        for x in range(size):
            if margin <= x < size - margin and margin <= y < size - margin:
                raw.extend((240, 240, 240))
            else:
                raw.extend((16, 16, 16))
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw)))
        + _png_chunk(b"IEND", b"")
    )

MIN_API_LEVEL = "3.2.0"


def validate_name(name: str) -> str:
    """Validate project name; return PascalCase class prefix.

    Rules: letters/digits only, must start with a letter.
    """
    if not _NAME_RE.fullmatch(name):
        raise ValueError(
            f"invalid project name {name!r}: use letters and digits only, "
            "starting with a letter (e.g. MyFace)"
        )
    return name[:1].upper() + name[1:]


def validate_devices(devices: list[str] | tuple[str, ...]) -> list[str]:
    """Validate --device ids; return de-duplicated list preserving order."""
    unknown = [d for d in devices if d not in SUPPORTED_DEVICES]
    if unknown:
        raise ValueError(
            f"unknown device id(s): {', '.join(unknown)}; "
            f"allowed ids: {', '.join(SUPPORTED_DEVICES)}"
        )
    seen: list[str] = []
    for d in devices:
        if d not in seen:
            seen.append(d)
    if not seen:
        raise ValueError(
            f"no devices selected; allowed ids: {', '.join(SUPPORTED_DEVICES)}"
        )
    return seen


def manifest_xml(*, prefix: str, manifest_type: str, app_id: str, devices: list[str]) -> str:
    products = "\n".join(f'            <iq:product id="{d}" />' for d in devices)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Replace the id below with your own app UUID from the Connect IQ developer portal.
     This is a randomly generated placeholder. -->
<iq:manifest version="3" xmlns:iq="http://www.garmin.com/xml/connectiq">
    <iq:application id="{app_id}" type="{manifest_type}" name="@Strings.AppName" entry="{prefix}App" launcherIcon="@Drawables.LauncherIcon" minApiLevel="{MIN_API_LEVEL}">
        <iq:products>
{products}
        </iq:products>
        <iq:permissions />
        <iq:languages>
            <iq:language>eng</iq:language>
        </iq:languages>
    </iq:application>
</iq:manifest>
"""


def strings_xml(*, prefix: str) -> str:
    return f"""<strings>
    <string id="AppName">{prefix}</string>
</strings>
"""


def layout_xml() -> str:
    return """<layouts>
    <layout id="MainLayout">
        <label id="TitleLabel" text="@Strings.AppName" x="center" y="center" font="Gfx.FONT_MEDIUM" justification="Gfx.TEXT_JUSTIFY_CENTER" color="Gfx.COLOR_WHITE" />
    </layout>
</layouts>
"""


def drawables_xml() -> str:
    return """<drawables>
    <bitmap id="LauncherIcon" filename="launcher_icon.png" />
</drawables>
"""


def app_mc(*, prefix: str) -> str:
    return f"""import Toybox.Lang;
import Toybox.Application;
import Toybox.WatchUi;

class {prefix}App extends Application.AppBase {{

    function initialize() {{
        AppBase.initialize();
    }}

    function getInitialView() as [Views] or Null {{
        return [{prefix}View.create()];
    }}

}}
"""


def view_mc(*, prefix: str, app_type: str) -> str:
    base = VIEW_BASES[app_type]
    return f"""using Toybox.Graphics;
using Toybox.WatchUi;

class {prefix}View extends {base} {{

    function initialize() {{
        {base.split(".")[-1]}.initialize();
    }}

    function onLayout(dc as Dc) as Void {{
        setLayout(Rez.Layouts.MainLayout(dc));
    }}

    function onUpdate(dc as Dc) as Void {{
        View.onUpdate(dc);
    }}

}}
"""


def jungle_file() -> str:
    return "project.manifest = manifest.xml\n"


def project_readme(*, name: str, prefix: str, app_type: str, devices: list[str]) -> str:
    manifest_type = MANIFEST_TYPES[app_type]
    # monkeyc builds one device at a time; point at the first target.
    device = devices[0]
    return f"""# {name}

Starter Garmin Connect IQ project ({manifest_type}) generated by ciq-scaffold.

Target device(s): {", ".join(devices)}.

## Build (requires the official Connect IQ SDK)

```sh
monkeyc -d {device} -f monkey.jungle -o bin/{prefix}.prg -y <developer_key>
```

Replace `<developer_key>` with the path to your Connect IQ developer key.
Repeat the build with `-d <id>` for each target device.

## Run in the simulator

Open the Connect IQ simulator, load `bin/{prefix}.prg`, and select the
{device} device profile.

This skeleton has not been compiled or tested on-device; it is a minimal
starting point for use with the official SDK.
"""


def generate_project(
    *,
    name: str,
    app_type: str,
    out: Path | None,
    force: bool = False,
    devices: list[str] | tuple[str, ...] | None = None,
) -> Path:
    """Generate the project tree. Returns the target directory."""
    if app_type not in VALID_TYPES:
        raise ValueError(f"invalid type {app_type!r}: choose from {', '.join(VALID_TYPES)}")
    prefix = validate_name(name)
    manifest_type = MANIFEST_TYPES[app_type]
    selected = validate_devices(list(devices) if devices is not None else list(DEFAULT_DEVICES))

    base = Path(out) if out is not None else Path.cwd()
    target = base / name

    if target.exists() and any(target.iterdir()) and not force:
        raise FileExistsError(
            f"target directory {target} exists and is not empty; "
            "use --force to overwrite"
        )
    target.mkdir(parents=True, exist_ok=True)

    app_id = str(uuid.uuid4())

    files: dict[str, str] = {
        "manifest.xml": manifest_xml(prefix=prefix, manifest_type=manifest_type, app_id=app_id, devices=selected),
        "resources/strings/strings.xml": strings_xml(prefix=prefix),
        "resources/layouts/layout.xml": layout_xml(),
        "resources/drawables/drawables.xml": drawables_xml(),
        f"source/{prefix}App.mc": app_mc(prefix=prefix),
        f"source/{prefix}View.mc": view_mc(prefix=prefix, app_type=app_type),
        "monkey.jungle": jungle_file(),
        "README.md": project_readme(name=name, prefix=prefix, app_type=app_type, devices=selected),
    }
    for rel, content in files.items():
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    icon = target / "resources" / "drawables" / "launcher_icon.png"
    icon.parent.mkdir(parents=True, exist_ok=True)
    icon.write_bytes(launcher_icon_png())

    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ciq-scaffold",
        description="Generate a starter Garmin Connect IQ project skeleton.",
    )
    parser.add_argument(
        "--version", action="version", version=f"ciq-scaffold {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="Generate a new Connect IQ project.")
    new.add_argument("name", help="Project name (letters/digits, starts with a letter).")
    new.add_argument(
        "--type",
        dest="type",
        required=True,
        choices=list(VALID_TYPES),
        help="Project type.",
    )
    new.add_argument(
        "--out",
        default=None,
        help="Parent directory for the new project (default: current directory).",
    )
    new.add_argument(
        "--force",
        action="store_true",
        help="Overwrite a non-empty target directory.",
    )
    new.add_argument(
        "--device",
        dest="device",
        action="append",
        default=None,
        metavar="ID",
        help=(
            "Target device product id; repeat for multiple devices "
            f"(default: {DEFAULT_DEVICES[0]}; "
            f"allowed: {', '.join(SUPPORTED_DEVICES)})."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "new":
        try:
            target = generate_project(
                name=args.name,
                app_type=args.type,
                out=Path(args.out) if args.out else None,
                force=args.force,
                devices=args.device,
            )
        except (ValueError, FileExistsError) as exc:
            print(f"ciq-scaffold: error: {exc}", file=sys.stderr)
            return 1
        print(f"Created {target}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
