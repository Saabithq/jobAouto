"""Offline test: fake jobs + fake LLM, checks pipeline and CV build without any API keys."""
import os, shutil, main, brain, sources

shutil.rmtree("output", ignore_errors=True)
if os.path.exists("tracker.csv"): os.remove("tracker.csv")

sources.collect = lambda cfg: [
    sources.job("Windows System Engineer", "Acme Tech", "https://example.com/1", "Kochi",
                "Windows Server, Active Directory, Group Policy, SCCM, ITSM support.", 7.5, "test"),
    sources.job("Senior DevOps Engineer", "BigCo", "https://example.com/2", "Bangalore", "Senior role", None, "test"),
    sources.job("GenAI Engineer", "AI Labs", "https://example.com/3", "Remote", "Python RAG LLM", None, "test"),
    sources.job("Support Engineer", "LowPay", "https://example.com/4", "Chennai", "support", 3.0, "test"),
]
def fake_score(job, p, m):
    fam = "ai" if "AI" in job["title"] else "infra"
    return {"score": 80, "family": fam, "missing_skills": ["Azure"], "blockers": [], "reason": "test match"}
def fake_tailor(job, fam, p, m):
    return {"summary": p["experience_summary"] + ". Windows infrastructure and support engineer.",
            "bullets": {"sutherland": [0, 1, 99, 5, 7], "techmindz": [0, 1], "mea": [1, 4]},
            "skills": ["Active Directory", "Python", "Made Up Skill", "SCCM"],
            "projects": ["rag_tutor", "emotion_detection", "nonexistent"],
            "cover_note": "Test cover note & more_text 100%."}
brain.score, brain.tailor = fake_score, fake_tailor
import yaml
cfg = yaml.safe_load(open("config.yaml")); cfg["llm"]["delay_seconds"] = 0
import time; time.sleep = lambda s: None
main.main()
print(open("tracker.csv").read())
