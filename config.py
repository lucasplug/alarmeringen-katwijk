import os

def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("true", "1", "yes", "on")

FEED_URL = os.getenv("FEED_URL", "https://alarmeringen.nl/feeds/city/katwijk.rss")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC_BASE = os.getenv("MQTT_TOPIC_BASE", "alarmeringen/katwijk")

INTERVAL = int(os.getenv("INTERVAL", "60"))
HISTORY_SIZE = int(os.getenv("HISTORY_SIZE", "5"))

GEOCODING_ENABLED = env_bool("GEOCODING_ENABLED", True)
HOME_LAT = os.getenv("HOME_LAT")
HOME_LON = os.getenv("HOME_LON")
GEOCODER_USER_AGENT = os.getenv(
    "GEOCODER_USER_AGENT",
    "alarmeringen-katwijk/1.0"
)
