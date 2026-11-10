import csv, datetime, os, re, time, yaml
import brain, cv_builder, notify, profile_io, sources

FIELDS = ["id", "date_found", "company", "title", "location", "source", "url", "score", "family",
          "cv_file", "status", "date_applied", "follow_up_date"]

def load_tracker(path="tracker.csv"):
    if not os.path.exists(path):
        return []
    return list(csv.DictReader(open(path, encoding="utf-8")))

def save_tracker(rows, path="tracker.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:30]

def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    profile = profile_io.load()
    model = cfg["llm"]["model"]
    s = cfg["search"]
    min_lpa = profile["preferences"].get("min_salary_lpa", 0)

    rows = load_tracker()
    seen = {r["id"] for r in rows}
    today = datetime.date.today().isoformat()
    outdir = os.path.join("output", today)

    jobs, ids = [], set()
    for j in sources.collect(cfg):
        title = j["title"].lower()
        if j["id"] in seen or j["id"] in ids:
            continue
        if any(re.search(rf"\b{re.escape(w)}", title) for w in s["exclude_title_words"]):
            continue
        if j["salary_lpa"] is not None and j["salary_lpa"] < min_lpa:
            continue
        ids.add(j["id"])
        jobs.append(j)
    print(f"{len(jobs)} new jobs after filters; scoring up to {cfg['llm']['max_jobs_per_run']}")

    digest = [f"# Job digest {today}\n"]
    matches, pdfs = 0, []
    for j in jobs[: cfg["llm"]["max_jobs_per_run"]]:
        try:
            sc = brain.score(j, profile, model)
            time.sleep(cfg["llm"]["delay_seconds"])
            score = int(sc.get("score", 0))
            fam = sc.get("family") if sc.get("family") in profile["headlines"] else "infra"
            row = dict(id=j["id"], date_found=today, company=j["company"], title=j["title"],
                       location=j["location"], source=j["source"], url=j["url"], score=score,
                       family=fam, cv_file="", status="skipped_low_score",
                       date_applied="", follow_up_date="")
            if score >= s["min_score"]:
                t = brain.tailor(j, fam, profile, model)
                time.sleep(cfg["llm"]["delay_seconds"])
                name = f"{slug(j['company'])}_{slug(j['title'])}_{j['id']}"
                row["cv_file"] = os.path.join(outdir, cv_builder.build(profile, fam, t, outdir, name))
                row["status"] = "to_review"
                matches += 1
                pdfs.append(row["cv_file"])
                sal = f"{j['salary_lpa']} LPA" if j["salary_lpa"] else "salary not stated"
                digest.append(f"## {j['title']} - {j['company']} ({j['location']}) - score {score}\n"
                              f"- Apply: {j['url']}\n- CV family: {fam} | {sal}\n"
                              f"- Why: {sc.get('reason', '')}\n"
                              f"- Missing: {', '.join(sc.get('missing_skills', [])) or 'none'}"
                              f"{' | Blockers: ' + ', '.join(sc['blockers']) if sc.get('blockers') else ''}\n"
                              f"- CV: {row['cv_file']}\n\n**Cover note**\n\n> {t.get('cover_note', '')}\n")
            rows.append(row)
            print(f"{score:3d}  {j['title']} @ {j['company']}")
        except Exception as e:
            print(f"error on {j['title']} @ {j['company']}: {e}")

    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, "digest.md"), "w", encoding="utf-8").write("\n".join(digest))
    save_tracker(rows)
    if matches == 0:
        digest.append("No new matches today.")
    notify.send(f"Job digest {today}: {matches} new match(es)", "\n".join(digest), pdfs)

if __name__ == "__main__":
    main()
