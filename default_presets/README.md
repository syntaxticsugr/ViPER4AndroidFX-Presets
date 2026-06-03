<div align="center">

# Default Presets

Baseline ViPER4Android presets, one per output mode, with `Master Limiter` &
`Playback Gain Control` left at ViPER defaults.

| Suffix | Mode   | Output                  |
| ------ | ------ | ----------------------- |
| `m1`   | Mode 1 | Headset, Bluetooth, USB |
| `m2`   | Mode 2 | Speaker                 |

</div>

<br>

## Formats

| Folder          | Format                | Used by                               | App                         |
| --------------- | --------------------- | ------------------------------------- | --------------------------- |
| [`xml/`](xml)   | Legacy `.xml` `<map>` | ViPER4Android **2.7.2.x** and earlier | `com.pittvandewitt.viperfx` |
| [`json/`](json) | New `.json`           | The modern ViPER4Android rewrite      | `com.llsl.viper4android`    |

### `xml/`

- `default_m{1,2}.xml` — the baseline presets in the legacy `<map>` layout.
- `m{1,2}_keys.txt` — the parameter-id ↔ effect-name map for each mode (which
  numeric `name="…"` id drives which effect).

### `json/`

- `default_m{1,2}.json` — the same baselines in the new format.
