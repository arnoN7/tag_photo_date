# tag_photo_date

A set of Python tools to retroactively enrich photo EXIF metadata with **dates** and **GPS coordinates** — useful for photos taken with DSLRs or cameras without GPS, or for photos that are missing metadata entirely.

GPS data can be sourced from a folder of reference photos (e.g. taken on your smartphone) or directly from a **Home Assistant** location history database.

---

## Features

- Extract dates from filenames and write them into EXIF metadata
- Tag photos with GPS coordinates using reference photos or a Home Assistant PostgreSQL database
- Fix or remove malformed EXIF date fields
- Adjust EXIF timestamps by a time offset (e.g. to correct timezone issues)
- Analyse GPS tracks: detect trips, compute distance/speed, classify travel modes
- Export location data points to Parquet for further analysis
- Visualise trips with Folium, KeplerGL, and GeoJSON

---

## Project Structure

```
src/
├── retag_dates.py        # Tag photos with dates extracted from filenames
├── geotag_photos.py      # Tag photos with GPS coordinates (file or DB mode)
├── exif.py               # EXIF GPS helpers (decimal → DMS conversion)
├── tag_activities.py     # GPS track analysis and trip visualisation
├── analyse_data_points.py # Export location data from Home Assistant DB to Parquet
├── delay.py              # Adjust EXIF timestamps by a fixed offset
├── geotag_ui.py          # Minimal file browser UI (PySimpleGUI)
└── utils.py              # Shared utilities
```

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file in the project root:

```env
# Database (Home Assistant PostgreSQL)
DB_HOST=192.168.1.x
DB_PORT=5432
DB_NAME=homeassistant
DB_USER=your_user
DB_PASSWORD=your_password

# Comma-separated device/person names as tracked in Home Assistant
PERSONS=IPHONE_ALICE,IPHONE_BOB

# Set to true to overwrite existing GPS tags
FORCE_UPDATE=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log
```

---

## Usage

### 1. Tag photos with dates from filenames

Extracts the date from the filename and writes it into the EXIF `DateTime`, `DateTimeOriginal`, and `DateTimeDigitized` fields.

```bash
python src/retag_dates.py --path /path/to/photos
```

**Supported filename formats:**

| Example | Format |
|---|---|
| `IMG-20170412-WA0004.jpg` | WhatsApp |
| `Screenshot_2016-04-12-21-17-46.jpg` | Android screenshot |
| `2013-12-03 19.23.48.jpg` | Generic datetime |
| `20150420_202551-1.jpg` | Camera/Android |

**Optional: adjust timestamps by N hours**

```bash
python src/retag_dates.py --path /path/to/photos --offset -2
```

---

### 2. Tag photos with GPS coordinates

#### From a folder of GPS-tagged reference photos (e.g. smartphone photos)

```bash
python src/geotag_photos.py --tag /path/to/photos --gps /path/to/reference_photos
```

Each untagged photo is matched to the nearest reference photo by timestamp. Use `--delay` to set the maximum allowed time gap in days (default: 1 day).

```bash
python src/geotag_photos.py --tag /path/to/photos --gps /path/to/gps_photos --delay 0.5
```

#### From Home Assistant database

Set `DB_HOST` (and other DB variables) in `.env`, then run:

```bash
python src/geotag_photos.py --tag /path/to/photos --tz Europe/Paris
```

The script queries the Home Assistant `states` table for the closest GPS position (within ±1 day) to each photo's timestamp, for the persons listed in `PERSONS`.

---

### 3. Analyse GPS tracks and trips

```bash
python src/tag_activities.py
```

Reads location data, segments it into trips, computes statistics (distance, speed, duration), classifies travel modes (walk, run, bike, car, train, plane), and outputs GeoJSON and interactive map files.

---

### 4. Export location data points

```bash
python src/analyse_data_points.py
```

Queries the Home Assistant PostgreSQL database for location tracking data over a date range and exports it to Parquet files for further analysis.

---

## Docker

A `docker-compose.yml` is included to run the tool in a container.

```bash
docker-compose up
```

The service runs on port `10600` (mapped to internal port `5000`), with timezone set to `Europe/Paris`.

---

## Dependencies

| Package | Purpose |
|---|---|
| `piexif` | Read/write EXIF metadata |
| `pandas` | Data manipulation |
| `psycopg2-binary` | PostgreSQL connector |
| `python-dotenv` | `.env` file support |
| `tqdm` | Progress bars |
| `flask` | Minimal web server endpoint |
| `geojson` | GeoJSON output |
| `keplergl` | Interactive geospatial visualisation |
