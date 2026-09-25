# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- `ciq-scaffold new` accepts repeatable `--device <id>` to target more than the
  default `instinct2` (e.g. `--device instinct2 --device instinct2s`). The
  generated `manifest.xml` `iq:products` lists every selected device, and the
  generated project README points `monkeyc -d` at the first target. Unknown
  ids are refused with the allowed list. Supported ids (Instinct 2 family):
  `instinct2`, `instinct2s`, `instinct2x`; see README for details.

### Fixed

- Launcher icon now lives at `resources/drawables/launcher_icon.png` and
  `drawables.xml` references it as `filename="launcher_icon.png"` (relative
  to the XML file), so `monkeyc` resolves it.
- Placeholder launcher icon is a real 62x62 PNG matching the Instinct 2
  launcher icon size, so no scaling warning and no missing-bitmap error.
- App and View templates use `import Toybox.X;` (with `import Toybox.Lang;`)
  instead of `using Toybox.X;`, bringing type names like `Views`,
  `InputDelegates`, and `Dc` into scope.
- `getInitialView` now has the correct signature
  `function getInitialView() as [Views] or [Views, InputDelegates]` and
  returns `[new <Prefix>View()]` (views have no static `create()`).
- Removed invalid device ids `instinct2_solar` and
  `instinct2_solar_tactical` (not real SDK ids; Solar/Tactical models use
  `instinct2` / `instinct2s` / `instinct2x`).

## [0.1.0]

### Added

- `ciq-scaffold new <name> --type <watchface|datafield|widget|app> [--out DIR] [--force]`
  generator emitting the official Connect IQ SDK project structure
  (`manifest.xml`, `source/`, `resources/`, `monkey.jungle`, project `README.md`).
- `ciq-scaffold --version`.
- Name validation (letters/digits, starts with a letter) and PascalCase class prefix derivation.
- Refusal to overwrite a non-empty target directory without `--force`.
- Placeholder UUID app id (random uuid4, commented as placeholder) and Instinct 2 product target.
- pytest suite covering all four types, manifest/resource XML parsing, overwrite and
  name validation, and `--version`.
- GitHub Actions CI: pytest on Ubuntu Python 3.9–3.13 plus a macOS job.
