import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Ondergrens voor het pollinterval, om alarmeringen.nl niet te hameren.
MIN_INTERVAL = 10


class ConfigError(ValueError):
    """Ongeldige configuratie; de container hoort hierop te stoppen."""


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("true", "1", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(f"{name}={raw!r} is geen geldig getal")


@dataclass(frozen=True)
class Config:
    feed_url: str
    mqtt_host: str
    mqtt_port: int
    mqtt_user: str
    mqtt_password: str
    mqtt_topic_base: str
    interval: int
    history_size: int
    geocoding_enabled: bool
    home_lat: float | None
    home_lon: float | None
    geocoder_user_agent: str
    state_file: str
    max_seen_ids: int
    heartbeat_file: str


def load_config() -> Config:
    """Leest en valideert alle configuratie uit environment variables.

    Ongeldige verplichte waarden geven een ConfigError (container stopt met
    een duidelijke fout); herstelbare waarden worden geclampt met een warning.
    """
    mqtt_port = _env_int("MQTT_PORT", 1883)
    if not 1 <= mqtt_port <= 65535:
        raise ConfigError(f"MQTT_PORT={mqtt_port} valt buiten 1-65535")

    interval = _env_int("INTERVAL", 60)
    if interval <= 0:
        raise ConfigError(f"INTERVAL={interval} moet positief zijn")
    if interval < MIN_INTERVAL:
        logger.warning("INTERVAL=%d is erg kort; geclampt naar %d", interval, MIN_INTERVAL)
        interval = MIN_INTERVAL

    history_size = _env_int("HISTORY_SIZE", 5)
    if history_size < 1:
        raise ConfigError(f"HISTORY_SIZE={history_size} moet minimaal 1 zijn")

    max_seen_ids = _env_int("MAX_SEEN_IDS", 1000)
    if max_seen_ids < history_size:
        logger.warning(
            "MAX_SEEN_IDS=%d is kleiner dan HISTORY_SIZE=%d; verhoogd naar %d",
            max_seen_ids,
            history_size,
            history_size,
        )
        max_seen_ids = history_size

    # Geocoding: alleen aan als de thuiscoördinaten er allebei zijn en geldig
    # zijn. Dit wordt éénmalig bij het opstarten gecontroleerd, zodat de
    # poll-loop niet iedere minuut dezelfde warning logt.
    geocoding_enabled = env_bool("GEOCODING_ENABLED", True)
    home_lat: float | None = None
    home_lon: float | None = None
    if geocoding_enabled:
        raw_lat = os.getenv("HOME_LAT", "").strip()
        raw_lon = os.getenv("HOME_LON", "").strip()
        try:
            if raw_lat and raw_lon:
                home_lat = float(raw_lat)
                home_lon = float(raw_lon)
            else:
                raise ValueError("HOME_LAT/HOME_LON ontbreken")
        except ValueError as exc:
            logger.warning("Geocoding uitgeschakeld: %s", exc)
            geocoding_enabled = False

    return Config(
        feed_url=os.getenv("FEED_URL", "https://alarmeringen.nl/feeds/city/katwijk.rss"),
        mqtt_host=os.getenv("MQTT_HOST", "localhost"),
        mqtt_port=mqtt_port,
        mqtt_user=os.getenv("MQTT_USER", ""),
        mqtt_password=os.getenv("MQTT_PASSWORD", ""),
        mqtt_topic_base=os.getenv("MQTT_TOPIC_BASE", "alarmeringen/katwijk"),
        interval=interval,
        history_size=history_size,
        geocoding_enabled=geocoding_enabled,
        home_lat=home_lat,
        home_lon=home_lon,
        geocoder_user_agent=os.getenv("GEOCODER_USER_AGENT", "alarmeringen-katwijk/1.0"),
        state_file=os.getenv("STATE_FILE", "/app/data/state.json"),
        max_seen_ids=max_seen_ids,
        heartbeat_file=os.getenv("HEARTBEAT_FILE", "/app/data/heartbeat"),
    )
