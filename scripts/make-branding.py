"""Generate the sports studio's original TV launcher artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).resolve().parents[1]
out=root/'android/app/src/main/res/drawable'
out.mkdir(parents=True,exist_ok=True)
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if bold else 'segoeui.ttf'),size)
im=Image.new('RGB',(320,180),'#0c191d');d=ImageDraw.Draw(im)
for i in range(180):
 color=(12,int(25+i/45),int(29+i/70));d.line((0,i,320,i),fill=color)
d.rounded_rectangle((25,58,52,95),radius=3,outline='#43e4db',width=2);d.rounded_rectangle((32,65,59,102),radius=3,fill='#0e2022',outline='#43e4db',width=2);d.polygon([(42,75),(42,91),(52,83)],fill='#43e4db')
d.text((79,53),'BEYOND',font=font(23,True),fill='#f2f6f2');d.text((79,80),'THE FRAME.',font=font(23),fill='#f2f6f2');d.text((80,120),'THE TACTICAL STUDIO',font=font(8),fill='#52b3a4');im.save(out/'banner.png')
icon=Image.new('RGB',(192,192),'#0c191d');d=ImageDraw.Draw(icon);d.rounded_rectangle((44,42,111,131),radius=7,outline='#43e4db',width=4);d.rounded_rectangle((60,58,127,147),radius=7,fill='#0c191d',outline='#43e4db',width=4);d.polygon([(84,82),(84,123),(111,102)],fill='#43e4db');icon.save(out/'icon.png')
