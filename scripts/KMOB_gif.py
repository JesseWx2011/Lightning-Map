import os
import requests
import re
from io import BytesIO
from datetime import datetime, timezone, timedelta
from pathlib import Path

# --- Plotting and Meteorology Libraries ---
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import cartopy.feature as cfeature
from metpy.io import Level3File
from metpy.calc import azimuth_range_to_lat_lon
from metpy.plots import add_metpy_logo, add_timestamp, colortables, USCOUNTIES
from metpy.units import units

# --- Image Library for GIF Creation (Requires: pip install Pillow) ---
from PIL import Image

# Output directory and file naming constants
OUTPUT_DIR = Path("docs/radar_maps")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR = OUTPUT_DIR / "temp_pngs"

# NEXRAD S3 base URL
S3_BASE_URL = "https://unidata-nexrad-level3.s3.amazonaws.com/"
RADAR_ID = "MOB"
PRODUCT_CODE = "N0B" # Base Reflectivity
MAX_FRAMES = 5 # The required number of latest files

# ====================================================================
# S3 Fetching Logic
# ====================================================================

def find_n0b_keys_for_date(target_date: datetime):
    """Fetch all N0B file Keys for a specific UTC date from S3 listing."""
    date_str = target_date.strftime("%Y_%m_%d")
    s3_prefix = f"{RADAR_ID}_{PRODUCT_CODE}_{date_str}"
    s3_url = f"{S3_BASE_URL}?prefix={s3_prefix}"
    
    print(f"Searching S3 for files with prefix: {s3_prefix}")
    
    try:
        resp = requests.get(s3_url)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Could not fetch S3 listing for {date_str}. Status: {e.response.status_code}")
        return []

    # Match N0B file names like MOB_N0B_2025_09_25_22_13_17
    key_pattern = re.escape(s3_prefix) + r'_\d{2}_\d{2}_\d{2}'
    matches = re.findall(key_pattern, resp.text)
    
    # Return unique and sorted list of Keys
    file_keys = sorted(list(set(matches)))
    return file_keys

def get_latest_n0b_files_across_days():
    """Fetch up to MAX_FRAMES N0B file Keys, checking the previous day if needed."""
    
    # 1. Start with the current UTC day
    current_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    current_day_keys = find_n0b_keys_for_date(current_utc)
    
    # 2. Check if we have enough files
    if len(current_day_keys) >= MAX_FRAMES:
        print(f"Found {len(current_day_keys)} files on the current day. Using the latest {MAX_FRAMES}.")
        return current_day_keys[-MAX_FRAMES:]
    
    print(f"Only found {len(current_day_keys)} files on the current day. Checking previous day...")
    
    # 3. Check the previous UTC day
    previous_utc = current_utc - timedelta(days=1)
    previous_day_keys = find_n0b_keys_for_date(previous_utc)
    
    # 4. Combine and select the latest
    all_keys = previous_day_keys + current_day_keys
    
    if not all_keys:
        raise ValueError("No N0B files found across the last two days.")
    
    # Ensure the combined list is sorted (should be, but a double check)
    all_keys = sorted(all_keys)

    # Return the latest MAX_FRAMES from the combined list
    return all_keys[-MAX_FRAMES:]

# ====================================================================
# Download, Plotting, and GIF Creation
# ====================================================================

def download_n0b(key):
    """Download a single N0B file Key from S3 to memory."""
    file_url = f"{S3_BASE_URL}{key}"
    resp = requests.get(file_url)
    resp.raise_for_status()
    return BytesIO(resp.content)

def plot_radar_level3(file_obj, key):
    """Open Level3 file and plot radar reflectivity, saving as a PNG."""
    f = Level3File(file_obj)

    # Use Path for platform-independent path construction
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get the first sym_block with radial data
    datadict = f.sym_block[0][0]
    data = f.map_data(datadict['data'])

    # Compute azimuths and ranges
    az = units.Quantity(np.array(datadict['start_az'] + [datadict['end_az'][-1]]), 'degrees')
    rng = units.Quantity(np.linspace(0, f.max_range, data.shape[-1] + 1), 'kilometers')

    cent_lon = f.lon
    cent_lat = f.lat
    
    # Define plot extent based on radar center (+/- 2 degrees)
    lon_min = cent_lon - 2.0
    lon_max = cent_lon + 2.0
    lat_min = cent_lat - 2.0
    lat_max = cent_lat + 2.0

    # Convert to lat/lon
    lons, lats = azimuth_range_to_lat_lon(az, rng, cent_lon, cent_lat)

    # Plot setup
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.LambertConformal()})
    
    # Set extent explicitly on the radar center (KMOB)
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

    # Colormap
    norm, cmap = colortables.get_with_steps('NWSStormClearReflectivity', -20, 0.5)
    ax.pcolormesh(lons, lats, data, norm=norm, cmap=cmap, transform=ccrs.PlateCarree())

    # Map Features
    ax.add_feature(USCOUNTIES, linewidth=0.5)
    ax.add_feature(cfeature.OCEAN.with_scale('10m'), facecolor='lightblue')
    ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor="tan") 
    ax.add_feature(cfeature.STATES.with_scale('10m'), linestyle=':', edgecolor='gray', linewidth=1)

    # City markers (Complete list, but plotting is filtered)
    cities = {
        # Alabama Cities
        "Mobile": (-88.0399, 30.6954),
        "Atmore": (-87.4961, 31.0235),
        "Brewton": (-87.0725, 31.1052),
        "Bay Minette": (-87.7714, 30.8838),
        "Gulf Shores": (-87.6997, 30.2577), 
        
        # Florida Cities
        "Pensacola": (-87.2169, 30.4213),
        "Milton": (-87.0400, 30.6324),
        "Destin": (-86.4950, 30.3932), # Likely out of bounds
        "Crestview": (-86.5861, 30.7577), # Likely out of bounds
        "Niceville": (-86.4716, 30.5402), # Likely out of bounds
        
        # Mississippi Cities
        "Waynesboro": (-88.4714, 31.6705), # Likely out of bounds
        "Lucedale": (-88.5864, 31.1982),
        "Pascagoula": (-88.5567, 30.3655), 
        "Hattiesburg": (-89.2905, 31.3271), # Likely out of bounds
    }

    # Plot city markers and labels with bounds check
    for city, (lon, lat) in cities.items():
        # --- MODIFICATION: Check if city is within the current plot extent ---
        if lon_min < lon < lon_max and lat_min < lat < lat_max:
            ax.plot(lon, lat, 'ro', markersize=5, transform=ccrs.PlateCarree(), zorder=10) # Red dot
            
            # Adjust text offset for a clearer view
            x_offset = 0.08
            y_offset = 0.08
            ha = 'left' # Default horizontal alignment
    
            # Manual adjustments for specific cities to prevent overlap
            if city == "Pensacola":
                y_offset = -0.05
                x_offset = 0.02
            elif city == "Gulf Shores":
                y_offset = -0.05
                x_offset = 0.02
            elif city == "Pascagoula":
                y_offset = 0.02
                x_offset = -0.05
                ha = 'right'
            elif city == "Mobile":
                x_offset = 0.02
                y_offset = 0.02
            elif city == "Atmore":
                y_offset = 0.02
                x_offset = -0.05
                ha = 'right'
    
            ax.text(lon + x_offset, lat + y_offset, city, fontsize=9, transform=ccrs.PlateCarree(),
                    ha=ha, va='bottom', color='black', weight='bold', zorder=10,
                    path_effects=[plt.matplotlib.patheffects.withStroke(linewidth=2, foreground="white")])

    # Logo and Timestamp (MetPy's timestamp is at y=0.02)
    add_metpy_logo(fig)
    prod_time = f.metadata['prod_time']
    vtime_utc = prod_time.astimezone(timezone.utc)
    add_timestamp(ax, vtime_utc, y=0.02, high_contrast=True)

    # Watermark just above the timestamp (using normalized axis coordinates)
    ax.text(0.1, 0.08, 'Maps by JesseLikesWeather', 
             fontsize=10, color='gray', ha='left', va='bottom', transform=ax.transAxes, zorder=10)
    ax.text(0.1, 0.05, 'Reusable with attribution.', 
             fontsize=9, color='gray', ha='left', va='bottom', transform=ax.transAxes, zorder=10)

    # Save output with timestamp as PNG. 
    out_path = PNG_DIR / f"{key}.png"
    plt.savefig(out_path, bbox_inches='tight', dpi=100) 
    plt.close(fig)
    
    return out_path

def create_radar_gif(png_files):
    """Combines a list of PNG files into a single animated GIF."""
    if not png_files:
        print("No PNG files to create a GIF.")
        return

    print(f"Creating GIF from {len(png_files)} frames...")
    
    # Sort files by name to ensure correct time order
    png_files.sort()
    
    # Open all images
    images = [Image.open(f) for f in png_files]
    
    # Determine the GIF file name (use the earliest date found in the filenames)
    earliest_key = png_files[0].stem
    date_match = re.search(r'(\d{4}_\d{2}_\d{2})', earliest_key)
    date_str = date_match.group(1).replace('_', '') if date_match else datetime.utcnow().strftime("%Y%m%d")
    
    gif_path = OUTPUT_DIR / f"{RADAR_ID}.gif"
    
    # Save as GIF
    # duration is in milliseconds. 500ms = 0.5s per frame
    images[0].save(gif_path, 
                   save_all=True, 
                   append_images=images[1:], 
                   duration=500, 
                   loop=0) # loop=0 means loop indefinitely
    
    print(f"✅ GIF saved to {gif_path}")
    
    # Clean up temporary PNGs
    for f in png_files:
        os.remove(f)
    os.rmdir(PNG_DIR)
    print(f"Cleaned up temporary directory: {PNG_DIR}")


def main():
    print(f"--- NEXRAD {RADAR_ID}/{PRODUCT_CODE} Latest {MAX_FRAMES} GIF Creator (Cross-Day Check) ---")
    
    try:
        # 1. Fetch the latest MAX_FRAMES file keys, checking the previous day if needed
        file_keys = get_latest_n0b_files_across_days()
        print(f"Successfully retrieved the latest {len(file_keys)} file keys.")
        
        # Ensure they are sorted (guaranteed by the fetch function, but good to ensure)
        file_keys.sort()
            
        png_paths = []
        
        # 2. Download and plot each file
        for i, key in enumerate(file_keys):
            print(f"[{i+1}/{len(file_keys)}] Downloading and plotting: {key}")
            file_obj = download_n0b(key)
            out_path = plot_radar_level3(file_obj, key)
            png_paths.append(out_path)
        
        # 3. Compile plots into a GIF
        create_radar_gif(png_paths)
    
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Done!")


if __name__ == "__main__":
    main()
