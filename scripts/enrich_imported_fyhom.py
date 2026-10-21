#!/usr/bin/env python3
"""Fill missing descriptions of imported FYHOM listings from their own source pages.

SAFETY: existing fields never overwritten; every listing remains hidden.
Never edits live statuses, prices, photographs or team data.
"""
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

ROOT=Path(__file__).resolve().parents[1]
PROPERTIES=ROOT/"content/properties.json"
SOURCE_REPORT=ROOT/"content/import-review.json"
OUTPUT_REPORT=ROOT/"content/enrichment-review.json"
HEADINGS={
    "beschreibung", "descripción", "descripcion", "description",
    "description de la propriété", "property description",
}
STOP_HEADINGS={
    "details", "detalles", "détails", "eigenschaften", "características",
    "caracteristicas", "features", "ausstattung", "merkmalen",
    "dokumente", "documentos", "documents", "ubicación de la propiedad",
    "property location", "lage der immobilie", "ubicación", "location",
    "similar listings", "similares", "ähnliche immobilien",
    "contact me", "contacto", "energy class", "energieeffizienzklasse",
    "clase energética", "newsletter", "abonnieren", "subscribe",
}
CLIENT=requests.Session()
CLIENT.headers.update({"User-Agent":"FYHOM authorized property migration/1.1"})
def heading_text(node):
    return " ".join(node.stripped_strings).strip().lower().strip(":")
def extract_description(html):
    soup=BeautifulSoup(html,"html.parser")
    for node in soup(["script","style","nav","footer","noscript"]):
        node.decompose()
    heads=[node for node in soup.find_all(["h2","h3","h4","h5","h6","strong"])]
    for h in heads:
        txt=heading_text(h)
        if txt not in HEADINGS:
            continue
        chunks=[]; seen=set()
        # Iterate through document order after this heading until the next
        # unrelated section heading. Preserve paragraphs and list items only.
        for item in h.next_elements:
            if not isinstance(item,Tag):
                continue
            if item.name in ("h2","h3","h4","h5","h6"):
                title=heading_text(item)
                if title in STOP_HEADINGS:
                    break
                if item.name=="h2" and title not in HEADINGS:
                    # Descriptions often include h2 subheadings; stop only
                    # after content when a new top-level section is encountered.
                    if chunks and ("details" in title or "document" in title):
                        break
                continue
            if item.name not in ("p","li"):continue
            # Don't collect nested duplicate items.
            if item.find_parent(["p","li"]) is not None:continue
            content=" ".join(item.stripped_strings)
            content=re.sub(r"\s+"," ",content).strip()
            if len(content)<35 or content in seen:continue
            if any(x in content.lower() for x in (
                "suscríbete a nuestra newsletter","subscribe to our newsletter",
                "abonniere unseren newsletter")):break
            chunks.append(content)
            seen.add(content)
            if sum(map(len,chunks))>=7500 or len(chunks)>=35:break
        result="\n\n".join(chunks).strip()
        if len(result)>=85:
            return result[:7500]
    return ""
def safe_url(u):
    p=urlparse(u)
    return p.scheme=="https" and p.hostname in ("fyhom.es","www.fyhom.es") and "/property/" in p.path
def main():
    listings=json.loads(PROPERTIES.read_text(encoding="utf-8"))
    entries=listings.get("items",[])
    source=json.loads(SOURCE_REPORT.read_text(encoding="utf-8"))
    by_id={str(x.get("id")):x for x in entries}
    report={"attempted":0,"filled":0,"unchanged":0,"not_found":0,"errors":[],"items":[]}
    for entry in source.get("offers",[]):
        if entry.get("status")!="hidden_for_review":continue
        ident=str(entry.get("id",""))
        p=by_id.get(ident)
        if not p or p.get("status")!="hidden":continue
        if p.get("description_es") or p.get("description_de"):
            report["unchanged"]+=1;continue
        url=entry.get("source","")
        if not safe_url(url):
            report["errors"].append({"id":ident,"issue":"unapproved_url"});continue
        report["attempted"]+=1
        try:
            r=CLIENT.get(url,timeout=(12,35))
            r.raise_for_status()
            desc=extract_description(r.text)
            if desc:
                p["description_es"]=desc
                report["filled"]+=1
                report["items"].append({"id":ident,"source":url,"characters":len(desc),"sample":desc[:165]})
            else:
                report["not_found"]+=1
                report["items"].append({"id":ident,"source":url,"issue":"description_not_found"})
            print(ident, "description characters",len(desc),flush=True)
        except requests.RequestException as exc:
            report["errors"].append({"id":ident,"issue":str(exc)[:160]})
            print("WARN",ident,exc,flush=True)
        time.sleep(.07)
    # All imported properties MUST remain hidden. Do not write data otherwise.
    imported_ids={str(e["id"]) for e in source.get("offers",[]) if e.get("status")=="hidden_for_review"}
    assert all(x["status"]=="hidden" for x in entries if str(x.get("id")) in imported_ids)
    if report["filled"]:
        PROPERTIES.write_text(json.dumps(listings,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    OUTPUT_REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("DESCRIPTION ENRICHMENT",json.dumps({k:v for k,v in report.items() if k not in ("items","errors")}),flush=True)
    # Failure to scrape is reported but never causes loss of existing data.
if __name__=="__main__": main()
