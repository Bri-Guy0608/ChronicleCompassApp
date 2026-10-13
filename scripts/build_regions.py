import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVENT_FILE = PROJECT_ROOT / "data" / "processed" / "events.csv"
REGION_FILE = PROJECT_ROOT / "data" / "processed" / "regions.csv"
UPDATED_EVENT_FILE = PROJECT_ROOT / "data" / "processed" / "events.csv"

COUNTRY_LOOKUP = {

    "france":"Europe",
    "germany":"Europe",
    "england":"Europe",
    "britain":"Europe",
    "united kingdom":"Europe",
    "uk":"Europe",
    "italy":"Europe",
    "spain":"Europe",
    "portugal":"Europe",
    "belgium":"Europe",
    "netherlands":"Europe",
    "poland":"Europe",
    "russia":"Europe",
    "ukraine":"Europe",
    "switzerland":"Europe",
    "greece":"Europe",

    "china":"Asia",
    "japan":"Asia",
    "india":"Asia",
    "korea":"Asia",
    "mongolia":"Asia",
    "iran":"Asia",
    "iraq":"Asia",

    "united states":"North America",
    "usa":"North America",
    "america":"North America",
    "canada":"North America",
    "mexico":"North America",

    "brazil":"South America",
    "argentina":"South America",
    "chile":"South America",
    "peru":"South America",

    "egypt":"Africa",
    "ethiopia":"Africa",
    "south africa":"Africa",
    "morocco":"Africa",

    "australia":"Oceania",
    "new zealand":"Oceania"
}

events = pd.read_csv(EVENT_FILE)
regionRows = []
countryToID = {}
regionID = 1
eventRegionIDs = []

for _, row in events.iterrows():
    text = (str(row["Title"]) + " " + str(row["Description"])).lower()
    foundCountry = "Unknown"
    foundContinent = "Unknown"

    for country, continent in COUNTRY_LOOKUP.items():
        if country in text:
            foundCountry = country.title()
            foundContinent = continent
            break

    key = (foundCountry, foundContinent)

    if key not in countryToID:
        countryToID[key] = regionID
        regionRows.append({"RegionID": regionID, "Country": foundCountry, "Continent": foundContinent})
        regionID += 1

    eventRegionIDs.append(countryToID[key])

events["RegionID"] = eventRegionIDs
regions = pd.DataFrame(regionRows)
regions.to_csv(REGION_FILE,index=False)
events.to_csv(UPDATED_EVENT_FILE,index=False)

print("Regions:",len(regions))
print("Events Updated")