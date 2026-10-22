#!/usr/bin/env python3
"""Read-only diagnostic for gallery boundaries on the original FYHOM WordPress site."""
import json,requests,re
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlsplit
from pathlib import Path
sites={
"20678":"https://fyhom.es/property/terreno-urbano-en-la-marina-alta-con-vistas-despejadas/",
"20597":"https://fyhom.es/property/chalet-pareado-diseno-moderno-els-poblets/",
"21191":"https://fyhom.es/property/parcela-rustica-de-mas-de-10-000-m%c2%b2-a-solo-15-minutos-del-mar-costa-blanca-2/"
}
def summarize(el):
  parents=[];parent=el
  while parent is not None and len(parents)<6:
    cls=' '.join(parent.get('class',[])[:3])
    ident=parent.get('id','')
    parents.append(f"{parent.name}#{ident}.{cls}"[:110])
    parent=parent.parent if getattr(parent,'parent',None) and hasattr(parent.parent,'name') else None
  return parents
def main():
  data={}
  session=requests.Session();session.headers['User-Agent']='FYHOM-gallery-verification/1.0'
  for identity,url in sites.items():
    entry={'url':url,'photos':[],'containerCounts':{},'galleryContainers':{}}
    try:
      r=session.get(url,timeout=32);r.raise_for_status()
      soup=BeautifulSoup(r.text,'html.parser')
      entry['title']=soup.title.get_text(" ",strip=True) if soup.title else None
      for el in soup.select('a[href],img[src],img[data-src],img[data-lazy-src]'):
        raw=el.get('href') or el.get('data-src') or el.get('data-lazy-src') or el.get('src') or ''
        if not re.search(r'/wp-content/uploads/.+?\.(?:jpg|jpeg|webp|png)',raw,re.I):continue
        parents=summarize(el);entry['photos'].append({'url':urljoin(url,raw).split('?')[0].split('/')[-1], 'ancestor':parents})
        for par in parents[1:4]:entry['containerCounts'][par]=entry['containerCounts'].get(par,0)+1
      for css in ['#property-gallery','.property-gallery','.property-gallery-wrap','.detail-media','.lightbox-gallery','.property-detail-media','.property-banner','.gallery-wrap','.property-media','.listing-gallery-wrap','.property-gallery-slider','.gallery-image','.top-gallery-section','.houzez-gallery']:
        nodes=soup.select(css)
        if nodes:entry['galleryContainers'][css]=[{'tag':n.name,'images':len(n.select('img')),'anchors':len(n.select('a'))} for n in nodes[:3]]
      entry['photos']=entry['photos'][:55]
    except Exception as exc:entry['error']=str(exc)[:300]
    data[identity]=entry
  dest=Path('content/source-gallery-diagnostic.json');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
  for k,v in data.items():print(k,len(v.get('photos',[])),v.get('error'),v.get('galleryContainers'))
if __name__=='__main__':main()
