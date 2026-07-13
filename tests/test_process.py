"""Tests voor de publiceer-en-onthoud-volgorde: een melding mag pas als
gezien worden gemarkeerd nadat alle MQTT-publicaties bevestigd zijn."""

from pathlib import Path

import pytest

import main as app_main
from config import Config
from rss_feed import parse_feed
from state import AlertState

FIXTURE = Path(__file__).parent / "fixtures" / "feed_sample.xml"


class FakeMqtt:
    """Registreert publicaties; kan per subtopic of volledig falen."""

    def __init__(self, fail_topics=(), fail_all=False):
        self.fail_topics = set(fail_topics)
        self.fail_all = fail_all
        self.published = []  # (subtopic, payload, retain)

    def publish_json(self, subtopic, payload, retain=False, qos=1):
        if self.fail_all or subtopic in self.fail_topics:
            return False
        self.published.append((subtopic, payload, retain))
        return True


def make_config(**overrides) -> Config:
    values = dict(
        feed_url="https://example.test/feed.rss",
        mqtt_host="localhost",
        mqtt_port=1883,
        mqtt_user="",
        mqtt_password="",
        mqtt_topic_base="alarmeringen/katwijk",
        interval=60,
        history_size=5,
        geocoding_enabled=False,
        home_lat=None,
        home_lon=None,
        geocoder_user_agent="test/1.0",
        state_file="/tmp/state.json",
        max_seen_ids=100,
        heartbeat_file="/tmp/heartbeat",
    )
    values.update(overrides)
    return Config(**values)


@pytest.fixture()
def alerts():
    return parse_feed(FIXTURE.read_bytes(), limit=5)


def test_multiple_new_alerts_published_oldest_first(alerts):
    state = AlertState(max_seen_ids=100, history_size=5)
    mqtt = FakeMqtt()

    changed = app_main.process_alerts(alerts, state, mqtt, make_config())

    assert changed is True
    # 3 meldingen x 3 topics, oudste (politie) eerst.
    assert len(mqtt.published) == 9
    melding_titels = [p[1]["titel"] for p in mqtt.published if p[0] == "melding"]
    assert melding_titels[0].startswith("Politie")
    assert melding_titels[-1].startswith("P1 Woningbrand")
    # Nieuwste melding staat vooraan in de historie.
    assert state.history[0]["titel"].startswith("P1 Woningbrand")
    assert all(state.is_seen(a.id) for a in alerts)


def test_second_poll_publishes_nothing_new(alerts):
    state = AlertState(max_seen_ids=100, history_size=5)
    mqtt = FakeMqtt()
    cfg = make_config()

    assert app_main.process_alerts(alerts, state, mqtt, cfg) is True
    mqtt.published.clear()

    assert app_main.process_alerts(alerts, state, mqtt, cfg) is False
    assert mqtt.published == []


def test_publish_failure_does_not_mark_alert_as_seen(alerts):
    state = AlertState(max_seen_ids=100, history_size=5)
    mqtt = FakeMqtt(fail_all=True)

    changed = app_main.process_alerts(alerts, state, mqtt, make_config())

    assert changed is False
    assert not state.seen_ids
    assert state.history == []


def test_partial_publish_failure_does_not_mark_alert_as_seen(alerts):
    # 'laatste' en 'historie' lukken, het niet-retained 'melding' faalt.
    state = AlertState(max_seen_ids=100, history_size=5)
    mqtt = FakeMqtt(fail_topics={"melding"})

    changed = app_main.process_alerts(alerts, state, mqtt, make_config())

    assert changed is False
    assert not state.seen_ids
    assert state.history == []


def test_retry_after_mqtt_recovery_publishes_alert(alerts):
    state = AlertState(max_seen_ids=100, history_size=5)
    cfg = make_config()

    # Eerste poll: broker onbereikbaar -> niets als gezien gemarkeerd.
    assert app_main.process_alerts(alerts, state, FakeMqtt(fail_all=True), cfg) is False

    # Tweede poll: broker terug -> alles alsnog gepubliceerd.
    mqtt = FakeMqtt()
    assert app_main.process_alerts(alerts, state, mqtt, cfg) is True
    assert len([p for p in mqtt.published if p[0] == "melding"]) == 3


def test_history_is_bounded(alerts):
    state = AlertState(max_seen_ids=100, history_size=2)
    mqtt = FakeMqtt()

    app_main.process_alerts(alerts, state, mqtt, make_config(history_size=2))

    assert len(state.history) == 2
    # De gepubliceerde historie is ook begrensd.
    last_history = [p for p in mqtt.published if p[0] == "historie"][-1][1]
    assert len(last_history) == 2


def test_heartbeat_written(tmp_path):
    path = tmp_path / "data" / "heartbeat"
    app_main.touch_heartbeat(str(path))
    assert path.exists()
