import os, re, subprocess
import profile_io

def esc(t):
    t = t.replace("\\", " ")
    for a, b in {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "|": r"\textbar{}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}.items():
        t = t.replace(a, b)
    return t

def link(url, label=None):
    u = url if url.startswith("http") else "https://" + url
    return rf"\href{{{u}}}{{{esc(label or url)}}}"

def pick_bullets(exp, wanted, limit, fallback_tag=None):
    ok = {i: b["text"] for i, b in enumerate(exp["bullets"]) if profile_io.usable(b["text"])}
    chosen = []
    for n in (wanted or []):
        try:
            n = int(n)
        except (TypeError, ValueError):
            continue
        if n in ok and n not in chosen:
            chosen.append(n)
    if not chosen:                      # LLM gave nothing valid: take the first bullets
        chosen = list(ok)[:limit]
    return [ok[n] for n in chosen[:limit]]

def build(profile, family, t, outdir, name):
    P = profile["personal"]
    skills_ok = {s.lower(): s for s in profile_io.all_skills(profile)}
    skills = [skills_ok[s.lower()] for s in t.get("skills", []) if s.lower() in skills_ok][:14]
    if not skills:
        skills = profile_io.all_skills(profile)[:14]

    limits = {"sutherland": 7, "techmindz": 4, "mea": 4}
    exp_tex = ""
    for e in profile["experience"]:
        items = pick_bullets(e, t.get("bullets", {}).get(e["id"]), limits.get(e["id"], 4))
        exp_tex += (rf"\textbf{{{esc(e['title'])}}} \hfill {esc(e['dates'])}\\" "\n"
                    rf"\textit{{{esc(e['company'])}}}" "\n\\begin{itemize}\n"
                    + "".join(rf"\item {esc(x)}" + "\n" for x in items) + "\\end{itemize}\n\\vspace{3pt}\n")

    proj_tex = ""
    by_id = {p["id"]: p for p in profile["projects"]}
    chosen = [i for i in t.get("projects", []) if i in by_id][:3] or \
             profile["role_families"].get(family, {}).get("projects", [])[:3]
    for pid in chosen:
        pr = by_id[pid]
        bl = [b for b in pr["bullets"] if profile_io.usable(b)][:2]
        if not bl:
            continue
        lk = f" \\hfill {link(pr['link'], 'GitHub')}" if profile_io.usable(pr.get("link", "")) else ""
        proj_tex += (rf"\textbf{{{esc(pr['name'])}}}{lk}" "\n\\begin{itemize}\n"
                     + "".join(rf"\item {esc(b)}" + "\n" for b in bl) + "\\end{itemize}\n\\vspace{3pt}\n")

    edu = "".join(rf"\textbf{{{esc(e['degree'])}}} \hfill {esc(e['dates'])}\\ {esc(e['school'])}\\[2pt]" "\n"
                  for e in profile["education"])
    certs = "".join(rf"\item {esc(c)}" + "\n" for c in profile["certifications"])
    pub = ""
    if family == "ai" and profile_io.usable(profile["publication"].get("venue", "")):
        pb = profile["publication"]
        pub = (r"\section*{RESEARCH PAPER}" "\n" rf"\textbf{{{esc(pb['title'])}}}\\" "\n"
               rf"{esc(pb['status'])}: {esc(pb['venue'])}" "\n")

    tex = rf"""\documentclass[a4paper,10pt]{{article}}
\usepackage[a4paper,margin=0.55in]{{geometry}}
\usepackage{{enumitem}}\usepackage[hidelinks]{{hyperref}}\usepackage{{titlesec}}\usepackage{{parskip}}
\pagenumbering{{gobble}}
\titleformat{{\section}}{{\large\bfseries}}{{}}{{0em}}{{}}[\titlerule]
\titlespacing*{{\section}}{{0pt}}{{6pt}}{{3pt}}
\setlist[itemize]{{leftmargin=*,noitemsep,topsep=2pt}}
\begin{{document}}
\begin{{center}}
{{\LARGE \textbf{{{esc(P['name'])}}}}}\\[3pt]
\textbf{{{esc(profile['headlines'][family])}}}\\[3pt]
{link('mailto:'+P['email'], P['email'])} \quad {esc(P['phone'])} \quad {esc(P['location'])}\\[2pt]
{link(P['linkedin'])} \quad {link(P['github'])} \quad {link(P['portfolio'], 'Portfolio')}
\end{{center}}
\section*{{PROFESSIONAL SUMMARY}}
{esc(t.get('summary', profile['experience_summary']))}
\section*{{TECHNICAL SKILLS}}
{esc(', '.join(skills))}
\section*{{PROFESSIONAL EXPERIENCE}}
{exp_tex}
\section*{{PROJECTS}}
{proj_tex}
\section*{{EDUCATION}}
{edu}
\section*{{CERTIFICATIONS}}
\begin{{itemize}}
{certs}\end{{itemize}}
{pub}
\end{{document}}
"""
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, name + ".tex")
    open(path, "w", encoding="utf-8").write(tex)
    try:
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", name + ".tex"],
                       cwd=outdir, capture_output=True, timeout=120, check=True)
        pages = subprocess.run(["pdfinfo", name + ".pdf"], cwd=outdir, capture_output=True, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", pages)
        if m and int(m.group(1)) > 1:
            print(f"  warning: {name}.pdf is {m.group(1)} pages")
        return name + ".pdf"
    except Exception as e:
        print("  LaTeX build failed:", e)
        return name + ".tex"
