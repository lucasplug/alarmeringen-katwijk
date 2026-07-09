import logging
import time

from config import (
    FEED_URL,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_USER,
    MQTT_PASSWORD,
    MQTT_TOPIC_BASE,
    INTERVAL,
    HISTORY_SIZE,
    GEOCODING_ENABLED,
    HOME_LAT,
    HOME_LON,
    GEOCODER_USER_AGENT,
)
from geocoding import geocode, haversine_km
from mqtt_client import MqttPublisher
from rss_feed import fetch_alerts


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

seen_ids = set()
history = []


def enrich_alert(alert):
    """
    Verrijkt een melding met geocoding en afstand.
    Werkt alleen als GEOCODING_ENABLED=true en HOME_LAT/HOME_LON zijn ingesteld.
    """

    if not GEOCODING_ENABLED:
        return alert

    if not HOME_LAT or not HOME_LON:
        logging.warning("Geocoding staat aan, maar HOME_LAT/HOME_LON ontbreken")
        return alert

    location_parts = []

    if getattr(alert, "locatie", ""):
        location_parts.append(alert.locatie)

    if getattr(alert, "plaats", ""):
        location_parts.append(alert.plaats)
    else:
        location_parts.append("Katwijk")

    location_parts.append("Nederland")

    query = ", ".join(location_parts)

    try:
        geo = geocode(query, GEOCODER_USER_AGENT)

        if not geo:
            logging.warning("Geen geocode-resultaat voor: %s", query)
            return alert

        alert.lat = geo["lat"]
        alert.lon = geo["lon"]
        alert.afstand_km = haversine_km(
            HOME_LAT,
            HOME_LON,
            alert.lat,
            alert.lon,
        )

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


def main():
    global history

    logging.info("Alarmeringen Katwijk gestart")
    logging.info("Feed: %s", FEED_URL)
    logging.info("MQTT broker: %s:%s", MQTT_HOST, MQTT_PORT)
    logging.info("MQTT topic base: %s", MQTT_TOPIC_BASE)

    mqtt = MqttPublisher(
        host=MQTT_HOST,
        port=MQTT_PORT,
        user=MQTT_USER,
        password=MQTT_PASSWORD,
        topic_base=MQTT_TOPIC_BASE,
    )

    while True:
        try:
            alerts = fetch_alerts(FEED_URL, HISTORY_SIZE)

            for alert in reversed(alerts):
                if alert.id in seen_ids:
                    continue

                seen_ids.add(alert.id)

                alert = enrich_alert(alert)

                alert_payload = alert.to_dict()

                history.insert(0, alert_payload)
                history = history[:HISTORY_SIZE]

                mqtt.publish_json("laatste", alert_payload, retain=True)
                mqtt.publish_json("historie", history, retain=True)
                mqtt.publish_json("melding", alert_payload, retain=False)

                logging.info("Nieuwe melding gepubliceerd: %s", alert.titel)

        except Exception as exc:
            logging.exception("Fout bij ophalen/publiceren: %s", exc)

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
