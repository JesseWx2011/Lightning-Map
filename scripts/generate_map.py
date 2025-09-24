import requests
import cartopy.crs as ccrs
import cartopy
import matplotlib.pyplot as plt
import re
import os

API_URL = "https://saratoga-weather.org/USA-blitzortung/placefile.txt"  # Remove corsproxy
OUTPUT_PATH = "docs/lightning_map.png"

def fetch_placefile(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text  
      
def parse_icons(text):
    # Matches lines like: Icon: lat,lon,0,1,9,Blitzortung @ time
    icons = []
    for line in text.splitlines():
        if line.startswith("Icon:"):
            m = re.match(r"Icon:\s*([-\d.]+),([-\d.]+)", line)
            if m:
                lat, lon = float(m.group(1)), float(m.group(2))
                icons.append((lat, lon))
    return icons

def plot_map(points):
    fig = plt.figure(figsize=(10, 7))
    ax = plt.axes(projection=ccrs.LambertConformal())
    ax.set_extent([-125, -65, 20, 50], ccrs.Geodetic()) # USA
    ax.coastlines()
    ax.add_feature(cartopy.feature.BORDERS)
    ax.add_feature(cartopy.feature.STATES)

    if points:
        lats, lons = zip(*points)
        ax.scatter(lons, lats, color='yellow', s=10, marker='o', transform=ccrs.Geodetic())
    plt.title("Blitzortung Lightning - USA")
    plt.savefig(OUTPUT_PATH, bbox_inches='tight')
    plt.close(fig)

def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    text = fetch_placefile(API_URL)
    points = parse_icons(text)
    plot_map(points)

if __name__ == "__main__":
    main()
