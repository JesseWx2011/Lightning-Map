import requests
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import re
import os

API_URL = "https://corsproxy.io/?url=https://saratoga-weather.org/USA-blitzortung/placefile.txt"
OUTPUT_PATH = "docs/lightning_map.png"

def fetch_placefile(url):
    resp = requests.get(url)
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
    ax.set_extent([-125, -65, 24, 50], ccrs.Geodetic()) # USA
    ax.coastlines()
    ax.add_feature(cartopy.feature.BORDERS)
    ax.add_feature(cartopy.feature.STATES)

    if points:
        lats, lons = zip(*points)
        ax.scatter(lons, lats, color='red', s=40, marker='o', transform=ccrs.Geodetic())
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