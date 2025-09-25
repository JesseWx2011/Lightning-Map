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

# NEXRAD S3 bucket (UTC files)
S3_URL = "https://unidata-nexrad-level3.s3.amazonaws.com/?prefix=MOB_N0B_2025_09_25"

def get_latest_n0b_file():
    """Fetch the latest N0B file URL from S3 listing."""
    resp = requests.get(S3_URL)
    resp.raise_for_status()
    # Match N0B file names like MOB_N0B_2025_09_25_22_13_17
    matches = re.findall(r'(MOB_N0B_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})', resp.text)
    if not matches:
        raise ValueError("No N0B files found.")
    latest_file = sorted(matches)[-1]
    file_url = f"https://unidata-nexrad-level3.s3.amazonaws.com/{latest_file}"
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

    # Colormap (default NWS reflectivity)
    norm, cmap = colortables.get_with_steps('NWSStormClearReflectivity', -20, 0.5)
    ax.pcolormesh(lons, lats, data, norm=norm, cmap=cmap, transform=ccrs.PlateCarree())

    # Add counties
    ax.add_feature(USCOUNTIES, linewidth=0.5)

    # Add MetPy logo
    add_metpy_logo(fig)

    # Handle prod_time robustly
    prod_time = f.metadata.get('prod_time')
    if isinstance(prod_time, str):
        prod_time = datetime.fromisoformat(prod_time)
    elif not isinstance(prod_time, datetime):
        # fallback: convert timestamp to datetime
        prod_time = datetime.utcfromtimestamp(prod_time)

    vtime_utc = prod_time.astimezone(timezone.utc)

    # Add timestamp (pass datetime object, not string)
    add_timestamp(ax, vtime_utc, y=0.02, high_contrast=True, time_format='%Y-%m-%d %H:%M:%S UTC')

    # Save output
    out_path = os.path.join(OUTPUT_DIR, "latest_radar.png")
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
