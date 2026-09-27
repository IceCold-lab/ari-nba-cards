#!/usr/bin/env python3
from pathlib import Path
import json,tempfile,time,argparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parent;APP=ROOT/'image-approvals.json';OUT=ROOT/'images';MAN=ROOT/'image-manifest.json'
def load(p,d): return json.loads(p.read_text()) if p.exists() else d
def chosen(p):
 c=p.get('candidates',[]);i=p.get('selected')
 if isinstance(i,int) and 0<=i<len(c): return c[i],i
 return None,None
def get(url,path):
 for n in range(5):
  try:
   r=urlopen(Request(url,headers={'User-Agent':'Ari-NBA-Cards/1.3'}),timeout=40)
   with path.open('wb') as f:f.write(r.read(25*1024*1024+1))
   return
  except HTTPError as e:
   if e.code not in (429,500,502,503,504):raise
   time.sleep(min(60,5*2**n))
  except (URLError,TimeoutError):
   time.sleep(min(30,3*2**n))
 raise RuntimeError('download failed after retries')
def process(src,dst,c):
 with Image.open(src) as im:
  im=ImageOps.exif_transpose(im).convert('RGB');c=c or {};z=max(1,float(c.get('zoom',1)));x=max(0,min(100,float(c.get('x',50))));y=max(0,min(100,float(c.get('y',50))))
  w,h=im.size;bw=min(w,h*3/4);bh=bw*4/3;cw=bw/z;ch=bh/z;left=max(0,w-cw)*x/100;top=max(0,h-ch)*y/100
  im.crop((round(left),round(top),round(left+cw),round(top+ch))).resize((900,1200),Image.Resampling.LANCZOS).save(dst,'JPEG',quality=88,optimize=True)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');a=ap.parse_args();d=load(APP,{'players':{}}).get('players',{});OUT.mkdir(exist_ok=True)
 for pid,p in d.items():
  if p.get('state')!='approved':continue
  c,i=chosen(p)
  if not c:print('SKIP',p.get('name',pid));continue
  url=c.get('url') or c.get('original');dst=OUT/f'{pid}.jpg'
  if dst.exists() and not a.force:continue
  crop=(p.get('crops') or {}).get(str(i),{})
  try:
   with tempfile.TemporaryDirectory() as td:
    raw=Path(td)/'src';print('DOWN',p.get('name',pid),'candidate',i);get(url,raw);process(raw,dst,crop)
   print('OK',p.get('name',pid),'900x1200')
  except Exception as e:print('FAIL',p.get('name',pid),e)
if __name__=='__main__':main()
