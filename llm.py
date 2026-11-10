import os, json, re, time, requests

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

def ask_json(prompt, model, retries=4):
    key = os.environ["GEMINI_API_KEY"]
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}}
    for attempt in range(retries):
        r = requests.post(URL.format(model=model),
                          headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                          json=body, timeout=90)
        if r.status_code in (429, 500, 503):
            time.sleep(20 * (attempt + 1))
            continue
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        return json.loads(text)
    raise RuntimeError("Gemini API unavailable or rate limited")
