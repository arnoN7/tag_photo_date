import logging
import os
import pandas as pd
import psycopg2
from psycopg2 import OperationalError
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from tqdm import tqdm

EUROPE_PARIS = "Europe/Paris"
load_dotenv()
FORMAT = '%Y-%m-%d %H:%M:%S'

def get_data_points_month(cnx, start_date, end_date, tz, persons=["IPHONEARO", "IPHONEAS"]):
    cursor = cnx.cursor()

    query = f"""
    SELECT 
        state_id,
        (sa.shared_attrs::json ->> 'latitude')::FLOAT AS latitude,
        (sa.shared_attrs::json ->> 'longitude')::FLOAT AS longitude,
        (sa.shared_attrs::json ->> 'altitude')::FLOAT AS altitude,
        (sa.shared_attrs::json ->> 'friendly_name')::VARCHAR AS friendly_name,
        to_timestamp(last_updated_ts) as last_updated_ts
    FROM states s
    JOIN state_attributes sa ON s.attributes_id = sa.attributes_id
    WHERE
        last_updated_ts BETWEEN EXTRACT(EPOCH FROM timezone('{tz}', TIMESTAMP '{start_date.strftime(FORMAT)}'))
                           AND EXTRACT(EPOCH FROM timezone('{tz}', TIMESTAMP '{end_date.strftime(FORMAT)}'))
        AND last_updated_ts IS NOT NULL
        AND state in ('home', 'not_home')
        AND (sa.shared_attrs::json ->> 'longitude') IS NOT NULL
        AND (sa.shared_attrs::json ->> 'altitude') IS NOT NULL
        AND (sa.shared_attrs::json ->> 'latitude') IS NOT NULL
        ;"""
    cursor.execute(query)
    rows = cursor.fetchall()
    colnames = [desc[0] for desc in cursor.description]

    df = pd.DataFrame(rows, columns=colnames)

    return df

def main():
    try:
        cnx = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
    except OperationalError as err:
        logging.error(f"Database connection error: {err}")
        return
    else:
        logging.info("Connection OK!")

        # Define the time range
        start_year = 2022
        start_month = 1
        end_year = 2025
        end_month = 4

        start_date = datetime(start_year, start_month, 1)
        end_date = datetime(end_year, end_month, 1)

        current_date = start_date
        months = []
        while current_date < end_date:
            months.append(current_date)
            if current_date.month == 12:
                current_date = datetime(current_date.year + 1, 1, 1)
            else:
                current_date = datetime(current_date.year, current_date.month + 1, 1)

        # Progress bar over months
        for month_start in tqdm(months, desc="Extracting months"):
            next_month = (month_start + timedelta(days=32)).replace(day=1)

            df = get_data_points_month(cnx, month_start, next_month, EUROPE_PARIS)

            if not df.empty:
                filename = f"./data_points/data_{month_start.year}_{month_start.month:02d}.parquet"
                df.to_parquet(filename, index=False)
                logging.info(f"Saved {filename} ({len(df)} rows)")
            else:
                logging.info(f"No data for {month_start.year}-{month_start.month:02d}")

if __name__ == "__main__":
    main()
