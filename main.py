import time
import logging

from config import (
    FEED_URL,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_USER,
    MQTT_PASSWORD,
    MQTT_TOPIC_BASE,
    INTERVAL,
    HISTORY_SIZE,
)
from mqtt_client import MqttPublisher
from rss_feed import fetch_alerts


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

seen_ids = set()
history = []


def main():
    global history

    logging.info("Alarmeringen Katwijk gestart")
    logging.info("Feed: %s", FEED_URL)
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
                history.insert(0, alert.to_dict())
                history = history[:HISTORY_SIZE]

                mqtt.publish_json("laatste", alert.to_dict(), retain=True)
                mqtt.publish_json("historie", history, retain=True)
                mqtt.publish_json("melding", alert.to_dict(), retain=False)

                logging.info("Nieuwe melding: %s", alert.titel)

        except Exception as exc:
            logging.exception("Fout bij ophalen/publiceren: %s", exc)

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
