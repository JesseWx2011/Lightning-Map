import os
os.environ["CARTOPY_DATA_DIR"] = "./rootrepo/cartopy_data/"
import requests
import cartopy.crs as ccrs
import cartopy
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import re
from datetime import datetime, timedelta
import pytz

API_URL = "https://saratoga-weather.org/USA-blitzortung/placefile.txt"
OUTPUT_DIR = "docs/lightning_maps"

SECTORS = {
    "Southeast": [-90, -75, 24, 36],
    "Northeast": [-80, -66, 39, 47],
    "Mid-Atlantic": [-83, -74, 36, 41],
    "Lower Mississippi Valley": [-94, -88, 29, 36],
    "Central Miss. Valley": [-94, -88, 36, 43],
    "Upper Miss. Valley": [-97, -88, 43, 50],
    "South Plains": [-104, -94, 29, 37],
    "Central Plains": [-104, -94, 37, 43],
    "North Plains": [-104, -94, 43, 49],
    "Four Corners": [-112, -102, 31, 39],
    "Rockies": [-115, -102, 39, 49],
    "Northwest": [-125, -111, 42, 49],
    "Southwest": [-125, -111, 31, 42],
    "Alaska": [-170, -130, 51, 72],
    "Hawaii": [-161, -154, 18, 23],
    "Guam": [144.6, 144.9, 13.2, 13.7],
    "Puerto Rico": [-67.3, -65.2, 17.9, 18.5],
    "US Mariana Islands": [144.6, 146.1, 13.2, 15.3]
}

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
                    strike_dt = now_pdt.replace(
                        hour=strike_time.hour, minute=strike_time.minute, second=strike_time.second, microsecond=0
                    )
                except Exception:
                    print(f"Failed to parse time for line: {line}")
                    strike_dt = None
                if strike_dt and strike_dt >= one_hour_ago and strike_dt <= now_pdt:
                    icons.append((lat, lon, strike_dt))
                    count += 1
    print(f"Found {count} icons in the last hour.")
    return icons

def plot_sector_map(points, sector_name, extent):
    print(f"Plotting lightning map for {sector_name}...")
    fig = plt.figure(figsize=(8, 6))
    ax = plt.axes(projection=ccrs.Mercator())
    ax.set_extent(extent, crs=ccrs.Geodetic())

    # Use lower-res features for faster rendering and smaller downloads
    ax.add_feature(cfeature.OCEAN.with_scale('110m'), facecolor='lightblue')
    ax.add_feature(cfeature.LAND.with_scale('110m'), facecolor='whitesmoke')
    ax.coastlines(resolution='110m')
    ax.add_feature(cfeature.BORDERS.with_scale('110m'))
    try:
        ax.add_feature(cfeature.STATES.with_scale('50m'))
    except Exception:
        pass

    filtered_points = [(lat, lon, t) for lat, lon, t in points
                      if extent[2] <= lat <= extent[3] and extent[0] <= lon <= extent[1]]
    print(f"Valid lightning strikes in {sector_name}: {len(filtered_points)}")
    if filtered_points:
        lats, lons, times = zip(*filtered_points)
        latest = max(times)
        ages = [(latest - t).total_seconds() for t in times]
        min_alpha, max_alpha = 0.2, 1.0
        max_age = 3600
        alphas = [max_alpha - (a / max_age) * (max_alpha - min_alpha) for a in ages]
        for lat, lon, alpha in zip(lats, lons, alphas):
            ax.scatter(lon, lat, color='yellow', s=20, marker='o', alpha=alpha, transform=ccrs.Geodetic())
    plt.title(f"Lightning - {sector_name} (Last Hour)")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fname = os.path.join(OUTPUT_DIR, f"lightning_{sector_name.replace(' ', '_')}.png")
    print(f"Saving map to {fname} ...")
    plt.savefig(fname, bbox_inches='tight')
    plt.close(fig)
    print(f"Map for {sector_name} saved successfully.")

def main():
    print("Starting sector lightning map generation...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("./rootrepo/cartopy_data/", exist_ok=True)
    text = fetch_placefile(API_URL)
    points = parse_icons(text)
    for sector_name, extent in SECTORS.items():
        plot_sector_map(points, sector_name, extent)
    print("All sector maps completed.")

if __name__ == "__main__":
    main()
