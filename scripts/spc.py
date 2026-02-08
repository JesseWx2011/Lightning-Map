import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patheffects import withStroke
from matplotlib.patches import Polygon, FancyBboxPatch, PathPatch
from matplotlib.path import Path
import requests
import json
from datetime import datetime, timedelta
import numpy as np

def rounded_rect(x, y, width, height, radius=0.05):
    """
    Create a Path for a rounded rectangle.
    
    Parameters:
    - x, y: bottom-left corner coordinates (in axes coordinates 0-1)
    - width, height: dimensions (in axes coordinates 0-1)
    - radius: corner radius (in axes coordinates 0-1)
    """
    # Limit radius to half of the smallest dimension
    radius = min(radius, width/2, height/2)
    
    # Define the path vertices
    vertices = [
        # Start at bottom-left, after the radius
        (x + radius, y),
        # Bottom side
        (x + width - radius, y),
        # Bottom-right arc
        (x + width - radius, y),
        (x + width, y),
        (x + width, y + radius),
        # Right side
        (x + width, y + height - radius),
        # Top-right arc
        (x + width, y + height - radius),
        (x + width, y + height),
        (x + width - radius, y + height),
        # Top side
        (x + radius, y + height),
        # Top-left arc
        (x + radius, y + height),
        (x, y + height),
        (x, y + height - radius),
        # Left side
        (x, y + radius),
        # Bottom-left arc
        (x, y + radius),
        (x, y),
        (x + radius, y),
    ]
    
    codes = [
        Path.MOVETO,
        Path.LINETO,
        Path.CURVE3,
        Path.CURVE3,
        Path.LINETO,
        Path.LINETO,
        Path.CURVE3,
        Path.CURVE3,
        Path.LINETO,
        Path.LINETO,
        Path.CURVE3,
        Path.CURVE3,
        Path.LINETO,
        Path.LINETO,
        Path.CURVE3,
        Path.CURVE3,
        Path.CLOSEPOLY,
    ]
    
    return Path(vertices, codes)

def fetch_spc_geojson(day_number):
    """Fetch SPC outlook GeoJSON data."""
    urls = {
        1: "https://www.spc.noaa.gov/products/outlook/day1otlk_cat.lyr.geojson",
        2: "https://www.spc.noaa.gov/products/outlook/day2otlk_cat.lyr.geojson",
        3: "https://www.spc.noaa.gov/products/outlook/day3otlk_cat.lyr.geojson"
    }
    
    try:
        response = requests.get(urls[day_number], timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Could not fetch SPC data for Day {day_number}: {e}")
    return None

def plot_outlook_polygons(ax, geojson_data):
    """Plot SPC outlook polygons from GeoJSON data."""
    if not geojson_data or 'features' not in geojson_data:
        return
    
    # Risk level mapping
    risk_colors = {
        'TSTM': '#C1E9C1',  # General thunderstorm
        'MRGL': '#66CC66',  # Marginal
        'SLGT': '#FFFF66',  # Slight
        'ENH': '#FF9966',   # Enhanced
        'MDT': '#FF6666',   # Moderate
        'HIGH': '#FF00FF'   # High
    }
    
    for feature in geojson_data['features']:
        if feature['type'] != 'Feature':
            continue
            
        geometry = feature['geometry']
        properties = feature.get('properties', {})
        
        # Get the risk label
        label = properties.get('LABEL', 'TSTM')
        fill_color = properties.get('fill', risk_colors.get(label, '#C1E9C1'))
        stroke_color = properties.get('stroke', '#555555')
        
        if geometry['type'] == 'Polygon':
            coords = geometry['coordinates'][0]
            lons = [coord[0] for coord in coords]
            lats = [coord[1] for coord in coords]
            
            # Plot filled polygon
            ax.fill(lons, lats, color=fill_color, alpha=0.6, 
                   transform=ccrs.PlateCarree(), zorder=3)
            # Plot outline
            ax.plot(lons, lats, color=stroke_color, linewidth=2, 
                   transform=ccrs.PlateCarree(), zorder=4)
        
        elif geometry['type'] == 'MultiPolygon':
            for polygon in geometry['coordinates']:
                coords = polygon[0]
                lons = [coord[0] for coord in coords]
                lats = [coord[1] for coord in coords]
                
                # Plot filled polygon
                ax.fill(lons, lats, color=fill_color, alpha=0.6,
                       transform=ccrs.PlateCarree(), zorder=3)
                # Plot outline
                ax.plot(lons, lats, color=stroke_color, linewidth=2,
                       transform=ccrs.PlateCarree(), zorder=4)

def create_spc_outlook_map(day_number, date_str, output_filename):
    """
    Create an SPC outlook map with full-screen map and absolutely positioned overlays.
    
    Parameters:
    - day_number: Day number (1, 2, or 3)
    - date_str: Date string in format MM/DD/YYYY
    - output_filename: Output filename (e.g., 'spc1.png')
    """
    
    # Create figure with larger size
    fig = plt.figure(figsize=(20, 11), facecolor='#E8E8E8')
    
    # Create map projection - FILLS ENTIRE FIGURE
    proj = ccrs.LambertConformal(central_longitude=-95, central_latitude=38)
    ax = plt.axes([0, 0, 1, 1], projection=proj)  # Full screen map
    
    # Set extent to cover CONUS
    ax.set_extent([-125, -66, 24, 50], crs=ccrs.PlateCarree())
    
    # Add map features with light colors
    ax.add_feature(cfeature.OCEAN, facecolor='#E6F2FF', zorder=0)
    ax.add_feature(cfeature.LAND, facecolor='#FFFFFF', zorder=0)
    ax.add_feature(cfeature.LAKES, facecolor='#E6F2FF', zorder=1)
    
    # Fetch and plot SPC outlook (above land, below borders)
    geojson_data = fetch_spc_geojson(day_number)
    if geojson_data:
        plot_outlook_polygons(ax, geojson_data)
        print(f"Successfully plotted Day {day_number} outlook")
    else:
        print(f"No outlook data available for Day {day_number}")
    
    # Add state/country borders on top
    ax.add_feature(cfeature.STATES, linewidth=0.8, edgecolor='#555555', zorder=5)
    ax.add_feature(cfeature.COASTLINE, linewidth=1.0, edgecolor='#333333', zorder=5)
    ax.add_feature(cfeature.BORDERS, linewidth=1.0, edgecolor='#333333', zorder=5)
    
    # Plot cities
    cities = {
        'Bismarck': (46.8083, -100.7837),
        'Pensacola': (30.4213, -87.2169),
        'Miami': (25.7617, -80.1918),
        'Atlanta': (33.7490, -84.3880),
        'Oklahoma City': (35.4676, -97.5164),
        'Dallas': (32.7767, -96.7970),
        'El Paso': (31.7619, -106.4850),
        'Albuquerque': (35.0844, -106.6504),
        'Washington DC': (38.9072, -77.0369),
        'New York': (40.7128, -74.0060),
        'Pittsburgh': (40.4406, -79.9959),
        'Lansing': (42.7325, -84.5555),
        'Int Falls': (48.6013, -93.4109),
        'Des Moines': (41.6005, -93.6091),
        'Nashville': (36.1627, -86.7816),
        'Kansas City': (39.0997, -94.5786),
        'Omaha': (41.2565, -95.9345),
        'Houston': (29.7604, -95.3698),
        'Chicago': (41.8781, -87.6298),
        'Cheyenne': (41.1400, -104.8202),
        'Denver': (39.7392, -104.9903),
        'Los Angeles': (34.0522, -118.2437),
        'Sacramento': (38.5816, -121.4944),
        'Seattle': (47.6062, -122.3321),
        'Great Falls': (47.5003, -111.3008),
        'Rapid City': (44.0805, -103.2310),
        'Little Rock': (34.7465, -92.2896)
    }
    
    # Plot city markers and labels
    for city_name, (lat, lon) in cities.items():
        ax.plot(lon, lat, 'o', color='black', markersize=4, 
               transform=ccrs.PlateCarree(), zorder=6)
        ax.text(lon, lat, f'  {city_name}', fontsize=12, 
               color='black', fontweight='bold',
               transform=ccrs.PlateCarree(), zorder=6,
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                        edgecolor='none', alpha=0.0))
    
    # Text shadow effect
    shadow = withStroke(linewidth=5, foreground='black', alpha=0.7)
    
    # ABSOLUTE POSITIONED TITLE BANNER - at top
    title_ax = fig.add_axes([0.02, 0.89, 0.78, 0.10], zorder=100)
    title_ax.set_xlim(0, 1)
    title_ax.set_ylim(0, 1)
    title_ax.axis('off')
    
    # Add gray background with rounded corners
    # Create rounded rectangle path (radius = 0.03 for nice rounded corners)
    header_path = rounded_rect(0, 0, 1, 1, radius=0.03)
    header_patch = PathPatch(header_path, 
                             facecolor='#5A5A5A',
                             edgecolor='none',
                             transform=title_ax.transAxes,
                             zorder=1)
    title_ax.add_patch(header_patch)
    
    # Add title text
    title_ax.text(0.03, 0.65, 'Severe Weather Outlook',
                 fontsize=39, fontweight='black', color='white',
                 family='rubik', va='center',
                 path_effects=[shadow], zorder=2)
    
    # Add date text
    title_ax.text(0.03, 0.25, f'{date_str}',
                 fontsize=30, fontweight='black', color='white',
                 family='rubik', va='center', style='italic',
                 path_effects=[shadow], zorder=2)
    
    # Add data courtesy text
    title_ax.text(0.97, 0.45, 'Data Courtesy of Storm Prediction Center',
                 fontsize=20, fontweight='black', color='white',
                 family='rubik', va='center', ha='right',
                 path_effects=[withStroke(linewidth=3, foreground='black', alpha=0.6)],
                 zorder=2)
    
    # ABSOLUTE POSITIONED LEGEND - at right side
    legend_ax = fig.add_axes([0.82, 0.30, 0.16, 0.50], zorder=100)
    legend_ax.set_xlim(0, 1)
    legend_ax.set_ylim(0, 1)
    legend_ax.axis('off')
    
    # Legend background with rounded corners
    legend_path = rounded_rect(0, 0, 1, 1, radius=0.02)
    legend_patch = PathPatch(legend_path,
                             facecolor='#5A5A5A',
                             edgecolor='none',
                             transform=legend_ax.transAxes)
    legend_ax.add_patch(legend_patch)
    
    # Risk levels
    risk_levels = [
        ('High', '#FF00FF', 0.05),
        ('Moderate', '#FF6666', 0.22),
        ('Enhanced', '#FF9966', 0.39),
        ('Slight', '#FFFF66', 0.56),
        ('Marginal', '#66CC66', 0.73)
    ]
    
    # Add title to legend
    legend_ax.text(0.5, 0.92, 'Risk Levels',
                  fontsize=24, fontweight='black', color='white',
                  ha='center', va='top', family='sans-serif',
                  path_effects=[withStroke(linewidth=3, foreground='black', alpha=0.6)])
    
    # Add risk level boxes and labels with rounded corners
    for label, color, y_pos in risk_levels:
        # Color box with rounded corners
        box_path = rounded_rect(0.10, y_pos, 0.22, 0.12, radius=0.015)
        box_patch = PathPatch(box_path,
                              facecolor=color,
                              edgecolor='none',
                              transform=legend_ax.transAxes)
        legend_ax.add_patch(box_patch)
        
        # Label
        legend_ax.text(0.88, y_pos + 0.06, label,
                      fontsize=24, fontweight='black', color='white',
                      ha='right', va='center', family='sans-serif',
                      path_effects=[withStroke(linewidth=3, foreground='black', alpha=0.6)])
    
    # ABSOLUTE POSITIONED COPYRIGHT - at bottom left
    copyright_ax = fig.add_axes([0.02, 0.02, 0.3, 0.06], zorder=100)
    copyright_ax.set_xlim(0, 1)
    copyright_ax.set_ylim(0, 1)
    copyright_ax.axis('off')
    
    copyright_ax.text(0, 0.5, '©2024-2026 @JesseLikesWeather',
                     fontsize=26, fontweight='black', color='#666666',
                     ha='left', va='center', family='sans-serif',
                     path_effects=[withStroke(linewidth=2, foreground='white', alpha=0.8)])
    
    # Save figure
    plt.savefig(output_filename, dpi=150, facecolor='#E8E8E8', bbox_inches='tight')
    plt.close()
    print(f"Created {output_filename}")

# Example usage - create maps for Day 1, 2, and 3
if __name__ == "__main__":
    from datetime import datetime, timedelta
    import os
    
    # Create output directory if it doesn't exist
    output_dir = "docs/spc"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get current date and next two days
    today = datetime.now()
    day1_date = today.strftime("%m/%d/%Y")
    day2_date = (today + timedelta(days=1)).strftime("%m/%d/%Y")
    day3_date = (today + timedelta(days=2)).strftime("%m/%d/%Y")
    
    # Create Day 1 outlook
    create_spc_outlook_map(1, day1_date, f"{output_dir}/spc1.png")
    
    # Create Day 2 outlook
    create_spc_outlook_map(2, day2_date, f"{output_dir}/spc2.png")
    
    # Create Day 3 outlook
    create_spc_outlook_map(3, day3_date, f"{output_dir}/spc3.png")
    
    print("\nAll SPC outlook maps created successfully!")
