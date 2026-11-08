# Job Hunter (semi-automatic)

Runs daily on GitHub Actions: collects jobs -> scores them against `master_profile.yaml` ->
builds a tailored 1-page CV (PDF) + cover note for good matches -> you review and click Apply yourself.

## One-time setup (about 20 minutes)
1. Create a **PRIVATE** GitHub repository (your phone and email are in the profile) and upload all these files.
2. Get a free Gemini key: Google AI Studio -> "Get API key".
3. Get free Adzuna keys: developer.adzuna.com -> register -> app id + app key.
4. Repo -> Settings -> Secrets and variables -> Actions -> add three secrets:
   `GEMINI_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`
5. Actions tab -> "daily-job-run" -> Run workflow (first test). Then it runs every day at 8:00 AM IST.
6. Each day: open `output/<date>/digest.md` in the repo (job link, score, missing skills, cover note)
   and download the CVs from the run's Artifacts. Set `status` / `date_applied` in `tracker.csv`.

## Things to know
- Free-tier Gemini may use your prompts to improve Google products. Your CV text is sent to it.
- If the model name stops working, change `llm.model` in `config.yaml` (see names in Google AI Studio).
- The AI can only pick bullets, skills and projects that exist in `master_profile.yaml`. Fix the profile, not the CVs.
- Test without any keys: `pip install -r requirements.txt && python test_offline.py`
- Adzuna job text is short, so scores are approximate. Always read the full job post before applying.
- Fill remaining `TODO` items in `master_profile.yaml` (project links) when you can.
