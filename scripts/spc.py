#  Copyright (c) 2021 MetPy Developers.
#  Distributed under the terms of the BSD 3-Clause License.
#  SPDX-License-Identifier: BSD-3-Clause
"""
SPC Day 1 Convective Outlook (Live)
===================================

Fetch the latest SPC Day 1 Convective Outlook GeoJSON and plot it
with major U.S. cities and a banner added on a CONUS map.
"""

import requests
import geopandas as gpd
from shapely.geometry import Point
from metpy.plots import MapPanel, PanelContainer, PlotGeometry
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime
import matplotlib.patheffects as path_effects

###########################
# Download the latest SPC Day 1 Outlook GeoJSON
url = "https://www.spc.noaa.gov/products/outlook/day1otlk_cat.lyr.geojson"
r = requests.get(url)
r.raise_for_status()

with open("day1_outlook.geojson", "wb") as f:
    f.write(r.content)

day1_outlook = gpd.read_file("day1_outlook.geojson")

###########################
# Plot the SPC outlook polygons
geo = PlotGeometry()
geo.geometry = day1_outlook['geometry']
geo.fill = day1_outlook['fill']
geo.stroke = day1_outlook['stroke']
geo.labels = day1_outlook['LABEL']
geo.label_fontsize = 14

###########################
# Define major cities as (name, lat, lon)
cities = [
    ("Pensacola, FL", 30.4213, -87.2169),
    ("Bangor, ME", 44.8016, -68.7790),
    ("International Falls, MN", 48.6017, -93.4083),
    ("New York, NY", 40.7128, -74.0060),
    ("Chicago, IL", 41.8781, -87.6298),
    ("Dallas, TX", 32.7767, -96.7970),
    ("Denver, CO", 39.7392, -104.9903),
    ("Los Angeles, CA", 34.0522, -118.2437),
    ("Seattle, WA", 47.6062, -122.3321),
    ("Atlanta, GA", 33.7490, -84.3880),
    ("Kansas City, MO", 39.0997, -94.5786),
    ("Minneapolis, MN", 44.9778, -93.2650)
]

# Convert to shapely Points + labels
city_points = [Point(lon, lat) for (_, lat, lon) in cities]
city_labels = [name for (name, _, _) in cities]

city_geo = PlotGeometry()
city_geo.geometry = city_points
city_geo.labels = city_labels
city_geo.marker = 'o'
city_geo.fill = 'white'
city_geo.label_fontsize = 'medium'
city_geo.mpl_args = {'markersize': 6, 'markeredgewidth': 0.8, 'markerfacecolor': 'black'}

###########################
# Build the map panel
panel = MapPanel()
panel.title = ""  # we’ll use a custom banner instead
panel.plots = [geo, city_geo]
panel.area = [-125, -66.5, 24, 50]  # CONUS view
panel.projection = 'lcc'
panel.layers = ['lakes', 'land', 'ocean', 'states', 'coastline', 'borders']

pc = PanelContainer()
pc.size = (19.2, 10.8)  # inches, matches 1920x1080 at dpi=100
pc.panels = [panel]

pc.draw()  

###########################
# Get the figure created by MetPy
fig = plt.gcf()
fig.set_size_inches(19.2, 10.8)  # ensure 1920x1080
fig.patch.set_facecolor("gray")

# Add banner rectangle across top
ax_banner = fig.add_axes([0, 0.88, 1, 0.10])
ax_banner.add_patch(Rectangle((0, 0), 1, 1, transform=ax_banner.transAxes,
                              color='darkblue', zorder=10))
ax_banner.axis('off')

# Add banner text (left aligned with shadow)
today_str = datetime.now().strftime("%b %d, %Y").upper()
text = fig.text(
    0.02, 0.925,
    f"DAY 1 SEVERE WEATHER OUTLOOK\n{today_str}",
    color='white', fontsize=25, fontweight='bold',  # slightly larger for 1080p
    ha='left', va='center'
)
text.set_path_effects([
    path_effects.withStroke(linewidth=4, foreground='black')
])

fig.savefig("docs/spc/day1_outlook.png", dpi=100, bbox_inches='tight')

plt.show()
