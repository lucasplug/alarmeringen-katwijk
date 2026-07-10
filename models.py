from dataclasses import dataclass, asdict
from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo
import hashlib
import re


def parse_local_time(value: str) -> str:
    """
    Zet RSS UTC tijd om naar Europe/Amsterdam.
    Retourneert ISO8601.
    """

    if not value:
        return ""

    try:
        dt = parsedate_to_datetime(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))

        dt = dt.astimezone(ZoneInfo("Europe/Amsterdam"))

        return dt.isoformat(timespec="seconds")

    except Exception:
        return value


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

        raw_time = entry.get("published", "") or entry.get("updated", "")
        tijd = parse_local_time(raw_time)

        raw = f"{entry.get('id','')}-{titel}-{tijd}-{link}"

        alert_id = hashlib.sha256(raw.encode()).hexdigest()

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

    if "a1" in text:
        return "A1"

    if "a2" in text:
        return "A2"

    if "b1" in text:
        return "B1"

    if "b2" in text:
        return "B2"

    if "prio 1" in text or "p1" in text:
        return "P1"

    if "prio 2" in text or "p2" in text:
        return "P2"

    return ""


def detect_dienst(titel: str, omschrijving: str):

    text = f"{titel} {omschrijving}".lower()

    if (
        "ambulance" in text
        or re.search(r"\ba1\b", text)
        or re.search(r"\ba2\b", text)
    ):
        return "ambulance"

    if (
        "brandweer" in text
        or "tankautospuit" in text
        or "ts " in text
        or "hv " in text
        or "hoogwerker" in text
        or "ovd-b" in text
    ):
        return "brandweer"

    if (
        "politie" in text
        or "ovd-p" in text
    ):
        return "politie"

    return ""


def extract_locatie(titel: str, omschrijving: str):

    # Eerst de omschrijving gebruiken (veel betrouwbaarder)
    patterns = [
        r"naar\s+(.+?)\s+in\s+Katwijk",
        r"op\s+(.+?)\s+in\s+Katwijk",
    ]

    for pattern in patterns:

        match = re.search(pattern, omschrijving, re.IGNORECASE)

        if match:
            locatie = match.group(1).strip()
            locatie = re.sub(r"\s+", " ", locatie)
            return locatie

    # Daarna de titel proberen
    patterns = [
        r"\b(N\d{3})\b",
        r"\b([A-Z][A-Za-z]+weg)\b",
        r"\b([A-Z][A-Za-z]+straat)\b",
        r"\b([A-Z][A-Za-z]+laan)\b",
        r"\b([A-Z][A-Za-z]+singel)\b",
        r"\b([A-Z][A-Za-z]+plein)\b",
        r"\b([A-Z][A-Za-z]+dijk)\b",
        r"\b([A-Z][A-Za-z]+pad)\b",
    ]

    for pattern in patterns:

        match = re.search(pattern, titel)

        if match:
            return match.group(1)

    return ""
