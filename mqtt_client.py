import json
import logging
import paho.mqtt.client as mqtt


class MqttPublisher:
    def __init__(self, host, port, user, password, topic_base):
        self.topic_base = topic_base.rstrip("/")
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        if user:
            self.client.username_pw_set(user, password)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self.client.connect(host, port, 60)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        logging.info("Verbonden met MQTT broker: %s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        logging.warning("MQTT verbinding verbroken: %s", reason_code)

    def publish_json(self, subtopic, payload, retain=False):
        topic = f"{self.topic_base}/{subtopic}"
        message = json.dumps(payload, ensure_ascii=False)
        result = self.client.publish(topic, message, retain=retain)
        result.wait_for_publish()
        logging.info("Gepubliceerd naar %s", topic)
