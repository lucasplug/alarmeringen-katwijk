"""Tests voor RSS-parsing en Alert-extractie — volledig zonder netwerk.

feed_sample.xml volgt het standaard RSS 2.0-formaat van alarmeringen.nl
(title/description/link/guid/pubDate), met representatieve P2000-teksten.
"""

from pathlib import Path
from unittest import mock

import pytest
import requests

from rss_feed import REQUEST_TIMEOUT, FeedError, fetch_alerts, parse_feed

FIXTURE = Path(__file__).parent / "fixtures" / "feed_sample.xml"


@pytest.fixture()
def feed_bytes() -> bytes:
    return FIXTURE.read_bytes()


def test_parse_feed_extracts_alert_fields(feed_bytes):
    alerts = parse_feed(feed_bytes, limit=5)
    assert len(alerts) == 3

    brand = alerts[0]
    assert brand.titel == "P1 Woningbrand Prins Hendrikkade Katwijk"
    assert brand.prioriteit == "P1"
    assert brand.dienst == "brandweer"
    assert brand.locatie == "Prins Hendrikkade"
    assert brand.plaats == "Katwijk"
    # 10:39 UTC wordt 12:39 Nederlandse zomertijd.
    assert brand.tijd == "2026-07-10T12:39:00+02:00"

    ambu = alerts[1]
    assert ambu.dienst == "ambulance"
    assert ambu.prioriteit == "A1"
    assert ambu.locatie == "Zeeweg"  # 'katwzh'-resttekst is opgeruimd

    politie = alerts[2]
    assert politie.dienst == "politie"
    assert politie.locatie == "Tramstraat"


def test_parse_feed_ids_are_stable_and_unique(feed_bytes):
    first = parse_feed(feed_bytes, limit=5)
    second = parse_feed(feed_bytes, limit=5)
    assert [a.id for a in first] == [a.id for a in second]
    assert len({a.id for a in first}) == 3


def test_parse_feed_respects_limit(feed_bytes):
    assert len(parse_feed(feed_bytes, limit=2)) == 2


def test_empty_feed_is_valid():
    empty = b'<?xml version="1.0"?><rss version="2.0"><channel><title>x</title></channel></rss>'
    assert parse_feed(empty, limit=5) == []


def test_invalid_feed_raises_feed_error():
    with pytest.raises(FeedError):
        parse_feed(b"dit is geen xml <<<", limit=5)


def test_fetch_alerts_uses_timeout_and_status_check(feed_bytes):
    response = mock.Mock()
    response.content = feed_bytes
    with mock.patch("rss_feed.requests.get", return_value=response) as get:
        alerts = fetch_alerts("https://example.test/feed.rss", 5, "test-agent/1.0")

    assert len(alerts) == 3
    response.raise_for_status.assert_called_once()
    _, kwargs = get.call_args
    assert kwargs["timeout"] == REQUEST_TIMEOUT
    assert kwargs["headers"]["User-Agent"] == "test-agent/1.0"


def test_fetch_alerts_propagates_network_errors():
    with mock.patch(
        "rss_feed.requests.get", side_effect=requests.ConnectionError("kapot")
    ):
        with pytest.raises(requests.RequestException):
            fetch_alerts("https://example.test/feed.rss", 5, "test-agent/1.0")
