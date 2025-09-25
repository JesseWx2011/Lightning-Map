import os
import requests
from metpy.io import Level3File
from metpy.calc import azimuth_range_to_lat_lon
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from datetime import datetime

# 1. Get latest N0B file URL from S3
s3_url = "https://unidata-nexrad-level3.s3.amazonaws.com/?prefix=MOB_N0B_2025_09_25/"
resp = requests.get(s3_url)
# parse resp.text to find the latest file (use regex to match N0B pattern)

latest_file_url = "https://unidata-nexrad-level3.s3.amazonaws.com/...."  # fill after parsing
resp = requests.get(latest_file_url)
with open("latest.MOB_N0B", "wb") as f:
    f.write(resp.content)

# 2. Open file and extract data
f = Level3File("latest.MOB_N0B")
datadict = f.sym_block[0][0]
data = f.map_data(datadict['data'])
az = ...  # compute azimuth array
rng = ...  # compute range array
cent_lon = f.lon
cent_lat = f.lat
xlocs, ylocs = azimuth_range_to_lat_lon(az, rng, cent_lon, cent_lat)

# 3. Plot with cartopy
fig, ax = plt.subplots(subplot_kw={'projection': ccrs.LambertConformal()}, figsize=(12,8))
ax.add_feature(USCOUNTIES)
ax.pcolormesh(xlocs, ylocs, data, transform=ccrs.PlateCarree())
plt.savefig("docs/radar_maps/latest_radar.png")
