# Home Dashboard

En hjemmeskjerm-dashboard bygget med Streamlit for Raspberry Pi 4 med 7" touchscreen (800x480). Viser vær, kalender, ukesmeny og nyheter på en enkel og oversiktlig måte.

Optimalisert for:
- Raspberry Pi 4
- Offisiell 7" touchscreen (800x480)
- Touch-vennlige knapper og layout
- Kiosk-modus uten synlig nettleser-UI

## Funksjoner

- **Vær** - Værmelding fra yr.no/met.no med 24-timers prognose og 3-dagers oversikt
- **Kalender** - Synkroniserer med iCloud-kalender, viser dagens og kommende hendelser
- **Ukesmeny** - Henter middagsplaner fra Google Sheets
- **Nyheter** - Toppsaker fra NRK og BBC World News
- **Transport** - Sanntids avganger fra Ruter/Entur (T-bane, buss, trikk)
- **Hjem** - Oversikt over alt på én side

## Installasjon

### 1. Klon prosjektet

```bash
git clone https://github.com/your-username/home_dashboard_raspie.git
cd home_dashboard_raspie
```

### 2. Opprett virtuelt miljø

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer avhengigheter

```bash
pip install -r requirements.txt
```

### 4. Konfigurer miljøvariabler

```bash
cp .env.example .env
```

Rediger `.env` med dine verdier:

```env
# iCloud Calendar
ICLOUD_EMAIL=din@email.com
ICLOUD_PASSWORD=din-app-spesifikke-passord

# Google Sheets
GOOGLE_SHEET_ID=din-google-sheet-id

# Vær-lokasjon (valgfritt, standard er Oslo)
WEATHER_LAT=59.91
WEATHER_LON=10.75
```

### 5. Sett opp Google Sheets (for ukesmeny)

1. Gå til [Google Cloud Console](https://console.cloud.google.com/)
2. Opprett et nytt prosjekt
3. Aktiver Google Sheets API og Google Drive API
4. Opprett en Service Account og last ned JSON-nøkkelen
5. Lagre filen som `credentials.json` i prosjektmappen
6. Del Google Sheet-et ditt med service account-emailen

Google Sheet-et må ha kolonner: `Dag` og `Middag`

| Dag | Middag |
|-----|--------|
| Mandag | Taco |
| Tirsdag | Pasta |
| ... | ... |

### 6. Sett opp transport-stopp (Ruter/Entur)

1. Gå til [stoppested.entur.org](https://stoppested.entur.org/)
2. Søk etter ditt stoppested (f.eks. "Jernbanetorget")
3. Kopier stop-ID (f.eks. `NSR:StopPlace:58366`)
4. Legg til i `.env`:

```env
# Ett stoppested
TRANSPORT_STOPS=NSR:StopPlace:61268=Sinsen T

# Flere stoppesteder (kommaseparert)
TRANSPORT_STOPS=NSR:StopPlace:61268=Sinsen T,NSR:StopPlace:58366=Jernbanetorget
```

### 7. Sett opp iCloud (for kalender)

1. Gå til [Apple ID](https://appleid.apple.com/)
2. Generer et app-spesifikt passord under Sikkerhet
3. Bruk dette passordet i `.env`-filen

## Kjøring (lokal utvikling)

```bash
streamlit run main.py
```

Dashboardet vil kjøre på `http://localhost:8501`

## Kjøring på Raspberry Pi (Docker med auto-oppdatering)

Med Docker og Watchtower oppdateres dashboardet automatisk når du pusher til GitHub.

### 1. Installer Docker på Pi

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Logg ut og inn igjen
```

### 2. Sett opp prosjektet

```bash
mkdir ~/dashboard && cd ~/dashboard

# Kopier secrets til Pi (kun én gang)
nano credentials.json  # Lim inn Google credentials
nano .env              # Lim inn miljøvariabler
```

### 3. Opprett docker-compose.yml

```bash
nano docker-compose.yml
```

```yaml
version: '3.8'

services:
  dashboard:
    image: ghcr.io/eireye/home_dashboard_raspie:latest
    container_name: home-dashboard
    restart: unless-stopped
    ports:
      - "8501:8501"
    volumes:
      - ./credentials.json:/app/credentials.json:ro
      - ./.env:/app/.env:ro
    environment:
      - TZ=Europe/Oslo
    labels:
      - "com.centurylinklabs.watchtower.enable=true"

  watchtower:
    image: containrrr/watchtower
    container_name: watchtower
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_POLL_INTERVAL=300
      - WATCHTOWER_LABEL_ENABLE=true
```

### 4. Start dashboardet

```bash
docker compose up -d
```

Nå vil Watchtower sjekke hvert 5. minutt om det finnes nye images, og automatisk oppdatere.

### 5. Se logger

```bash
docker logs -f home-dashboard
```

## Kjøring på Raspberry Pi (manuell)

### Autostart med systemd

Opprett en service-fil:

```bash
sudo nano /etc/systemd/system/dashboard.service
```

```ini
[Unit]
Description=Home Dashboard
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/home_dashboard_raspie
Environment="PATH=/home/pi/home_dashboard_raspie/venv/bin"
ExecStart=/home/pi/home_dashboard_raspie/venv/bin/streamlit run main.py --server.port 8501 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
```

Aktiver og start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dashboard
sudo systemctl start dashboard
```

### Kiosk-modus for 7" touchscreen

Opprett autostart-fil for Chromium i kiosk-modus:

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/dashboard.desktop
```

```ini
[Desktop Entry]
Type=Application
Name=Dashboard
Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble --incognito http://localhost:8501
X-GNOME-Autostart-enabled=true
```

### Skjerminnstillinger for 7" touchscreen

Rediger `/boot/config.txt` for å optimalisere skjermen:

```bash
sudo nano /boot/config.txt
```

Legg til/endre:

```ini
# Skjermrotasjon (0=normal, 1=90°, 2=180°, 3=270°)
display_rotate=0

# Deaktiver skjermsparer
disable_overscan=1

# GPU-minne for jevnere grafikk
gpu_mem=128
```

### Deaktiver skjermsparer

```bash
sudo apt install xscreensaver
```

Kjør `xscreensaver` og velg "Disable Screen Saver", eller:

```bash
# Legg til i ~/.bashrc eller kjør manuelt
xset s off
xset -dpms
xset s noblank
```

### Skjul musepeker (valgfritt)

```bash
sudo apt install unclutter
```

Legg til i autostart:
```bash
echo "unclutter -idle 0.5 -root &" >> ~/.xsessionrc
```

## Prosjektstruktur

```
home_dashboard_raspie/
├── main.py                 # Hovedfil med navigasjon
├── requirements.txt        # Python-avhengigheter
├── .env                    # Miljøvariabler (ikke i git)
├── .env.example            # Mal for miljøvariabler
├── credentials.json        # Google API-nøkkel (ikke i git)
├── pages/
│   ├── home.py             # Hjemmeside med oversikt
│   ├── weather.py          # Værside
│   ├── calendar.py         # Kalenderside
│   ├── meals.py            # Ukesmeny
│   ├── news.py             # Nyheter
│   └── transport.py        # Sanntids avganger
├── utils/
│   └── weather_api.py      # Vær-API wrapper
└── lists/
    ├── weather_emoji.py    # Værikon-mapping
    └── english_norwegian.py # Oversettelser
```

## API-er brukt

| Tjeneste | API | Nøkkel |
|----------|-----|--------|
| Vær | yr.no / met.no | Nei |
| Kalender | iCloud CalDAV | App-passord |
| Ukesmeny | Google Sheets | Service account |
| Nyheter | NRK RSS, BBC RSS | Nei |
| Transport | Entur (Ruter m.fl.) | Nei |

## Tilpasninger for 7" touchscreen

Dashboardet er optimalisert for den lille skjermen:

- **Kompakt layout**: 3+2 rutenett på hjemmesiden
- **Store knapper**: Touch-vennlige navigasjonsknapper
- **Liten skrift**: Reduserte fontstørrelser for bedre plass
- **Skjult UI**: Streamlit-meny og footer er skjult
- **Kort graf**: Værgraf viser 12 timer (ikke 24)
- **Færre elementer**: Maks 4 kalenderhendelser, 3 nyheter på hjem

CSS-tilpasningene ligger i `main.py` og kan justeres etter behov.

## Feilsøking

**Kalender vises ikke:**
- Sjekk at iCloud-passordet er app-spesifikt (ikke vanlig passord)
- Sjekk at 2FA er aktivert på Apple-kontoen

**Ukesmeny vises ikke:**
- Sjekk at `credentials.json` finnes
- Sjekk at Google Sheet er delt med service account-emailen
- Sjekk at `GOOGLE_SHEET_ID` er korrekt i `.env`

**Vær vises ikke:**
- met.no krever internettilkobling
- API-et har rate-limiting, men 10 min cache bør være nok

**Touchscreen reagerer ikke:**
- Sjekk at DSI-kabelen sitter ordentlig
- Kjør `sudo apt update && sudo apt upgrade`
- Prøv `sudo reboot`

**Skjermen er rotert feil:**
- Endre `display_rotate` i `/boot/config.txt`
- 0=normal, 1=90°, 2=180°, 3=270°

**Dashboardet er tregt:**
- Raspberry Pi 4 med 2GB+ RAM anbefales
- Sjekk at `gpu_mem=128` er satt i `/boot/config.txt`
- Lukk andre programmer

**Transport viser ikke avganger:**
- Sjekk at stop-ID er riktig format: `NSR:StopPlace:XXXXX`
- Finn riktig ID på [stoppested.entur.org](https://stoppested.entur.org/)
- Sjekk internettforbindelse

## Lisens

MIT
