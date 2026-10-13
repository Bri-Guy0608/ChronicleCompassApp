import requests
import json
import calendar
import time
from pathlib import Path
from tqdm import tqdm

BASE_URL = "https://en.wikipedia.org/w/api.php"
START_YEAR = 2022
END_YEAR = 2022
OUTPUT_DIR = Path("data/raw/wikipedia")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()

for year in range(START_YEAR, END_YEAR + 1):
    for month in range(1, 13):
        days = calendar.monthrange(year, month)[1]
        monthName = calendar.monthName[month]
        for day in tqdm(range(1, days + 1), desc=f"{monthName} {year}"):
            page = f"Portal:Current_events/{year}_{monthName}_{day}"
            params = {"action": "parse", "page": page, "format": "json", "prop": "text"}

            try:
                r = session.get(BASE_URL, params=params, timeout=30)
                if r.status_code != 200:
                    continue
                data = r.json()
                filename = OUTPUT_DIR / f"{year}-{month:02d}-{day:02d}.json"

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)

                time.sleep(0.1)

            except Exception:
                pass

print("Finished downloading Wikipedia Current Events.")