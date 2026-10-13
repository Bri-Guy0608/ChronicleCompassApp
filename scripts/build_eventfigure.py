import pandas as pd
import re
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVENT_FILE = PROJECT_ROOT / "data" / "processed" / "events.csv"
FIGURE_FILE = PROJECT_ROOT / "data" / "processed" / "historical_figures.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "eventfigure.csv"

def normalize(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

print("Loading...")
events = pd.read_csv(EVENT_FILE)
figures = pd.read_csv(FIGURE_FILE)
print("Events:", len(events))
print("Figures:", len(figures))

personInd = defaultdict(list)
print("Building lookup index...")

for _, row in figures.iterrows():

    name = normalize(row["Name"])
    if len(name) < 6:
        continue
    pieces = name.split()
    if len(pieces) < 2:
        continue
    last = pieces[-1]
    firstLetter = last[0]

    personInd[firstLetter].append((name, row["FigureID"]))

rows = []
print("Matching events...")

for _, event in tqdm(events.iterrows(), total=len(events)):

    text = normalize(str(event["Title"]) + " " + str(event["Description"]))
    used = set()
    letters = set(text)

    for letter in letters:
        if letter not in personInd:
            continue

        for personName, figureID in personInd[letter]:
            if personName in text:
                if figureID not in used:
                    rows.append({"EventID": event["EventID"], "FigureID": figureID})
                    used.add(figureID)

matches = pd.DataFrame(rows)
matches.to_csv(OUTPUT_FILE,index=False)

print()
print("Relationships Created:",len(matches))