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
| `HEARTBEAT_FILE` | Pad naar het heartbeat-bestand voor de healthcheck | `/app/data/heartbeat` |
| `LOG_LEVEL` | Logniveau (`DEBUG`, `INFO`, `WARNING`, ...) | `INFO` |

Ongeldige verplichte waarden (bv. een MQTT-poort buiten 1–65535) stoppen de container met een duidelijke foutmelding; herstelbare waarden worden geclampt met een warning in de log.

---

## Installatie

`docker-compose.yml` is zelfstandig: alle environment variables staan inline en het gebruikt het kant-en-klare image van GHCR — er is geen `.env` nodig.

**Portainer:** ga naar **Stacks → Add stack → Web editor**, plak de inhoud van `docker-compose.yml`, vul je MQTT-gegevens in en deploy.

**Zonder Portainer:**

```bash
docker compose up -d
```

**Updaten:** `docker compose pull && docker compose up -d` (de stack volgt `:latest`).

**Terugrollen:** zet in de compose tijdelijk een specifieke versietag (bv.
`image: ghcr.io/lucasplug/alarmeringen-katwijk:1.0.0`) of een image-digest
(`docker images --digests`), en draai `docker compose up -d`. Terug naar
nieuwste: tag weer op `:latest` zetten en opnieuw pullen.

**Lokaal ontwikkelen** (bouwt uit de broncode, leest `.env`):

```bash
git clone https://github.com/lucasplug/alarmeringen-katwijk.git
cd alarmeringen-katwijk
cat > .env << 'EOF'
MQTT_HOST=mqtt.example.local
MQTT_PORT=1883
MQTT_USER=mqtt
MQTT_PASSWORD=vervang_dit
HOME_LAT=52.2
HOME_LON=4.4
EOF
docker compose -f docker-compose.dev.yml up -d --build
```

Beide compose-varianten mounten een named volume op `/app/data`, zodat `state.json`
(en dus je "reeds geziene meldingen") een herstart van de container overleeft.

---

## Betrouwbaarheid

- Meldingen worden met **MQTT QoS 1** gepubliceerd en pas als "gezien" gemarkeerd
  nadat de broker alle drie de publicaties heeft bevestigd. Valt MQTT tijdelijk
  weg, dan wordt de melding bij een volgende poll gewoon opnieuw geprobeerd —
  er gaat geen alarmering permanent verloren.
- De RSS-feed wordt opgehaald met expliciete timeouts en statuscontrole, zodat
  een hangende verbinding de poll-loop niet blokkeert.
- De container heeft een **healthcheck** op basis van een heartbeat die de
  hoofdloop na iedere iteratie schrijft. Tijdelijke uitval van de feed of MQTT
  houdt de container gewoon healthy (geen restart-loop); alleen een echt
  hangende of gestopte loop wordt unhealthy.
- Bij `SIGTERM` (Portainer-update, herstart) wordt de state weggeschreven en de
  MQTT-verbinding netjes gesloten.

---

## Ontwikkelen & testen

```bash
pip install -r requirements-dev.txt
pytest
```

De tests draaien volledig zonder netwerk (RSS, MQTT en geocoding zijn gemockt)
en dekken o.a. feed-parsing, nieuw-vs-gezien, de publiceer-dan-onthouden-volgorde
bij MQTT-storingen, state-opslag, historie- en seen-ids-begrenzing, de
geocodecache en configuratievalidatie.

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
