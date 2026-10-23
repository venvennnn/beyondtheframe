from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class SoccerPitchConfiguration:
    width: int = 7000  # [cm]
    length: int = 12000  # [cm]
    penalty_box_width: int = 4100  # [cm]
    penalty_box_length: int = 2015  # [cm]
    goal_box_width: int = 1832  # [cm]
    goal_box_length: int = 550  # [cm]
    centre_circle_radius: int = 915  # [cm]
    penalty_spot_distance: int = 1100  # [cm]

    @property
    def vertices(self) -> List[Tuple[int, int]]:
        return [
            (0, 0),  # 1
            (0, (self.width - self.penalty_box_width) / 2),  # 2
            (0, (self.width - self.goal_box_width) / 2),  # 3
            (0, (self.width + self.goal_box_width) / 2),  # 4
            (0, (self.width + self.penalty_box_width) / 2),  # 5
            (0, self.width),  # 6
            (self.goal_box_length, (self.width - self.goal_box_width) / 2),  # 7
            (self.goal_box_length, (self.width + self.goal_box_width) / 2),  # 8
            (self.penalty_spot_distance, self.width / 2),  # 9
            (self.penalty_box_length, (self.width - self.penalty_box_width) / 2),  # 10
            (self.penalty_box_length, (self.width - self.goal_box_width) / 2),  # 11
            (self.penalty_box_length, (self.width + self.goal_box_width) / 2),  # 12
            (self.penalty_box_length, (self.width + self.penalty_box_width) / 2),  # 13
            (self.length / 2, 0),  # 14
            (self.length / 2, self.width / 2 - self.centre_circle_radius),  # 15
            (self.length / 2, self.width / 2 + self.centre_circle_radius),  # 16
            (self.length / 2, self.width),  # 17
            (
                self.length - self.penalty_box_length,
                (self.width - self.penalty_box_width) / 2
            ),  # 18
            (
                self.length - self.penalty_box_length,
                (self.width - self.goal_box_width) / 2
            ),  # 19
            (
                self.length - self.penalty_box_length,
                (self.width + self.goal_box_width) / 2
            ),  # 20
            (
                self.length - self.penalty_box_length,
                (self.width + self.penalty_box_width) / 2
            ),  # 21
            (self.length - self.penalty_spot_distance, self.width / 2),  # 22
            (
                self.length - self.goal_box_length,
                (self.width - self.goal_box_width) / 2
            ),  # 23
            (
                self.length - self.goal_box_length,
                (self.width + self.goal_box_width) / 2
            ),  # 24
            (self.length, 0),  # 25
            (self.length, (self.width - self.penalty_box_width) / 2),  # 26
            (self.length, (self.width - self.goal_box_width) / 2),  # 27
            (self.length, (self.width + self.goal_box_width) / 2),  # 28
            (self.length, (self.width + self.penalty_box_width) / 2),  # 29
            (self.length, self.width),  # 30
            (self.length / 2 - self.centre_circle_radius, self.width / 2),  # 31
            (self.length / 2 + self.centre_circle_radius, self.width / 2),  # 32
        ]

    edges: List[Tuple[int, int]] = field(default_factory=lambda: [
        (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (7, 8),
        (10, 11), (11, 12), (12, 13), (14, 15), (15, 16),
        (16, 17), (18, 19), (19, 20), (20, 21), (23, 24),
        (25, 26), (26, 27), (27, 28), (28, 29), (29, 30),
        (1, 14), (2, 10), (3, 7), (4, 8), (5, 13), (6, 17),
        (14, 25), (18, 26), (23, 27), (24, 28), (21, 29), (17, 30)
    ])

    labels: List[str] = field(default_factory=lambda: [
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
        "11", "12", "13", "15", "16", "17", "18", "20", "21", "22",
        "23", "24", "25", "26", "27", "28", "29", "30", "31", "32",
        "14", "19"
    ])

    colors: List[str] = field(default_factory=lambda: [
        "#FF1493", "#FF1493", "#FF1493", "#FF1493", "#FF1493", "#FF1493",
        "#FF1493", "#FF1493", "#FF1493", "#FF1493", "#FF1493", "#FF1493",
        "#FF1493", "#00BFFF", "#00BFFF", "#00BFFF", "#00BFFF", "#FF6347",
        "#FF6347", "#FF6347", "#FF6347", "#FF6347", "#FF6347", "#FF6347",
        "#FF6347", "#FF6347", "#FF6347", "#FF6347", "#FF6347", "#FF6347",
        "#00BFFF", "#00BFFF"
    ])


'Beyond The Frame: clip-level tracking, approximate moving-camera field mapping, exports.'

from pathlib import Path

import json, base64, subprocess, math, hashlib

import cv2

import numpy as np

import pandas as pd

from tqdm.auto import tqdm

def load_video(path, end_s=None):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not cap.isOpened() or fps <= 0:
        raise ValueError('Cannot decode video')
    frames = []
    while True:
        ok, f = cap.read()
        if not ok or (end_s is not None and len(frames) / fps >= end_s):
            break
        frames.append(f)
    cap.release()
    if not frames:
        raise ValueError('No frames decoded')
    return (frames, float(fps))

def project(points, H):
    p = np.asarray(points, np.float64).reshape(-1, 2)
    q = np.c_[p, np.ones(len(p))] @ np.asarray(H).T
    out = np.full((len(p), 2), np.nan)
    ok = np.abs(q[:, 2]) > 1e-09
    out[ok] = q[ok, :2] / q[ok, 2, None]
    return out

def field_lines():
    lines = [[(0, 0), (105, 0), (105, 68), (0, 68), (0, 0)], [(52.5, 0), (52.5, 68)]]
    for x, sgn in [(0, 1), (105, -1)]:
        lines += [[(x, 13.84), (x + sgn * 16.5, 13.84), (x + sgn * 16.5, 54.16), (x, 54.16)], [(x, 24.84), (x + sgn * 5.5, 24.84), (x + sgn * 5.5, 43.16), (x, 43.16)]]
    theta = np.linspace(0, 2 * np.pi, 100)
    lines.append(np.c_[52.5 + 9.15 * np.cos(theta), 34 + 9.15 * np.sin(theta)].tolist())
    return lines

def calibration_preview(frame, H, points=None):
    out = frame.copy()
    inv = np.linalg.inv(H)
    for line in field_lines():
        q = project(line, inv)
        if np.isfinite(q).all() and np.max(np.abs(q)) < 1000000.0:
            cv2.polylines(out, [q.astype(np.int32)], False, (0, 240, 255), 1, cv2.LINE_AA)
    if points is not None:
        for k, (x, y) in enumerate(points):
            cv2.circle(out, (int(x), int(y)), 4, (0, 0, 255), -1)
            cv2.putText(out, str(k + 1), (int(x) + 5, int(y) - 5), 0, 0.5, (255, 255, 255), 1)
    return out

def draw_ids(frame, rows, selected=None):
    out = frame.copy()
    for r in rows.itertuples():
        a = (int(r.x1), int(r.y1))
        b = (int(r.x2), int(r.y2))
        c = (0, 210, 255) if r.id == selected else (225, 160, 55)
        cv2.rectangle(out, a, b, c, 2 if r.id == selected else 1)
        cv2.putText(out, f'#{r.id}', (a[0], max(14, a[1] - 3)), 0, 0.42, c, 1, cv2.LINE_AA)
    return out

def field_mask(frame, boxes=None):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([25, 25, 20]), np.array([100, 255, 255]))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    mask = cv2.erode(mask, np.ones((5, 5), np.uint8))
    mask[:int(frame.shape[0] * 0.14)] = 0
    if boxes is not None:
        for r in boxes.itertuples():
            cv2.rectangle(mask, (max(0, int(r.x1) - 10), max(0, int(r.y1) - 10)), (min(frame.shape[1] - 1, int(r.x2) + 10), min(frame.shape[0] - 1, int(r.y2) + 10)), 0, -1)
    return mask

def estimate_motion(frames, tracks):
    motions = [np.eye(3)]
    quality = [dict(frame=0, inliers=0, error_px=0, valid=True)]
    for i in tqdm(range(1, len(frames)), desc='Camera motion on pitch'):
        a = cv2.cvtColor(frames[i - 1], cv2.COLOR_BGR2GRAY)
        b = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        mask = field_mask(frames[i - 1], tracks[tracks.frame == i - 1])
        p = cv2.goodFeaturesToTrack(a, maxCorners=1200, qualityLevel=0.006, minDistance=5, mask=mask)
        M = None
        n = 0
        err = float('nan')
        if p is not None and len(p) >= 12:
            q, st, _ = cv2.calcOpticalFlowPyrLK(a, b, p, None, winSize=(25, 25), maxLevel=3)
            if q is not None:
                back, stb, _ = cv2.calcOpticalFlowPyrLK(b, a, q, None, winSize=(25, 25), maxLevel=3)
                if back is not None:
                    good = (st.ravel() == 1) & (stb.ravel() == 1) & (np.linalg.norm(back - p, axis=2).ravel() < 1.5)
                    aa = p[good].reshape(-1, 2)
                    bb = q[good].reshape(-1, 2)
                    if len(aa) >= 12:
                        cand, ins = cv2.findHomography(aa, bb, cv2.RANSAC, 2.5)
                        if cand is not None and ins is not None:
                            keep = ins.ravel().astype(bool)
                            n = int(keep.sum())
                            err = float(np.median(np.linalg.norm(project(aa[keep], cand) - bb[keep], axis=1))) if n else float('inf')
                            hh, ww = a.shape
                            corners = np.float32([[0, 0], [ww, 0], [ww, hh], [0, hh]])
                            mapped = project(corners, cand)
                            area = abs(cv2.contourArea(mapped.astype(np.float32))) if np.isfinite(mapped).all() else 0
                            displacement = np.median(np.linalg.norm(mapped - corners, axis=1))
                            if n >= 12 and n / len(aa) > 0.45 and (err < 2) and (0.6 < area / (hh * ww) < 1.5) and (displacement < ww * 0.15):
                                M = cand / cand[2, 2]
        motions.append(M)
        quality.append(dict(frame=i, inliers=n, error_px=err, valid=M is not None))
    return (motions, pd.DataFrame(quality))

def propagate_calibrations(motions, anchors, max_age_s=3.0, fps=25.0):
    n = len(motions)
    best = [None] * n
    age = np.full(n, np.inf)
    for anchor, H in anchors.items():
        anchor = int(anchor)
        if not 0 <= anchor < n:
            raise ValueError('Calibration anchor outside analysed range')
        for direction in [-1, 1]:
            current = np.array(H, float)
            j = anchor
            while 0 <= j < n and abs(j - anchor) / fps <= max_age_s:
                d = abs(j - anchor) / fps
                if d < age[j]:
                    best[j] = current.copy()
                    age[j] = d
                edge = j + 1 if direction == 1 else j
                nxt = j + direction
                if not 0 <= nxt < n or motions[edge] is None:
                    break
                try:
                    current = current @ (np.linalg.inv(motions[edge]) if direction == 1 else motions[edge])
                except np.linalg.LinAlgError:
                    break
                current = current / current[2, 2]
                j = nxt
    return (best, age)

def map_tracks(df, homographies, ages):
    rows = df.copy()
    rows['field_x'] = np.nan
    rows['field_y'] = np.nan
    rows['calibration_age_s'] = np.nan
    for frame, g in rows.groupby('frame'):
        H = homographies[int(frame)]
        if H is None:
            continue
        feet = np.c_[(g.x1 + g.x2) / 2, g.y2]
        xy = project(feet, H)
        valid = np.isfinite(xy).all(axis=1) & (xy[:, 0] >= 0) & (xy[:, 0] <= 105) & (xy[:, 1] >= 0) & (xy[:, 1] <= 68)
        xy[~valid] = np.nan
        rows.loc[g.index, ['field_x', 'field_y']] = xy
        rows.loc[g.index, 'calibration_age_s'] = ages[int(frame)]
    return rows

def pitch_image(rows, selected=None, trail=None, width=600, height=430):
    im = np.full((height, width, 3), 248, np.uint8)
    scale = min((width - 40) / 105, (height - 70) / 68)
    ox = (width - 105 * scale) / 2
    oy = 40

    def xy(p):
        return (int(ox + p[0] * scale), int(oy + p[1] * scale))
    cv2.rectangle(im, xy((0, 0)), xy((105, 68)), (238, 247, 235), -1)
    for line in field_lines():
        cv2.polylines(im, [np.array([xy(p) for p in line])], False, (120, 145, 125), 1, cv2.LINE_AA)
    if trail:
        for a, b in zip(trail[:-1], trail[1:]):
            if b[0] - a[0] <= 2:
                cv2.line(im, xy(a[1:]), xy(b[1:]), (0, 160, 230), 2, cv2.LINE_AA)
    valid = rows.dropna(subset=['field_x', 'field_y'])
    for r in valid.itertuples():
        p = xy((r.field_x, r.field_y))
        c = (0, 170, 235) if r.id == selected else (190, 105, 40)
        cv2.circle(im, p, 6 if r.id == selected else 4, c, -1)
        cv2.putText(im, str(r.id), (p[0] + 6, p[1] - 5), 0, 0.35, (40, 40, 40), 1)
    cv2.putText(im, 'FIELD VIEW | approximate, assumed 105 x 68 m', (15, 23), 0, 0.43, (55, 55, 55), 1)
    if valid.empty:
        cv2.putText(im, 'Field mapping unavailable at this frame', (35, height - 15), 0, 0.45, (20, 20, 180), 1)
    else:
        age = float(valid.calibration_age_s.max())
        cv2.putText(im, f'Anchor age {age:.1f}s | ' + ('REVIEW DRIFT' if age > 3 else 'approximate'), (15, height - 32), 0, 0.4, (30, 90, 180), 1)
        cv2.putText(im, 'Visible detections only; no off-screen players invented', (15, height - 15), 0, 0.39, (70, 70, 70), 1)
    return im

def follow_crop(frame, box, scale=3):
    h, w = frame.shape[:2]
    if box is None:
        return np.full_like(frame, 25)
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    cw = w / scale
    ch = h / scale
    x = int(np.clip(cx - cw / 2, 0, w - cw))
    y = int(np.clip(cy - ch / 2, 0, h - ch))
    return cv2.resize(frame[y:y + int(ch), x:x + int(cw)], (w, h))

def encode_video(raw, dest):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(raw), '-an', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(dest)], check=True)
    Path(raw).unlink()

def render_outputs(frames, fps, tracks, target, outdir, name='automatic_selection'):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    pw = 600
    specs = {'tracked': (w, h), 'follow': (w, h), 'tactical': (w + pw, h)}
    writers = {k: cv2.VideoWriter(str(out / f'{name}_{k}_raw.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), fps, size) for k, size in specs.items()}
    if not all((v.isOpened() for v in writers.values())):
        raise RuntimeError('Video encoder unavailable')
    groups = {int(i): g for i, g in tracks.groupby('frame')}
    empty = tracks.iloc[:0]
    smooth = None
    last = None
    trail = []
    try:
        for i, f in enumerate(tqdm(frames, desc=f'Render {name}')):
            rows = groups.get(i, empty)
            sel = rows[rows.id == target]
            annotated = draw_ids(f, rows, target)
            box = None
            if len(sel):
                r = sel.iloc[0]
                box = np.array([r.x1, r.y1, r.x2, r.y2])
                smooth = box if smooth is None or last != i - 1 else 0.6 * smooth + 0.4 * box
                last = i
                if pd.notna(r.field_x):
                    trail.append((i, float(r.field_x), float(r.field_y)))
            else:
                smooth = None
            trail = [p for p in trail if i - p[0] <= int(fps * 3)]
            cv2.putText(annotated, f'Following #{target} | {i / fps:.2f}s' + (' | NOT VISIBLE' if box is None else ''), (12, h - 15), 0, 0.55, (0, 220, 255), 2)
            crop = follow_crop(f, smooth)
            cv2.putText(crop, f'FOLLOW #{target}' + (' - NOT VISIBLE' if box is None else ''), (15, 30), 0, 0.65, (0, 220, 255), 2)
            pitch = pitch_image(rows, target, trail, pw, h)
            writers['tracked'].write(annotated)
            writers['follow'].write(crop)
            writers['tactical'].write(np.hstack([annotated, pitch]))
    finally:
        for v in writers.values():
            v.release()
    paths = []
    for k in writers:
        dest = out / f'{name}_{k}.mp4'
        encode_video(out / f'{name}_{k}_raw.mp4', dest)
        paths.append(dest)
    return paths

def create_viewer(video_path, tracks, fps, target, out_path):
    by_frame = {}
    for f, g in tracks.groupby('frame'):
        by_frame[int(f)] = [dict(id=int(r.id), box=[r.x1, r.y1, r.x2, r.y2], field=[r.field_x, r.field_y] if np.isfinite(r.field_x + r.field_y) else None, age=float(r.calibration_age_s) if np.isfinite(r.calibration_age_s) else None) for r in g.itertuples()]
    ids = sorted(map(int, tracks.id.unique()))
    payload = json.dumps(dict(fps=fps, frames=by_frame, ids=ids, target=int(target), lines=field_lines()), allow_nan=False)
    video = base64.b64encode(Path(video_path).read_bytes()).decode()
    html = VIEWER.replace('__DATA__', payload).replace('__VIDEO__', video)
    Path(out_path).write_text(html)
    return Path(out_path)

VIEWER = '<!doctype html><html><head><meta charset="utf-8"><title>Beyond The Frame • Follow anyone</title>\n<style>body{font:15px system-ui;background:#f5f6f8;color:#17212b;margin:24px}h1{margin-bottom:4px}button,select{padding:9px;border:1px solid #ccd3dc;border-radius:8px;background:white}main{max-width:1500px;margin:auto}.grid{display:grid;grid-template-columns:1.4fr 1fr;gap:16px}canvas{width:100%;background:white;border-radius:10px}video{width:100%;max-height:400px}p{color:#526174}.bar{display:flex;gap:12px;align-items:center;margin:15px 0;flex-wrap:wrap}.card{background:white;padding:12px;border-radius:12px}#note{color:#a45a00}@media(max-width:850px){.grid{grid-template-columns:1fr}}</style></head>\n<body><main><h1>Beyond The Frame / follow anyone</h1><p>Click a player box or choose an ID. Field positions are approximate; blank means unavailable.</p>\n<div class="bar"><label>Follow <select id="ids"></select></label><button id="reset">Follow automatic selection</button><button id="back">−1 second</button><button id="next">+1 second</button><span id="note"></span></div>\n<div class="grid"><div class="card"><canvas id="overlay"></canvas><video id="v" controls playsinline src="data:video/mp4;base64,__VIDEO__"></video><small>Video controls below mirror the annotated view above. IDs restart after detected camera cuts.</small></div>\n<div><div class="card"><h3>Overhead field</h3><canvas id="pitch" width="630" height="440"></canvas></div><div class="card"><h3>Follow camera</h3><canvas id="crop" width="640" height="360"></canvas></div></div></div>\n<p>Anonymous person IDs may include officials. Occlusions can cause ID switches. No unseen player positions are inferred. Assumed field dimensions: 105 × 68 m. Foot-point projection is unsuitable for airborne players.</p></main>\n<script>const D=__DATA__;const v=document.getElementById(\'v\'),o=document.getElementById(\'overlay\'),p=document.getElementById(\'pitch\'),c=document.getElementById(\'crop\'),s=document.getElementById(\'ids\');let chosen=D.target;\nfor(const id of D.ids){let opt=document.createElement(\'option\');opt.value=id;opt.textContent=\'Player #\'+id;s.append(opt)}s.value=chosen;s.onchange=()=>{chosen=+s.value;draw()};document.getElementById(\'reset\').onclick=()=>{chosen=D.target;s.value=chosen;draw()};document.getElementById(\'back\').onclick=()=>v.currentTime=Math.max(0,v.currentTime-1);document.getElementById(\'next\').onclick=()=>v.currentTime=Math.min(v.duration,v.currentTime+1);\nfunction frame(){return Math.floor(v.currentTime*D.fps+0.001)}function rows(){return D.frames[frame()]||[]}function fp(a){return [20+a[0]*5.6,30+a[1]*5.6]}\nfunction draw(){if(v.readyState<2)return;let w=v.videoWidth,h=v.videoHeight;if(o.width!==w){o.width=w;o.height=h}let ctx=o.getContext(\'2d\');ctx.drawImage(v,0,0,w,h);ctx.font=\'15px sans-serif\';let list=rows();\nfor(const r of list){let [a,b,x,y]=r.box;ctx.strokeStyle=r.id===chosen?\'#ffba08\':\'#56b9ed\';ctx.lineWidth=r.id===chosen?3:1;ctx.strokeRect(a,b,x-a,y-b);ctx.fillStyle=ctx.strokeStyle;ctx.fillText(\'#\'+r.id,a,Math.max(15,b-4))}\nlet pc=p.getContext(\'2d\');pc.fillStyle=\'#f7fbf7\';pc.fillRect(0,0,p.width,p.height);pc.strokeStyle=\'#9baea0\';pc.lineWidth=1;\nfor(const line of D.lines){pc.beginPath();line.forEach((a,i)=>{let q=fp(a);i?pc.lineTo(...q):pc.moveTo(...q)});pc.stroke()}\nlet prev=null;pc.strokeStyle=\'#eea400\';pc.lineWidth=2;pc.beginPath();for(let f=Math.max(0,frame()-Math.round(D.fps*3));f<=frame();f++){let r=(D.frames[f]||[]).find(r=>r.id===chosen);if(r&&r.field){let q=fp(r.field);prev===f-1?pc.lineTo(...q):pc.moveTo(...q);prev=f}else prev=null}pc.stroke();\nlet valid=0;for(const r of list){if(!r.field)continue;valid++;let q=fp(r.field);pc.fillStyle=r.id===chosen?\'#e8a000\':\'#2871a3\';pc.beginPath();pc.arc(...q,r.id===chosen?6:4,0,7);pc.fill();pc.font=\'12px sans-serif\';pc.fillText(\'#\'+r.id,q[0]+7,q[1]-5)}pc.fillStyle=\'#535e67\';pc.fillText(valid?\'Approximate positions • visible players only\':\'Field mapping unavailable at this frame\',20,430);\nlet r=list.find(x=>x.id===chosen),cc=c.getContext(\'2d\');cc.fillStyle=\'#202630\';cc.fillRect(0,0,c.width,c.height);if(r){let [a,b,x,y]=r.box,cw=w/3,ch=h/3,l=Math.max(0,Math.min(w-cw,(a+x)/2-cw/2)),t=Math.max(0,Math.min(h-ch,(b+y)/2-ch/2));cc.drawImage(v,l,t,cw,ch,0,0,c.width,c.height)}else{cc.fillStyle=\'white\';cc.font=\'20px sans-serif\';cc.fillText(\'Selected player not visible\',30,180)}document.getElementById(\'note\').textContent=\'t = \'+v.currentTime.toFixed(2)+\'s • \'+(r?\'Following #\'+chosen:\'Track unavailable\');}\no.onclick=e=>{let b=o.getBoundingClientRect(),x=(e.clientX-b.left)*o.width/b.width,y=(e.clientY-b.top)*o.height/b.height;let rr=rows().filter(r=>x>=r.box[0]&&x<=r.box[2]&&y>=r.box[1]&&y<=r.box[3]);if(rr.length){chosen=rr[0].id;s.value=chosen;draw()}};\nv.addEventListener(\'seeked\',draw);v.addEventListener(\'loadeddata\',draw);function tick(){draw();requestAnimationFrame(tick)}tick();</script></body></html>'

from ultralytics import YOLO

MODEL_IDS = {'ball': '1isw4wx-MK9h9LMr36VvIWlJD6ppUvw7V', 'player': '17PXFNlx-jI7VjVo_vQnB1sONjRyvoB-q', 'pitch': '1Ma5Kt86tgpdjCTKfum79YMgNnSjcoOyf'}

def download_models(root, kinds=None):
    import gdown
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, ident in MODEL_IDS.items():
        if kinds is not None and name not in kinds: continue
        path = root / f'football-{name}-detection.pt'
        if not path.exists():
            gdown.download(id=ident, output=str(path), quiet=False)
        if not path.exists() or path.stat().st_size < 1000000:
            raise RuntimeError(f'{name} model download failed; rerun later (public host quota). No manual annotation fallback.')
        paths[name] = path
    return paths

def detect_cuts(frames):
    cuts = {0}
    prev = None
    histprev = None
    for i, f in enumerate(frames):
        small = cv2.resize(f, (160, 90))
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [24, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        if prev is not None:
            change = np.mean(np.abs(small.astype(float) - prev)) / 255
            histdiff = cv2.compareHist(histprev, hist, cv2.HISTCMP_BHATTACHARYYA)
            if change > 0.16 and histdiff > 0.32:
                cuts.add(i)
        prev = small.astype(float)
        histprev = hist
    return cuts

def auto_homography(result, shape):
    cfg = SoccerPitchConfiguration(length=10500, width=6800, penalty_box_length=1650, penalty_box_width=4032)
    world = np.asarray(cfg.vertices, float) / 100
    if result.keypoints is None or len(result.keypoints.xy) == 0:
        return (None, {'reason': 'no_keypoints', 'points': 0})
    kp = result.keypoints
    has_conf = kp.conf is not None
    k = int(kp.conf.mean(dim=1).argmax()) if has_conf else 0
    xy = kp.xy[k].cpu().numpy()
    conf = kp.conf[k].cpu().numpy() if has_conf else np.ones(len(xy))
    if len(xy) != len(world):
        raise ValueError('Unexpected pitch model keypoint schema')
    h, w = shape[:2]
    keep = (conf >= 0.5) & np.isfinite(xy).all(axis=1) & (xy[:, 0] > 1) & (xy[:, 0] < w) & (xy[:, 1] > 1) & (xy[:, 1] < h)
    a = xy[keep]
    b = world[keep]
    count = len(a)
    base = dict(points=count, confidence_available=has_conf)
    if count < 4:
        return (None, dict(base, reason='too_few_keypoints'))
    coverage = cv2.contourArea(cv2.convexHull(a.astype(np.float32))) / (w * h)
    field_area = cv2.contourArea(cv2.convexHull(b.astype(np.float32)))
    if coverage < 0.008 or field_area < 20:
        return (None, dict(base, reason='poor_spatial_coverage'))
    if count == 4:
        from itertools import combinations
        for ix in combinations(range(4), 3):
            if cv2.contourArea(a[list(ix)].astype(np.float32)) < 4 or cv2.contourArea(b[list(ix)].astype(np.float32)) < 1:
                return (None, dict(base, reason='degenerate_four_points'))
    tol = max(4.0, w * 0.005)
    inv, mask = cv2.findHomography(b, a, cv2.RANSAC, tol)
    if inv is None or mask is None or (not np.isfinite(inv).all()) or (abs(np.linalg.det(inv)) < 1e-09):
        return (None, dict(base, reason='degenerate'))
    inliers = mask.ravel().astype(bool)
    n = int(inliers.sum())
    err = float(np.median(np.linalg.norm(project(b[inliers], inv) - a[inliers], axis=1))) if n else 1000000000.0
    if n < 4 or n / count < 0.65 or err > tol:
        return (None, dict(base, reason='weak_fit', inliers=n, error_px=err))
    if cv2.contourArea(cv2.convexHull(a[inliers].astype(np.float32))) < 0.008 * w * h:
        return (None, dict(base, reason='inliers_too_narrow', inliers=n))
    try:
        H = np.linalg.inv(inv)
    except np.linalg.LinAlgError:
        return (None, dict(base, reason='singular'))
    den = np.c_[a[inliers], np.ones(n)] @ H[2]
    if not (np.all(den > 1e-08) or np.all(den < -1e-08)):
        return (None, dict(base, reason='unstable_projection'))
    return (H, dict(base, reason='accepted', inliers=n, error_px=err, support='limited_four_or_five' if n < 6 else 'six_or_more'))

def ball_candidates(frame, model, device):
    h, w = frame.shape[:2]
    candidates = []
    windows = [(0, 0, w, h)]
    for y in (0, int(h * 0.4)):
        for x in (0, int(w * 0.4)):
            windows.append((x, y, min(w, x + int(w * 0.6)), min(h, y + int(h * 0.6))))
    for x, y, x2, y2 in windows:
        r = model.predict(frame[y:y2, x:x2], conf=0.2, imgsz=640, device=device, verbose=False)[0]
        if r.boxes is None:
            continue
        for b, c in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy()):
            cx = float((b[0] + b[2]) / 2 + x)
            cy = float((b[1] + b[3]) / 2 + y)
            if b[2] - b[0] > w * 0.06 or b[3] - b[1] > h * 0.08:
                continue
            if all((np.hypot(cx - q[0], cy - q[1]) > 5 for q in candidates)):
                candidates.append((cx, cy, float(c)))
    return candidates

def analyse_automatic(frames, fps, paths, device):
    player = YOLO(str(paths['player']))
    ball = YOLO(str(paths['ball']))
    pitch = YOLO(str(paths['pitch']))
    allowed = [int(k) for k, v in player.names.items() if str(v).lower() in ('player', 'goalkeeper')]
    if not allowed:
        raise RuntimeError(f'Unexpected player classes: {player.names}')
    cuts = detect_cuts(frames)
    rows = []
    balls = []
    anchors = {}
    diagnostics = []
    offset = 0
    maxid = 0
    segment = -1
    history = []
    for i, f in enumerate(tqdm(frames, desc='Automatic players / ball / field')):
        if i in cuts:
            segment += 1
            offset = maxid + 1
            history = []
            if getattr(player, 'predictor', None) is not None:
                for t in getattr(player.predictor, 'trackers', []):
                    t.reset()
        r = player.track(f, persist=True, tracker='botsort.yaml', classes=allowed, conf=0.2, imgsz=1280, device=device, verbose=False)[0]
        if r.boxes is not None and r.boxes.id is not None:
            for box, ident, c in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.id.cpu().numpy(), r.boxes.conf.cpu().numpy()):
                ident = int(ident) + offset
                maxid = max(maxid, ident)
                rows.append(dict(frame=i, id=ident, x1=float(box[0]), y1=float(box[1]), x2=float(box[2]), y2=float(box[3]), confidence=float(c), segment=segment))
        pr = pitch.predict(f, conf=0.05, imgsz=640, device=device, verbose=False)[0]
        H, diag = auto_homography(pr, f.shape)
        resolution = 640
        if H is None:
            pr = pitch.predict(f, conf=0.05, imgsz=1280, device=device, verbose=False)[0]
            H, diag = auto_homography(pr, f.shape)
            resolution = 1280
        diagnostics.append(dict(frame=i, resolution=resolution, **diag))
        if H is not None:
            anchors[i] = H
        candidates = ball_candidates(f, ball, device)
        if candidates:
            recent = [q for q in history if i - q[0] <= max(2, int(0.2 * fps))]
            if recent:
                last = recent[-1]
                dt = i - last[0]
                prediction = np.array(last[1:3])
                if len(recent) >= 2:
                    prev = recent[-2]
                    prediction = prediction + (np.array(last[1:3]) - np.array(prev[1:3])) * dt / max(1, last[0] - prev[0])
                candidates = [q for q in candidates if np.linalg.norm(np.array(q[:2]) - prediction) < f.shape[1] * 0.12 * dt]
                score = lambda q: q[2] - 0.5 * min(1, np.linalg.norm(np.array(q[:2]) - prediction) / (f.shape[1] * 0.12 * dt))
            else:
                score = lambda q: q[2]
            if candidates:
                q = max(candidates, key=score)
                history.append((i, *q))
                balls.append(dict(frame=i, x=q[0], y=q[1], confidence=q[2], segment=segment))
    tracks = pd.DataFrame(rows, columns=['frame', 'id', 'x1', 'y1', 'x2', 'y2', 'confidence', 'segment'])
    if tracks.empty:
        raise RuntimeError('No players detected. No invented sample tracks were created.')
    motions, mq = estimate_motion(frames, tracks)
    for cut in cuts:
        if cut > 0:
            motions[cut] = None
    Hs, ages = propagate_calibrations(motions, anchors, max_age_s=0.2, fps=fps)
    tracks = map_tracks(tracks, Hs, ages)
    bd = pd.DataFrame(balls, columns=['frame', 'x', 'y', 'confidence', 'segment'])
    bd['field_x'] = np.nan
    bd['field_y'] = np.nan
    for j, r in bd.iterrows():
        H = Hs[int(r.frame)]
        if H is not None:
            xy = project([[r.x, r.y]], H)[0]
            if np.isfinite(xy).all() and -5 < xy[0] < 110 and (-5 < xy[1] < 73):
                bd.loc[j, ['field_x', 'field_y']] = xy
    return (tracks, bd, Hs, pd.DataFrame(diagnostics), mq, cuts)

def scorer_candidates(tracks, balls, fps):
    events = []
    valid = balls.dropna(subset=['field_x', 'field_y'])
    for b in valid.itertuples():
        people = tracks[(tracks.frame == b.frame) & (tracks.segment == b.segment)]
        if people.empty:
            continue
        dist = np.hypot((people.x1 + people.x2) / 2 - b.x, people.y2 - b.y) / np.maximum(people.y2 - people.y1, 1)
        order = np.argsort(dist.to_numpy())
        if dist.iloc[order[0]] > 0.65:
            continue
        if len(order) > 1 and dist.iloc[order[1]] - dist.iloc[order[0]] < 0.12:
            continue
        player = people.iloc[order[0]]
        future = valid[(valid.frame > b.frame + fps * 0.12) & (valid.frame <= b.frame + fps * 2) & (valid.segment == b.segment)]
        if len(future) < 3:
            continue
        start = np.array([b.field_x, b.field_y])
        best = None
        for goalx in (0.0, 105.0):
            startdist = np.linalg.norm(start - [goalx, 34.0])
            gd = np.hypot(future.field_x - goalx, future.field_y - 34.0)
            j = gd.idxmin()
            end = future.loc[j]
            progress = startdist - float(gd.loc[j])
            near = future[(abs(future.field_x - goalx) < 10) & (abs(future.field_y - 34) < 9)]
            if progress < 4 or startdist > 40 or len(near) < 2:
                continue
            speed = progress / ((end.frame - b.frame) / fps)
            if not 3 < speed < 50:
                continue
            score = (1 - float(dist.iloc[order[0]]) / 0.65) * 0.35 + min(progress / 20, 1) * 0.35 + min(len(near) / 5, 1) * 0.3
            e = dict(id=int(player.id), frame=int(b.frame), time_s=b.frame / fps, evidence_score=float(score), progress_m_approx=progress, near_goal_observations=len(near), goal_side='left' if goalx == 0 else 'right')
            if best is None or score > best['evidence_score']:
                best = e
        if best:
            events.append(best)
    rank = pd.DataFrame(events)
    if rank.empty:
        return (None, rank, {'status': 'unresolved', 'reason': 'Insufficient visible ball/contact/goal-approach evidence.'})
    rank = rank.sort_values('evidence_score', ascending=False).drop_duplicates('id').reset_index(drop=True)
    first = rank.iloc[0]
    margin = float(first.evidence_score - rank.iloc[1].evidence_score) if len(rank) > 1 else float(first.evidence_score)
    if first.evidence_score < 0.45 or margin < 0.08:
        return (None, rank, {'status': 'unresolved', 'reason': 'Weak or ambiguous scorer-candidate evidence.'})
    return (int(first.id), rank, {'status': 'scorer_candidate_not_verified', 'reason': 'Likely contact followed by ball approaching goal; a goal, deflection or save is not verified.', 'evidence_score': float(first.evidence_score), 'margin': margin})

def ball_overlay(frame, rows):
    im = frame.copy()
    for r in rows.itertuples():
        cv2.circle(im, (int(r.x), int(r.y)), 8, (255, 0, 255), 2)
        cv2.putText(im, 'ball detection', (int(r.x) + 10, int(r.y)), 0, 0.4, (255, 0, 255), 1)
    return im