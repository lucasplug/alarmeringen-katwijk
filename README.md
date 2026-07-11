# alarmeringen-katwijk

Home Assistant MQTT bridge for alarmeringen.nl Katwijk RSS feed
# 🚒 Alarmeringen Katwijk

Een lichte Docker-container die de RSS-feed van **alarmeringen.nl** uitleest en nieuwe meldingen publiceert naar een MQTT-broker. Ontworpen voor gebruik met Home Assistant, Frigate, Node-RED en andere MQTT-clients.

## Features

- 🚒 Leest de RSS-feed van alarmeringen.nl
- 📡 Publiceert meldingen via MQTT
- 🏠 Integratie met Home Assistant
- 📜 Houdt de laatste 5 meldingen bij
- 📍 Optionele geocoding + afstand tot huis (via Nominatim)
- 💾 Bewaart state op schijf (overleeft een container-herstart)
- 🔄 Polling-interval instelbaar
- 🐳 Docker Compose ondersteuning
- 🔐 MQTT authenticatie

---

## MQTT Topics

| Topic | Retained | Omschrijving |
|--------|:--------:|--------------|
| `alarmeringen/katwijk/laatste` | ✅ | Laatste melding |
| `alarmeringen/katwijk/historie` | ✅ | Laatste 5 meldingen |
| `alarmeringen/katwijk/melding` | ❌ | Alleen nieuwe meldingen |

---

## Environment variables

| Variabele | Omschrijving | Standaard |
|------------|--------------|-----------|
| `MQTT_HOST` | MQTT Broker | `localhost` |
| `MQTT_PORT` | MQTT Poort | `1883` |
| `MQTT_USER` | MQTT Gebruiker | *(leeg)* |
| `MQTT_PASSWORD` | MQTT Wachtwoord | *(leeg)* |
| `MQTT_TOPIC_BASE` | Basis MQTT-topic | `alarmeringen/katwijk` |
| `FEED_URL` | RSS Feed | `https://alarmeringen.nl/feeds/city/katwijk.rss` |
| `INTERVAL` | Polling interval (seconden) | `60` |
| `HISTORY_SIZE` | Aantal meldingen in historie | `5` |
| `GEOCODING_ENABLED` | Geocoding aan/uit | `true` |
| `HOME_LAT` | Breedtegraad van je huis (voor afstand) | *(leeg)* |
| `HOME_LON` | Lengtegraad van je huis (voor afstand) | *(leeg)* |
| `GEOCODER_USER_AGENT` | User-Agent voor Nominatim-verzoeken | `alarmeringen-katwijk/1.0` |
| `STATE_FILE` | Pad naar het state-bestand (seen_ids/historie) | `/app/data/state.json` |
| `MAX_SEEN_IDS` | Max. aantal onthouden alert-ID's | `1000` |

---

## Installatie

Clone de repository:

```bash
git clone https://github.com/<github-gebruikersnaam>/alarmeringen-katwijk.git
cd alarmeringen-katwijk
```

Maak een `.env` bestand:

```env
MQTT_HOST=mqtt.example.local
MQTT_PORT=1883
MQTT_USER=mqtt
MQTT_PASSWORD=vervang_dit
HOME_LAT=52.2
HOME_LON=4.4
```

Start de container:

```bash
docker compose up -d --build
```

De `docker-compose.yml` mount een named volume op `/app/data`, zodat `state.json`
(en dus je "reeds geziene meldingen") een herstart van de container overleeft.

---

## Home Assistant

Voeg de MQTT-integratie toe en configureer deze met dezelfde broker.

Voorbeeldtopics:

```
alarmeringen/katwijk/laatste
alarmeringen/katwijk/historie
alarmeringen/katwijk/melding
```

---

## MQTT Payload

Voorbeeld van een melding:

```json
{
  "id": "6f5f7f0b...",
  "titel": "P1 Woningbrand",
  "omschrijving": "Prins Hendrikkade Katwijk",
  "tijd": "2026-07-09T18:20:00",
  "link": "https://alarmeringen.nl/...",
  "dienst": "brandweer",
  "prioriteit": "P1",
  "locatie": "Prins Hendrikkade",
  "plaats": "Katwijk",
  "lat": 52.2011,
  "lon": 4.3997,
  "afstand_km": 1.4
}
```
