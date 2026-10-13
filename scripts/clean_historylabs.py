import json
import csv
import re
from pathlib import Path
from datetime import datetime
from tqdm import tqdm


RAW_DIR = Path("data/raw/historylabs")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "events.csv"

MONTHS = {
    "January":1,
    "February":2,
    "March":3,
    "April":4,
    "May":5,
    "June":6,
    "July":7,
    "August":8,
    "September":9,
    "October":10,
    "November":11,
    "December":12
}


def splitTitle(content):
    if ":" in content:
        title, description = content.split(":",1)

        if len(title) < 100:
            return title.strip(), description.strip()

    return "", content.strip()


def parseDate(year, dateString):
    if not dateString:
        return ""

    try:
        monthName, day = dateString.split()
        month = MONTHS[monthName]
        return f"{year:04d}-{month:02d}-{int(day):02d}"

    except:
        return ""


def cleanText(text):
    text = re.sub(r"\s+"," ",text)
    return text.strip()


eventID = 1
rows = []
jsonFiles = sorted(RAW_DIR.glob("*.json"))
print(f"Found {len(jsonFiles)} files")

for file in tqdm(jsonFiles):
    with open(file,"r",encoding="utf-8") as f:
        data = json.load(f)

    year = int(file.stem)
    events = data.get("events",[])

    for event in events:
        title, description = splitTitle(event["content"])
        description = cleanText(description)
        title = cleanText(title)
        date = parseDate(year,event.get("date",""))
        rows.append([eventID, title, description, date, year, "HistoryLabs"])
        eventID += 1


with open(OUTPUT_FILE,"w",newline="",encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["EventID", "Title", "Description", "EventDate", "Year", "Source"])
    writer.writerows(rows)

print()
print(f"Created {OUTPUT_FILE}")
print(f"Total Events: {len(rows)}")