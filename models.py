from dataclasses import dataclass, asdict
import hashlib


@dataclass
class Alert:
    id: str
    titel: str
    omschrijving: str
    link: str
    tijd: str

    @classmethod
    def from_entry(cls, entry):
        raw = f"{entry.get('id','')}-{entry.get('title','')}-{entry.get('published','')}"
        alert_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return cls(
            id=alert_id,
            titel=entry.get("title", ""),
            omschrijving=entry.get("summary", ""),
            link=entry.get("link", ""),
            tijd=entry.get("published", ""),
        )

    def to_dict(self):
        return asdict(self)
