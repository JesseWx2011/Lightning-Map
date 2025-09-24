import requests
import cartopy.crs as ccrs
import cartopy
import matplotlib.pyplot as plt
import re
import os
from datetime import datetime, timedelta
import pytz

API_URL = "https://saratoga-weather.org/USA-blitzortung/placefile.txt"
OUTPUT_PATH = "docs/lightning_map.png"

def fetch_placefile(url):
    print("Fetching placefile from:", url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers)
    print(f"HTTP status code: {resp.status_code}")
    resp.raise_for_status()
    print("Placefile fetched successfully.")
    return resp.text

def parse_icons(text):
    print("Parsing icons from placefile...")
    icons = []
    count = 0
    # Current time in US/Pacific (PDT)
    pacific = pytz.timezone("US/Pacific")
    now_pdt = datetime.now(pacific)
    one_hour_ago = now_pdt - timedelta(hours=1)
    for line in text.splitlines():
        if line.startswith("Icon:"):
            m = re.match(r"Icon:\s*([-\d.]+),([-\d.]+)[^@]*@ ([\d:]+[ap]m) PDT", line)
            if m:
                lat, lon = float(m.group(1)), float(m.group(2))
                time_str = m.group(3)
                try:
                    strike_time = datetime.strptime(time_str, "%I:%M:%S%p")
                    # Use today's date
                    strike_dt = now_pdt.replace(
                        hour=strike_time.hour, minute=strike_time.minute, second=strike_time.second, microsecond=0
                    )
                except Exception:
                    print(f"Failed to parse time for line: {line}")
                    strike_dt = None
                # Only keep if within last hour
                if strike_dt and strike_dt >= one_hour_ago and strike_dt <= now_pdt:
                    icons.append((lat, lon, strike_dt))
                    count += 1
    print(f"Found {count} icons in the last hour.")
    return icons

def plot_map(points):
    print("Plotting lightning map...")
    fig = plt.figure(figsize=(10, 7))
    ax = plt.axes(projection=ccrs.Mercator())
    ax.set_extent([-125, -65, 20, 50], crs=ccrs.Geodetic()) # USA

    print("Adding features to map (ocean, land, borders, states)...")
    ax.add_feature(cartopy.feature.OCEAN, facecolor='lightblue')
    ax.add_feature(cartopy.feature.LAND, facecolor='whitesmoke')
    ax.coastlines()
    ax.add_feature(cartopy.feature.BORDERS)
    ax.add_feature(cartopy.feature.STATES)

    print(f"Valid lightning strikes to plot: {len(points)}")
    if points:
        lats, lons, times = zip(*points)
        latest = max(times)
        ages = [(latest - t).total_seconds() for t in times]
        min_alpha, max_alpha = 0.2, 1.0
        max_age = 3600  # 1 hour in seconds
        alphas = [max_alpha - (a / max_age) * (max_alpha - min_alpha) for a in ages]
        for idx, (lat, lon, alpha) in enumerate(zip(lats, lons, alphas)):
            ax.scatter(lon, lat, color='yellow', s=20, marker='o', alpha=alpha, transform=ccrs.Geodetic())
            if idx < 3:
                print(f"Plotted: lat={lat}, lon={lon}, alpha={alpha}") # Show first few for debugging
    else:
        print("No valid lightning strikes to plot.")
    plt.title("Blitzortung Lightning - USA (Last Hour)")
    print(f"Saving map to {OUTPUT_PATH} ...")
    plt.savefig(OUTPUT_PATH, bbox_inches='tight')
    plt.close(fig) 
    print("Map saved successfully.")

def main():
    print("Lightning in the Last Hour - JesseLikesWeather")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    print(f"Ensured directory exists for output: {os.path.dirname(OUTPUT_PATH)}")
    text = fetch_placefile(API_URL)
    points = parse_icons(text)
    plot_map(points)
    print("Script completed successfully.")

if __name__ == "__main__":
    main()
