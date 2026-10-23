package com.beyondtheframe.tv;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.content.Context;
import android.widget.FrameLayout;
import android.webkit.*;
import java.io.*;
import java.util.*;

/** Offline Fire OS host. No network permission and no JS/native credential bridge. */
public class MainActivity extends Activity {
  private WebView web;
  private ValueCallback<Uri[]> chooser;
  private FrameLayout container;
  private View fullscreenView;
  private WebChromeClient.CustomViewCallback fullscreenCallback;
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    web=new WebView(this);container=new FrameLayout(this);container.addView(web,new FrameLayout.LayoutParams(-1,-1));setContentView(container);
    WebSettings s=web.getSettings();s.setUserAgentString(s.getUserAgentString()+" BeyondTheFrameTV");s.setJavaScriptEnabled(true);s.setDomStorageEnabled(true);s.setMediaPlaybackRequiresUserGesture(false);s.setAllowFileAccess(false);s.setAllowContentAccess(true);s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
    web.setWebViewClient(new WebViewClient(){
      @Override public boolean shouldOverrideUrlLoading(WebView w,WebResourceRequest r){return !"appassets.androidplatform.net".equals(r.getUrl().getHost());}
      @Override public WebResourceResponse shouldInterceptRequest(WebView w,WebResourceRequest r){
        Uri u=r.getUrl();if(!"https".equals(u.getScheme())||!"appassets.androidplatform.net".equals(u.getHost()))return denied();
        String p=u.getPath();if(p==null||p.contains(".."))return denied();if(p.equals("/"))p="/index.html";
        try {
          String name=p.substring(1);long length;
          try(android.content.res.AssetFileDescriptor fd=getAssets().openFd(name)){length=fd.getLength();}
          catch(IOException compressed){try(InputStream stream=getAssets().open(name)){long total=0;byte[] b=new byte[8192];int n;while((n=stream.read(b))!=-1)total+=n;length=total;}}
          InputStream stream=getAssets().open(name);Map<String,String> h=new HashMap<>();h.put("Accept-Ranges","bytes");h.put("Cache-Control","no-cache");h.put("Access-Control-Allow-Origin","https://appassets.androidplatform.net");int status=200;String reason="OK";
          String range=r.getRequestHeaders().get("Range");if(range==null)range=r.getRequestHeaders().get("range");
          if(range!=null&&range.matches("bytes=\\d+-\\d*")){
            String[] parts=range.substring(6).split("-",-1);long start=Long.parseLong(parts[0]),end=parts[1].isEmpty()?length-1:Math.min(Long.parseLong(parts[1]),length-1);
            if(start>=length||end<start){stream.close();return new WebResourceResponse("text/plain","utf-8",416,"Range Not Satisfiable",Collections.singletonMap("Content-Range","bytes */"+length),new ByteArrayInputStream(new byte[0]));}
            long remaining=start;while(remaining>0){long n=stream.skip(remaining);if(n<=0)throw new IOException("Seek failed");remaining-=n;}
            h.put("Content-Range","bytes "+start+"-"+end+"/"+length);h.put("Content-Length",String.valueOf(end-start+1));status=206;reason="Partial Content";
            stream=new LimitedStream(stream,end-start+1);
          }else h.put("Content-Length",String.valueOf(length));
          return new WebResourceResponse(mime(name),"utf-8",status,reason,h,stream);
        } catch(Exception e){return new WebResourceResponse("text/plain","utf-8",404,"Not Found",new HashMap<>(),new ByteArrayInputStream(new byte[0]));}
      }
      @Override public void onPageFinished(WebView w,String url){w.evaluateJavascript("document.getElementById('play').focus()",null);}
    });
    web.setWebChromeClient(new WebChromeClient(){
      @Override public boolean onShowFileChooser(WebView w,ValueCallback<Uri[]> callback,FileChooserParams params){
        if(chooser!=null)chooser.onReceiveValue(null);chooser=callback;
        try{startActivityForResult(params.createIntent(),100);return true;}catch(Exception e){chooser.onReceiveValue(null);chooser=null;return true;}
      }
      @Override public void onShowCustomView(View v,CustomViewCallback cb){
        if(fullscreenView!=null){cb.onCustomViewHidden();return;}
        fullscreenView=v;fullscreenCallback=cb;web.setVisibility(View.GONE);container.addView(v,new FrameLayout.LayoutParams(-1,-1));
      }
      @Override public void onHideCustomView(){hideFullscreen();}
    });
    web.loadUrl("https://appassets.androidplatform.net/index.html");
  }
  private void hideFullscreen(){if(fullscreenView==null)return;container.removeView(fullscreenView);fullscreenView=null;web.setVisibility(View.VISIBLE);WebChromeClient.CustomViewCallback cb=fullscreenCallback;fullscreenCallback=null;if(cb!=null)cb.onCustomViewHidden();}
  private static WebResourceResponse denied(){return new WebResourceResponse("text/plain","utf-8",403,"Forbidden",new HashMap<>(),new ByteArrayInputStream(new byte[0]));}
  private static String mime(String p){if(p.endsWith(".html"))return "text/html";if(p.endsWith(".js"))return "text/javascript";if(p.endsWith(".css"))return "text/css";if(p.endsWith(".json"))return "application/json";if(p.endsWith(".mp4"))return "video/mp4";if(p.endsWith(".jpg"))return "image/jpeg";if(p.endsWith(".png"))return "image/png";if(p.endsWith(".vtt"))return "text/vtt";return "application/octet-stream";}
  private static class LimitedStream extends FilterInputStream {long left;LimitedStream(InputStream s,long size){super(s);left=size;}public int read()throws IOException{if(left<=0)return -1;int v=super.read();if(v>=0)left--;return v;}public int read(byte[] b,int o,int n)throws IOException{if(left<=0)return -1;int v=super.read(b,o,(int)Math.min(left,n));if(v>0)left-=v;return v;}}
  @Override protected void onActivityResult(int request,int result,Intent intent){super.onActivityResult(request,result,intent);if(request==100&&chooser!=null){chooser.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result,intent));chooser=null;}}
  @Override public boolean dispatchKeyEvent(KeyEvent event){
    if(event.getKeyCode()==KeyEvent.KEYCODE_BACK&&fullscreenView!=null){if(event.getAction()==KeyEvent.ACTION_DOWN)hideFullscreen();return true;}
    String k=null;switch(event.getKeyCode()){case KeyEvent.KEYCODE_DPAD_UP:k="ArrowUp";break;case KeyEvent.KEYCODE_DPAD_DOWN:k="ArrowDown";break;case KeyEvent.KEYCODE_DPAD_LEFT:k="ArrowLeft";break;case KeyEvent.KEYCODE_DPAD_RIGHT:k="ArrowRight";break;case KeyEvent.KEYCODE_BACK:k="Back";if(event.getAction()==KeyEvent.ACTION_DOWN)((InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(web.getWindowToken(),0);break;case KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE:k="MediaPlayPause";break;case KeyEvent.KEYCODE_MEDIA_PLAY:k="MediaPlay";break;case KeyEvent.KEYCODE_MEDIA_PAUSE:k="MediaPause";break;case KeyEvent.KEYCODE_DPAD_CENTER:case KeyEvent.KEYCODE_ENTER:if(event.getAction()==KeyEvent.ACTION_DOWN){web.evaluateJavascript("(function(){var a=document.activeElement;if(a&&a.tagName==='INPUT'&&a.type==='text'){a.focus();return 'text';}window.btfRemote&&window.btfRemote('Select');return 'control';})()",new ValueCallback<String>(){public void onReceiveValue(String value){if("\"text\"".equals(value)){web.requestFocus();((InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE)).showSoftInput(web,InputMethodManager.SHOW_IMPLICIT);}}});}return true;}
    if(k!=null){if(event.getAction()==KeyEvent.ACTION_DOWN)web.evaluateJavascript("window.btfRemote && window.btfRemote('"+k+"')",null);return true;}return super.dispatchKeyEvent(event);
  }
  @Override protected void onPause(){web.evaluateJavascript("document.querySelectorAll('video').forEach(function(v){v.pause()})",null);web.onPause();super.onPause();}
  @Override protected void onResume(){super.onResume();if(web!=null)web.onResume();}
  @Override protected void onDestroy(){if(chooser!=null)chooser.onReceiveValue(null);if(web!=null)web.destroy();super.onDestroy();}
}
