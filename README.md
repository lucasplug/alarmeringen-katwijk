# alarmeringen-katwijk

Home Assistant MQTT bridge for Zwaailicht.nu Katwijk RSS feed
# 🚒 Alarmeringen Katwijk

Een lichte Docker-container die de RSS-feed van **Zwaailicht.nu** uitleest en nieuwe meldingen publiceert naar een MQTT-broker. Ontworpen voor gebruik met Home Assistant, Frigate, Node-RED en andere MQTT-clients.

## Features

- 🚒 Leest de RSS-feed van Zwaailicht.nu
- 📡 Publiceert meldingen via MQTT
- 🏠 Integratie met Home Assistant
- 📜 Houdt de laatste 5 meldingen bij
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

| Variabele | Omschrijving | Voorbeeld |
|------------|--------------|-----------|
| `MQTT_HOST` | MQTT Broker | `mqtt.example.local` |
| `MQTT_PORT` | MQTT Poort | `1883` |
| `MQTT_USER` | MQTT Gebruiker | `mqtt` |
| `MQTT_PASSWORD` | MQTT Wachtwoord | `********` |
| `MQTT_TOPIC_BASE` | Basis MQTT-topic | `alarmeringen/katwijk` |
| `FEED_URL` | RSS Feed | `https://zwaailicht.nu/feed/meldingen/katwijk.xml` |
| `INTERVAL` | Polling interval (seconden) | `60` |
| `HISTORY_SIZE` | Aantal meldingen in historie | `5` |

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
```

Start de container:

```bash
docker compose up -d --build
```

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
  "link": "https://zwaailicht.nu
