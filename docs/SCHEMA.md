# Analysis JSON v1.0 — sports pipeline v2

The client imports `version: "1.0"`, `coordinateSystem: "normalized-image"`, `video`, `provenance` and timestamped `frames`. The JSON schema version stays 1.0; the producing pipeline is version 2.0.

| Record | Fields |
|---|---|
| video | name, sha256 (64 lowercase hex characters), duration seconds, width, height, fps |
| provenance | kind, source, pipelineVersion, models, appearanceGrouping, limitations |
| frame | time seconds, segment integer, calibration, tracks, balls |
| calibration | valid, homography image pixels → meters or null, quality, assumedPitchMeters [105,68] |
| track | id integer, box [x1,y1,x2,y2] normalized to 0–1, confidence, field [x,y] meters or null, team (tentative appearance-group string or null) |
| ball | normalized image [x,y], confidence |
| scorer | uncertain inherited heuristic status and reason; never a verified identity |

The app verifies source hash and duration, rejects malformed or duplicate tracks, backward segments and invalid timestamps, and requires accepted calibration for field coordinates. Nearest-frame lookup tolerates half a video frame plus rounding error. Observations are not held through missing frames. Trails never bridge missing observations or camera cuts. Follow camera smoothing resets on cuts, seeks and player changes.

Passing options use tracks from the same tentative appearance group if available. Opposite known groups are geometric obstacles. When appearance groups are unknown, the interface labels the choices exploratory. Screen-space corridors do not produce meters or arrival-time claims.

The metric model samples 48 points along the passing lane and compares constant-speed ground-ball arrival with each visible obstacle's straight-line arrival after a reaction delay. Default ball speed 18 m/s, reaction .4 s, defender speed 7 m/s. Labels are interpretable assumptions, not calibrated probabilities or forecasts. No visible obstacle is labelled “No visible obstacles”, not certain success.

The local question panel cites playback timestamp and track IDs. It has no external LLM, microphone or transcription dependency. No detective/evidence schema is used by the application.
