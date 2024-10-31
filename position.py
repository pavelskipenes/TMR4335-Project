import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import json
from datetime import datetime


def get_points(time_start, time_end, data):
    start_time = datetime.strptime(time_start, "%H:%M:%S").time()
    end_time = datetime.strptime(time_end, "%H:%M:%S").time()

    return [
        (entry['latitude'], entry['longitude'])
        for entry in data
        if start_time <= datetime.fromisoformat(entry['date_time_utc']).time() <= end_time
    ]


def get_position_boundaries(data):
    positions = [(entry['latitude'], entry['longitude']) for entry in data]
    max_lat = max(pos[0] for pos in positions)
    min_lat = min(pos[0] for pos in positions)
    max_long = max(pos[1] for pos in positions)
    min_long = min(pos[1] for pos in positions)
    return min_long, max_long, min_lat-0.0020, max_lat


file = open('data/gunnerus_position_10_09_2024.json')
data = json.load(file)

min_long, long_max, lat_min, lat_max = get_position_boundaries(data)

time_spots = [
    # "06:34:00", "06:56:00", "07:06:00", "07:22:00", "07:37:00", "07:44:00"
    "06:30:00",
    "06:34:00", "06:56:00", "07:06:00",
    "07:44:00"
]

routes = [get_points(time_spots[i], time_spots[i+1], data) for i in range(len(time_spots) - 1)]

one_route = [get_points(time_spots[0], time_spots[-1], data)]
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})

for i, route in enumerate(routes):
    latitudes, longitudes = zip(*route)
    label = "route " + str(i+1) + " " + time_spots[i] + " - " + time_spots[i+1]
    ax.plot(longitudes, latitudes, label=label, marker="o", markersize=5, transform=ccrs.PlateCarree())


other_positions = [
    (63.4575, 10.3723, "SINTEF DataBuoy"),
    (63.4511, 10.3833, "Munkholmen"),
    (63.4371, 10.3972, "NTNU/SINTEF SeaLab"),
    (63.4464, 10.4167, "Lighthouse")
]

for lat, long, title, in other_positions:
    ax.plot(long, lat, marker="o", color="black", markersize=5, transform=ccrs.PlateCarree())
    ax.annotate(title, xy=(long, lat), xytext=(long - 0.0050, lat + 0.001), fontsize=10, transform=ccrs.PlateCarree())

ax.set_extent([min_long, long_max, lat_min, lat_max], crs=ccrs.PlateCarree())

# Add geographical features
ax.add_feature(cfeature.OCEAN, facecolor='lightblue')  # Ocean color
ax.add_feature(cfeature.LAND, facecolor='lightgreen')  # Land color
ax.add_feature(cfeature.LAKES, facecolor='darkblue')  # Lakes
ax.add_feature(cfeature.RIVERS, edgecolor='blue')      # Rivers
ax.add_feature(cfeature.COASTLINE, edgecolor='black')  # Coastlines

ax.gridlines(draw_labels=True)
ax.set_title('RV Gunnerus AIS position')
ax.legend()

plt.savefig('plots/trondheim_map.png', format="png", dpi=300)
