const http=require('http'),fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'../web');
http.createServer((req,res)=>{
 let p;try{p=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]));}catch{res.writeHead(400).end();return;}
 if(!p.startsWith(root+path.sep)&&p!==root){res.writeHead(403).end();return;}
 if(p===root)p=path.join(root,'index.html');
 fs.stat(p,(err,s)=>{if(err||!s.isFile()){res.writeHead(404).end('Not found');return;}
 const types={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.mp4':'video/mp4','.jpg':'image/jpeg','.svg':'image/svg+xml','.vtt':'text/vtt'};
 const headers={'Content-Type':types[path.extname(p)]||'application/octet-stream','Accept-Ranges':'bytes','Cache-Control':'no-cache'};
 const range=req.headers.range?.match(/^bytes=(\d+)-(\d*)$/);
 if(range){const start=+range[1],end=range[2]?Math.min(+range[2],s.size-1):s.size-1;if(start>=s.size||end<start){res.writeHead(416,{'Content-Range':`bytes */${s.size}`}).end();return;}res.writeHead(206,{...headers,'Content-Range':`bytes ${start}-${end}/${s.size}`,'Content-Length':end-start+1});fs.createReadStream(p,{start,end}).pipe(res);}
 else{res.writeHead(200,{...headers,'Content-Length':s.size});fs.createReadStream(p).pipe(res);}});
}).listen(4173,'127.0.0.1',()=>console.log('Beyond The Frame → http://127.0.0.1:4173'));
