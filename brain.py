"""Two LLM steps: score a job, then pick (never invent) CV content for it."""
import llm, profile_io

FAMILIES = "infra, devops, ai, trainer, embedded"

def score(job, profile, model):
    prompt = f"""You are a strict recruiter-side matcher. Compare the CANDIDATE to the JOB.
The candidate has about 3.7 years of IT experience but only 1 year as System Engineer.
Penalise roles needing 5+ years or skills the candidate lacks. Skills under "Learning" are NOT skills.

CANDIDATE:
{profile_io.digest(profile)}

JOB: {job['title']} at {job['company']} ({job['location']})
{job['description'][:3500]}

Return JSON only:
{{"score": 0-100, "family": one of [{FAMILIES}],
 "matched_skills": [..], "missing_skills": [..], "blockers": [..], "reason": "one sentence"}}"""
    return llm.ask_json(prompt, model)

def tailor(job, family, profile, model):
    prompt = f"""Tailor the candidate's CV for this job. You may ONLY choose from the facts below.
Never add skills, tools, numbers or claims that are not listed. Skills under "Learning" must not be called skills.

CANDIDATE:
{profile_io.digest(profile)}

JOB: {job['title']} at {job['company']}
{job['description'][:3500]}

Return JSON only:
{{"summary": "2-3 sentences. Start with: {profile['experience_summary']}. Mirror the job's wording only where it is true for the candidate.",
 "bullets": {{"sutherland": [bullet numbers in best order, max 7], "techmindz": [max 4], "mea": [max 4]}},
 "skills": [up to 14 items copied exactly from the candidate's Skills list, most relevant first],
 "projects": [up to 3 project ids],
 "cover_note": "under 110 words, plain and honest, mentions 45 day notice (negotiable) only if useful"}}
Bullet numbers are the number after the colon in ids such as sutherland:3."""
    return llm.ask_json(prompt, model)
