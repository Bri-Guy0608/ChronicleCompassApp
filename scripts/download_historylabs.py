import requests
import json
import time
from pathlib import Path
from tqdm import tqdm

BASE_URL = "https://events.historylabs.io/year"
START_YEAR = -500
END_YEAR = 2023
OUTPUT_DIR = Path("data/raw/historylabs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def downloadYear(year):
    url = f"{BASE_URL}/{year}"

    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"Failed {year}: HTTP {response.status_code}")
            return False

        data = response.json()
        outfile = OUTPUT_DIR / f"{year}.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"Error downloading {year}: {e}")
        return False


successful = 0
failed = 0
print("Downloading HistoryLabs Events...\n")

for year in tqdm(range(START_YEAR, END_YEAR + 1)):
    if downloadYear(year):
        successful += 1
    else:
        failed += 1

    time.sleep(0.1)

print("\nFinished!")
print(f"Downloaded: {successful}")
print(f"Failed: {failed}")