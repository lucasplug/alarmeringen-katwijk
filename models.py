from dataclasses import dataclass, asdict
import hashlib
import re


@dataclass
class Alert:
    id: str
    titel: str
    omschrijving: str
    link: str
    tijd: str

    dienst: str = ""
    prioriteit: str = ""
    locatie: str = ""
    plaats: str = "Katwijk"

    lat: float | None = None
    lon: float | None = None
    afstand_km: float | None = None

    @classmethod
    def from_entry(cls, entry):
        titel = entry.get("title", "").strip()
        omschrijving = entry.get("summary", "").strip()
        link = entry.get("link", "").strip()
        tijd = entry.get("published", "") or entry.get("updated", "")

        raw = f"{entry.get('id','')}-{titel}-{tijd}-{link}"
        alert_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return cls(
            id=alert_id,
            titel=titel,
            omschrijving=omschrijving,
            link=link,
            tijd=tijd,
            dienst=detect_dienst(titel, omschrijving),
            prioriteit=detect_prioriteit(titel),
            locatie=extract_locatie(titel, omschrijving),
            plaats="Katwijk",
        )

    def to_dict(self):
        return asdict(self)


def detect_prioriteit(text: str) -> str:
    text = text.lower()

    match = re.search(r"\b(a1|a2|b1|b2|prio 1|prio 2|p1|p2)\b", text)
    if not match:
        return ""

    value = match.group(1).upper()
    return value.replace("PRIO ", "P")


def detect_dienst(titel: str, omschrijving: str) -> str:
    text = f"{titel} {omschrijving}".lower()

    if "ambulance" in text or re.search(r"\ba1\b|\ba2\b", text):
        return "ambulance"

    if "brandweer" in text or "prio 1" in text or "prio 2" in text:
        return "brandweer"

    if "politie" in text:
        return "politie"

    return ""


def extract_locatie(titel: str, omschrijving: str) -> str:
    text = f"{titel} {omschrijving}".strip()

    patterns = [
        r"naar\s+(.+?)\s+in\s+Katwijk",
        r"op\s+(.+?)\s+in\s+Katwijk",
        r"\b(n\d{3})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            locatie = match.group(1).strip()
            locatie = re.sub(r"\s+", " ", locatie)
            return locatie

    return ""
