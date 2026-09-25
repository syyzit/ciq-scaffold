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
ciq-scaffold --version
```

- `<name>`: letters and digits only, must start with a letter (e.g. `MyFace`).
- `--type`: one of `watchface`, `datafield`, `widget`, `app`.
- `--out DIR`: parent directory for the new project (default: current directory).
- `--force`: allow overwriting a non-empty target directory. Without it, a non-empty
  target is refused.

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

Target device is `instinct2` (Instinct 2). A `--device` flag for more targets is a later milestone.

## Building a generated project

Requires the official Connect IQ SDK:

```sh
monkeyc -d instinct2 -f monkey.jungle -o bin/MyFace.prg -y <developer_key>
```

Then run `bin/MyFace.prg` in the Connect IQ simulator with the Instinct 2 profile.

## Official docs

- Garmin Connect IQ SDK: <https://developer.garmin.com/connect-iq/sdk/>

## License

MIT — see [LICENSE](LICENSE).
