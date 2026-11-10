import yaml

def load(path="master_profile.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def usable(text):
    return isinstance(text, str) and "TODO" not in text

def all_skills(p):
    out = []
    for grp in ("core", "working"):
        for items in p["skills"][grp].values():
            out += items
    return out

def digest(p):
    """Compact text of the profile for the LLM. Bullets get ids like sutherland:3."""
    L = [f"Experience: {p['experience_summary']}",
         "Education: MCA (pursuing, IGNOU); BCA (University of Calicut, 2021)",
         "Skills: " + "; ".join(all_skills(p)),
         "Learning (do NOT present as skills): " + "; ".join(p["skills"]["learning"]), ""]
    for e in p["experience"]:
        L.append(f"{e['title']} at {e['company']} ({e['dates']})")
        for i, b in enumerate(e["bullets"]):
            if usable(b["text"]):
                L.append(f"  {e['id']}:{i} [{','.join(b['tags'])}] {b['text']}")
    L.append("")
    for pr in p["projects"]:
        txt = " ".join(x for x in pr["bullets"] if usable(x))
        if txt:
            L.append(f"  project {pr['id']}: {pr['name']} - {txt}")
    return "\n".join(L)
