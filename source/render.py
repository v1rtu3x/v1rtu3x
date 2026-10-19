#!/usr/bin/env python3
"""Render the self-contained TUI header for Mark-Paul Tamas.

Pillow and NumPy; no network calls. Each frame is drawn from editable primitives.
25 fps, 14-second loop. No fonts are bundled. Pass --font and --bold-font
when DejaVu Sans Mono is not installed at one of the detected locations.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import random
import sys
import time
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont, ImageChops
from aes_trace import first_round, encrypt_example, PLAINTEXT, KEY, CIPHERTEXT
from optimize_gif import save_delta_gif

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
DURATION = 14.0
FPS = 25
SCALE = 2
NAME = 'MARK-PAUL TAMAS'
ROLE = 'Product Security Engineer'
SUBTITLE = 'Cryptography / secure software / embedded systems'
STAGES = ('SubBytes', 'ShiftRows', 'MixColumns', 'AddRoundKey')
TRACE = first_round()
PALETTES = {
    'dark': {
        'bg': '#09141c', 'bar': '#0d1c27', 'panel': '#0c1822',
        'line': '#304e5e', 'grid': '#1b3645', 'fg': '#eee9db',
        'secondary': '#b7cbd0', 'muted': '#85a7b7', 'dim': '#4f7285',
        'accent': '#e7b26b', 'blue': '#8bb8cb', 'green': '#a9bfae',
    },
    'light': {
        'bg': '#f3efe5', 'bar': '#e9e5d9', 'panel': '#f8f5ec',
        'line': '#a4b5b7', 'grid': '#d8dfda', 'fg': '#12354e',
        'secondary': '#274c5f', 'muted': '#516c78', 'dim': '#8a9ca1',
        'accent': '#925e1a', 'blue': '#34697d', 'green': '#426451',
    },
}


def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return max(a, min(b, x))


def smooth(x: float) -> float:
    x = clamp(x)
    return x * x * (3 - 2 * x)


def rgba(v: str, alpha: int = 255) -> tuple[int, int, int, int]:
    return tuple(int(v[i:i+2], 16) for i in (1, 3, 5)) + (alpha,)


def mix(a: str, b: str, q: float) -> str:
    q = clamp(q)
    aa, bb = rgba(a), rgba(b)
    return '#' + ''.join(f'{round(aa[i] + (bb[i] - aa[i]) * q):02x}' for i in range(3))


def find_font(bold: bool = False, requested: str | None = None) -> str:
    if requested:
        p = Path(requested).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f'Font not found: {p}')
        return str(p)
    filename = 'DejaVuSansMono-Bold.ttf' if bold else 'DejaVuSansMono.ttf'
    candidates = [Path('/usr/share/fonts/truetype/dejavu') / filename,
                  Path('/usr/local/share/fonts') / filename,
                  Path.home() / '.local/share/fonts' / filename,
                  Path.home() / 'Library/Fonts' / filename]
    for p in candidates:
        if p.is_file():
            return str(p)
    raise FileNotFoundError('Install DejaVu Sans Mono or pass --font and --bold-font.')


class Renderer:
    def __init__(self, theme: str, mobile: bool, font: str, bold_font: str, scale: int = 2):
        self.theme, self.mobile = theme, mobile
        self.p = PALETTES[theme]
        self.scale = scale
        self.font_path, self.bold_path = font, bold_font
        self.w, self.h = (800, 792) if mobile else (1600, 548)
        self.idbox = (24, 84, 752, 244) if mobile else (28, 88, 858, 274)
        self.aesbox = (24, 358, 752, 216) if mobile else (910, 88, 662, 274)
        self.fonts = {}
        self.base = self.make_base()
        self.fade_masks = {}
        rng = random.Random(197)
        self.sequences = []
        alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ023456789'
        for i, ch in enumerate(NAME):
            seq = [ch] + [rng.choice(alphabet) for _ in range(8 + i % 4)] + [ch]
            self.sequences.append(seq)

    def font(self, size: float, bold: bool = False):
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(self.bold_path if bold else self.font_path,
                                                round(size * self.scale))
        return self.fonts[key]

    def draw(self, im: Image.Image):
        return ImageDraw.Draw(im)

    def text(self, im, x, y, value, size=16, color='fg', bold=False, anchor='ls', opacity=1):
        fill = self.p.get(color, color)
        if opacity != 1:
            fill = mix(self.p['panel'], fill, opacity)
        self.draw(im).text((round(x*self.scale), round(y*self.scale)), value,
                          font=self.font(size, bold), fill=fill, anchor=anchor,
                          stroke_width=0)

    def text_width(self, value, size, bold=False):
        return self.font(size, bold).getlength(value)/self.scale

    def line(self, im, x1, y1, x2, y2, color='line', width=1):
        self.draw(im).line(tuple(round(v*self.scale) for v in (x1, y1, x2, y2)),
                           fill=self.p.get(color, color), width=max(1,round(width*self.scale)))

    def rect(self, im, x, y, w, h, fill=None, outline=None, radius=0, width=1):
        fill = self.p.get(fill, fill)
        outline = self.p.get(outline, outline)
        box = tuple(round(v*self.scale) for v in (x, y, x+w, y+h))
        if radius:
            self.draw(im).rounded_rectangle(box, radius=round(radius*self.scale), fill=fill,
                                             outline=outline, width=max(1,round(width*self.scale)))
        else:
            self.draw(im).rectangle(box, fill=fill, outline=outline,
                                     width=max(1,round(width*self.scale)))

    def dot(self, im, x, y, r, color='accent'):
        self.draw(im).ellipse(tuple(round(v*self.scale) for v in (x-r,y-r,x+r,y+r)),
                              fill=self.p.get(color,color))

    def box(self, im, x, y, w, h, label, size=15):
        self.rect(im,x,y,w,h,'panel','line',radius=2)
        ww=self.text_width(label,size)+24
        self.rect(im,x+16,y-11,ww,22,'bg')
        self.text(im,x+24,y+5,label,size,'muted')

    def icon(self, im, x, y, kind, size=46):
        self.rect(im,x,y,size,size,'panel','line',radius=2)
        cx,cy=x+size/2,y+size/2
        c='accent'
        if kind==0:
            self.rect(im,cx-10,cy-1,20,16,None,c,radius=1,width=1.4)
            self.draw(im).arc(tuple(round(v*self.scale) for v in (cx-7,cy-13,cx+7,cy+5)),
                             180,360,fill=self.p[c],width=round(1.5*self.scale))
            self.dot(im,cx,cy+6,1.8,c)
            self.line(im,cx,cy+7,cx,cy+10,c,1.2)
        elif kind==1:
            pts=[(cx,cy-13),(cx-13,cy+11),(cx+13,cy+11)]
            for a,b in ((0,1),(0,2),(1,2)):
                self.line(im,*pts[a],*pts[b],c,1.5)
            for px,py in pts:
                self.dot(im,px,py,4,c)
                self.dot(im,px,py,2,'panel')
        else:
            self.rect(im,cx-10,cy-10,20,20,None,c,width=1.5)
            for d in (-6,0,6):
                self.line(im,cx+d,cy-15,cx+d,cy-11,c,1.4)
                self.line(im,cx+d,cy+11,cx+d,cy+15,c,1.4)
                self.line(im,cx-15,cy+d,cx-11,cy+d,c,1.4)
                self.line(im,cx+11,cy+d,cx+15,cy+d,c,1.4)

    def make_base(self):
        im=Image.new('RGB',(self.w*self.scale,self.h*self.scale),self.p['bg'])
        self.rect(im,1,1,self.w-2,self.h-2,None,'line',radius=10,width=1.5)
        self.rect(im,2,2,self.w-4,53,'bar',radius=8)
        self.line(im,1,56,self.w-1,56)
        self.dot(im,30,28,4)
        self.text(im,52,35,'v1rtu3x@github',18,'secondary',True)
        self.text(im,244,35,': ~/profile',18,'muted')
        if not self.mobile:
            self.text(im,self.w-28,35,'PRODUCT SECURITY / ENGINEERING',16,'muted',anchor='rs')
        else:
            self.text(im,self.w-26,35,'SECURITY / ENGINEERING',13,'muted',anchor='rs')
        self.box(im,*self.idbox,'01 / IDENTITY')
        self.box(im,*self.aesbox,'AES-128 / ROUND 01')
        x,y,w,h=self.idbox
        # Only a small, stationary dot field. No texture behind the primary text.
        for xx in range(round(x+w-210),round(x+w-22),20):
            for yy in range(round(y+34),round(y+h-26),20):
                self.dot(im,xx,yy,.7,'grid')
        self.text(im,x+28,y+35,'$ whoami',18,'muted')
        if self.mobile:
            cards=[(24,610,240,116),(280,610,240,116),(536,610,240,116)]
            labels=['02 / KEY HANDLING','03 / PROTOCOL STATE','04 / EMBEDDED TESTING']
            for i,(xx,yy,ww,hh) in enumerate(cards):
                self.box(im,xx,yy,ww,hh,labels[i],11)
                self.icon(im,xx+17,yy+27,i,36)
                a,b=[('Mbed TLS','TF-PSA-Crypto'),('DMTF','libspdm'),('Zephyr','RTOS')][i]
                self.text(im,xx+66,yy+49,a,18,'secondary',True)
                self.text(im,xx+66,yy+76,b,15,'muted')
            footer=750
        else:
            labels=['02 / KEY HANDLING','03 / PROTOCOL STATE','04 / EMBEDDED TESTING']
            for i,(xx,ww) in enumerate([(28,499),(550,499),(1072,500)]):
                self.box(im,xx,398,ww,90,labels[i],15)
                self.icon(im,xx+20,422,i,46)
                self.text(im,xx+88,453,['Mbed TLS / TF-PSA','DMTF / libspdm','Zephyr RTOS'][i],25,'secondary',True)
            footer=510
        self.line(im,1,footer,self.w-1,footer)
        self.text(im,28,footer+26,'v1rtu3x:~$ cat README.md',17,'muted')
        if not self.mobile:
            self.line(im,self.w-439,footer+11,self.w-439,footer+27,'line')
            self.text(im,self.w-28,footer+26,'SELECTED MERGED UPSTREAM WORK',14,'muted',anchor='rs')
        # AES grid headings / outline are static; values are redrawn for motion.
        for k,stage in enumerate(STAGES):
            gx,gy,cell=self.grid_location(k)
            self.text(im,gx,gy-34,f'{k+1:02}',11,'dim')
            self.text(im,gx+12,gy-15,stage,13 if not self.mobile else 14,'muted')
            self.dot(im,gx+3,gy-20,2.5,'dim')
            if k<3:
                nx,_,_=self.grid_location(k+1)
                mid=(gx+4*cell+nx)/2
                self.text(im,mid,gy+2*cell+5,'\u2192',19,'dim',anchor='ms')
        return im

    def grid_location(self,k):
        x,y,w,h=self.aesbox
        cell=27 if not self.mobile else 28
        grid_w=cell*4
        margin=25
        step=(w-2*margin-grid_w)/3
        return x+margin+k*step,y+(88 if not self.mobile else 59),cell

    def glyph(self, ch, size, color, height, bold=True):
        return self._glyph(ch,size,color,height,bold)

    @lru_cache(maxsize=2048)
    def _glyph(self, ch, size, color, height, bold):
        width=math.ceil(self.text_width('M',size,bold)+3)
        tile=Image.new('RGBA',(width*self.scale,round(height*self.scale)),(0,0,0,0))
        ImageDraw.Draw(tile).text((0,round((height-8)*self.scale)),ch,
            font=self.font(size,bold),fill=rgba(color),anchor='ls')
        return tile

    def identity(self,im,t,poster=False):
        x,y,w,h=self.idbox
        size=46 if not self.mobile else 43
        rowh=58 if not self.mobile else 55
        name_x=x+28
        baseline=y+(142 if not self.mobile else 128)
        pitch=self.text_width('M',size,True)+1.0
        active=1.2<=t<5.1 and not poster
        for i,ch in enumerate(NAME):
            char_x=name_x+i*pitch
            seq=self.sequences[i]
            if active and ch not in ' -':
                start=1.2+i*.035
                end=3.95+i*.072
                u=clamp((t-start)/(end-start))
                # Smooth acceleration, then easing into the final plaintext glyph.
                progress=smooth(u)*(len(seq)-1)
                n=int(progress)
                frac=progress-n
                current=seq[min(n,len(seq)-1)]
                nxt=seq[min(n+1,len(seq)-1)]
                color=self.p['fg'] if u>.72 or u==0 else mix(self.p['secondary'],self.p['fg'],.55)
                viewport=Image.new('RGBA',(math.ceil(pitch+3)*self.scale,round(rowh*self.scale)),(0,0,0,0))
                g1=self.glyph(current,size,color,rowh)
                g2=self.glyph(nxt,size,color,rowh)
                viewport.alpha_composite(g1,(0,round(-frac*rowh*self.scale)))
                viewport.alpha_composite(g2,(0,round((1-frac)*rowh*self.scale)))
                # Soft clipping at top/bottom avoids harsh cut edges on rolling glyphs.
                shape=viewport.size
                if shape not in self.fade_masks:
                    mask=Image.new('L',shape,255)
                    md=ImageDraw.Draw(mask)
                    for yy in range(7*self.scale):
                        a=round(255*smooth(yy/(7*self.scale)))
                        md.line((0,yy,shape[0],yy),fill=a)
                        md.line((0,shape[1]-1-yy,shape[0],shape[1]-1-yy),fill=a)
                    self.fade_masks[shape]=mask
                viewport.putalpha(ImageChops.multiply(viewport.getchannel('A'),self.fade_masks[shape]))
                im.paste(viewport,(round(char_x*self.scale),round((baseline-rowh+8)*self.scale)),viewport)
            else:
                self.text(im,char_x,baseline,ch,size,'fg',True)
        # Two understated ghost rows visible only during the rotating-name phase.
        if active:
            opacity=.27*math.sin(math.pi*clamp((t-1.2)/3.9))
            for row in (0,1):
                ghost=''.join(ch if ch in ' -' else self.sequences[i][(int(t*6)+i+row*3) % (len(self.sequences[i])-1)]
                              for i,ch in enumerate(NAME))
                self.text(im,name_x,y+66+row*22,ghost,18,'blue',opacity=opacity*(.55+.45*row))
        # Terminal typing is decorative, not a live command or cryptographic attack.
        if poster or t<1.2 or t>=8.25:
            nr,ns=len(ROLE),len(SUBTITLE)
        elif t<4.75:
            nr,ns=0,0
        else:
            nr=round(len(ROLE)*clamp((t-4.75)/1.45))
            ns=round(len(SUBTITLE)*clamp((t-6.3)/1.9))
        role_y=y+(191 if not self.mobile else 173)
        self.text(im,name_x,role_y,'>',27,'accent')
        self.text(im,name_x+26,role_y,ROLE[:nr],28 if not self.mobile else 26,'blue')
        sub_y=y+(230 if not self.mobile else 210)
        self.text(im,name_x,sub_y,'|',18,'accent')
        self.text(im,name_x+24,sub_y,SUBTITLE[:ns],18 if not self.mobile else 16.8,'secondary')
        if not self.mobile:
            status='[resolving]' if active else '[decrypted]'
            self.text(im,x+w-22,y+h-15,status,12,'accent' if active else 'dim',anchor='rs')
        cursor_alpha=.35+.55*(.5+.5*math.cos(2*math.pi*t/1.8))
        if poster:
            cursor_alpha=.8
        # A slim name caret only after a name is resolved.
        if not active:
            self.rect(im,name_x+len(NAME)*pitch+7,baseline-size*.75,5,size*.79,
                      mix(self.p['panel'],self.p['accent'],cursor_alpha))
        if 4.75<=t<6.25:
            xx=name_x+26+self.text_width(ROLE[:nr],28 if not self.mobile else 26)+3
            self.rect(im,xx,role_y-22,9,25,'accent')
        elif 6.3<=t<8.25:
            fs=18 if not self.mobile else 16.8
            xx=name_x+24+self.text_width(SUBTITLE[:ns],fs)+3
            self.rect(im,xx,sub_y-14,7,17,'accent')

    def stage_progress(self,k,t,poster=False):
        if poster or t<1.2:
            return 1.0
        if t<1.5:
            return 1-smooth((t-1.2)/.3)
        starts=(1.5,4.0,6.5,9.0)
        return smooth((t-starts[k])/2.2)

    def cell(self,im,x,y,size,v,color='secondary',highlight=0):
        bg=mix(self.p['panel'],self.p['accent'],.13*highlight)
        edge=mix(self.p['line'],self.p['accent'],.72*highlight)
        self.rect(im,x,y,size,size,bg,edge,width=.8)
        self.text(im,x+size/2,y+size/2+5,f'{v:02X}',14 if not self.mobile else 15,
                  color,anchor='ms')

    def aes(self,im,t,poster=False):
        states=[(TRACE['start'],TRACE['sub']),(TRACE['sub'],TRACE['shift']),
                (TRACE['shift'],TRACE['mix']),(TRACE['mix'],TRACE['out'])]
        starts=(1.5,4.0,6.5,9.0)
        active=-1
        for k,(before,after) in enumerate(states):
            gx,gy,cell=self.grid_location(k)
            q=self.stage_progress(k,t,poster)
            if starts[k]<=t<=starts[k]+2.2 and not poster:
                active=k
                self.dot(im,gx+3,gy-20,3,'accent')
                self.text(im,gx+12,gy-15,STAGES[k],13 if not self.mobile else 14,'secondary')
            if k==1 and 0<q<1:
                # Cyclic row motion. Real AES rows move left by 0,1,2,3 cells.
                for r in range(4):
                    row=Image.new('RGB',(round(4*cell*self.scale),round(cell*self.scale)),self.p['panel'])
                    for c in range(4):
                        offset=((c-r*q)%4)*cell
                        for xx in (offset,offset-4*cell):
                            self.cell(row,xx,0,cell,before[4*c+r],highlight=.45*math.sin(math.pi*q)*(r>0))
                    im.paste(row,(round(gx*self.scale),round((gy+r*cell)*self.scale)))
                self.rect(im,gx,gy,4*cell,4*cell,None,'line',width=.8)
            else:
                for r in range(4):
                    for c in range(4):
                        idx=4*c+r
                        if k==0:
                            vq=smooth((q-.027*idx)/.595)
                        elif k==2:
                            vq=smooth((q-.18*c)/.46)
                        elif k==3:
                            vq=smooth((q-.035*idx)/.475)
                        else:
                            vq=q
                        vv=after[idx] if vq>=.5 else before[idx]
                        hi=math.sin(math.pi*vq) if 0<vq<1 else 0
                        self.cell(im,gx+c*cell,gy+r*cell,cell,vv,highlight=hi)
                        if 0<vq<1:
                            # Values cross-fade using a local text-only overlay.
                            bx=gx+c*cell; by=gy+r*cell
                            bg=mix(self.p['panel'],self.p['accent'],.13*hi)
                            self.rect(im,bx+2,by+2,cell-4,cell-4,bg)
                            fg=mix(bg,self.p['secondary'],abs(vq-.5)*2)
                            self.text(im,bx+cell/2,by+cell/2+5,f'{vv:02X}',14 if not self.mobile else 15,fg,anchor='ms')
                if k==2 and 0<q<1:
                    col=min(3,int(q*4))
                    self.rect(im,gx+col*cell,gy,cell,cell*4,None,
                              mix(self.p['line'],self.p['accent'],.9*math.sin(math.pi*(q*4-col))),width=1.2)
            # Each stage keeps a small progress baseline, never a fake live metric.
            self.line(im,gx,gy+4*cell+13,gx+4*cell,gy+4*cell+13,'line',.8)
            if q:
                self.line(im,gx,gy+4*cell+13,gx+4*cell*q,gy+4*cell+13,'accent',1.1)
        x,y,w,h=self.aesbox
        if active==0:
            idx=min(15,int(clamp((t-1.5)/2.2)*16))
            detail=f'S-box  {TRACE["start"][idx]:02X}  ->  {TRACE["sub"][idx]:02X}'
        elif active==1:
            detail='rows rotate left by 0 / 1 / 2 / 3 bytes'
        elif active==2:
            detail='column diffusion in GF(2^8)'
        elif active==3:
            idx=min(15,int(clamp((t-9.0)/2.2)*16))
            detail=f'K01  |  {TRACE["mix"][idx]:02X}  XOR  {TRACE["key"][idx]:02X}  =  {TRACE["out"][idx]:02X}'
        else:
            detail='forward round / FIPS 197'
        line_y=y+h-48 if not self.mobile else y+h-38
        self.line(im,x+25,line_y,x+w-25,line_y,'line',.8)
        self.text(im,x+w/2,y+h-22 if not self.mobile else y+h-15,detail,
                  14 if not self.mobile else 14,'muted',anchor='ms')

    def frame(self,t,poster=False):
        im=self.base.copy()
        self.identity(im,t,poster)
        self.aes(im,t,poster)
        footer=750 if self.mobile else 510
        x=28+self.text_width('v1rtu3x:~$ cat README.md',17)+8
        alpha=.35+.5*(.5+.5*math.cos(2*math.pi*t/1.8))
        if poster:
            alpha=.85
        self.rect(im,x,footer+12,8,17,mix(self.p['bg'],self.p['accent'],alpha))
        return im.resize((self.w,self.h),Image.Resampling.LANCZOS)

    def export(self, poster_only=False):
        stem='header-'+self.theme+('-mobile' if self.mobile else '')
        ASSETS.mkdir(exist_ok=True)
        poster=self.frame(0,poster=True)
        poster.save(ASSETS/(stem+'.png'),optimize=True)
        if poster_only:
            print(stem+' poster',flush=True)
            return
        # A single global palette gives stable text edges (no per-frame shimmer).
        sample=poster.copy()
        dr=ImageDraw.Draw(sample)
        for i in range(128):
            xx=(i%64)*5; yy=(i//64)*5
            dr.rectangle((xx,yy,xx+4,yy+4),fill=mix(self.p['panel'],self.p['accent'],i/127))
        pal=sample.quantize(colors=192,method=Image.Quantize.MEDIANCUT)
        frames=[]
        count=round(DURATION*FPS)
        for n in range(count):
            im=self.frame(n/FPS)
            frames.append(im.quantize(palette=pal,dither=Image.Dither.NONE))
            if n%100==0:
                print(stem+f' {n}/{count}',flush=True)
        path=ASSETS/(stem+'.gif')
        print(stem+' frames ready, starting GIF encoder',time.time(),flush=True)
        save_delta_gif(frames, path, round(1000/FPS))
        print(stem+' GIF saved, validating',time.time(),flush=True)
        with Image.open(path) as check:
            total=0
            for n in range(check.n_frames):
                check.seek(n)
                total+=check.info.get('duration',0)
            assert total==round(DURATION*1000),(path,total)
            assert check.info.get('loop')==0
            assert check.n_frames>200
            info=dict(file=path.name,width=self.w,height=self.h,frames=check.n_frames,
                      duration_ms=total,bytes=path.stat().st_size,loop=0)
        (ROOT/'source'/f'{stem}-validation.json').write_text(json.dumps(info,indent=2)+'\n')
        print(json.dumps(info),flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--theme',choices=['dark','light','all'],default='all')
    ap.add_argument('--layout',choices=['desktop','mobile','all'],default='all')
    ap.add_argument('--font')
    ap.add_argument('--bold-font')
    ap.add_argument('--posters-only',action='store_true')
    args=ap.parse_args()
    assert encrypt_example(PLAINTEXT,KEY)==CIPHERTEXT,'AES known-answer test failed'
    regular=find_font(False,args.font)
    bold=find_font(True,args.bold_font or args.font)
    themes=PALETTES if args.theme=='all' else [args.theme]
    layouts=[False,True] if args.layout=='all' else [args.layout=='mobile']
    for theme in themes:
        for mobile in layouts:
            Renderer(theme,mobile,regular,bold).export(args.posters_only)


if __name__=='__main__':
    main()
