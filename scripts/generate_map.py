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

CITY_LABELS = [
    ("Seattle, WA", 47.6062, -122.3321),
    ("Washington DC", 38.8951, -77.0364),
    ("Bangor, ME", 44.8012, -68.7778),
    ("New York, NY", 40.7128, -74.0060),
    ("Buffalo, NY", 42.8864, -78.8784),
    ("Pensacola, FL", 30.4213, -87.2169),
    ("Miami, FL", 25.7617, -80.1918),
    ("Orlando, FL", 28.5383, -81.3792),
    ("San Angelo, TX", 31.4638, -100.4370),
    ("Dothan, AL", 31.2232, -85.3905),
    ("Birmingham, AL", 33.5186, -86.8104),
    ("Chattanooga, TN", 35.0456, -85.3097),
    ("Nashville, TN", 36.1627, -86.7816),
    ("Roanoke, VA", 37.2719, -79.9414),
    ("Pittsburgh, PA", 40.4406, -79.9959),
    ("State College, PA", 40.7934, -77.8600),
    ("Kansas City, MO", 39.0997, -94.5786),
    ("Rapid City, SD", 44.0805, -103.2310),
    ("Fargo, ND", 46.8772, -96.7898),
    ("Des Moines, IA", 41.5868, -93.6250),
    ("Dubuque, IA", 42.5006, -90.6646),
    ("Chicago, IL", 41.8781, -87.6298),
    ("Springfield, IL", 39.7817, -89.6501),
    ("Paducah, KY", 37.0827, -88.6000),
    ("Dayton, OH", 39.7589, -84.1916),
    ("Los Angeles, CA", 34.0522, -118.2437),
    ("Sacramento, CA", 38.5816, -121.4944),
    ("Medford, OR", 42.3265, -122.8756),
    ("Yakima, WA", 46.6021, -120.5059),
    ("Salt Lake City, UT", 40.7608, -111.8910),
    ("Billings, MT", 45.7833, -108.5007),
    ("Grand Island, NE", 40.9264, -98.3420),
    ("Omaha, NE", 41.2565, -95.9345),
    ("Dallas, TX", 32.7767, -96.7970),
    ("Oklahoma City, OK", 35.4676, -97.5164),
    ("Guymon, OK", 36.6822, -101.4810),
    ("Little Rock, AR", 34.7465, -92.2896),
    ("Jackson, MS", 32.2988, -90.1848),
    ("Atlanta, GA", 33.7490, -84.3880),
    ("Columbia, SC", 34.0007, -81.0348),
    ("Charlotte, NC", 35.2271, -80.8431),
    ("Greenville, SC", 34.8526, -82.3940),
    ("Raleigh, NC", 35.7796, -78.6382),
    ("Asheville, NC", 35.5951, -82.5515),
    ("Phoenix, AZ", 33.4484, -112.0740),
    ("San Antonio, TX", 29.4241, -98.4936),
    ("Jackson Hole, WY", 43.4799, -110.7624),
    ("Minneapolis, MN", 44.9778, -93.2650),
    ("International Falls, MN", 48.6019, -93.4108),
    ("Lexington, KY", 38.0406, -84.5037),
    ("Boston, MA", 42.3601, -71.0589),
    ("Anchorage, AK", 61.2181, -149.9003),
    ("Hilo, HI", 19.7297, -155.0900),
    ("Honolulu, HI", 21.3069, -157.8583),
    ("Barrow, AK", 71.2906, -156.7886),
    ("Nome, AK", 64.5011, -165.4064),
    ("Adak, AK", 51.8792, -176.6300),
    ("Juneau, AK", 58.3019, -134.4197),
    ("Bethel, AK", 60.7922, -161.7558),
    ("Point Hope, AK", 68.3474, -166.8081),
    ("Tamuning, GU", 13.4877, 144.8017),
    ("San Jose, GU", 13.5151, 144.8260),
    ("Burlington, VT", 44.4759, -73.2121)
]

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

def get_resolution(sector_name):
    high_res_sectors = ["Puerto Rico", "Guam", "US Mariana Islands"]
    return '10m' if sector_name in high_res_sectors else '50m'

def plot_sector_map(points, sector_name, extent, last_updated_utc):
    print(f"Plotting lightning map for {sector_name}...")
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)  # 1920x1080

    # Calculate padded extent to center the region
    lon_min, lon_max, lat_min, lat_max = extent
    region_width = lon_max - lon_min
    region_height = lat_max - lat_min
    img_width, img_height = 1920, 1080
    img_aspect = img_width / img_height
    region_aspect = region_width / region_height

    # Centering logic: pad longitude or latitude so region is centered
    center_lon = (lon_min + lon_max) / 2
    center_lat = (lat_min + lat_max) / 2

    if region_aspect > img_aspect:
        # Region is wider than image aspect; pad latitude
        new_height = region_width / img_aspect
        pad = (new_height - region_height) / 2
        lat_min_pad = center_lat - new_height / 2
        lat_max_pad = center_lat + new_height / 2
        lon_min_pad = lon_min
        lon_max_pad = lon_max
    else:
        # Region is taller than image aspect; pad longitude
        new_width = region_height * img_aspect
        pad = (new_width - region_width) / 2
        lon_min_pad = center_lon - new_width / 2
        lon_max_pad = center_lon + new_width / 2
        lat_min_pad = lat_min
        lat_max_pad = lat_max

    ax = plt.axes(projection=ccrs.Mercator())
    ax.set_extent([lon_min_pad, lon_max_pad, lat_min_pad, lat_max_pad], crs=ccrs.Geodetic())

    res = get_resolution(sector_name)
    ax.add_feature(cfeature.OCEAN.with_scale(res), facecolor='lightblue')
    ax.add_feature(cfeature.LAND.with_scale(res), facecolor='tan')
    ax.coastlines(resolution=res)
    ax.add_feature(cfeature.BORDERS.with_scale(res))
    try:
        ax.add_feature(cfeature.STATES.with_scale(res))
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

    # Plot city labels in each sector
    for city, city_lat, city_lon in CITY_LABELS:
        if extent[2] <= city_lat <= extent[3] and extent[0] <= city_lon <= extent[1]:
            ax.plot(city_lon, city_lat, marker='o', color='blue', markersize=4, transform=ccrs.Geodetic(), zorder=5)
            ax.text(city_lon, city_lat, city, fontsize=9, color='black', weight='bold',
                    transform=ccrs.Geodetic(), ha='left', va='bottom', zorder=6)

    # Add last updated time in UTC at bottom right
    fig.text(0.99, 0.01, f"Last updated: {last_updated_utc}", ha='right', va='bottom', fontsize=12, color='black')

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
    # Get current UTC time for "Last updated"
    now_utc = datetime.utcnow()
    last_updated_utc = now_utc.strftime("%m/%d/%Y %-I:%M:%S %p UTC") if hasattr(now_utc, 'strftime') else now_utc.strftime("%m/%d/%Y %I:%M:%S %p UTC")
    for sector_name, extent in SECTORS.items():
        plot_sector_map(points, sector_name, extent, last_updated_utc)
    print("All sector maps completed.")

if __name__ == "__main__":
    main()
