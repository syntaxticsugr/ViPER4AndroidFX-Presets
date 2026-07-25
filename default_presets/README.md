<div align="center">

# Default Presets

The ViPER4Android baseline — every effect at its ViPER default.

`xml` and `json_v1` ship one baseline per output mode; `json_v2` is
device-agnostic (the modes were merged) and ships a single baseline.

| Suffix | Mode   | Output                  |
| ------ | ------ | ----------------------- |
| `m1`   | Mode 1 | Headset, Bluetooth, USB |
| `m2`   | Mode 2 | Speaker                 |

</div>

<br>

## Formats

| Folder                | Format                | Used by                                                                                                                                          | App                         |
| --------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------- |
| [`xml/`](xml)         | Legacy `.xml` `<map>` | ViPER4Android **2.7.2.x**                                                                                                                        | `com.pittvandewitt.viperfx` |
| [`json_v1/`](json_v1) | v1 flat `.json`       | The modern rewrite, **until** [`c4d160d`](https://github.com/likelikeslike/ViPER4Android/commit/c4d160d90689c175fb669fa06d45a77bbd0b9560)        | `com.llsl.viper4android`    |
| [`json_v2/`](json_v2) | v2 grouped `.json`    | The modern rewrite, **from** [`7f1f07c`](https://github.com/likelikeslike/ViPER4Android/commit/7f1f07c1c288d54446eae8d1b145653daa4de3ee) onwards | `com.llsl.viper4android`    |

### `xml/`

- `default_m{1,2}.xml` — the baseline presets in the legacy `<map>` layout.
- `m{1,2}_keys.txt` — the parameter-id ↔ effect-name map for each mode (which
  numeric `name="…"` id drives which effect).

### `json_v1/`

- `default_m{1,2}.json` — the same baselines in the v1 flat schema. Speaker
  (`m2`) keys use the `spk*` prefix.

### `json_v2/`

- `default.json` — the baseline in the v2 grouped schema. v2 is device-agnostic,
  so there is a single file rather than one per mode.
