import feedparser
from models import Alert


def fetch_alerts(feed_url, limit):
    feed = feedparser.parse(feed_url)

    if feed.bozo:
        raise RuntimeError(f"RSS-feed fout: {feed.bozo_exception}")

    return [Alert.from_entry(entry) for entry in feed.entries[:limit]]
