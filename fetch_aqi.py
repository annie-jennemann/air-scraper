import json
import urllib.request
import os
from datetime import datetime, timedelta

key   = os.environ["AIRNOW_API_KEY"]
now   = datetime.utcnow()
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

with urllib.request.urlopen(url) as r:
    data = json.loads(r.read().decode())

# De-duplicate — keep latest reading per station
seen = {}
for d in data:
    k = f"{d['SiteName']}|{d['Latitude']}|{d['Longitude']}"
    if k not in seen or d["UTC"] > seen[k]["UTC"]:
        seen[k] = d

output = {
    "updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "count":   len(seen),
    "stations": list(seen.values())
}

os.makedirs("data", exist_ok=True)
with open("data/aqi.json", "w") as f:
    json.dump(output, f)

print(f"✅ Saved {len(seen)} stations → data/aqi.json")

