from goes2go import goes_latest
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from datetime import datetime, timezone
import pytz

G = goes_latest(satellite='goes19', product='ABI', return_as='xarray') 

ct_timezone = pytz.timezone('America/Chicago')

now_utc = datetime.now(timezone.utc)

now_ct = now_utc.astimezone(ct_timezone)

plot_time_string = now_ct.strftime("%m-%d-%Y %H:%M:%S CT")

fig = plt.figure(figsize=(10, 10), dpi=300)
ax = fig.add_subplot(1, 1, 1, projection=G.rgb.crs) 

ax.imshow(G.rgb.TrueColor(), **G.rgb.imshow_kwargs)
ax.coastlines(resolution='50m', color='white', linewidth=1)
ax.add_feature(cfeature.STATES, linewidth=3, edgecolor='white')

ax.set_extent([-89.843, -76.66, 34.574, 21.128  ])

ax.text(
    x=0.5,
    y=0.01,
    s=f'GOES-19 Image | {plot_time_string}',
    ha='center',
    va='bottom',
    transform=ax.transAxes,
    fontsize=12,
    color='white',
    bbox=dict(facecolor='black', alpha=0.6, edgecolor='none', pad=4)
)

plt.savefig("docs/satelliteimgs/Florida.png")

plt.show()
