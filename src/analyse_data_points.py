import pandas as pd
import numpy as np
import folium
from geopy.distance import geodesic
from datetime import datetime, timezone, timedelta
import os
import geojson
from geojson import Feature, FeatureCollection, LineString

# ----------------------------
# Parameters
# ----------------------------
TIME_GAP_THRESHOLD_SEC = 300  # 5 minutes
europe_paris_tz = 'Europe/Paris'
mode_colors = {
    "walk": "blue",
    "run": "purple",
    "bike": "green",
    "car": "orange",
    "train": "red",
    "plane": "black",
    "unknown": "gray"
}

import yaml
from keplergl import KeplerGl

def build_kepler_map(trip_df, trip_features_df, config_path="kepler_config.yaml", output_html="kepler_map.html"):
    # Merge point and trip features
    enriched_df = trip_df.merge(
        trip_features_df,
        on=["trip_id", "person"],
        suffixes=('', '_meta')
    )

    enriched_df.rename(columns={
        'latitude': 'lat',
        'longitude': 'lon'
    }, inplace=True)

    enriched_df['timestamp'] = pd.to_datetime(enriched_df['last_updated_ts'], unit='s')

    # Convert types
    for col in ['duration_hr', 'distance_km', 'average_speed_kmh', 'max_speed_kmh', 'num_points']:
        if col in enriched_df.columns:
            enriched_df[col] = enriched_df[col].astype(float)

    # Load YAML config
    with open(config_path, "r") as f:
        kepler_config = yaml.safe_load(f)

    # Build map
    map_ = KeplerGl(height=1200, config=kepler_config)
    map_.add_data(data=enriched_df, name="Trips")
    map_.save_to_html(file_name=output_html)
    print(f"Kepler map saved to {output_html}")

# ----------------------------
# Trip segmentation (vectorized)
# ----------------------------
def segment_trips(df):
    df = df.sort_values('last_updated_ts').reset_index(drop=True)
    df['last_updated'] = pd.to_datetime(df['last_updated_ts'], unit='s', utc=True)

    # Shifted values for previous point
    df['lat_prev'] = df['latitude'].shift()
    df['lon_prev'] = df['longitude'].shift()
    df['time_prev'] = df['last_updated'].shift()

    # Time delta
    df['time_from_prev_sec'] = (df['last_updated'] - df['time_prev']).dt.total_seconds()

    # Distance delta (geodesic)
    coords_current = list(zip(df['latitude'], df['longitude']))
    coords_prev = list(zip(df['lat_prev'], df['lon_prev']))
    df['distance_from_prev_km'] = [
        geodesic(p1, p2).km if pd.notna(p1[0]) and pd.notna(p2[0]) else 0.0
        for p1, p2 in zip(coords_prev, coords_current)
    ]

    # Speed calculation
    df['speed_from_prev_kmh'] = df['distance_from_prev_km'] / (df['time_from_prev_sec'] / 3600)
    df['speed_from_prev_kmh'] = df['speed_from_prev_kmh'].replace([np.inf, -np.inf], 0).fillna(0)

    # Trip segmentation based on time gap
    df['trip_id'] = ((df['time_from_prev_sec'] > TIME_GAP_THRESHOLD_SEC) & (df['speed_from_prev_kmh'] < 1)).cumsum()


    # Drop intermediate columns
    df.drop(columns=['lat_prev', 'lon_prev', 'time_prev'], inplace=True)
    df.to_csv("trip_segments.csv", index=False)

    return df

# ----------------------------
# Feature computation
# ----------------------------
def compute_trip_features(df):
    trips = []
    for trip_id, trip_df in df.groupby('trip_id'):
        trip_df = trip_df.sort_values('last_updated_ts')
        start_time = trip_df['last_updated_ts'].iloc[0]
        end_time = trip_df['last_updated_ts'].iloc[-1]
        duration = (end_time - start_time).total_seconds() / 3600  # hours

        total_distance = trip_df['distance_from_prev_km'].sum()
        max_speed = trip_df['speed_from_prev_kmh'].max()
        avg_speed = total_distance / duration if duration > 0 else 0

        trips.append({
            'trip_id': trip_id,
            'start_time': start_time,
            'end_time': end_time,
            'duration_hr': duration,
            'distance_km': total_distance,
            'average_speed_kmh': avg_speed,
            'max_speed_kmh': max_speed,
            'num_points': len(trip_df)
        })

    return pd.DataFrame(trips)

# ----------------------------
# Transport mode classification
# ----------------------------
def classify_transport_mode(row):
    avg_speed = row['average_speed_kmh']
    max_speed = row['max_speed_kmh']
    duration = row['duration_hr']
    distance = row['distance_km']

    if max_speed > 300 and avg_speed > 200:
        return "plane"
    elif avg_speed > 70 and max_speed > 100 and distance < 1000:
        return "train"
    elif avg_speed > 20 and max_speed > 50:
        return "car"
    elif avg_speed > 12 and max_speed > 15 and distance < 150:
        return "bike"
    elif avg_speed > 3 and max_speed > 9 and distance > 5:
        return "run"
    elif avg_speed >= 0 and max_speed <= 5:
        return "walk"
    elif avg_speed >= 0 and max_speed > 5:
        return "bike"
    else:
        return "unknown"

# ----------------------------
# Plotting
# ----------------------------
def plot_trips_with_modes(df, trip_features_df, person, output_file="trip_map.html"):
    center = [df['latitude'].mean(), df['longitude'].mean()]
    m = folium.Map(location=center, zoom_start=12)

    for trip_id, trip_df in df.groupby('trip_id'):
        coords = list(zip(trip_df['latitude'], trip_df['longitude']))
        mode = trip_features_df.loc[trip_features_df['trip_id'] == trip_id, 'transport_mode'].values[0]
        color = mode_colors.get(mode, 'gray')

        trip_info = trip_features_df.loc[trip_features_df['trip_id'] == trip_id].iloc[0]
        tooltip = (
            f"{person} - Trip {trip_id} - Mode: {mode}<br>"
            f"Duration: {trip_info['duration_hr']:.2f} hr<br>"
            f"Distance: {trip_info['distance_km']:.2f} km<br>"
            f"Avg Speed: {trip_info['average_speed_kmh']:.2f} km/h<br>"
            f"Max Speed: {trip_info['max_speed_kmh']:.2f} km/h<br>"
            f"Points: {trip_info['num_points']}"
        )
        folium.PolyLine(coords, color=color, weight=5, tooltip=tooltip).add_to(m)
            # Add summary box
    summary = trip_features_df.groupby('transport_mode').agg(
        total_km=('distance_km', 'sum'),
        total_hr=('duration_hr', 'sum')
    ).reset_index()

    summary_html = "<b>Trip Summary</b><br>"
    for _, row in summary.iterrows():
        summary_html += f"{row['transport_mode'].capitalize()}: {row['total_km']:.1f} km, {row['total_hr']:.1f} hr<br>"

    summary_div = folium.Element(f"""
        <div style="
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 9999;
            background-color: white;
            padding: 10px;
            border: 2px solid gray;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
            font-size: 14px;
        ">
            {summary_html}
        </div>
    """)
    m.get_root().html.add_child(summary_div)

        #folium.Marker(coords[0], icon=folium.Icon(color="green"), popup=f"Start {trip_id}").add_to(m)
        #folium.Marker(coords[-1], icon=folium.Icon(color="red"), popup=f"End {trip_id}").add_to(m)

    m.save(output_file)
    print(f"Saved map to {output_file}")

# ----------------------------
# GeoJSON Export (All Persons)
# ----------------------------
def export_trips_to_geojson(df, trip_features_df, output_file="trips.geojson"):
    features = []

    for (person, trip_id), trip_df in df.groupby(['person', 'trip_id']):
        trip_df = trip_df.sort_values('last_updated_ts')
        coords = list(zip(trip_df['longitude'], trip_df['latitude']))

        trip_info = trip_features_df[
            (trip_features_df['trip_id'] == trip_id) & (trip_features_df['person'] == person)
        ].iloc[0]

        properties = {
            "person": str(person),
            "trip_id": int(trip_id),
            "transport_mode": str(trip_info['transport_mode']),
            "start_time": trip_info['start_time'].isoformat(),
            "end_time": trip_info['end_time'].isoformat(),
            "duration_hr": float(trip_info['duration_hr']),
            "distance_km": float(trip_info['distance_km']),
            "average_speed_kmh": float(trip_info['average_speed_kmh']),
            "max_speed_kmh": float(trip_info['max_speed_kmh']),
            "num_points": int(trip_info['num_points'])
        }

        features.append(Feature(geometry=LineString(coords), properties=properties))

    geojson_obj = FeatureCollection(features)

    with open(output_file, 'w') as f:
        geojson.dump(geojson_obj, f)

    print(f"Saved GeoJSON to {output_file}")


# ----------------------------
# Main processor
# ----------------------------
def process_trips(df):
    if df.empty or 'latitude' not in df.columns or 'longitude' not in df.columns or 'last_updated_ts' not in df.columns or 'friendly_name' not in df.columns:
        print(f"Skipping df: Missing required columns or empty.")
        return

    all_segments = []
    all_features = []

    for person, person_df in df.groupby('friendly_name'):
        person_df = segment_trips(person_df)
        features_df = compute_trip_features(person_df)
        features_df['transport_mode'] = features_df.apply(classify_transport_mode, axis=1)

        person_df['person'] = person
        features_df['person'] = person

        all_segments.append(person_df)
        all_features.append(features_df)

    combined_df = pd.concat(all_segments, ignore_index=True)
    combined_features_df = pd.concat(all_features, ignore_index=True)
    return combined_df, combined_features_df

# ----------------------------
# Runner
# ----------------------------

if __name__ == "__main__":

    parquet_dir = "./data_points"
    all_data = []
    # Step 1: Read and combine all Parquet files
    for file_name in os.listdir(parquet_dir):
        if file_name.endswith(".parquet"):
            file_path = os.path.join(parquet_dir, file_name)
            print(f"Reading {file_path}")
            df = pd.read_parquet(file_path)
            if not df.empty:
                all_data.append(df)

    if not all_data:
        print("No valid data found.")
        exit()

    combined_raw_df = pd.concat(all_data, ignore_index=True)
    combined_df, combined_features_df = process_trips(combined_raw_df)
    output_geojson = f"geojson_all.geojson"
    build_kepler_map(combined_df, combined_features_df, config_path="kepler_config.yaml", output_html="kepler_map.html")
    #export_trips_to_geojson(combined_df, combined_features_df, output_file=output_geojson)



