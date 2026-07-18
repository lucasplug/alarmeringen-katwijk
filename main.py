import logging
import os
import signal
import sys
import threading
import time

import requests

from config import Config, ConfigError, load_config
from geocoding import geocode, haversine_km
from mqtt_client import MqttPublisher
from rss_feed import FeedError, fetch_alerts
from state import AlertState

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s: %(message)s",
)


def enrich_alert(alert, cfg: Config):
    """Verrijkt een melding met geocoding en afstand tot huis. Config-fouten
    (ontbrekende coördinaten) zijn al bij het opstarten afgevangen."""
    if not cfg.geocoding_enabled:
        return alert

    location_parts = []

    if getattr(alert, "locatie", ""):
        location_parts.append(alert.locatie)

    if getattr(alert, "plaats", ""):
        location_parts.append(alert.plaats)
    else:
        location_parts.append(cfg.location_name)

    location_parts.append(cfg.country_name)

    query = ", ".join(location_parts)

    try:
        geo = geocode(query, cfg.geocoder_user_agent)

        if not geo:
            logging.warning("Geen geocode-resultaat voor: %s", query)
            return alert

        alert.lat = geo["lat"]
        alert.lon = geo["lon"]
        alert.afstand_km = haversine_km(cfg.home_lat, cfg.home_lon, alert.lat, alert.lon)

        logging.info(
            "Geocode OK: %s -> %.5f, %.5f (%s km)",
            query,
            alert.lat,
            alert.lon,
            alert.afstand_km,
        )

    except Exception as exc:
        logging.warning("Geocoding mislukt voor %s: %s", query, exc)

    return alert


def process_alerts(alerts, state: AlertState, mqtt, cfg: Config) -> bool:
    """Publiceert nieuwe meldingen en markeert ze PAS als gezien nadat alle
    drie de MQTT-publicaties door de broker bevestigd zijn. Zo raakt een
    melding niet permanent kwijt als MQTT tijdelijk onbereikbaar is: de
    volgende poll probeert het gewoon opnieuw.

    Geeft True terug als er state is gewijzigd (en dus opgeslagen moet worden).
    """
    state_changed = False

    for alert in reversed(alerts):
        if state.is_seen(alert.id):
            continue

        alert = enrich_alert(alert, cfg)
        payload = alert.to_dict()

        # Historie eerst lokaal opbouwen; pas definitief maken als de
        # publicaties gelukt zijn.
        candidate_history = ([payload] + state.history)[: cfg.history_size]

        published = (
            mqtt.publish_json("laatste", payload, retain=True)
            and mqtt.publish_json("historie", candidate_history, retain=True)
            and mqtt.publish_json("melding", payload, retain=False)
        )

        if not published:
            logging.warning(
                "MQTT-publicatie niet bevestigd; melding '%s' wordt bij de "
                "volgende poll opnieuw geprobeerd",
                alert.titel,
            )
            break

        state.history = candidate_history
        state.remember(alert.id)
        state_changed = True

        logging.info("Nieuwe melding gepubliceerd: %s", alert.titel)

    return state_changed


def touch_heartbeat(path: str) -> None:
    """Schrijft een heartbeat-timestamp na iedere voltooide poll-iteratie.
    De Docker-healthcheck controleert de leeftijd hiervan; zo faalt de check
    alleen als de hoofdloop echt hangt of gestopt is, en niet wanneer de
    feed of MQTT tijdelijk onbereikbaar is (dat zou een restart-loop geven)."""
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except Exception as exc:
        logging.debug("Kon heartbeat niet schrijven: %s", exc)


def main() -> int:
    try:
        cfg = load_config()
    except ConfigError as exc:
        logging.error("Ongeldige configuratie: %s", exc)
        return 1

    logging.info("P2000-monitor gestart voor %s", cfg.location_name)
    logging.info("Feed: %s", cfg.feed_url)
    logging.info("MQTT broker: %s:%s", cfg.mqtt_host, cfg.mqtt_port)
    logging.info("MQTT topic base: %s", cfg.mqtt_topic_base)

    state = AlertState(max_seen_ids=cfg.max_seen_ids, history_size=cfg.history_size)
    state.load(cfg.state_file)

    mqtt = MqttPublisher(
        host=cfg.mqtt_host,
        port=cfg.mqtt_port,
        user=cfg.mqtt_user,
        password=cfg.mqtt_password,
        topic_base=cfg.mqtt_topic_base,
    )

    # Graceful shutdown: bij SIGTERM/SIGINT (Portainer-update, herstart)
    # de lopende iteratie afmaken, state wegschrijven en MQTT netjes sluiten.
    stop = threading.Event()

    def _handle_signal(signum, frame):
        logging.info("Signaal %s ontvangen, netjes afsluiten...", signum)
        stop.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    while not stop.is_set():
        try:
            alerts = fetch_alerts(
                cfg.feed_url,
                cfg.history_size,
                cfg.geocoder_user_agent,
                cfg.location_name,
            )
        except requests.RequestException as exc:
            logging.warning("Feed niet bereikbaar: %s", exc)
        except FeedError as exc:
            logging.warning("Feed niet te parsen: %s", exc)
        else:
            try:
                if process_alerts(alerts, state, mqtt, cfg):
                    state.save(cfg.state_file)
            except Exception:
                logging.exception("Fout bij verwerken/publiceren")

        touch_heartbeat(cfg.heartbeat_file)
        stop.wait(cfg.interval)

    state.save(cfg.state_file)
    mqtt.close()
    logging.info("Gestopt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
