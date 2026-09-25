# ciq-scaffold

A small public MIT Python CLI that generates a starter Garmin Connect IQ project skeleton.
Think "create-react-app for Connect IQ", but thin and honest: it emits only the official
Connect IQ SDK project structure.

## What it is

- A `ciq-scaffold new <name> --type <watchface|datafield|widget|app>` generator.
- Output is a minimal project tree (`manifest.xml`, `source/`, `resources/`, `monkey.jungle`)
  that you build with the official Garmin Connect IQ SDK.

## What it is not

- Not a compiler, simulator, or SDK replacement. You need the official Connect IQ SDK
  (`monkeyc` and the simulator) to build and run generated projects.
- No firmware hacking, no exploits, no device-side tricks. No downloading of the SDK.
- No on-device testing claims: generated projects are uncompiled skeletons.

## Install

Not on PyPI yet. For now:

```sh
pip install -e .
```

With dev/test extras:

```sh
pip install -e '.[dev]'
```

Requires Python 3.9+.

## Usage

```sh
ciq-scaffold new MyFace --type watchface
ciq-scaffold new MyField --type datafield --out /tmp/ciq --force
ciq-scaffold new MyFace --type watchface --device instinct2 --device instinct2s
ciq-scaffold --version
```

- `<name>`: letters and digits only, must start with a letter (e.g. `MyFace`).
- `--type`: one of `watchface`, `datafield`, `widget`, `app`.
- `--out DIR`: parent directory for the new project (default: current directory).
- `--force`: allow overwriting a non-empty target directory. Without it, a non-empty
  target is refused.
- `--device ID`: target device product id; repeat the flag for multiple devices
  (default: `instinct2`). Unknown ids are refused with the allowed list.
  See [Supported devices](#supported-devices).

## Generated tree

For `ciq-scaffold new MyFace --type watchface`:

```
MyFace/
├── manifest.xml                 # Connect IQ manifest (placeholder app id — replace with your own)
├── monkey.jungle                # project.manifest = manifest.xml
├── README.md                    # build/run instructions (official SDK)
├── resources/
│   ├── strings/strings.xml      # AppName
│   ├── layouts/layout.xml       # minimal layout
│   ├── drawables/drawables.xml  # LauncherIcon bitmap
│   └── images/launcher_icon.png # tiny placeholder icon
└── source/
    ├── MyFaceApp.mc             # Toybox.Application.AppBase subclass
    └── MyFaceView.mc            # WatchFace view
```

The view base class depends on `--type`:

| `--type`   | Manifest `type` | View base class      |
|------------|-----------------|----------------------|
| watchface  | watchface       | `WatchUi.WatchFace`  |
| datafield  | datafield       | `WatchUi.DataField`  |
| widget     | widget          | `WatchUi.View`       |
| app        | watch-app       | `WatchUi.View`       |

## Supported devices

`--device` accepts a small curated subset of the Instinct 2 family
(the generated `manifest.xml` `iq:products` lists every selected id):

| `--device` id              | Device                          |
|----------------------------|---------------------------------|
| `instinct2` (default)      | Instinct 2                      |
| `instinct2s`               | Instinct 2S                     |
| `instinct2x`               | Instinct 2X Solar               |
| `instinct2_solar`          | Instinct 2 Solar                |
| `instinct2_solar_tactical` | Instinct 2 Solar, Tactical ed.  |

Ids follow the Connect IQ SDK's `devices.xml` product naming; verify
against your installed SDK before building. Need another target?
File an issue — the list is intentionally small for now.

## Building a generated project

Requires the official Connect IQ SDK:

```sh
monkeyc -d instinct2 -f monkey.jungle -o bin/MyFace.prg -y <developer_key>
```

Repeat with `-d <id>` for each target device. Then run `bin/MyFace.prg`
in the Connect IQ simulator with the matching device profile.

## Official docs

- Garmin Connect IQ SDK: <https://developer.garmin.com/connect-iq/sdk/>

## License

MIT — see [LICENSE](LICENSE).
