#!/usr/bin/env python3
"""One-time import of FYHOM WordPress property listings. All imported offers stay HIDDEN.
Copies photos into this repository so the new site does not use old-site images.
Existing offers are not overwritten."""
import io,json,re,time,sys
from pathlib import Path
from urllib.parse import urljoin,urlsplit,urlunsplit
from xml.etree import ElementTree
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]
ORIGIN="https://fyhom.es"
PROPERTY=re.compile(r"^/(?:[a-z]{2}/)?property/[^/]+/?$",re.I)
MEDIA=re.compile(r"\.(?:jpe?g|png|webp)$",re.I)
SKIP=re.compile(r"logo|fyh[_-]?oro|favicon|icon|avatar|placeholder",re.I)
PLACES=["La Vall de Gallinera","Vall de Gallinera","Els Poblets","El Verger","El Vergel","Beniarbeig","Benitachell","Jávea","Javea","Xàbia","Dénia","Denia","Pego","Oliva","Calpe","Altea","Pedreguer","Ondara","Teulada","Moraira","Benissa"]
s=requests.Session()
s.headers.update({"User-Agent":"FYHOM owner migration/1.0"})
def clean(url):
    p=urlsplit(urljoin(ORIGIN,url))
    return urlunsplit(("https","fyhom.es",p.path,"","")) if p.hostname in ("fyhom.es","www.fyhom.es") else ""
def page(url):
    try:
        r=s.get(url,timeout=(12,40));r.raise_for_status()
        return BeautifulSoup(r.text,"html.parser")
    except Exception as e:
        print("WARN page",url,str(e)[:150],flush=True);return None
def sitemap(url,seen,depth=0):
    if url in seen or depth>3:return []
    seen.add(url)
    try:
        r=s.get(url,timeout=(10,25));r.raise_for_status()
        if len(r.content)>3000000:return []
        root=ElementTree.fromstring(r.content)
    except Exception:return []
    out=[]
    for el in root.iter():
        if el.tag.split("}")[-1]!="loc" or not el.text:continue
        u=clean(el.text.strip())
        if PROPERTY.match(urlsplit(u).path):out.append(u)
        elif depth<3 and u and ("sitemap" in u or u.endswith(".xml")):out+=sitemap(u,seen,depth+1)
    return out
def find_urls():
    urls=set()
    for p in ("/sitemap_index.xml","/property-sitemap.xml","/wp-sitemap.xml","/wp-sitemap-posts-property-1.xml"):
        urls.update(sitemap(ORIGIN+p,set()))
    for p in ("/","/es/","/?post_type=property"):
        soup=page(ORIGIN+p)
        if soup:
            for a in soup.select("a[href]"):
                u=clean(a["href"])
                if PROPERTY.match(urlsplit(u).path):urls.add(u)
    return sorted(urls)
def number(t,words):
    m=re.search(r"(?:%s)\s*:?\s*(\d{1,5})\b"%words,t,re.I)
    return int(m.group(1)) if m else 0
def area(t):
    m=re.search(r"(?:m2|Superficie|Tamaño|Size|Quadratmeter)\s*:?\s*(\d{2,5})",t,re.I)
    if not m:m=re.search(r"(\d{2,5})\s*m\s*[²2]",t,re.I)
    return int(m.group(1)) if m else 0
def photos(soup):
    out=[]
    def add(v):
        if not v:return
        u=clean(str(v).split()[0])
        if u and MEDIA.search(u) and "/wp-content/uploads/" in u and not SKIP.search(u) and u not in out:out.append(u)
    for a in soup.select('a[href*="/wp-content/uploads/"]'):add(a.get("href"))
    for img in soup.select("img"):add(img.get("data-src") or img.get("data-lazy-src") or img.get("src"))
    for meta in soup.select('meta[property="og:image"]'):add(meta.get("content"))
    return out
def description(soup):
    for selector in ("#property-description .block-content-wrap","#property-description",".property-description-wrap .block-content-wrap",".property-description-wrap",".property-description"):
        section=soup.select_one(selector)
        if section:
            paras=[" ".join(p.stripped_strings) for p in section.find_all(["p","li"])]
            val="\n\n".join(x for x in paras[:20] if len(x)>15)[:4200]
            if len(val)>60:return val
    return ""
def parse(soup,url):
    h=soup.select_one("h1")
    if not h:return None
    title=" ".join(h.stripped_strings)
    if not title:return None
    main=soup.select_one("main") or soup
    body=" ".join(main.stripped_strings)
    where=body.find(title)
    first=body[where:where+9000] if where>=0 else body[:9000]
    before=body[max(0,where-250):where] if where>=0 else body[:100]
    mid=re.search(r"\bID\s*:?\s*(\d{3,10})\b",first,re.I)
    if not mid:return None
    price=re.search(r"(?:€\s*[\d.,]{5,}|[\d.,]{5,}\s*€)",before) or re.search(r"(?:€\s*[\d.,]{5,}|[\d.,]{5,}\s*€)",first[:350])
    value=int(re.sub(r"\D","",price.group(0))) if price else 0
    intro=first[:1400]
    desc=description(soup)
    beds=number(intro,"Dormitorios|Camas|Bedrooms|Schlafzimmer") or number(desc[:400],"Dormitorios|Bedrooms")
    baths=number(intro,"Baños|Banos|Bathrooms|Badezimmer") or number(desc[:400],"Baños|Bathrooms")
    sqm=area(intro) or area(desc[:500])
    city=next((p for p in PLACES if re.search(r"(?<!\w)"+re.escape(p)+r"(?!\w)",title,re.I)),None) or next((p for p in PLACES if p.lower() in intro[:500].lower()),"Costa Blanca Norte")
    kind=(title+" "+intro[:150]).lower()
    ptype="newbuild" if "obra nueva" in kind else "apartment" if any(x in kind for x in ("apartamento","piso","ático","dúplex","duplex")) else "townhouse" if any(x in kind for x in ("pareado","adosado")) else "villa" if any(x in kind for x in ("villa","chalet","finca")) else "house"
    sold=bool(re.search(r"\b(vendido|vendida|sold|verkauft)\b",before+" "+intro[:80],re.I))
    record={"id":mid.group(1),"title":title,"city":city,"type":ptype,"price":value,"beds":beds,"baths":baths,"area":sqm,"status":"hidden","featured":False,"description_es":desc}
    issues=[]
    if not value:issues.append("check_price")
    if not sqm:issues.append("check_area")
    if not desc:issues.append("check_description")
    if city=="Costa Blanca Norte":issues.append("check_city")
    if sold:issues.append("was_sold_on_old_site")
    return record,photos(soup),issues
def download(url,dest):
    if dest.exists():return True
    try:
        r=s.get(url,timeout=(12,40));r.raise_for_status()
        if not r.headers.get("Content-Type","").startswith("image/") or len(r.content)>9000000:return False
        im=ImageOps.exif_transpose(Image.open(io.BytesIO(r.content)))
        im.thumbnail((1600,1600),Image.Resampling.LANCZOS)
        if im.mode=="RGBA":
            bg=Image.new("RGB",im.size,"white");bg.paste(im,mask=im.getchannel("A"));im=bg
        elif im.mode!="RGB":im=im.convert("RGB")
        dest.parent.mkdir(parents=True,exist_ok=True)
        im.save(dest,"JPEG",quality=78,optimize=True,progressive=True)
        return True
    except Exception as e:
        print("WARN image",url,str(e)[:130],flush=True);return False
def main():
    urls=find_urls()[:100]
    print("Discovered",len(urls),"property pages",flush=True)
    if not urls:sys.exit("No listings found: existing data unchanged")
    path=ROOT/"content/properties.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    items=data.get("items",[])
    known={str(p.get("id")) for p in items}
    report=[];added=0
    for i,url in enumerate(urls,1):
        soup=page(url)
        if not soup:continue
        parsed=parse(soup,url)
        if not parsed:continue
        entry,pics,issues=parsed
        if entry["id"] in known:
            report.append({"id":entry["id"],"source":url,"status":"already_exists"});continue
        saved=[]
        for src in pics:
            if len(saved)>=16:break
            target=ROOT/"images/properties/imported"/entry["id"]/("%02d.jpg"%(len(saved)+1))
            if download(src,target):
                saved.append("/"+str(target.relative_to(ROOT)).replace("\\","/"))
            time.sleep(.08)
        if not saved:issues.append("no_photo_copied")
        entry["img"]=saved[0] if saved else ""
        entry["gallery"]=saved[1:]
        items.append(entry);known.add(entry["id"]);added+=1
        report.append({"id":entry["id"],"title":entry["title"],"source":url,"status":"hidden_for_review","photos_saved":len(saved),"photos_found":len(pics),"check":issues})
        print("%d/%d %s: %d images saved"%(i,len(urls),entry["id"],len(saved)),flush=True)
        time.sleep(.15)
    if added:path.write_text(json.dumps({"items":items},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (ROOT/"content/import-review.json").write_text(json.dumps({"total_discovered":len(urls),"new_offers":added,"all_hidden":True,"offers":report},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("COMPLETE:",added,"new drafts, all hidden",flush=True)
    if not report:sys.exit("Could not parse any property records")
if __name__=="__main__":main()
