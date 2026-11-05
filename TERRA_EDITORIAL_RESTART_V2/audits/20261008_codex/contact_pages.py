from pathlib import Path
from PIL import Image,ImageDraw
A=Path(__file__).parent/'render'
for prefix in ('main','supp'):
    fs=sorted(A.glob(prefix+'-*.png'))
    for i in range(0,len(fs),2):
        ims=[Image.open(p).convert('RGB') for p in fs[i:i+2]]
        canvas=Image.new('RGB',(sum(x.width for x in ims),max(x.height for x in ims)+30),'#dddddd')
        x=0
        for p,im in zip(fs[i:i+2],ims):
            canvas.paste(im,(x,30));ImageDraw.Draw(canvas).text((x+10,5),p.name,fill='black');x+=im.width
        canvas.save(A/f'qa_{prefix}_{i+1:02}.png')
