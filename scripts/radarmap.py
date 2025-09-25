import os
import requests
from metpy.io import Level3File
from metpy.calc import azimuth_range_to_lat_lon
from metpy.plots import add_metpy_logo, add_timestamp, USCOUNTIES
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from datetime import datetime
import re
from io import BytesIO

# Output directory
OUTPUT_DIR = "docs/radar_maps"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# NEXRAD S3 bucket
S3_URL = "https://unidata-nexrad-level3.s3.amazonaws.com/?prefix=MOB_N0B_2025_09_25/"

def get_latest_n0b_file():
    """Fetch the latest N0B file URL from S3 listing."""
    resp = requests.get(S3_URL)
    resp.raise_for_status()
    # Match N0B file names like MOB_N0B_20250925_1234
    matches = re.findall(r'(MOB_N0B_\d+_\d+)', resp.text)
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
    """Open Level3 file and plot radar reflectivity."""
    f = Level3File(file_obj)

    # For demonstration, use the first sym_block (typical for reflectivity)
    block = f.sym_block[0][0]
    data = f.map_data(block['data'])
    az = block['azimuths']  # degrees
    rng = block['ranges']   # meters

    # Convert to lat/lon
    cent_lon = f.lon
    cent_lat = f.lat
    lons, lats = azimuth_range_to_lat_lon(az, rng, cent_lon, cent_lat)

    # Plot with Cartopy
    fig, ax = plt.subplots(subplot_kw={'projection': ccrs.LambertConformal()},
                           figsize=(12, 10))
    ax.set_extent([cent_lon-2, cent_lon+2, cent_lat-2, cent_lat+2], crs=ccrs.PlateCarree())
    
    ax.pcolormesh(lons, lats, data, transform=ccrs.PlateCarree(), cmap='pyart_NWSRef')
    
    # Optional: add counties and timestamp
    ax.add_feature(USCOUNTIES)
    add_metpy_logo(ax)
    add_timestamp(ax, f.vtime, y=0.02, high_contrast=True)
    
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
