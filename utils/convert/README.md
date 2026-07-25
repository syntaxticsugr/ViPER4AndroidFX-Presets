# Old XML → New XML

- `v` = raw/old-scale value.
- Observed = `(min, max, step)` of raw values across ~3,400 real presets. `*` = irregular step.
- `identity` = value copied unchanged.

| Feature                          | Key (new ← old) | Observed (min, max, step) | Formula                                                                                 | Output Range (Min-Max) | In Range?   |
| -------------------------------- | --------------- | ------------------------- | --------------------------------------------------------------------------------------- | ---------------------- | ----------- |
| Mode (headphone / speaker)       | `32775`         | (1, 2, 1)                 | identity                                                                                | 1-2                    | ✓           |
| Master Limiter – output gain     | `65586 ← 65608` | (10, 200, 10)             | index in `[1,5,10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200]` | 0–21                   | ✓           |
| Master Limiter – channel pan     | `65587`         | (0, 40, *)                | `(v + 100) / 2`                                                                         | 0–100                  | ✓           |
| Master Limiter – threshold       | `65588 ← 65609` | (30, 100, 10)             | index in `[30,50,70,80,90,100]`                                                         | 0–5                    | ✓           |
| Playback Gain – strength         | `65566 ← 65605` | (50, 300, 50)             | index in `[50,100,300]`                                                                 | 0–2                    | ✓           |
| Playback Gain – output threshold | `65567 ← 65606` | (50, 100, 10)             | index in `[30,50,70,80,90,100]`                                                         | 0–5                    | ✓           |
| Playback Gain – max gain         | `65568 ← 65607` | (100, 3000, 100)          | index in `[100,200,300,400,500,600,700,800,900,1000,3000]`                              | 0–10                   | ✓           |
| FET Compressor – threshold       | `65611 ← 65628` | (0, 100, *)               | identity                                                                                | 0–100                  | ✓           |
| FET Compressor – ratio           | `65612 ← 65629` | (0, 100, *)               | identity                                                                                | 0–100                  | ✓           |
| FET Compressor – knee            | `65613 ← 65630` | (0, 100, 2)               | identity                                                                                | 0–100                  | ✓           |
| FET Compressor – gain            | `65615 ← 65632` | (0, 76, *)                | identity                                                                                | 0–100                  | ✓           |
| FET Compressor – attack          | `65617 ← 65634` | (20, 100, *)              | identity                                                                                | 0–100                  | ✓           |
| FET Compressor – release         | `65619 ← 65636` | (30, 89, *)               | identity                                                                                | 0–100                  | ✓           |
| FET Compressor – knee multi      | `65621 ← 65638` | (0, 100, *)               | identity                                                                                | 0–100                  | ✓           |
| FET Compressor – max attack      | `65622 ← 65639` | (42, 100, *)              | identity                                                                                | 0–100                  | ✓           |
| FET Compressor – max release     | `65623 ← 65640` | (23, 100, *)              | identity                                                                                | 0–100                  | ✓           |
| FET Compressor – crest           | `65624 ← 65641` | (0, 100, *)               | identity                                                                                | 0–300                  | ✓           |
| FET Compressor – adapt           | `65625 ← 65642` | (27, 100, *)              | identity                                                                                | 0–100                  | ✓           |
| Spectrum Extension – strength    | `65549;65550`   | (0, 100, *)               | identity                                                                                | 0–100                  | ✓           |
| Convolver – cross channel        | `65543 ← 65594` | (0, 100, *)               | identity                                                                                | 0–100                  | ✓           |
| Field Surround – coeffs/width    | `65554;65556`   | (120, 200, 10)            | `(v − 120) / 10`                                                                        | 0–8                    | ✓           |
| Field Surround – mid image       | `65555`         | (100, 200, 10)            | `(v − 100) / 10`                                                                        | 0–10                   | ✓           |
| Differential Surround – delay    | `65558`         | (200, 2000, 100)          | `(v / 100) − 1`                                                                         | 0–19                   | ✓           |
| Headphone Surround – quality     | `65545`         | (0, 4, 1)                 | identity                                                                                | 0–4                    | ✓           |
| Reverberation – room size        | `65560 ← 65598` | (0, 100, *)               | `v / 10`                                                                                | 0–10                   | ✓           |
| Reverberation – room width       | `65561 ← 65599` | (0, 100, *)               | `v / 10`                                                                                | 0–10                   | ✓           |
| Reverberation – damp             | `65562 ← 65600` | (0, 100, *)               | identity                                                                                | 0–100                  | ✓           |
| Reverberation – wet              | `65563 ← 65601` | (0, 100, *)               | identity                                                                                | 0–100                  | ✓           |
| Reverberation – dry              | `65564 ← 65602` | (0, 100, *)               | identity                                                                                | 0–100                  | ✓           |
| Dynamic System – strength        | `65573`         | (0, 2100, *)              | `(v − 100) / 20`                                                                        | 0–100                  | raw 0 → −5  |
| ViPER Bass – cutoff freq         | `65576`         | (0, 150, *)               | `v − 15`                                                                                | 0–135                  | raw 0 → −15 |
| ViPER Bass – strength            | `65577`         | (50, 600, 50)             | `(v − 50) / 50`                                                                         | 0–11                   | ✓           |
| ViPER Bass – mode                | `65575`         | (0, 2, 1)                 | identity                                                                                | 0–2                    | ✓           |
| ViPER Clarity – strength         | `65580`         | (0, 450, 50)              | `v / 50`                                                                                | 0–9                    | ✓           |
| ViPER Clarity – mode             | `65579`         | (0, 2, 1)                 | identity                                                                                | 0–2                    | ✓           |
| Cure – crossfeed                 | `65582`         | (0, 2, 1)                 | identity                                                                                | 0–2                    | ✓           |
| AnalogX – mode                   | `65585`         | (0, 2, 1)                 | identity                                                                                | 0–2                    | ✓           |

## Cleanup

**Old ID → new ID migration**

Numeric-param renames are already the table's `Key (new ← old)` column. Only these **non-numeric** params (enables / EQ / kernel — not in the table) are additionally migrated:

- `65604→65565` (playback enable)
- `65627→65610` (FET enable) · `65631→65614`, `65633→65616`, `65635→65618`, `65637→65620` (FET auto knee/gain/attack/release) · `65643→65626` (FET no-clip)
- `65595→65551`, `65596→65552` (FIR EQ enable + bands)
- `65589→65538` (convolver enable) · `65591;65592;65593→65540;65541;65542` (convolver kernel)
- `65597→65559` (reverb enable)

**Convolver kernel name cleaning** (`65540;65541;65542`)

- Fix `&`-encoding corruption in `.irs` filenames: `></string>amp;` → `&amp;`, `>…file</string>amp;` → `&amp;`.
- Blank out placeholder kernel names: `Select impulse response file`, `Kernel`, `Choose Impulse Response`, `Selecione o arquivo de impulso de resposta`.

<br>
<br>

# New XML → JSON V2 [7f1f07c](https://github.com/likelikeslike/ViPER4Android/commit/7f1f07c1c288d54446eae8d1b145653daa4de3ee)

- `v` = the XML **output** value from the table above (i.e. Observed here = XML Output Range).
- Output Range (Min-Max) = the app's slider `valueRange` in `EffectSections.kt` at `5b08d15`.
- `index → [list]` means JSON = `list[v]` (un-normalizes the XML index back to a real value).

| Feature                          | JSON field                            | Observed (min-max) | Formula (XML → JSON)                                                                   | Output Range (Min-Max) | In Range?   |
| -------------------------------- | ------------------------------------- | ------------------ | -------------------------------------------------------------------------------------- | ---------------------- | ----------- |
| Master Limiter – output gain     | `masterLimiter.outputVolume`          | 0–21               | index → `[1,5,10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200]` | 1–200                  | ✓           |
| Master Limiter – channel pan     | `masterLimiter.channelPan`            | 0–100              | `2v − 100`                                                                             | -100–100               | ✓           |
| Master Limiter – threshold       | `masterLimiter.threshold`             | 0–5                | index → `[30,50,70,80,90,100]`                                                         | 30–100                 | ✓           |
| Playback Gain – strength         | `playbackGainControl.strength`        | 0–2                | index → `[50,100,300]`                                                                 | 50–300                 | ✓           |
| Playback Gain – output threshold | `playbackGainControl.outputThreshold` | 0–5                | index → `[30,50,70,80,90,100]`                                                         | 30–100                 | ✓           |
| Playback Gain – max gain         | `playbackGainControl.maxGain`         | 0–10               | index → `[100,200,300,400,500,600,700,800,900,1000,3000]`                              | 100–1000               | v=10 → 3000 |
| FET Compressor – threshold       | `fetCompressor.threshold`             | 0–100              | `−0.6·v` (dB)                                                                          | -48–0                  | v>80 → <−48 |
| FET Compressor – ratio           | `fetCompressor.ratio`                 | 0–100              | identity                                                                               | 0–200                  | ✓           |
| FET Compressor – knee            | `fetCompressor.knee`                  | 0–100              | `0.6·v` (dB)                                                                           | 0–12                   | v>20 → >12  |
| FET Compressor – gain            | `fetCompressor.gain`                  | 0–100              | `0.6·v` (dB)                                                                           | 0–24                   | v>40 → >24  |
| FET Compressor – attack          | `fetCompressor.attack`                | 0–100              | identity                                                                               | 1–100                  | ✓           |
| FET Compressor – release         | `fetCompressor.release`               | 0–100              | identity                                                                               | 5–500                  | ✓           |
| FET Compressor – knee multi      | `fetCompressor.kneeMulti`             | 0–100              | identity                                                                               | 0–100                  | ✓           |
| FET Compressor – max attack      | `fetCompressor.maxAttack`             | 0–100              | identity                                                                               | 1–100                  | ✓           |
| FET Compressor – max release     | `fetCompressor.maxRelease`            | 0–100              | identity                                                                               | 5–500                  | ✓           |
| FET Compressor – crest           | `fetCompressor.crest`                 | 0–300              | identity                                                                               | 5–300                  | v<5 → <5    |
| FET Compressor – adapt           | `fetCompressor.adapt`                 | 0–100              | identity                                                                               | 0–200                  | ✓           |
| Spectrum Extension – strength    | `spectrumExtension.strength`          | 0–100              | `2200 + 60·v` (Hz)                                                                     | 2200–8200              | ✓           |
| Convolver – cross channel        | `convolver.crossChannel`              | 0–100              | identity                                                                               | 0–100                  | ✓           |
| Field Surround – widening        | `fieldSurround.widening`              | 0–8                | identity                                                                               | 0–8                    | ✓           |
| Field Surround – mid image       | `fieldSurround.midImage`              | 0–10               | identity                                                                               | 0–10                   | ✓           |
| Field Surround – depth           | `fieldSurround.depth`                 | 0–10               | identity                                                                               | 0–10                   | ✓           |
| Differential Surround – delay    | `diffSurround.delay`                  | 0–19               | `v + 1`                                                                                | 1–20                   | ✓           |
| Headphone Surround – quality     | `headphoneSurround.quality`           | 0–4                | identity                                                                               | 0–4                    | ✓           |
| Reverberation – room size        | `reverb.roomSize`                     | 0–10               | identity                                                                               | 0–10                   | ✓           |
| Reverberation – room width       | `reverb.width`                        | 0–10               | identity                                                                               | 0–10                   | ✓           |
| Reverberation – damp             | `reverb.damp`                         | 0–100              | `v / 10`                                                                               | 0–10                   | ✓           |
| Reverberation – wet              | `reverb.wet`                          | 0–100              | identity                                                                               | 0–100                  | ✓           |
| Reverberation – dry              | `reverb.dry`                          | 0–100              | identity                                                                               | 0–100                  | ✓           |
| Dynamic System – strength        | `dynamicSystem.strength`              | 0–100              | identity                                                                               | 0–100                  | ✓           |
| ViPER Bass – cutoff freq         | `bass.frequency`                      | 0–135              | identity                                                                               | 0–135                  | ✓           |
| ViPER Bass – strength            | `bass.gain`                           | 0–11               | `50·v + 50`                                                                            | 50–1000                | ✓           |
| ViPER Bass – mode                | `bass.mode`                           | 0–2                | identity                                                                               | 0–2                    | ✓           |
| ViPER Clarity – strength         | `clarity.gain`                        | 0–9                | `50·v`                                                                                 | 0–450                  | ✓           |
| ViPER Clarity – mode             | `clarity.mode`                        | 0–2                | identity                                                                               | 0–2                    | ✓           |
| Cure – crossfeed                 | `cure.crossfeedPreset`                | 0–2                | identity                                                                               | 0–N                    | ✓           |
| AnalogX – mode                   | `analogX.mode`                        | 0–2                | identity                                                                               | 0–2                    | ✓           |
