import os

FEED_URL = os.getenv("FEED_URL", "https://zwaailicht.nu/feed/meldingen/katwijk.xml")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC_BASE = os.getenv("MQTT_TOPIC_BASE", "alarmeringen/katwijk")
INTERVAL = int(os.getenv("INTERVAL", "60"))
HISTORY_SIZE = int(os.getenv("HISTORY_SIZE", "5"))
