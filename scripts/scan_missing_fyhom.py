#!/usr/bin/env python3
"""Safely scan the old FYHOM website for additional listings missed by the first import.
New entries and photos are local copies and remain HIDDEN until the owner reviews them.
No existing listings are modified.
"""
import json,re,time
from pathlib import Path
from urllib.parse import urlsplit
from import_old_fyhom import ROOT,ORIGIN,PROPERTY,find_urls,clean,page,parse,download
from enrich_imported_fyhom import extract_description

PATH=ROOT/"content/properties.json"
REPORT=ROOT/"content/missing-import-review.json"
EXTRA=[
    "/property/espectacular-vivienda-de-116m%C2%B2-en-pego-con-acabados-de-lujo/",
    "/en/property/espectacular-vivienda-de-116m%C2%B2-en-pego-con-acabados-de-lujo/"
]
ARCHIVES=[
    "/","/de/","/en/","/es/",
    "/en/property-type/casa/","/en/property-type/apartment/",
    "/en/property-type/commercial/","/en/property-type/local-comercial/",
    "/property-type/casa/","/property-type/apartamento/",
    "/property-type/local-comercial/","/property-type/terreno/",
    "/comprar-propiedades/","/en/properties/","/property/"
]

def url_set():
    urls={u for u in find_urls() if PROPERTY.match(urlsplit(u).path)}
    for fragment in EXTRA:urls.add(clean(ORIGIN+fragment))
    for fragment in ARCHIVES:
        for n in range(1,4):
            suffix="" if n==1 else "page/"+str(n)+"/"
            u=ORIGIN+fragment.rstrip("/")+"/"+suffix
            soup=page(u)
            if soup is None:continue
            for anchor in soup.select("a[href]"):
                candidate=clean(anchor["href"])
                if candidate and PROPERTY.match(urlsplit(candidate).path):
                    urls.add(candidate)
            time.sleep(.06)
    return sorted(u for u in urls if u)

def infer_kind(item):
    title=item["title"].lower()
    if re.search(r"\b(local comercial|restaurante|negocio|local en venta|ladenlokal)\b",title):return "retail"
    if re.search(r"\b(parcela|terreno|solar|grundstück)\b",title):return "land"
    if re.search(r"\b(ático|atico|apartamento|piso|wohnung|penthouse)\b",title):return "apartment"
    if re.search(r"\b(adosado|pareado|reihenhaus)\b",title):return "townhouse"
    if re.search(r"\b(villa|chalet independiente)\b",title):return "villa"
    return item["type"]

def scan():
    data=json.loads(PATH.read_text(encoding="utf-8"))
    known={str(x.get("id")) for x in data.get("items",[])}
    found=url_set()
    record={"checked_urls":len(found),"new_offers":0,"all_hidden":True,"offers":[]}
    for i,url in enumerate(found):
        soup=page(url)
        if soup is None:continue
        parsed=parse(soup,url)
        if not parsed:
            if "espectacular-vivienda-de-116" in url:
                record["offers"].append({"source":url,"error":"Property details or reference ID could not be verified"})
            continue
        item,pictures,warnings=parsed
        ident=str(item["id"])
        if ident in known:continue
        item["type"]=infer_kind(item)
        item["new_build"]=bool(re.search(r"obra nueva|neubau|new build",item["title"],re.I))
        detailed=extract_description(str(soup))
        if detailed:
            # Prefer the actual language of the source text instead of
            # claiming English just because the old URL contains /en/.
            language="de" if "/de/property/" in url else "es"
            item["description_"+language]=detailed
        # Remove placeholder field from importer, unless it contains a real description.
        if not item.get("description_es"):item.pop("description_es",None)
        pictures=list(dict.fromkeys(pictures))
        local=[]
        for source in pictures:
            if len(local)>=16:break
            dest=ROOT/"images/properties/imported"/ident/(f"{len(local)+1:02d}.jpg")
            if download(source,dest):
                local.append("/"+str(dest.relative_to(ROOT)).replace("\\","/"))
            time.sleep(.05)
        if not local:
            record["offers"].append({"id":ident,"source":url,"error":"Photo download failed; not imported"})
            continue
        item["img"]=local[0]
        item["gallery"]=local[1:]
        item["status"]="hidden"
        data["items"].append(item)
        known.add(ident)
        record["new_offers"]+=1
        record["offers"].append({
            "id":ident,"title":item["title"],"source":url,
            "status":"hidden","photo_count":len(local),"check":warnings
        })
        print(f"Imported HIDDEN extra {ident}: {item['title'][:75]} / {len(local)} photos",flush=True)
        time.sleep(.06)
    if record["new_offers"]:
        PATH.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    REPORT.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Additional offers: {record['new_offers']} from {record['checked_urls']} pages",flush=True)

if __name__=="__main__":scan()
