import json
import time
import urllib.request
import urllib.error
import os
from datetime import datetime, timedelta, timezone

key = os.environ["AIRNOW_API_KEY"]

now = datetime.now(timezone.utc)
start = now - timedelta(hours=1)

def fmt(d):
    return d.strftime("%Y-%m-%dT%H")

bbox = "-125.0,24.0,-66.0,50.0"  # contiguous US

url = (
    "https://www.airnowapi.org/aq/data/"
    f"?startDate={fmt(start)}"
    f"&endDate={fmt(now)}"
    f"&parameters=PM25"
    f"&BBOX={bbox}"
    f"&dataType=A"
    f"&format=application/json"
    f"&verbose=1"
    f"&monitorType=0"
    f"&includerawconcentrations=0"
    f"&API_KEY={key}"
)

def fetch_with_retry(url, retries=4, timeout=30, backoff=5):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "air-scraper/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            print(f"⚠️ Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)  # simple linear backoff
    raise last_err

data = fetch_with_retry(url)

# De-duplicate — keep latest reading per station
seen = {}
for d in data:
    k = f"{d['SiteName']}|{d['Latitude']}|{d['Longitude']}"
    if k not in seen or d["UTC"] > seen[k]["UTC"]:
        seen[k] = d

output = {
    "updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "count": len(seen),
    "stations": list(seen.values())
}

os.makedirs("data", exist_ok=True)
with open("data/aqi.json", "w") as f:
    json.dump(output, f)

print(f"✅ Saved {len(seen)} stations → data/aqi.json")


