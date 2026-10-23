# Beyond The Frame — The Tactical Studio

Version 2 focuses entirely on football. The full-screen video interface follows the supplied design references: cyan passing lanes, tracked-player boxes and trails, a gold choice-lock state, actual/hypothetical replays, and a tactical question panel. Library and settings dialogs retain a white interface. The movie/detective experience and its media have been removed from the application.

## Run

```powershell
npm start
```

Open http://127.0.0.1:4173. No frontend dependencies, API keys or cloud backend are needed. Use Node 18+.

The signed Fire OS development APK is `artifacts/Beyond-The-Frame-debug.apk`. Install it over version 1 using `adb install -r`. Version code 2 preserves the Android package name. Compilation is separate from device verification: **no Fire TV or official cloud-device run has been performed here.** See [device setup](docs/DEVICE-SETUP.md), including Amazon's cloud-hosted Fire TV virtual devices, which can be used from Windows.

## Use the studio

1. The supplied clip opens at 3.2 seconds, paused. Select a player from the bottom strip or **All players**. These numbers are anonymous track IDs, not verified jersey numbers or identities.
2. While focus is on a player chip, press Left/Right on the remote to immediately change the selected player. Dedicated previous/next buttons also work. **All players** can seek to the first/next observation of a track that is currently out of view.
3. Select **Follow player**, then play. The crop follows the selected detection with a smoothed camera. Selected-player trails cover recent observations in the same camera shot. Missing observations clear the crop rather than inventing a position.
4. Choose **Freeze this moment** and pick A, B or C. The choice locks in gold. Watch the actual footage, animate the hypothetical straight passing lane on frozen positions, or compare the alternatives.
5. Open **Ask the frame**. Select a question with the remote or type one. Questions about what to do next, passing options, space, movement and identity are answered by local rules and measurements, citing the frame and track IDs. This is not an online LLM or speech assistant.
6. **Movement** shows available recent samples and approximate field path when calibrated. Screen movement includes camera motion. Calibration jitter can inflate distances; these are not validated athletic speed statistics.
7. **Space & timing** lets you vary ball speed and defender reaction. Defender speed defaults to 7 m/s. **Field view** uses accepted calibration only; unavailable segments retain a clear fallback.

## Data and honesty

The bundled video is the user's original football clip. Raw player coordinates are generated locally using the automatic pipeline adapted from notebook (4), not manually drawn or inferred from the reference screenshots. The app draws and synchronizes its own overlays; player selection is no longer restricted to the old rendered #3 replay.

The offline pipeline detects players/ball/pitch keypoints, tracks with BoT-SORT, detects cuts, estimates homographies and propagates accepted calibration for short intervals. Version 2 adds tentative two-group jersey-appearance clustering from torso LAB colors. Appearance groups are not verified team assignments. Candidate recipients are drawn from the selected appearance group when available; unknown groups remain exploratory.

Metric passing calculations require accepted field calibration and both track field coordinates. Otherwise the app uses labelled screen-space corridors without metric distance or arrival-time claims. No off-screen players, pass-completion probabilities, expected goals or certain match outcomes are invented. The hypothetical replay animates a ball along a straight lane on a frozen frame; it is not a generated alternate match video. Scorer identity is unverified.

See [provenance](docs/PROVENANCE.md), [schema](docs/SCHEMA.md), [validation](docs/VALIDATION.md) and [demo script](docs/DEMO.md).

## Regenerate analysis

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install -r pipeline/requirements.txt
.\.venv\Scripts\python pipeline/analyze.py "path\to\clip.mp4" --out analysis --device cpu --threads 4 --studio
```

Use a compatible CUDA PyTorch installation and `--device 0` for practical throughput. The football models are large; CPU processing can be very slow. Models download from the same public sources used by the supplied notebook. The bundled studio profile uses per-frame player inference at 640 pixels and pitch anchors every five frames at 640/1280 pixels, with FP16 CUDA inference. It skips ball inference and claims no ball possession or scorer attribution. Omit `--studio` to run the slower full notebook pipeline, including ball detection. Import the video and its `analysis/analysis.json` from Your clips. The app verifies the exact video SHA-256, duration, timeline and coordinate schema before accepting data.

For the bundled clip, copy a successful output to `web/assets/football-analysis.json` before packaging. Model hashes, Ultralytics version, source-video hash and pipeline version are recorded in the output. Review model/dataset and Ultralytics licensing before redistribution.

## Build and test

```powershell
node --test tests/core.test.cjs
node --check web/app.js
powershell -ExecutionPolicy Bypass -File scripts/setup-android.ps1
powershell -ExecutionPolicy Bypass -File scripts/build-android.ps1
```

The build uses local JDK 17, Android API 35, aapt, javac, D8, zipalign and apksigner. The host is a lean Java Android activity with a local HTTPS asset origin, byte-range media responses, native fullscreen, file chooser and remote-key forwarding. APKs request no internet permission. Hardware decoding, WebView compatibility and IME behavior still require Fire TV testing. This APK targets Fire OS, not Vega OS.

`scripts/qa.cjs` and `scripts/qa-import.cjs` exercise the app in headless Chrome. They currently use this workstation's bundled Playwright and Chrome paths; adjust those on another machine. Screenshots in `artifacts/v2-*.png` are browser captures, not Fire TV captures.

| Directory | Purpose |
|---|---|
| `web/` | Full-screen sports UI, synchronized overlays, assistant, geometry and remote navigation |
| `android/` | Offline Fire OS package host |
| `pipeline/` | Automatic inference, appearance grouping and v1 JSON export |
| `scripts/` | Server, browser QA, branding and APK setup/build |
| `tests/` | Synchronization, cut/gap boundaries, geometry and data validation |
| `artifacts/` | APK and current screenshots |

The original user-supplied football clip contains broadcast footage. No public deployment has been made, and redistribution permission has not been established. Confirm rights or replace the footage before distributing the APK publicly.
