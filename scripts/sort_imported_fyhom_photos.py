#!/usr/bin/env python3
"""Review imported FYHOM images and move likely floorplans/docs behind property photos.

Only adjusts imported hidden listings, never publishes them. Does not change image
bytes, property prices, text or availability. Preserves per-listing all image paths.
A score is a visual heuristic (not an AI guarantee): each result needs human review.
"""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image,ImageOps

ROOT=Path(__file__).resolve().parents[1]
PROPERTIES=ROOT/"content/properties.json"
IMPORT_REPORT=ROOT/"content/import-review.json"
OUTPUT=ROOT/"content/photo-sort-review.json"

def evaluate(relative):
    path=ROOT/relative.lstrip("/")
    if not path.is_file():return None
    try:
        with Image.open(path) as img:
            im=ImageOps.exif_transpose(img).convert("RGB")
            width,height=im.size
            im.thumbnail((240,240))
            pix=np.asarray(im,dtype=np.float32)/255
        maximum=pix.max(axis=2)
        minimum=pix.min(axis=2)
        saturation=(maximum-minimum)/(maximum+.015)
        brightness=(pix[:,:,0]*.299+pix[:,:,1]*.587+pix[:,:,2]*.114)
        white=np.mean((pix[:,:,0]>.87)&(pix[:,:,1]>.87)&(pix[:,:,2]>.87))
        paper=np.mean((pix[:,:,0]>.95)&(pix[:,:,1]>.95)&(pix[:,:,2]>.95))
        grayscale=np.mean((maximum-minimum)<.055)
        vivid=np.mean(saturation>.2)
        saturation_mean=float(saturation.mean())
        contrast=float(brightness.std())
        edge=float(((np.abs(np.diff(brightness,axis=0))>.11).mean()+
                    (np.abs(np.diff(brightness,axis=1))>.11).mean())/2)
        ratio=width/max(1,height)
        # Architectural drawings, brochures and floor plans frequently have
        # large white/grey background areas and very little real-world colour.
        graphic=(white>.58 and grayscale>.73 and vivid<.14) or (
            white>.38 and grayscale>.85 and vivid<.065
        ) or (paper>.72 and saturation_mean<.095)
        portrait=ratio<.79
        score=45+70*saturation_mean+48*contrast+19*vivid+12*edge-34*white-10*grayscale
        if portrait:score-=7
        if graphic:score-=90
        if width<560 or height<360:score-=12
        return {
            "score":round(float(score),2),
            "likely_plan_or_document":bool(graphic),
            "width":width,"height":height,
            "white_ratio":round(float(white),2),
            "color_ratio":round(float(vivid),2)
        }
    except (OSError,ValueError) as error:
        print("Image could not be inspected",path,str(error)[:130],flush=True)
        return None

def main():
    doc=json.loads(PROPERTIES.read_text(encoding="utf-8"))
    report=json.loads(IMPORT_REPORT.read_text(encoding="utf-8"))
    imported={str(item["id"]) for item in report["offers"] if item.get("status")=="hidden_for_review"}
    output={"review_required":True,"method":"Pillow/NumPy image characteristics; not human verified",
        "analyzed":0,"changed":0,"hero_replaced":0,"possible_documents_moved":0,
        "offers":[]}
    for entry in doc.get("items",[]):
        identity=str(entry.get("id"))
        if identity not in imported:continue
        if entry.get("status")!="hidden":
            print("Skipping non-hidden property",identity,flush=True)
            continue
        paths=[entry.get("img","")]+[
            value if isinstance(value,str) else value.get("image","")
            for value in entry.get("gallery",[])
        ]
        paths=[p for p in paths if isinstance(p,str) and p]
        if not paths:continue
        # Strictly operate on copied GitHub assets, not external URL images.
        if any(not p.startswith("/images/properties/imported/"+identity+"/") for p in paths):
            print("Skipping unexpected image paths",identity,flush=True)
            continue
        scores=[evaluate(p) for p in paths]
        candidates=[(i,m) for i,m in enumerate(scores) if m]
        if not candidates:
            output["offers"].append({"id":identity,"issue":"image_files_missing"})
            continue
        first=scores[0]
        viable=[(i,m) for i,m in candidates if not m["likely_plan_or_document"]]
        hero_idx=0
        if viable:
            best_i,best=max(viable,key=lambda x:x[1]["score"])
            # Preserve original photographer order unless the first item is
            # likely to be a plan or a candidate is substantially better.
            if (first is None or first["likely_plan_or_document"] or
                best["score"] > first["score"]+17):
                hero_idx=best_i
        revised=[paths[hero_idx]]
        rest=[i for i in range(len(paths)) if i!=hero_idx]
        # Keep the sequence of property photos; move documents/plans to end.
        rest.sort(key=lambda i:(1 if scores[i] and scores[i]["likely_plan_or_document"] else 0))
        revised.extend(paths[i] for i in rest)
        assert len(revised)==len(paths) and set(revised)==set(paths)
        changed=revised!=paths
        if changed:
            entry["img"]=revised[0]
            entry["gallery"]=revised[1:]
            output["changed"]+=1
            output["hero_replaced"]+=int(hero_idx!=0)
        moved=sum(1 for i in rest if scores[i] and scores[i]["likely_plan_or_document"])
        output["possible_documents_moved"]+=moved
        output["analyzed"]+=1
        output["offers"].append({
            "id":identity,"title":entry.get("title",""),
            "old_hero":paths[0],"new_hero":revised[0],
            "hero_changed":hero_idx!=0,
            "possible_documents":moved,
            "heuristic_scores":[{"image":paths[i],**(scores[i] or {"issue":"unreadable"})} for i in range(len(paths))]
        })
        print(identity,"hero",hero_idx+1,"of",len(paths),"images; doc-like",moved,flush=True)
    assert all(p.get("status")=="hidden" for p in doc["items"] if str(p.get("id")) in imported), "Imported offer would become public"
    if output["changed"]:
        PROPERTIES.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    OUTPUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("RESULT",json.dumps({k:v for k,v in output.items() if k!="offers"}),flush=True)
if __name__=="__main__":main()
