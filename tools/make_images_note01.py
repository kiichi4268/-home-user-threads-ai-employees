"""note_01 の画像3枚（1280×720）を作る。使い方：python3 tools/make_images_note01.py（Pillow が必要）"""
import pathlib
OUT=str(pathlib.Path(__file__).resolve().parent.parent/"content"/"note"/"note_01_hitori"/"images")
from PIL import Image, ImageDraw, ImageFont
F='/usr/share/fonts/truetype/ipafont-gothic/ipag.ttf'
import os
if not os.path.exists(F):
    import glob; F=glob.glob('/usr/share/fonts/**/ipag*.tt*',recursive=True)[0]
NAVY=(20,42,92); YEL=(255,236,30); TEAL=(24,160,178); WHITE=(255,255,255); LIGHT=(243,245,249); MUTED=(86,99,127)
def f(s): return ImageFont.truetype(F,s)
def txt(d,xy,s,size,fill,sw=None,anchor='la'):
    d.text(xy,s,font=f(size),fill=fill,stroke_width=sw if sw is not None else max(1,size//40),stroke_fill=fill,anchor=anchor)
def court(d,x0,y0,w,h,col,wd=4):
    d.rectangle([x0,y0,x0+w,y0+h],outline=col,width=wd)
    d.line([x0+w/2,y0,x0+w/2,y0+h],fill=col,width=wd)
    for k in (0.2,0.8): d.line([x0+w*k,y0,x0+w*k,y0+h],fill=col,width=wd)
    for k in (0.08,0.92): d.line([x0,y0+h*k,x0+w,y0+h*k],fill=col,width=wd)
    d.line([x0,y0+h/2,x0+w*0.2,y0+h/2],fill=col,width=wd); d.line([x0+w*0.8,y0+h/2,x0+w,y0+h/2],fill=col,width=wd)

# 01 header
W,H=1280,720
im=Image.new('RGB',(W,H),NAVY); d=ImageDraw.Draw(im)
court(d,700,90,720,540,(40,66,128),5)
d.polygon([(0,0),(470,0),(440,58),(0,58)],fill=TEAL)
txt(d,(64,14),'運動ブランクの社会人へ',30,WHITE)
txt(d,(64,170),'ひとりで行っても、',86,WHITE)
d.rectangle([56,290,56+86*9+20,400],fill=YEL)
txt(d,(64,300),'気まずくならない。',86,NAVY)
txt(d,(64,440),'スポーツサークルの選び方と、当日の立ち回り',38,WHITE)
d.line([64,610,W-64,610],fill=(60,86,148),width=2)
txt(d,(64,632),'マカシェットスポーツ',34,YEL)
txt(d,(W-64,640),'バドミントン・バレーボール・卓球・野球',26,(200,210,232),anchor='ra')
im.save(OUT+'/01_header.png')

# 02 checklist
im=Image.new('RGB',(W,H),LIGHT); d=ImageDraw.Draw(im)
d.rectangle([0,0,W,120],fill=NAVY)
txt(d,(64,34),'失敗しないサークル選び',48,WHITE)
d.rectangle([640,30,640+300,92],fill=YEL); txt(d,(660,38),'4つのチェック',42,NAVY)
items=[('ひとり参加がどのくらいいるか書いてある','「ひとり参加歓迎」だけでなく、実際の様子が分かるか'),
('参加費と、持ち物・貸出品が書いてある','お金と持ち物がはっきりしている＝運営がきちんとしている'),
('参加者のレベルが書いてある','分からないまま行くと、気をつかって楽しめない'),
('運営している人が分かる','誰が運営しているか分からない場は避ける')]
y=150
for i,(a,b) in enumerate(items):
    d.rounded_rectangle([56,y,W-56,y+118],radius=14,fill=WHITE)
    d.rectangle([56,y,68,y+118],fill=TEAL)
    d.rounded_rectangle([96,y+30,152,y+86],radius=8,outline=NAVY,width=5)
    txt(d,(124,y+58),str(i+1),34,NAVY,anchor='mm')
    txt(d,(180,y+22),a,36,NAVY)
    txt(d,(180,y+72),b,26,MUTED,sw=0)
    y+=134
txt(d,(W-64,H-22),'2つ以上当てはまらなければ、別のサークルを探そう',26,NAVY,anchor='rs')
im.save(OUT+'/02_checklist.png')

# 03 team rules
im=Image.new('RGB',(W,H),NAVY); d=ImageDraw.Draw(im)
txt(d,(64,40),'ひとり参加でも入りやすい',46,WHITE)
d.rectangle([56,104,56+46*11+10,170],fill=YEL); txt(d,(64,110),'チーム分け 5つのポイント',46,NAVY)
txt(d,(W-64,60),'サークル選びの目安に',30,TEAL,anchor='ra')
rules=[('レベルを聞いてから分ける','未経験・ブランクあり・経験者が偏らない'),
('初参加の人が固まらない','初参加どうしで止まらないように'),
('慣れた人が声かけ役に入る','ルール説明や「次はこっち」の声かけ'),
('試合ごとにメンバーが入れ替わる','合わなくても逃げ場がある'),
('勝ち負けより、プレーが続くこと','ラリーが続いたら喜ぶ空気')]
y=200
for i,(a,b) in enumerate(rules):
    d.ellipse([64,y+6,124,y+66],fill=TEAL); txt(d,(94,y+36),str(i+1),34,WHITE,anchor='mm')
    txt(d,(150,y+8),a,36,WHITE)
    txt(d,(150,y+54),b,24,(200,210,232),sw=0)
    y+=100
court(d,860,300,360,300,(40,66,128),4)
txt(d,(W-64,H-28),'マカシェットスポーツ',28,YEL,anchor='rs')
im.save(OUT+'/03_team_rules.png')
