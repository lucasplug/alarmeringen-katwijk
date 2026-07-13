"""Tests voor configuratievalidatie bij het opstarten."""

import pytest

from config import MIN_INTERVAL, ConfigError, load_config


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in (
        "MQTT_PORT",
        "INTERVAL",
        "HISTORY_SIZE",
        "MAX_SEEN_IDS",
        "GEOCODING_ENABLED",
        "HOME_LAT",
        "HOME_LON",
    ):
        monkeypatch.delenv(name, raising=False)


def test_defaults_are_valid():
    cfg = load_config()
    assert cfg.mqtt_port == 1883
    assert cfg.interval == 60
    assert cfg.history_size == 5


def test_invalid_mqtt_port_raises(monkeypatch):
    monkeypatch.setenv("MQTT_PORT", "70000")
    with pytest.raises(ConfigError, match="MQTT_PORT"):
        load_config()


def test_non_numeric_value_raises(monkeypatch):
    monkeypatch.setenv("INTERVAL", "vaak")
    with pytest.raises(ConfigError, match="INTERVAL"):
        load_config()


def test_zero_interval_raises(monkeypatch):
    monkeypatch.setenv("INTERVAL", "0")
    with pytest.raises(ConfigError, match="INTERVAL"):
        load_config()


def test_short_interval_is_clamped(monkeypatch):
    monkeypatch.setenv("INTERVAL", "2")
    assert load_config().interval == MIN_INTERVAL


def test_history_size_minimum(monkeypatch):
    monkeypatch.setenv("HISTORY_SIZE", "0")
    with pytest.raises(ConfigError, match="HISTORY_SIZE"):
        load_config()


def test_max_seen_ids_bumped_to_history_size(monkeypatch):
    monkeypatch.setenv("HISTORY_SIZE", "8")
    monkeypatch.setenv("MAX_SEEN_IDS", "3")
    assert load_config().max_seen_ids == 8


def test_geocoding_disabled_without_home_coordinates(monkeypatch):
    monkeypatch.setenv("GEOCODING_ENABLED", "true")
    cfg = load_config()
    assert cfg.geocoding_enabled is False


def test_geocoding_disabled_with_invalid_coordinates(monkeypatch):
    monkeypatch.setenv("GEOCODING_ENABLED", "true")
    monkeypatch.setenv("HOME_LAT", "tweeenvijftig")
    monkeypatch.setenv("HOME_LON", "4.4")
    cfg = load_config()
    assert cfg.geocoding_enabled is False


def test_geocoding_enabled_with_valid_coordinates(monkeypatch):
    monkeypatch.setenv("GEOCODING_ENABLED", "true")
    monkeypatch.setenv("HOME_LAT", "52.2")
    monkeypatch.setenv("HOME_LON", "4.4")
    cfg = load_config()
    assert cfg.geocoding_enabled is True
    assert cfg.home_lat == 52.2
    assert cfg.home_lon == 4.4
