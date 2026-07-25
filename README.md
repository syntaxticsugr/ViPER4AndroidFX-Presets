<div align="center">
<h1>ViPER4Android Presets</h1>

<b>Largest collection of DDC(.vdc), Kernel(.irs) & Preset(.xml) for ViPER4Android</b>

[![Release](https://img.shields.io/github/v/release/syntaxticsugr/ViPER4Android-Presets?color=blue&label=Release&style=flat-square)](https://github.com/syntaxticsugr/ViPER4Android-Presets/releases/latest) [![Downloads](https://img.shields.io/github/downloads/syntaxticsugr/ViPER4Android-Presets/total?color=brightgrey&label=Downloads&style=flat-square)](https://github.com/syntaxticsugr/ViPER4Android-Presets/releases)

</div>

<br>
<br>

`DDC(.vdc)` & `Kernel(.irs)` files are provided _as is_ from the original authors without any modifications.

`Preset(.xml)` are patched _as & if_ necessary to work on the latest ViPER4Android.

Values of `Master Limiter` & `Playback Gain Control` are set to [ViPER Defaults](https://github.com/syntaxticsugr/ViPER4Android-Presets/tree/main/default_presets) for all `Preset(.xml)`.

<br>

### Release Info

<table>
  <tr><th colspan="2"><a href="https://github.com/syntaxticsugr/ViPER4Android-Presets/releases/latest">v4.0.0</a></th><th>Full</th><th>Lite</th><th>Recommended</th></tr>
  <tr><td colspan="2">⭐</td><td>All <code>Preset</code>s<br>All <code>Kernel</code>s<br>All <code>DDC</code>s</td><td>Unique <code>Preset</code>s<br>Required <code>Kernel</code>s<br>Required <code>DDC</code>s</td><td>Unique <code>Preset</code>s<br>Unique <code>Kernel</code>s<br>Unique <code>DDC</code>s</td></tr>
  <tr><td rowspan="3"><b>Preset</b></td><td><code>XML</code></td><td>1055</td><td>792</td><td>792</td></tr>
  <tr><td><code>JSON_V1</code></td><td>1061</td><td>799</td><td>799</td></tr>
  <tr><td><code>JSON_V2</code></td><td>1028</td><td>774</td><td>774</td></tr>
  <tr><td colspan="2"><b>Kernel</b></td><td>2319</td><td>196</td><td>1716</td></tr>
  <tr><td colspan="2"><b>DDC</b></td><td>627</td><td>45</td><td>580</td></tr>
</table>

<br>

### [How To Use?](https://github.com/syntaxticsugr/ViPER4Android-Presets/discussions/3)

<br>

### Convert Your Own Presets

Got presets in another layout? Convert them faithfully in any direction — legacy / 2.7.2.x `XML` ↔ v1 flat `JSON` ↔ v2 grouped `JSON`.

**1. On-device (Magisk / KernelSU / APatch module)**

Flash the [ViPER4Android Presets Converter](https://github.com/syntaxticsugr/ViPER4Android-Presets-Converter) module. It scans your `Download` folder and writes every preset back in all three formats to `Download/syntaxticsugr/presets/{xml,json_v1,json_v2}` — during flash, no reboot, no system changes.

**2. With the Python here**

- **Batch (full pipeline):** drop your presets into `in/`, run `python main.py`, and collect the packaged result from `out/`. This applies the release flavour (master switch on, output stage pinned to [ViPER defaults](https://github.com/syntaxticsugr/ViPER4Android-Presets/tree/main/default_presets)).

- **Faithful one-off:** use the standalone converter — it carries every value unchanged and adds no flavour:

  ```sh
  python -m utils.convert.convert IN.xml     --target v2               --output OUT.v2.json
  python -m utils.convert.convert IN.v2.json --target xml   --mode 1   --output OUT.xml
  ```

  `--target` (`xml` / `v1` / `v2`) · `--mode` (`1` headphone / `2` speaker — needed for `xml`/`v1` when the source is device-agnostic). The leading `-m` is Python's own "run module" flag, unrelated to `--mode`.

<br>

### Want to share your collection of DDCs, Kernels & Presets?

[Fill this Form :)](https://forms.gle/1JShGMdbTbujJfKQ9)

<br>

## Credits

[![Jadilson Guedes](https://images.weserv.nl/?url=https://github.com/jadilson12.png&h=50&w=50&fit=cover&mask=circle)](https://github.com/jadilson12) [![Joe0Bloggs](https://images.weserv.nl/?url=https://github.com/Joe0Bloggs.png&h=50&w=50&fit=cover&mask=circle)](https://github.com/Joe0Bloggs) [![John Fawkes](https://images.weserv.nl/?url=https://github.com/JohnFawkes.png&h=50&w=50&fit=cover&mask=circle)](https://github.com/JohnFawkes) [![programminghoch10](https://images.weserv.nl/?url=https://github.com/programminghoch10.png&h=50&w=50&fit=cover&mask=circle)](https://github.com/programminghoch10) [![WSTxda](https://images.weserv.nl/?url=https://github.com/WSTxda.png&h=50&w=50&fit=cover&mask=circle)](https://github.com/WSTxda)
