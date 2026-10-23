"""Beyond The Frame CLI, adapted from the supplied notebook (4)."""
import argparse, hashlib, json, math
from pathlib import Path

def appearance_groups(frames, tracks):
    """Tentative jersey-appearance groups, never verified team identities."""
    import cv2
    import numpy as np
    samples={}
    for r in tracks.itertuples():
        if int(r.frame)%5:continue
        im=frames[int(r.frame)];h,w=im.shape[:2]
        x1=max(0,int(r.x1+(r.x2-r.x1)*.2));x2=min(w,int(r.x2-(r.x2-r.x1)*.2))
        y1=max(0,int(r.y1+(r.y2-r.y1)*.18));y2=min(h,int(r.y1+(r.y2-r.y1)*.48))
        crop=im[y1:y2,x1:x2]
        if crop.size<12:continue
        hsv=cv2.cvtColor(crop,cv2.COLOR_BGR2HSV);mask=~((hsv[:,:,0]>28)&(hsv[:,:,0]<95)&(hsv[:,:,1]>40))
        pixels=cv2.cvtColor(crop,cv2.COLOR_BGR2LAB)[mask]
        if len(pixels)<6:continue
        samples.setdefault(int(r.id),[]).append(np.median(pixels,axis=0))
    ids=[i for i,v in samples.items() if len(v)>=3]
    if len(ids)<4:return {}
    features=np.array([np.median(samples[i],axis=0) for i in ids],np.float32)
    cv2.setRNGSeed(7)
    _,labels,centers=cv2.kmeans(features,2,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,50,.1),8,cv2.KMEANS_PP_CENTERS)
    if np.linalg.norm(centers[0]-centers[1])<18:return {}
    order=np.argsort(-centers[:,0]);names={int(order[0]):'appearance-A',int(order[1]):'appearance-B'}
    return {ident:names[int(label)] for ident,label in zip(ids,labels.ravel())}

def export(video, frames, fps, tracks, balls, homographies, cuts, scorer, model_versions):
    h,w=frames[0].shape[:2]; records=[]; groups=appearance_groups(frames,tracks)
    grouped={int(i):g for i,g in tracks.groupby('frame')}
    ballgroups={int(i):g for i,g in balls.groupby('frame')}
    for i in range(len(frames)):
        segment=sum(c<=i for c in cuts)-1; items=[]
        if i in grouped:
            for r in grouped[i].itertuples():
                box=[max(0,min(1,v)) for v in [r.x1/w,r.y1/h,r.x2/w,r.y2/h]]
                if box[2]<=box[0] or box[3]<=box[1]:continue
                items.append(dict(id=int(r.id),box=box,confidence=float(r.confidence),field=[float(r.field_x),float(r.field_y)] if math.isfinite(r.field_x+r.field_y) else None,team=groups.get(int(r.id))))
        ball=[]
        if i in ballgroups:
            for r in ballgroups[i].itertuples():ball.append(dict(image=[float(r.x/w),float(r.y/h)],confidence=float(r.confidence)))
        H=homographies[i]
        records.append(dict(time=round(i/fps,5),segment=segment,calibration=dict(valid=H is not None,homography=H.tolist() if H is not None else None,quality='approximate',assumedPitchMeters=[105,68]),tracks=items,balls=ball))
    return dict(version='1.0',coordinateSystem='normalized-image',video=dict(name=video.name,sha256=hashlib.sha256(video.read_bytes()).hexdigest(),duration=len(frames)/fps,width=w,height=h,fps=fps),provenance=dict(kind='model-generated',source='Local inference adapted from supplied notebook (4)',pipelineVersion='2.0',models=model_versions,appearanceGrouping='Two-group torso LAB clustering; unverified team identities',limitations=['Anonymous track IDs','Tentative appearance groups','Scorer is a candidate heuristic, not verified identity','Approximate planar calibration']),scorer=scorer,frames=records,events=[])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('video',type=Path);p.add_argument('--out',type=Path,default=Path('analysis'));p.add_argument('--models',type=Path,default=Path('models'));p.add_argument('--device',default='cpu');p.add_argument('--threads',type=int,default=4);p.add_argument('--studio',action='store_true',help='Per-frame players and sparse pitch anchors; skips ball inference');p.add_argument('--render',action='store_true');a=p.parse_args()
    import torch
    torch.set_num_threads(max(1,a.threads))
    from notebook_pipeline import load_video, download_models, analyse_automatic, scorer_candidates, render_outputs
    import ultralytics
    if not a.video.is_file():p.error('Video does not exist')
    frames,fps=load_video(a.video,end_s=60)
    # Export must reference the exact input timeline; never silently analyse a truncated long clip.
    import cv2
    cap=cv2.VideoCapture(str(a.video));count=cap.get(cv2.CAP_PROP_FRAME_COUNT);cap.release()
    if count>len(frames)+1:p.error('Clips longer than 60 seconds must be trimmed first.')
    models=download_models(a.models,kinds=('player','pitch') if a.studio else None)
    if a.studio:
        from studio_pipeline import analyse_studio
        tracks,balls,hs,diag,motion,cuts=analyse_studio(frames,fps,models,a.device)
    else:tracks,balls,hs,diag,motion,cuts=analyse_automatic(frames,fps,models,a.device)
    target,ranking,scorer=scorer_candidates(tracks,balls,fps)
    a.out.mkdir(parents=True,exist_ok=True)
    versions={k:dict(file=v.name,sha256=hashlib.sha256(v.read_bytes()).hexdigest()) for k,v in models.items() if not a.studio or k!='ball'};versions['ultralytics']=ultralytics.__version__;versions['torch']=torch.__version__
    data=export(a.video,frames,fps,tracks,balls,hs,cuts,scorer,versions)
    data['provenance']['mode']='studio' if a.studio else 'full-notebook'
    data['provenance']['ballDetection']=not a.studio
    if a.studio:data['scorer']={'status':'unresolved','reason':'Ball inference skipped in studio profile; no scorer association claimed.'}
    (a.out/'analysis.json').write_text(json.dumps(data,allow_nan=False),encoding='utf-8')
    tracks.to_csv(a.out/'player_tracks.csv',index=False);balls.to_csv(a.out/'ball_detections.csv',index=False);diag.to_csv(a.out/'calibration.csv',index=False)
    if a.render:
        if target is None:target=int(tracks.groupby('id').size().idxmax())
        render_outputs(frames,fps,tracks,target,a.out)
    print(f'Wrote {a.out / "analysis.json"}; scorer: {scorer["status"]}')
if __name__=='__main__':main()
