"""Studio profile: per-frame players, sparse automatic pitch anchors; no ball/scorer claims."""
def analyse_studio(frames,fps,paths,device):
    import cv2
    import numpy as np
    import pandas as pd
    from ultralytics import YOLO
    from tqdm.auto import tqdm
    from notebook_pipeline import detect_cuts,auto_homography,estimate_motion,propagate_calibrations,map_tracks
    cv2.setNumThreads(4)
    player=YOLO(str(paths['player']));pitch=YOLO(str(paths['pitch']))
    allowed=[int(k) for k,v in player.names.items() if str(v).lower() in ('player','goalkeeper')]
    if not allowed:raise RuntimeError('Unexpected player classes')
    cuts=detect_cuts(frames);rows=[];anchors={};diagnostics=[];segment=-1;offset=0;maxid=0
    half=str(device)!='cpu'
    for i,frame in enumerate(tqdm(frames,desc='Studio players + pitch')):
        if i in cuts:
            segment+=1;offset=maxid+1
            if getattr(player,'predictor',None):
                for tracker in getattr(player.predictor,'trackers',[]):tracker.reset()
        r=player.track(frame,persist=True,tracker='botsort.yaml',classes=allowed,conf=.2,imgsz=640,device=device,half=half,verbose=False)[0]
        if r.boxes is not None and r.boxes.id is not None:
            for box,ident,conf in zip(r.boxes.xyxy.cpu().numpy(),r.boxes.id.cpu().numpy(),r.boxes.conf.cpu().numpy()):
                ident=int(ident)+offset;maxid=max(maxid,ident)
                rows.append(dict(frame=i,id=ident,x1=float(box[0]),y1=float(box[1]),x2=float(box[2]),y2=float(box[3]),confidence=float(conf),segment=segment))
        if i%5==0 or i in cuts:
            H=None;diag={}
            for resolution in (640,1280):
                pr=pitch.predict(frame,conf=.05,imgsz=resolution,device=device,half=half,verbose=False)[0]
                H,diag=auto_homography(pr,frame.shape)
                if H is not None:break
            diagnostics.append(dict(frame=i,resolution=resolution,**diag))
            if H is not None:anchors[i]=H
    tracks=pd.DataFrame(rows,columns=['frame','id','x1','y1','x2','y2','confidence','segment'])
    if tracks.empty:raise RuntimeError('No players detected; no sample tracks created')
    motions,mq=estimate_motion(frames,tracks)
    for cut in cuts:
        if cut>0:motions[cut]=None
    hs,ages=propagate_calibrations(motions,anchors,max_age_s=.24,fps=fps)
    tracks=map_tracks(tracks,hs,ages)
    balls=pd.DataFrame(columns=['frame','x','y','confidence','segment','field_x','field_y'])
    return tracks,balls,hs,pd.DataFrame(diagnostics),mq,cuts
