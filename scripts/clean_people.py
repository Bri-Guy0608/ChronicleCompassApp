import pandas as pd
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "people_wiki.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "historical_figures.csv"

def cleanText(text):
    if pd.isna(text):
        return ""

    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def getBirthYear(text):
    if pd.isna(text):
        return ""

    text = text.lower()
    m = re.search(
        r"born\s+\d{1,2}\s+[a-z]+\s+(1[0-9]{3}|20[0-2][0-9])",
        text
    )

    if m:
        return int(m.group(1))

    m = re.search(
        r"born\s+[a-z]+\s+\d{1,2}\s+(1[0-9]{3}|20[0-2][0-9])",
        text
    )

    if m:
        return int(m.group(1))

    m = re.search(
        r"born\s+in\s+(1[0-9]{3}|20[0-2][0-9])",
        text
    )

    if m:
        return int(m.group(1))

    m = re.search(
        r"born\s+(1[0-9]{3}|20[0-2][0-9])",
        text
    )

    if m:
        return int(m.group(1))

    return ""


def getDeathYear(text):

    return ""


print("Loading people dataset...")
df = pd.read_csv(INPUT_FILE)
print(f"Loaded {len(df)} rows.")
df = df.drop_duplicates(subset=["URI"])
print(f"After duplicates: {len(df)}")
records = []
figureID = 1

for _, row in df.iterrows():
    uri = cleanText(row["URI"])
    name = cleanText(row["name"])
    description = cleanText(row["text"])
    birth = getBirthYear(description)
    death = getDeathYear(description)
    records.append({"FigureID": figureID, "Name": name, "URI": uri, "BirthYear": birth, "DeathYear": death, "Description": description})
    figureID += 1

clean_df = pd.DataFrame(records)
clean_df.to_csv(OUTPUT_FILE, index=False)

print()
print("Finished!")
print(f"Saved to: {OUTPUT_FILE}")
print(f"Historical Figures: {len(clean_df)}")