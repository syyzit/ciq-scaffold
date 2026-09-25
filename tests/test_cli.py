"""Tests for ciq-scaffold project generation."""

import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from ciq_scaffold import __version__
from ciq_scaffold.cli import MANIFEST_TYPES, generate_project

TYPES = ["watchface", "datafield", "widget", "app"]

EXPECTED_FILES = [
    "manifest.xml",
    "monkey.jungle",
    "README.md",
    "resources/strings/strings.xml",
    "resources/layouts/layout.xml",
    "resources/drawables/drawables.xml",
    "resources/images/launcher_icon.png",
]

NS = {"iq": "http://www.garmin.com/xml/connectiq"}


@pytest.mark.parametrize("app_type", TYPES)
def test_generate_all_types(tmp_path: Path, app_type: str) -> None:
    target = generate_project(name="MyFace", app_type=app_type, out=tmp_path)

    for rel in EXPECTED_FILES:
        assert (target / rel).is_file(), rel
    assert (target / "source" / "MyFaceApp.mc").is_file()
    assert (target / "source" / "MyFaceView.mc").is_file()

    # manifest.xml parses; app type/entry/product correct.
    tree = ET.parse(target / "manifest.xml")
    root = tree.getroot()
    assert root.tag == "{http://www.garmin.com/xml/connectiq}manifest"
    assert root.get("version") == "3"
    app = root.find("iq:application", NS)
    assert app is not None
    assert app.get("type") == MANIFEST_TYPES[app_type]
    assert app.get("entry") == "MyFaceApp"
    assert app.get("name") == "@Strings.AppName"
    assert app.get("launcherIcon") == "@Drawables.LauncherIcon"
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        app.get("id", ""),
    )
    products = app.find("iq:products", NS)
    assert products is not None
    product_ids = [p.get("id") for p in products.findall("iq:product", NS)]
    assert "instinct2" in product_ids
    languages = app.find("iq:languages", NS)
    assert languages is not None
    assert [lang.text for lang in languages.findall("iq:language", NS)] == ["eng"]

    # strings/layout XML parse.
    ET.parse(target / "resources" / "strings" / "strings.xml")
    ET.parse(target / "resources" / "layouts" / "layout.xml")
    ET.parse(target / "resources" / "drawables" / "drawables.xml")

    # monkey.jungle references the manifest.
    jungle = (target / "monkey.jungle").read_text(encoding="utf-8")
    assert "project.manifest = manifest.xml" in jungle

    # Placeholder icon is a real PNG.
    icon = (target / "resources" / "images" / "launcher_icon.png").read_bytes()
    assert icon[:8] == b"\x89PNG\r\n\x1a\n"

    # App source references the view.
    app_mc = (target / "source" / "MyFaceApp.mc").read_text(encoding="utf-8")
    assert "MyFaceView" in app_mc


def test_refuses_non_empty_without_force(tmp_path: Path) -> None:
    generate_project(name="MyFace", app_type="watchface", out=tmp_path)
    with pytest.raises(FileExistsError):
        generate_project(name="MyFace", app_type="watchface", out=tmp_path)
    # --force overwrites.
    target = generate_project(
        name="MyFace", app_type="watchface", out=tmp_path, force=True
    )
    assert (target / "manifest.xml").is_file()


@pytest.mark.parametrize("bad", ["1abc", "my-face", "my face", "my_face", "", "a b"])
def test_invalid_names_rejected(tmp_path: Path, bad: str) -> None:
    with pytest.raises(ValueError):
        generate_project(name=bad, app_type="watchface", out=tmp_path)


def test_version_flag() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "ciq_scaffold.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "0.1.0" in proc.stdout


def test_cli_invalid_name_rejected(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "ciq_scaffold.cli", "new", "1bad", "--type", "watchface",
         "--out", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_package_version() -> None:
    assert __version__ == "0.1.0"
