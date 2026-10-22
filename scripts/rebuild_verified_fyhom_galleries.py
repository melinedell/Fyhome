#!/usr/bin/env python3
"""Rebuild FYHOM listing galleries strictly from the ORIGINAL property's lightbox.

Never include suggested-property thumbnails, page logos, floor plans from other
sections, or pictures belonging to other listing pages.
All images are self-hosted in GitHub. The property status and translations remain intact.
The script requires matching reference IDs before making any changes.
"""
import json,time,re
from pathlib import Path
from urllib.parse import urlsplit
from import_old_fyhom import ROOT, clean, page, parse, download

PATH=ROOT/"content/properties.json"
REPORT=ROOT/"content/verified-property-photos-review.json"
SOURCES=[ROOT/"content/import-review.json",ROOT/"content/missing-import-review.json"]

def make_sources():
    m={}
    for p in SOURCES:
        if not p.exists():continue
        data=json.loads(p.read_text(encoding="utf-8"))
        for item in data.get("offers",[]):
            identity=str(item.get("id",""))
            raw=item.get("source","")
            if not identity or not raw or "/property/" not in raw:continue
            url=clean(raw)
            if not url:continue
            m.setdefault(identity,[])
            if url not in m[identity]:m[identity].append(url)
    for identity,urls in m.items():
        urls.sort(key=lambda s:(0 if "/property/" in urlsplit(s).path and not re.match(r"^/(de|en|es)/property/",urlsplit(s).path) else 1, len(s)))
    return m

def official_gallery(soup):
    # Houzez original uses this slider for one property's image gallery,
    # distinct from related listings, floor-plan panels and broker profile.
    candidates=soup.select(".lightbox-gallery #lightbox-slider-js img")
    if not candidates:candidates=soup.select(".lightbox-gallery img")
    if not candidates:candidates=soup.select(".property-banner .hs-gallery-v5-grid img")
    urls=[]
    for el in candidates:
        for raw in (el.get("data-src"),el.get("data-lazy-src"),el.get("src")):
            if not raw or raw.startswith("data:"):continue
            src=clean(raw)
            if not src or "/wp-content/uploads/" not in src:continue
            if not re.search(r"\.(?:jpe?g|png|webp)$",urlsplit(src).path,re.I):continue
            if re.search(r"logo|favicon|placeholder|fyh[_-]?oro",src,re.I):continue
            if src not in urls:urls.append(src)
            break
    return urls

def load_source(identity,options):
    for url in options:
        soup=page(url)
        if not soup:continue
        result=parse(soup,url)
        if not result:continue
        orig,unused,warnings=result
        if str(orig.get("id"))!=identity:continue
        gallery=official_gallery(soup)
        if gallery:return url,gallery
    return None,[]

def rebuild():
    d=json.loads(PATH.read_text(encoding="utf-8"))
    sources=make_sources()
    audit={"timestamp":"2026-10-22","method":"Original WordPress lightbox only; reference ID matched","total":0,"updated":0,"failed":0,"saved_images":0,"listings":[]}
    all_ids=set()
    for entry in d.get("items",[]):
        identity=str(entry.get("id",""))
        if identity=="1":continue
        if identity in all_ids:raise ValueError("Duplicate property ID: "+identity)
        all_ids.add(identity)
        audit["total"]+=1
        report={"id":identity,"title":entry.get("title",""),"original_status":entry.get("status"),"old_count":int(bool(entry.get("img")))+len(entry.get("gallery",[]))}
        try:
            options=sources.get(identity,[])
            if not options:
                report["result"]="missing_original_url";audit["failed"]+=1
                audit["listings"].append(report);continue
            src,photos=load_source(identity,options)
            if not photos or len(photos)>55:
                report["result"]="no_verified_gallery";audit["failed"]+=1
                audit["listings"].append(report);continue
            report["source"]=src
            report["original_gallery_count"]=len(photos)
            files=[]
            for idx,url in enumerate(photos,1):
                dst=ROOT/"images/properties/verified"/identity/("%02d.jpg"%idx)
                if download(url,dst):
                    files.append("/"+str(dst.relative_to(ROOT)).replace("\\","/"))
                else:
                    report.setdefault("download_failures",[]).append(idx)
                time.sleep(.04)
            if len(files)<max(1,int(len(photos)*.8)) or len(files)==0:
                report["result"]="incomplete_download"
                audit["failed"]+=1
                audit["listings"].append(report);continue
            entry["img"]=files[0]
            entry["gallery"]=files[1:]
            report["result"]="verified"
            report["new_count"]=len(files)
            audit["updated"]+=1
            audit["saved_images"]+=len(files)
            print("VERIFIED",identity,len(files),"original gallery pictures; formerly",report["old_count"],flush=True)
        except Exception as exc:
            report["result"]="error"
            report["error"]=str(exc)[:210]
            audit["failed"]+=1
            print("FAILED",identity,str(exc)[:140],flush=True)
        audit["listings"].append(report)
        time.sleep(.06)
    assert len(audit["listings"])==audit["total"]
    assert all(str(x.get("id"))=="1" or x.get("img") for x in d["items"])
    if audit["updated"]:
        PATH.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    REPORT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SUMMARY",json.dumps({k:v for k,v in audit.items() if k!="listings"}),flush=True)

if __name__=="__main__":rebuild()
