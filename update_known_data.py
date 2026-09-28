#!/usr/bin/env python3
"""Small, explicit data corrections for Ari's NBA Cards."""
import json
from pathlib import Path
p=Path(__file__).resolve().parent/"players.json"
data=json.loads(p.read_text(encoding="utf-8"))
for x in data:
    if x.get("id")=="isaiah-hartenstein":
        x.setdefault("awards",{})["championships"]=1
        x["draftYear"]=2017
        x["draftPick"]=43
        x["draftedBy"]="Houston Rockets"
        x["teamName"]="Oklahoma City Thunder"
        x["dataComplete"]=True
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Updated Isaiah Hartenstein.")
