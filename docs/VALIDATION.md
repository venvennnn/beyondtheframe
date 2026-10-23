# Version 2 validation

The sports redesign removes the detective experience, replaces rendered-only overlays with selectable per-frame tracks, and adds remote player switching, smoothed follow view, a local question panel and passing-decision replay.

## Automated checks

Eleven core tests cover nearest-frame synchronization; missing observations and cut boundaries; metric-calibration fallback; appearance-group recipient filtering; reaction/speed assumptions; absence of visible obstacles; unavailable selected tracks; anonymous identity handling; malformed/hash/field validation; duplicate IDs/backward segments; and inversion of valid field calibration for reachable-region overlays.

`scripts/qa.cjs` exercises real bundled tracks in headless Chrome: player changes by buttons and D-pad, playing follow view, movement summaries, predefined and typed questions, choice lock, hypothetical and actual replay, comparison, field view, saved moments, focus restoration and mobile overflow.

`scripts/qa-import.cjs` checks wrong-video rejection, matching imported coordinates, absent calibration, restoring the bundled demo and a browser rendering of the TV layout. Schema fixtures exist only inside that test; they are not shipped as detections.

Final results and data-generation measurements are recorded in `artifacts/v2-verification.json` once executed. Screenshots with the `v2-` prefix are browser captures.

## Device limits

The debug APK is compiled, aligned and signature-verified separately from runtime testing. No Fire TV device, Android TV emulator or official Amazon cloud-device session has been run in this workspace. Native D-pad forwarding, hardware decode, WebView compatibility, fullscreen and the on-screen keyboard still require device QA. Use the cloud Fire TV instructions in `DEVICE-SETUP.md`; the local Vega SDK does not run on Windows, and this Fire OS APK is not a Vega package.

## Real friction observations

| Observation | Impact | Resolution |
|---|---|---|
| User rejected the prior dashboard-like match UI | The video did not feel like a TV tactical experience | Rebuilt as full-screen video with floating tactical controls based on the supplied references |
| Prior attachment included a rendered tracking replay but no raw JSON | Could not switch recorded selection in that replay | Ran the GPU studio profile to generate selectable coordinates |
| Full multi-model inference was impractically slow on CPU | Approximately tens of seconds per source frame in the first trial | Set up CUDA processing on the available RTX 4050 |
| Team identity is not verified by a detector box | Passing recommendations could misidentify recipients | Added explicitly tentative appearance groups and restricted metric claims to calibrated observations |

Future feedback template — fill only after real observation:

| Date / device / tester | Action | Observed friction | Evidence | Severity | Follow-up |
|---|---|---|---|---|---|
