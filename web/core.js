(function(root){
 'use strict';
 const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
 const point=t=>[(t.box[0]+t.box[2])/2,t.box[3]];
 function fieldToImage(matrix,field,width,height){if(!Array.isArray(matrix)||matrix.length!==3||matrix.some(r=>!Array.isArray(r)||r.length!==3||r.some(x=>!Number.isFinite(x))))return null;const [[a,b,c],[d,e,f],[g,h,i]]=matrix,A=e*i-f*h,B=c*h-b*i,C=b*f-c*e,D=f*g-d*i,E=a*i-c*g,F=c*d-a*f,G=d*h-e*g,H=b*g-a*h,I=a*e-b*d,det=a*A+b*D+c*G;if(Math.abs(det)<1e-12)return null;const den=G*field[0]+H*field[1]+I;if(Math.abs(den)<1e-9)return null;const x=(A*field[0]+B*field[1]+C)/den/width,y=(D*field[0]+E*field[1]+F)/den/height;return Number.isFinite(x)&&Number.isFinite(y)?[x,y]:null;}
 function frameAt(data,time){
  if(!data?.frames?.length)return null;let lo=0,hi=data.frames.length-1;
  while(lo<hi){const m=(lo+hi)>>1;if(data.frames[m].time<time)lo=m+1;else hi=m;}
  const a=data.frames[lo],b=data.frames[Math.max(0,lo-1)],f=Math.abs(a.time-time)<Math.abs(b.time-time)?a:b;
  return Math.abs(f.time-time)<=(data.video?.fps?0.5/data.video.fps+.004:.065)?f:null;
 }
 function passModel(from,to,defenders,speed=18,reaction=.4,defenderSpeed=7){
  if(speed<=0||defenderSpeed<=0||reaction<0)throw Error('Invalid movement assumptions');
  const distance=Math.hypot(to[0]-from[0],to[1]-from[1]),travel=distance/speed,dx=to[0]-from[0],dy=to[1]-from[1],len2=dx*dx+dy*dy;
  // Sample the entire corridor; the nearest geometric point alone can miss a later interception.
  let margin=Infinity;
  for(const d of defenders)for(let j=1;j<=48;j++){const t=j/48,x=from[0]+dx*t,y=from[1]+dy*t,arrival=reaction+Math.hypot(d[0]-x,d[1]-y)/defenderSpeed; margin=Math.min(margin,arrival-travel*t);}
  return {distance,travel,margin,label:defenders.length===0?'No visible obstacles':margin<0?'Likely obstructed':margin<.3?'Contested':'More open'};
 }
 function corridor(from,to,obstacles){let clearance=Infinity;const dx=to[0]-from[0],dy=to[1]-from[1],l=dx*dx+dy*dy;
  for(const d of obstacles){const t=clamp(((d[0]-from[0])*dx+(d[1]-from[1])*dy)/(l||1),0,1);clearance=Math.min(clearance,Math.hypot(d[0]-from[0]-dx*t,d[1]-from[1]-dy*t));}return clearance;
 }
 function optionsFor(frame,id,assumptions={speed:18,reaction:.4}){
  const from=frame?.tracks.find(t=>t.id===id);if(!from)return [];
  const group=from.team,others=frame.tracks.filter(t=>t.id!==id),same=group?others.filter(t=>t.team===group):others;
  const recipients=same.length?same:others,obstacles=group&&same.length?others.filter(t=>t.team&&t.team!==group):[];
  const a=point(from);let opts=recipients.map(t=>{const b=point(t),calibrated=!!(frame.calibration?.valid&&from.field&&t.field),defs=obstacles.filter(d=>d.field).map(d=>d.field);const model=calibrated?passModel(from.field,t.field,defs,assumptions.speed,assumptions.reaction):null;const imageClearance=corridor(a,b,obstacles.map(point));return {id:t.id,track:t,from:a,to:b,calibrated,model,imageDistance:Math.hypot(a[0]-b[0],a[1]-b[1]),clearance:imageClearance,teamVerified:false,hasGroups:!!group&&same.length>0,obstacles:obstacles.map(point),score:model?(Number.isFinite(model.margin)?model.margin:0):Number.isFinite(imageClearance)?imageClearance:0};}).filter(o=>o.imageDistance>.025).sort((a,b)=>a.imageDistance-b.imageDistance);
  if(opts.length>3)opts=[opts[0],opts[Math.floor((opts.length-1)/2)],opts[opts.length-1]];
  const names=opts.length===1?['Visible option']:opts.length===2?['Near pass','Wider pass']:['Short pass','Into space','Switch the play'];
  return opts.map((o,i)=>({...o,letter:'ABC'[i],name:names[i],label:o.model?o.model.label:o.obstacles.length?(o.clearance<.035?'Screen lane crowded':'Screen lane clearer'):'Visible option'}));
 }
 function trailFor(data,time,id,seconds=2.5){const f=frameAt(data,time);if(!f)return [];const fps=data.video?.fps||25,start=time-seconds;let last=null,trail=[];
  for(const q of data.frames){if(q.time<start||q.time>time+.001||q.segment!==f.segment)continue;const t=q.tracks.find(t=>t.id===id);if(!t){last=null;continue;}trail.push({time:q.time,point:point(t),field:t.field||null,break:!last||q.time-last.time>1.6/fps});last=q;}return trail;
 }
 function motionFor(data,time,id){const trail=trailFor(data,time,id,2.5),f=frameAt(data,time),t=f?.tracks.find(t=>t.id===id);if(!t)return {visible:false,label:'Out of view',samples:0};
  let distance=0,screen=0,seconds=0,pairs=0;
  for(let i=1;i<trail.length;i++){const a=trail[i-1],b=trail[i];if(b.break)continue;screen+=Math.hypot(b.point[0]-a.point[0],b.point[1]-a.point[1]);if(a.field&&b.field){distance+=Math.hypot(b.field[0]-a.field[0],b.field[1]-a.field[1]);seconds+=b.time-a.time;pairs++;}}
  const calibrated=!!f.calibration?.valid&&pairs>6&&seconds>.3,net=trail.length>1?trail[trail.length-1].point[0]-trail[0].point[0]:0;
  return {visible:true,calibrated,distance:calibrated?distance:null,speed:calibrated?distance/seconds:null,seconds,samples:trail.length,screen,description:Math.abs(net)<.012?'Holding a similar screen position':net>0?'Moving right across the frame':'Moving left across the frame',label:calibrated?'Approximate field movement':'Image-space movement'};
 }
 function answerQuestion(question,data,time,id,assumptions){const q=question.toLowerCase(),f=frameAt(data,time),t=f?.tracks.find(t=>t.id===id),m=motionFor(data,time,id),opts=optionsFor(f,id,assumptions);const at=`${time.toFixed(2)} s · track #${id}`;
  if(!t)return {title:'The selected player is out of view.',body:'Seek to a moment where this track is visible, or choose a different visible player. A missing detection does not establish absence.',evidence:at};
  if(/mov|run|speed|trail|follow/.test(q)){return {title:`How #${id} is moving`,body:m.samples<3?'Play a little more of the clip to build a movement trail.':`${m.description} over the available recent frames. ${m.calibrated?`Approximate field path: ${m.distance.toFixed(1)} m in ${m.seconds.toFixed(1)} s. Calibration jitter can inflate distance; this is not verified player speed.`:'The trail uses screen coordinates, so camera movement also contributes. Reliable speed in m/s is unavailable at this moment.'}`,evidence:at};}
  if(/scor|name|identity|who is (this|he|she)/.test(q))return {title:'Track ID, not a verified identity.',body:`#${id} is an anonymous model track. Neither the player’s name nor a scorer identity has been verified.`,evidence:at};
  if(/pass|option|space|next|do|better|compare|best|open|why/.test(q)){
   if(!opts.length)return {title:'No visible passing comparison.',body:'There are not enough eligible visible tracks to compare. Move to a wider shot or choose another player.',evidence:at};
   const ranked=[...opts].sort((a,b)=>b.score-a.score),best=ranked[0],reason=best.calibrated?`${best.model.distance.toFixed(1)} m and ${best.model.travel.toFixed(2)} s ball travel at ${assumptions.speed} m/s. ${best.label}.`:'This is a screen-space comparison; metric distance and ball-arrival timing are unavailable.';
   const ranking=ranked.some(o=>o.obstacles.length)?`Among these visible candidates, ${best.letter} has the largest measured corridor margin under the current assumptions.`:'No opposing appearance-group observations are available to rank lane safety. Start by inspecting this visible option.';
   return {title:`Explore ${best.name.toLowerCase()} to #${best.id}.`,body:`${ranking} ${reason} ${best.hasGroups?'Appearance-based groups are tentative, not verified team identities.':'Team membership is unknown, so the candidates are exploratory rather than verified teammates.'} No off-screen players or future outcome is assumed.`,evidence:at+' · candidates '+opts.map(o=>'#'+o.id).join(', ')};
  }
  return {title:'Ask about this football moment.',body:'I can compare visible passing lanes, describe the selected player’s movement, and explain the timing assumptions. Try “What should I do next?”, “Who has more space?”, or “How is this player moving?” This assistant uses local geometry, not an online language model.',evidence:at};
 }
 function validateAnalysis(d){
  if(d?.version!=='1.0'||d.coordinateSystem!=='normalized-image'||!Array.isArray(d.frames)||!(/^[a-f0-9]{64}$/.test(d.video?.sha256||''))||!Number.isFinite(d.video.duration)||d.video.duration<=0||!Number.isFinite(d.video.fps)||d.video.fps<=0||d.video.fps>240)throw Error('Expected v1.0 normalized-image analysis with a video SHA-256, duration, and frame rate.');
  if(d.frames.length>100000)throw Error('Analysis is too large.');let last=-1,segment=-1;
  for(const f of d.frames){if(!Number.isFinite(f.time)||f.time<last||f.time<0||f.time>d.video.duration||!Number.isInteger(f.segment)||f.segment<segment||!Array.isArray(f.tracks))throw Error('Invalid frame timeline.');last=f.time;segment=f.segment;const ids=new Set();
   for(const t of f.tracks){if(!Number.isInteger(t.id)||ids.has(t.id)||!Array.isArray(t.box)||t.box.length!==4||t.box.some(x=>!Number.isFinite(x)||x<0||x>1)||t.box[2]<=t.box[0]||t.box[3]<=t.box[1])throw Error('Invalid track box or duplicate ID.');ids.add(t.id);if(t.field&&(!f.calibration?.valid||t.field.length!==2||t.field.some((x,i)=>!Number.isFinite(x)||x<0||x>[105,68][i])))throw Error('Field positions require valid calibration.');if(t.team!=null&&typeof t.team!=='string')throw Error('Invalid appearance group.');}}
  return d;
 }
 const api={frameAt,passModel,corridor,optionsFor,point,fieldToImage,trailFor,motionFor,answerQuestion,validateAnalysis};if(typeof module!=='undefined')module.exports=api;else root.BTF=api;
})(typeof window!=='undefined'?window:globalThis);
