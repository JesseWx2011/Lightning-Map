# Copyright 2025 JesseLikesWeather.
# This script can be modified or reused in a different format with necessary attribution:
# ©2025 JesseLikesWeather on YouTube/MiltonWx
import requests
import zipfile
import io
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime, timezone
from matplotlib.patches import Rectangle
import os
import matplotlib.patheffects as path_effects
import pytz
from matplotlib.lines import Line2D

# -------------------------------
# Step 1: Download and unzip shapefile
# -------------------------------
url = "https://www.nhc.noaa.gov/xgtwo/gtwo_shapefiles.zip"
r = requests.get(url)
r.raise_for_status()

extract_dir = "gtwo_shapefiles"
with zipfile.ZipFile(io.BytesIO(r.content)) as z:
    z.extractall(extract_dir)

# Find all area shapefiles
shp_files = [f for f in os.listdir(extract_dir) if f.startswith("gtwo_areas") and f.endswith(".shp")]

if not shp_files:
    raise FileNotFoundError("No 5-day polygon shapefile found in the ZIP.")

# Pick the newest file based on filename timestamp
shp_files.sort()
shp_path = os.path.join(extract_dir, shp_files[-1])

# Load shapefile
tropics_gdf = gpd.read_file(shp_path)
print("Loaded shapefile:", shp_path)
print(tropics_gdf.head())

# -------------------------------
# Step 1b: Filter by basin (Atlantic only)
# -------------------------------
tropics_gdf = tropics_gdf[tropics_gdf["BASIN"] == "Atlantic"]

# -------------------------------
# Step 2: Assign colors based on PROB7DAY
# -------------------------------
def get_color(prob_str):
    try:
        prob = int(prob_str.strip('%'))
    except:
        return "gray"
    if prob < 30:
        return "yellow"
    elif 40 <= prob <= 60:
        return "orange"
    elif prob >= 70:
        return "red"
    else:
        return "gray"

tropics_gdf["color"] = tropics_gdf["PROB7DAY"].apply(get_color)

# -------------------------------
# Step 3: Set up the map
# -------------------------------
fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([-100, 20, 0, 50], crs=ccrs.PlateCarree())  # Entire Atlantic

# Land and ocean with 50m resolution
ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor="tan")
ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor="lightblue")
ax.add_feature(cfeature.COASTLINE.with_scale("50m"))
ax.add_feature(cfeature.BORDERS.with_scale("50m"), linestyle=":")

# -------------------------------
# Step 4: Plot tropical outlook polygons
# -------------------------------
for _, row in tropics_gdf.iterrows():
    row_gdf = gpd.GeoDataFrame([row], crs=tropics_gdf.crs)
    row_gdf.plot(ax=ax, facecolor=row["color"], edgecolor="darkred", alpha=0.5, linewidth=1)

    # Add probability text above the polygon
    centroid = row["geometry"].centroid
    ax.text(centroid.x, centroid.y + 0.5, row["PROB7DAY"],
            fontsize=14, fontweight="bold", color="black",
            ha="center", va="bottom", transform=ccrs.PlateCarree())

# -------------------------------
# Step 5: Add key labels
# -------------------------------
locations = {
    "Miami, FL": (25.7617, -80.1918),
    "New York, NY": (40.7128, -74.0060),
    "Puerto Rico": (18.2208, -66.5901),
    "Cuba": (21.5218, -77.7812),
    "Azores": (38.7169, -27.2327),
    "Cabo Verde": (16.0021, -24.0132),
    "Houston": (29.7601407,-95.3702473),
    "Wilmington": (34.2104291,-77.8867867),
    "Bermuda": (32.3073324,-64.7489045),
    "Halifax": (44.6509122,-63.5924037)
}

for name, (lat, lon) in locations.items():
    ax.plot(lon, lat, marker='o', color='black', markersize=6, transform=ccrs.PlateCarree())
    ax.text(lon + 0.5, lat + 0.5, name, fontsize=12, fontweight='bold',
            color='black', transform=ccrs.PlateCarree())

# -------------------------------
# Step 6: Add banner with drop shadow
# -------------------------------
fig.subplots_adjust(top=0.85)
ax_banner = fig.add_axes([0, 0.88, 1, 0.12])
ax_banner.add_patch(Rectangle((0,0), 1, 1, transform=ax_banner.transAxes, color='darkblue'))
ax_banner.axis('off')

# Extract timestamp from shapefile name
filename = os.path.basename(shp_path)
timestamp_str = filename.split("_")[-1].replace(".shp", "")  # e.g., "202310021723"
try:
    file_dt = datetime.strptime(timestamp_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
except:
    file_dt = datetime.now(timezone.utc)

# Local time in Central Time
local_tz = pytz.timezone("America/Chicago")
local_time = file_dt.astimezone(local_tz)

local_str = local_time.strftime("%I:%M %p %Z")   # e.g., "04:47 PM CDT"
utc_str = file_dt.strftime("%H:%M UTC")          # e.g., "21:47 UTC"

banner_date = file_dt.strftime("%b %d, %Y").upper()
banner_text = f"7-DAY TROPICS OUTLOOK\nVALID {banner_date} {local_str} ({utc_str})"

text = fig.text(0.02, 0.925, banner_text,
                color='white', fontsize=28, fontweight='bold', ha='left', va='center')
text.set_path_effects([path_effects.withStroke(linewidth=4, foreground='black')])

# -------------------------------
# Step 7: Add legend below the figure
# -------------------------------
legend_elements = [
    Line2D([0], [0], marker='s', color='w', label='<30% Low', markerfacecolor='yellow', markersize=20),
    Line2D([0], [0], marker='s', color='w', label='40-60% Medium', markerfacecolor='orange', markersize=20),
    Line2D([0], [0], marker='s', color='w', label='>70% High', markerfacecolor='red', markersize=20)
]

fig.legend(handles=legend_elements, loc='lower center', ncol=3,
           bbox_to_anchor=(0.5, 0.02), frameon=False, fontsize=14)

# -------------------------------
# Step 8: Add watermark on bottom right
# -------------------------------
fig.text(0.98, 0.02, "Maps By JesseLikesWeather", color="gray", fontsize=15,
         ha="right", va="bottom", alpha=1)

# -------------------------------
# Step 9: Save and show
# -------------------------------
plt.savefig("tropics_outlook.png", dpi=100, bbox_inches='tight')
plt.show()
