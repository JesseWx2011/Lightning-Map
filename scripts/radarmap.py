import os
import requests
import re
from io import BytesIO
from datetime import datetime, timezone

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

from metpy.io import Level3File
from metpy.calc import azimuth_range_to_lat_lon
from metpy.plots import add_metpy_logo, add_timestamp, colortables, USCOUNTIES
from metpy.units import units

# Output directory
OUTPUT_DIR = "docs/radar_maps"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# NEXRAD S3 base URL
S3_BASE_URL = "https://unidata-nexrad-level3.s3.amazonaws.com/"

def get_latest_n0b_file():
    """Fetch the latest N0B file URL from S3 listing dynamically."""
    # Get today in UTC
    today_str = datetime.utcnow().strftime("%Y_%m_%d")
    s3_url = f"{S3_BASE_URL}?prefix=MOB_N0B_{today_str}"
    
    resp = requests.get(s3_url)
    resp.raise_for_status()
    
    # Match N0B file names like MOB_N0B_2025_09_25_22_13_17
    matches = re.findall(r'(MOB_N0B_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})', resp.text)
    if not matches:
        raise ValueError("No N0B files found for today.")
    
    latest_file = sorted(matches)[-1]
    file_url = f"{S3_BASE_URL}{latest_file}"
    return file_url

def download_n0b(url):
    """Download N0B file to memory."""
    resp = requests.get(url)
    resp.raise_for_status()
    return BytesIO(resp.content)

def plot_radar_level3(file_obj):
    """Open Level3 file and plot radar reflectivity (N0B)."""
    f = Level3File(file_obj)

    # Get the first sym_block with radial data
    datadict = f.sym_block[0][0]
    data = f.map_data(datadict['data'])

    # Compute azimuths and ranges
    az = units.Quantity(np.array(datadict['start_az'] + [datadict['end_az'][-1]]), 'degrees')
    rng = units.Quantity(np.linspace(0, f.max_range, data.shape[-1] + 1), 'kilometers')

    cent_lon = f.lon
    cent_lat = f.lat

    # Convert to lat/lon
    lons, lats = azimuth_range_to_lat_lon(az, rng, cent_lon, cent_lat)

    # Plot
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.LambertConformal()})
    ax.set_extent([cent_lon-2, cent_lon+2, cent_lat-2, cent_lat+2], crs=ccrs.PlateCarree())

    # Colormap
    norm, cmap = colortables.get_with_steps('NWSStormClearReflectivity', -20, 0.5)
    ax.pcolormesh(lons, lats, data, norm=norm, cmap=cmap, transform=ccrs.PlateCarree())

    # Add counties, MetPy logo, timestamp
    ax.add_feature(USCOUNTIES, linewidth=0.5)
    add_metpy_logo(fig)

    prod_time = f.metadata['prod_time']
    vtime_utc = prod_time.astimezone(timezone.utc)
    add_timestamp(ax, vtime_utc, y=0.02, high_contrast=True)

    # Save output with timestamp
    timestamp_str = vtime_utc.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"KMOB_radar.png")
    plt.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Radar map saved to {out_path}")


def main():
    print("Fetching latest N0B file...")
    file_url = get_latest_n0b_file()
    print("Downloading file:", file_url)
    file_obj = download_n0b(file_url)
    print("Plotting radar...")
    plot_radar_level3(file_obj)
    print("Done!")


if __name__ == "__main__":
    main()
