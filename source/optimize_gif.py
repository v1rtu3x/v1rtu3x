"""Lossless, palette-stable GIF writer with transparent unchanged pixels.

Pillow's public legacy GIF helpers are used to write frame rectangles with
explicit durations. No lossy optimization, frame dropping, or dithering.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import GifImagePlugin, Image


def save_delta_gif(frames: Sequence[Image.Image], path: Path,
                   duration_ms: int | Sequence[int] = 40) -> None:
    if not frames:
        raise ValueError('At least one palette image is required')
    first=frames[0]
    if first.mode!='P':
        raise ValueError('Frames must share one palette (mode P)')
    palette=first.getpalette()
    if not palette:
        raise ValueError('A global palette is required')
    palette=(palette+[0]*(768-len(palette)))[:768]
    durations=([int(duration_ms)]*len(frames) if isinstance(duration_ms,int)
               else list(duration_ms))
    if len(durations)!=len(frames) or any(d<10 for d in durations):
        raise ValueError('Every GIF frame needs a duration of at least 10 ms')
    path=Path(path)
    temp=path.with_name(path.name+'.tmp')
    previous=None
    with temp.open('wb') as out:
        header,_=GifImagePlugin.getheader(first,info={'loop':0,'version':b'GIF89a'})
        for block in header:
            out.write(block)
        for i,frame in enumerate(frames):
            if frame.mode!='P' or frame.size!=first.size:
                raise ValueError('All frames must have the same size and palette mode')
            data=np.asarray(frame,dtype=np.uint8)
            if np.any(data==255):
                raise ValueError('Palette index 255 must be reserved for transparency')
            if previous is None:
                tile=frame.copy()
                offset=(0,0)
            else:
                changed=data!=previous
                ys=np.flatnonzero(changed.any(axis=1))
                xs=np.flatnonzero(changed.any(axis=0))
                if not len(xs):
                    tile=Image.new('P',(1,1),255)
                    offset=(0,0)
                else:
                    x0,x1=int(xs[0]),int(xs[-1])+1
                    y0,y1=int(ys[0]),int(ys[-1])+1
                    small=data[y0:y1,x0:x1].copy()
                    small[~changed[y0:y1,x0:x1]]=255
                    tile=Image.frombytes('P',(x1-x0,y1-y0),small.tobytes())
                    offset=(x0,y0)
                tile.putpalette(palette)
            for block in GifImagePlugin.getdata(tile,offset=offset,duration=durations[i],
                    disposal=1,transparency=255,include_color_table=False):
                out.write(block)
            previous=data.copy()
        out.write(b';')
    temp.replace(path)


def optimize_existing(path: Path) -> dict:
    path=Path(path)
    frames=[]
    durations=[]
    with Image.open(path) as im:
        pal=Image.new('P',(1,1))
        pal.putpalette(im.getpalette())
        for i in range(im.n_frames):
            im.seek(i)
            frames.append(im.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE))
            durations.append(im.info.get('duration',40))
    before=path.stat().st_size
    optimized=path.with_name(path.stem+'-optimized.gif')
    save_delta_gif(frames,optimized,durations)
    # Compare EVERY decoded frame to the uncompressed palette frames.
    with Image.open(optimized) as check:
        if check.n_frames!=len(frames):
            raise AssertionError((check.n_frames,len(frames)))
        total=0
        for i,frame in enumerate(frames):
            check.seek(i)
            if not np.array_equal(np.asarray(check.convert('RGB')),
                                  np.asarray(frame.convert('RGB'))):
                raise AssertionError(f'GIF pixel mismatch in frame {i}')
            total+=check.info.get('duration',0)
        if total!=sum(durations):
            raise AssertionError('GIF duration changed')
    optimized.replace(path)
    return {'file':path.name,'before_bytes':before,'after_bytes':path.stat().st_size,
            'frames_verified':len(frames),'duration_ms':sum(durations)}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('gif',nargs='+',type=Path)
    args=ap.parse_args()
    for path in args.gif:
        print(optimize_existing(path),flush=True)
