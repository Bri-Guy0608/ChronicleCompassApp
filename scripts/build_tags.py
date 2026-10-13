import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVENT_FILE = PROJECT_ROOT / "data" / "processed" / "events.csv"
TAG_FILE = PROJECT_ROOT / "data" / "processed" / "tags.csv"
EVENTTAG_FILE = PROJECT_ROOT / "data" / "processed" / "eventtag.csv"

TAGS = {
    "Military": {
        "description": "Wars, battles, sieges and armed conflicts",
        "keywords": [
            "battle","war","siege","army","navy","soldier","troops",
            "invades","invaded","defeat","victory","campaign",
            "rebellion","occupation","conquest","military"
        ]
    },

    "Politics": {
        "description": "Governments, elections and diplomacy",
        "keywords": [
            "government","president","prime minister","parliament",
            "election","treaty","senate","congress","constitution",
            "political","minister","vote","voting","diplomatic"
        ]
    },

    "Royalty": {
        "description": "Kings, queens and monarchies",
        "keywords": [
            "king","queen","prince","princess","emperor",
            "empress","duke","duchess","monarch","royal",
            "dynasty","crown"
        ]
    },

    "Religion": {
        "description": "Religious events",
        "keywords": [
            "church","pope","bishop","saint","religion","temple",
            "mosque","cathedral","christian","islam","buddhist",
            "hindu","jewish"
        ]
    },

    "Science": {
        "description": "Scientific discoveries",
        "keywords": [
            "scientist","physics","chemistry","biology",
            "discovery","discover","experiment","laboratory",
            "research"
        ]
    },

    "Technology": {
        "description": "Technology and engineering",
        "keywords": [
            "computer","internet","software","hardware","technology",
            "engineering","engine","telephone","radio",
            "television","electricity"
        ]
    },

    "Space": {
        "description": "Space exploration",
        "keywords": [
            "apollo","nasa","moon","mars","satellite",
            "space","astronaut","rocket","orbit","iss"
        ]
    },

    "Exploration": {
        "description": "Exploration and discovery",
        "keywords": [
            "explorer","expedition","voyage","discover",
            "discovered","mapping","crosses","crossed"
        ]
    },

    "Natural Disaster": {
        "description": "Natural disasters",
        "keywords": [
            "earthquake","tsunami","volcano","eruption",
            "flood","hurricane","cyclone","tornado",
            "wildfire","plague"
        ]
    },

    "Medicine": {
        "description": "Medical discoveries",
        "keywords": [
            "disease","virus","vaccine","medicine",
            "medical","hospital","doctor","physician",
            "pandemic","epidemic"
        ]
    },

    "Culture": {
        "description": "Arts and culture",
        "keywords": [
            "artist","painting","museum","music",
            "opera","book","novel","film",
            "theater","literature"
        ]
    },

    "Sports": {
        "description": "Sporting events",
        "keywords": [
            "olympics","football","soccer","basketball",
            "baseball","tennis","cricket","world cup",
            "championship"
        ]
    },

    "Economics": {
        "description": "Trade and finance",
        "keywords": [
            "economy","economic","market","trade",
            "bank","currency","inflation","financial",
            "stock"
        ]
    },

    "Revolution": {
        "description": "Political or social revolutions",
        "keywords": [
            "revolution","revolt","uprising","coup",
            "independence","civil war"
        ]
    }

}

events = pd.read_csv(EVENT_FILE)
tagRows = []
tagLookup = {}
tagID = 1

for tagName, info in TAGS.items():
    tagLookup[tagName] = tagID
    tagRows.append({"TagID": tagID, "TagName": tagName, "Description": info["description"]})
    tagID += 1

tagsDF = pd.DataFrame(tagRows)
eventTagRows = []

for _, row in events.iterrows():
    event_text = (str(row["Title"]) + " " + str(row["Description"])).lower()
    assigned = set()

    for tagName, info in TAGS.items():
        for keyword in info["keywords"]:
            if keyword in event_text:
                assigned.add(tagName)
                break

    for tagName in assigned:
        eventTagRows.append({"EventID": row["EventID"], "TagID": tagLookup[tagName]})

eventtagDF = pd.DataFrame(eventTagRows)
tagsDF.to_csv(TAG_FILE, index=False)
eventtagDF.to_csv(EVENTTAG_FILE, index=False)

print(f"Tags Created: {len(tagsDF)}")
print(f"Event-Tag Relationships: {len(eventtagDF)}")