import os, re, hashlib, requests

def job(title, company, url, location, desc, salary_lpa=None, source=""):
    jid = hashlib.md5(f"{company}|{title}|{location}".lower().encode()).hexdigest()[:12]
    return dict(id=jid, title=title or "", company=company or "", url=url or "",
                location=location or "", description=re.sub(r"\s+", " ", desc or ""),
                salary_lpa=salary_lpa, source=source)

def adzuna(queries, locations, max_age_days):
    app_id, app_key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        print("Adzuna keys not set, skipping Adzuna")
        return []
    out = []
    for q in queries:
        for loc in locations:
            params = {"app_id": app_id, "app_key": app_key, "what": q,
                      "results_per_page": 20, "max_days_old": max_age_days}
            if loc.lower() != "india":
                params["where"] = loc
            try:
                r = requests.get("https://api.adzuna.com/v1/api/jobs/in/search/1",
                                 params=params, timeout=30)
                r.raise_for_status()
            except Exception as e:
                print(f"Adzuna error for {q}/{loc}: {e}")
                continue
            for j in r.json().get("results", []):
                sal = None
                # ignore Adzuna's predicted salaries, only trust stated ones
                if j.get("salary_min") and str(j.get("salary_is_predicted")) != "1":
                    sal = round(j["salary_min"] / 100000, 1)
                out.append(job(j.get("title"), (j.get("company") or {}).get("display_name"),
                               j.get("redirect_url"), (j.get("location") or {}).get("display_name"),
                               j.get("description"), sal, "adzuna"))
    return out

def remotive(queries):
    """Remote jobs. Remotive asks for few requests per day, so only 3 queries."""
    out = []
    for q in queries[:3]:
        try:
            r = requests.get("https://remotive.com/api/remote-jobs", params={"search": q}, timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"Remotive error for {q}: {e}")
            continue
        for j in r.json().get("jobs", []):
            loc = j.get("candidate_required_location", "")
            if re.search(r"india|worldwide|anywhere|apac|asia", loc, re.I):
                out.append(job(j.get("title"), j.get("company_name"), j.get("url"),
                               f"Remote ({loc})", re.sub("<[^>]+>", " ", j.get("description", "")),
                               None, "remotive"))
    return out

def collect(cfg):
    s = cfg["search"]
    jobs = adzuna(s["queries"], s["locations"], s["max_age_days"])
    if s.get("remote_ok"):
        jobs += remotive(s["queries"])
    return jobs
