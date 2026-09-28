#!/usr/bin/env python3
from pathlib import Path
import json,tempfile,time,argparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parent;APP=ROOT/'image-approvals.json';APPROVED=ROOT/'approved-images.json';OUT=ROOT/'images'
def load(p,d): return json.loads(p.read_text(encoding='utf-8')) if p.exists() else d
def chosen(p):
 c=p.get('candidates',[]);i=p.get('selected')
 if isinstance(i,int) and 0<=i<len(c): return c[i],i
 return None,None
def get(url,path):
 last=None
 for n in range(5):
  try:
   r=urlopen(Request(url,headers={'User-Agent':'Ari-NBA-Cards/1.4'}),timeout=40)
   with path.open('wb') as f:
    while True:
     b=r.read(1024*1024)
     if not b:break
     f.write(b)
   return
  except HTTPError as e:
   last=e
   if e.code not in (429,500,502,503,504): raise
   time.sleep(min(60,5*2**n))
  except (URLError,TimeoutError) as e:
   last=e;time.sleep(min(30,3*2**n))
 raise RuntimeError(f'download failed: {last}')
def process(src,dst,c):
 with Image.open(src) as im:
  im=ImageOps.exif_transpose(im).convert('RGB');c=c or {}
  z=max(1,float(c.get('zoom',1)));x=max(0,min(100,float(c.get('x',50))));y=max(0,min(100,float(c.get('y',50))))
  w,h=im.size;bw=min(w,h*3/4);bh=bw*4/3;cw=bw/z;ch=bh/z
  left=max(0,w-cw)*x/100;top=max(0,h-ch)*y/100
  im.crop((round(left),round(top),round(left+cw),round(top+ch))).resize((900,1200),Image.Resampling.LANCZOS).save(dst,'JPEG',quality=88,optimize=True)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');a=ap.parse_args()
 d=load(APP,{'players':{}}).get('players',{});fallback=load(APPROVED,{'players':{}}).get('players',{});OUT.mkdir(exist_ok=True)
 failures=[]
 for pid,p in d.items():
  if p.get('state')!='approved':continue
  c,i=chosen(p);urls=[]
  if c:
   if c.get('url'):urls.append(c['url'])
   if c.get('original'):urls.append(c['original'])
  fx=fallback.get(pid,{})
  if fx.get('download_url'):urls.append(fx['download_url'])
  urls=list(dict.fromkeys(urls))
  if not urls: print('SKIP',p.get('name',pid));continue
  dst=OUT/f'{pid}.jpg'
  if dst.exists() and not a.force:continue
  crop=(p.get('crops') or {}).get(str(i),{}) if i is not None else {}
  ok=False
  for n,url in enumerate(urls):
   try:
    with tempfile.TemporaryDirectory() as td:
     raw=Path(td)/'src';print('DOWN',p.get('name',pid),'candidate',i,'source',n);get(url,raw);process(raw,dst,crop)
    print('OK',p.get('name',pid),'900x1200');ok=True;break
   except Exception as e:print('TRY FAILED',p.get('name',pid),e)
  if not ok: failures.append(p.get('name',pid))
 print('MISSING/FAILED IMAGES:',len(failures))
 for n in failures: print('  ',n)
if __name__=='__main__':main()
