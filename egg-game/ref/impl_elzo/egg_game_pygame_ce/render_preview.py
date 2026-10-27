"""Renderizador de prévia SEM Pygame para conferir a composição dos assets.
Para executar o jogo real, use main.py com pygame-ce instalado.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
P=Path(__file__).parent
A=P/'assets'
W,H=960,720
frame=Image.open(A/'background'/'sky.jpg').convert('RGB').crop((0,0,W,H)).convert('RGBA')
def paste(im,x,y):
 frame.alpha_composite(im,(int(x),int(y)))
mount=Image.open(A/'background'/'mountains.png').convert('RGBA')
village=Image.open(A/'background'/'village.png').convert('RGBA')
paste(mount,-100,205)
paste(village,-95,455)
core=Image.open(A/'tree'/'trunk_repeat.png').convert('RGBA')
for y in [-420,0,420]: paste(core,24,y+25)
for j,y in enumerate([-300,0,300,600]):
 part=Image.open(A/'tree'/f'trunk_{'ABCDEFG'[j%7]}.png').convert('RGBA')
 paste(part,172-part.width//2,y-(-446))
placements=[('fixa_01',580,480),('fixa_01',510,348),('movel_01',670,210),('fixa_01',730,70),('pequena_01',385,590)]
for nm,x,y in placements:
 surf=Image.open(A/'nests'/f'{nm}.png').convert('RGBA')
 w,h={'fixa_01':(170,85),'movel_01':(180,83),'pequena_01':(135,77)}[nm]
 surf=surf.resize((w,h),Image.Resampling.LANCZOS)
 paste(surf,x-w//2,y-29)
egg=Image.open(A/'egg'/'jump_03.png').convert('RGBA').resize((76,88),Image.Resampling.LANCZOS)
paste(egg,580-38,276)
draw=ImageDraw.Draw(frame)
draw.rounded_rectangle((18,15,215,113),radius=17,fill=(253,231,191,230),outline=(112,66,35,255),width=3)
try:
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',22)
 big=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',31)
except: font=big=ImageFont.load_default()
draw.text((34,24),'ALTURA',fill=(35,31,24),font=font)
draw.text((34,52),'0123 m',fill=(35,31,24),font=big)
frame.convert('RGB').save(P/'PREVIA_cenario.jpg',quality=90)
