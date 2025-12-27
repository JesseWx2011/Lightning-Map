from herbie.toolbox import EasyMap, pc, ccrs
from herbie import Herbie
from herbie import paint
import matplotlib.pyplot as plt
import imageio
import numpy as np
from datetime import datetime, timedelta

# Define major cities with their coordinates
cities = [
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
    {"name": "Houston", "lat": 29.7604, "lon": -95.3698},
    {"name": "Dallas", "lat": 32.7767, "lon": -96.7970},
    {"name": "Jacksonville", "lat": 30.3322, "lon": -81.6557},
    {"name": "Charlotte", "lat": 35.2271, "lon": -80.8431},
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"name": "Indianapolis", "lat": 39.7684, "lon": -86.1581},
    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321},
    {"name": "Denver", "lat": 39.7392, "lon": -104.9903},
    {"name": "Boston", "lat": 42.3601, "lon": -71.0589},
    {"name": "Kansas City", "lat": 39.0997, "lon": -94.5786},
    {"name": "International Falls", "lat": 48.6017, "lon": -93.4103},
    {"name": "Helena", "lat": 46.5884, "lon": -112.0245},
    {"name": "Salt Lake City", "lat": 40.7608, "lon": -111.8910},
    {"name": "Albuquerque", "lat": 35.0844, "lon": -106.6504},
    {"name": "Bismarck", "lat": 46.8083, "lon": -100.7837},
    {"name": "Bangor", "lat": 44.8012, "lon": -68.7778},
    {"name": "Eugene", "lat": 44.0521, "lon": -123.0868},
    {"name": "El Paso", "lat": 31.7619, "lon": -106.4850},
]


# Parameters
model = "gfs"
product = "pgrb2.0p25"
max_hours = 384  # Default to 384 hours

# Get current UTC time
now = datetime.utcnow()

# GFS model run hours
run_hours = [0, 6, 12, 18]

# Find the latest available run
def get_latest_gfs_run(now):
    for offset in range(0, 2):  # Check today and yesterday
        check_date = now - timedelta(days=offset)
        for hour in reversed(run_hours):
            run_time = check_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            if run_time <= now:
                return run_time
    # Fallback: just return the oldest possible
    return now.replace(hour=0, minute=0, second=0, microsecond=0)

latest_run = get_latest_gfs_run(now)
date = latest_run.strftime("%Y-%m-%d")
run_hour = latest_run.strftime("%H")
year = latest_run.strftime("%Y")
month = latest_run.strftime("%m")
day = latest_run.strftime("%d")

# Also get the 4 latest model runs for documentation
latest_runs = []
for i in range(4):
    run = latest_run - timedelta(hours=6*i)
    latest_runs.append(run.strftime("%Y-%m-%d %H:00 UTC"))

# Output directory
output_dir = f"./docs/models/{year}/{month}/{day}/{run_hour}/"
import os
os.makedirs(output_dir, exist_ok=True)


# List to hold image filenames for gif
image_files = []

try:
    for hour in range(0, max_hours + 1, 3):
        try:
            print(f"Processing forecast hour: {hour}")
            H = Herbie(date, model=model, product=product, fxx=hour)
            ds = H.xarray(":TMP:2 m above")

            # Convert temperature from Kelvin to Fahrenheit
            temp_c = ds.t2m - 273.15
            temp_f = (temp_c * 9/5) + 32

            # Adjust colorbar levels for Fahrenheit
            temp_kwargs = paint.NWSTemperature.kwargs2.copy()
            # Convert Celsius levels to Fahrenheit
            celsius_levels = np.array(temp_kwargs.get('levels', np.arange(-50, 41, 5)))
            fahrenheit_levels = (celsius_levels * 9/5) + 32

            temp_cbar_kwargs = paint.NWSTemperature.cbar_kwargs2.copy()
            # Set custom ticks in Fahrenheit
            fahrenheit_ticks = np.arange(-50, 121, 10)  # From -50°F to 120°F in 10° steps
            temp_cbar_kwargs['ticks'] = fahrenheit_ticks

            # Create figure with larger map subplot and space for right colorbar
            fig = plt.figure(figsize=(19.20, 10.80), dpi=100)
            ax1 = fig.add_axes([0.05, 0.10, 0.80, 0.85], projection=ccrs.Mercator())
            # Enhanced state borders: thicker and black
            ax = EasyMap("50m", ax=ax1, theme='dark').OCEAN().LAND().BORDERS().STATES(linewidth=3, edgecolor='black')
            # Add lat/lon gridlines every 5 degrees
            gl = ax1.gridlines(draw_labels=True, linewidth=0.8, color='black', alpha=0.5, linestyle='--')
            gl.xlocator = plt.MultipleLocator(5)
            gl.ylocator = plt.MultipleLocator(5)
            gl.top_labels = False
            gl.right_labels = False
            gl.xlabel_style = {'size': 8, 'color': 'gray'}
            gl.ylabel_style = {'size': 8, 'color': 'gray'}

            # Set extent to CONUS
            ax1.set_extent([-130, -60, 19.5, 51])

            # Plot temperature using pcolormesh with bilinear smoothing
            p = ax1.pcolormesh(
                ds.longitude,
                ds.latitude,
                temp_f,
                cmap=temp_kwargs.get('cmap', 'coolwarm'),
                vmin=fahrenheit_levels.min(),
                vmax=fahrenheit_levels.max(),
                shading='gouraud',  # Bilinear smoothing
                transform=pc,
            )
            # Add colorbar to the right
            cb = fig.colorbar(
                p, ax=ax1, orientation="vertical", pad=0.02, fraction=0.08, shrink=0.85, **temp_cbar_kwargs
            )
            cb.set_label('Temperature (°F)')  # Add label for Fahrenheit

            # Plot cities with enhanced, smaller labels
            for city in cities:
                ax1.scatter(city["lon"], city["lat"], color='red', s=70, edgecolor='black', linewidth=1.2, transform=pc, zorder=11)
                ax1.text(
                    city["lon"] + 0.5, city["lat"] + 0.5, city["name"],
                    fontsize=9, fontweight='bold', color='white',
                    bbox=dict(facecolor='black', alpha=0.6, boxstyle='round,pad=0.3'),
                    ha='left', va='center', transform=pc, zorder=12
                )

            # Set title
            ax1.set_title(f"GFS Temperature Forecast - Hour {hour}", loc="left")
            ax1.set_title(f"{H.model.upper()}: {H.product_description}", loc="right")

            # Save figure
            filename = os.path.join(output_dir, f"{hour}.png")
            # Ensure output directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            # Add copyright text at the bottom
            copyright_year = datetime.now().year
            fig.text(0.5, 0.02, f"©{copyright_year} JesseLikesWeather.", ha='center', va='center', fontsize=15, color='gray', alpha=0.8)
            plt.savefig(filename, dpi=100, bbox_inches='tight')
            image_files.append(filename)
            plt.close(fig)

        except Exception as e:
            print(f"Error processing hour {hour}: {e}")
            continue


    # Create gif
    if image_files:
        gif_path = os.path.join(output_dir, 'gfs_temperature_forecast.gif')
        images = [imageio.imread(f) for f in image_files]
        imageio.mimsave(gif_path, images, duration=0.5)
        print("GIF created successfully.")
    else:
        print("No images to create GIF.")

    # Write latest model runs list
    doc_path = f"./docs/models/latest_runs.txt"
    with open(doc_path, 'w') as f:
        f.write("Latest 4 GFS Model Runs (UTC):\n")
        for run in latest_runs:
            f.write(f"- {run}\n")

except KeyboardInterrupt:
    print("Process interrupted by user.")
    # Still create gif with available images
    if image_files:
        gif_path = os.path.join(output_dir, 'gfs_temperature_forecast_partial.gif')
        images = [imageio.imread(f) for f in image_files]
        imageio.mimsave(gif_path, images, duration=0.5)
        print("Partial GIF created.")
