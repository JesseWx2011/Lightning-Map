import os
import requests
from metpy.io import Level3File
from metpy.calc import azimuth_range_to_lat_lon
from metpy.plots import add_metpy_logo, add_timestamp, USCOUNTIES
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from io import BytesIO

# Output directory
OUTPUT_DIR = "docs/radar_maps"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Direct NEXRAD file URL
FILE_URL = "https://unidata-nexrad-level3.s3.amazonaws.com/MOB_N0B_2025_09_25_22_13_17"

def download_n0b(url):
    """Download N0B file to memory."""
    resp = requests.get(url)
    resp.raise_for_status()
    return BytesIO(resp.content)

def plot_radar_level3(file_obj):
    """Open Level3 file and plot radar reflectivity."""
    f = Level3File(file_obj)

    # Use the first sym_block (common for reflectivity)
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
    print("Downloading file:", FILE_URL)
    file_obj = download_n0b(FILE_URL)
    print("Plotting radar...")
    plot_radar_level3(file_obj)
    print("Done!")

if __name__ == "__main__":
    main()
