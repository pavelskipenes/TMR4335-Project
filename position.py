import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import json
from datetime import datetime, timezone
from functools import reduce
from enum import Enum


def get_points(time_start, time_end, data):
    start_time = datetime.strptime(time_start, "%H:%M:%S").time()
    end_time = datetime.strptime(time_end, "%H:%M:%S").time()

    return [
        (entry['latitude'], entry['longitude'])
        for entry in data
        if start_time <= datetime.fromisoformat(entry['date_time_utc']).time() <= end_time
    ]


def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def get_position_boundaries(position_arrays):

    data = flatten(position_arrays)
    positions = [(entry['latitude'], entry['longitude']) for entry in data]
    max_lat = max(pos[0] for pos in positions)
    min_lat = min(pos[0] for pos in positions)
    max_long = max(pos[1] for pos in positions)
    min_long = min(pos[1] for pos in positions)

    return min_long, max_long, min_lat, max_lat


def load_and_sort_json(files):
    return sorted(
        reduce(lambda acc, file: acc + (json.load(open(file))), files, []),
        key=lambda x: x['date_time_utc']
    )


class vessel(Enum):
    FLYER = 257012170
    GUNNERUS = 258342000
    RED_AUTONAUT = 258027530
    YELLOW_AUTONAUT = 257090930


MMSI_TO_NAME = {
    257012170: "NTNU Flyer",
    258342000: "RV Gunnerus",
    258027530: "NTNU red autonaut",
    257090930: "NTNU yellow autonaut",
}


def red_autonaut_sar(other_positions):
    filename = "sar_ntnu_autonaut.png"
    plot_title = "Search and rescue RED autonaut"

    file_paths = [
        '../../../Autonaut/red_autonaut_september_incident/flyer_position_26_09_2024.json',
        '../../../Autonaut/red_autonaut_september_incident/flyer_position_27_09_2024.json',
        '../../../Autonaut/red_autonaut_september_incident/red_autonaut_position_26_09_2024.json',
        '../../../Autonaut/red_autonaut_september_incident/red_autonaut_position_27_09_2024.json',
    ]

    # autonaut last recorded pos before going to bed
    date_time_start = datetime(2024, 9, 26, 22, 12, 0, tzinfo=timezone.utc)
    # Flyer first appears on the map
    # date_time_end = datetime(2024, 9, 26, 23, 13, 0, tzinfo=timezone.utc)

    # Flyer reached autonauts last known location
    # date_time_end = datetime(2024, 9, 26, 23, 45, 0, tzinfo=timezone.utc)

    date_time_end = datetime(2024, 9, 27, 2, 25, 0, tzinfo=timezone.utc)
    # autonaut found
    # date_time_end = datetime(2024, 9, 27, 8, 59, 59, tzinfo=timezone.utc)


def gunnerus_munkholmen_trip(other_positions):
    pass


def shared(file_paths, date_time_start, date_time_end, plot_title):
    ais_data = load_and_sort_json(file_paths)
    ais_data = [ais_sample for ais_sample in ais_data if date_time_start <=
                datetime.fromisoformat(ais_sample['date_time_utc']) <= date_time_end]
    ais_data = reduce(
        lambda acc, entry: {
            **acc,
            entry['mmsi']: acc.get(entry['mmsi'], []) +
            [(entry['latitude'], entry['longitude'])]
        },
        ais_data,
        {}
    )
    projection = ccrs.PlateCarree()

    fig, ax = plt.subplots(figsize=(20, 20), subplot_kw={'projection': projection})
    for vessel_mmsi in list(ais_data.keys()):
        latitudes, longitudes = zip(*ais_data[vessel_mmsi])
        label = MMSI_TO_NAME[vessel_mmsi]
        ax.plot(longitudes, latitudes, label=label, marker="o", markersize=5)

    for lat, long, title, in other_positions:
        ax.plot(long, lat, marker="o", color="black", markersize=5, transform=projection)
        ax.annotate(title, xy=(long, lat), xytext=(long - 0.0050, lat + 0.001), fontsize=10, transform=projection)

    ax.set_extent([long_min - 0.005, long_max + 0.005, lat_min - 0.001, lat_max + 0.001], transform=projection)

    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.add_feature(cfeature.LAND, facecolor='lightgreen')
    ax.add_feature(cfeature.LAKES, facecolor='darkblue')
    ax.add_feature(cfeature.RIVERS, edgecolor='blue')
    ax.add_feature(cfeature.COASTLINE, edgecolor='black')

    ax.gridlines(draw_labels=True)
    ax.set_title(plot_title)
    ax.legend()

    plt.savefig(filename, dpi=300)


def main():

    # arguments

    other_positions = [
        (63.4575, 10.3723, "SINTEF DataBuoy"),
        (63.4511, 10.3833, "Munkholmen"),
        (63.4371, 10.3972, "NTNU/SINTEF SeaLab"),
        (63.4464, 10.4167, "Lighthouse"),
        (63.4410, 10.3482, "TBS"),
    ]

    # function content
    ais_data = load_and_sort_json(file_paths)

    # filter by time
    ais_data = [ais_sample for ais_sample in ais_data if date_time_start <=
                datetime.fromisoformat(ais_sample['date_time_utc']) <= date_time_end]

    long_min, long_max, lat_min, lat_max = get_position_boundaries(ais_data)
    # here we loose time information
    ais_data = reduce(
        lambda acc, entry: {
            **acc,
            entry['mmsi']: acc.get(entry['mmsi'], []) +
            [(entry['latitude'], entry['longitude'])]
        },
        ais_data,
        {}
    )

    projection = ccrs.PlateCarree()
    # projection = ccrs.Mercator()

    fig, ax = plt.subplots(figsize=(20, 20), subplot_kw={'projection': projection})
    for vessel_mmsi in list(ais_data.keys()):
        latitudes, longitudes = zip(*ais_data[vessel_mmsi])
        label = MMSI_TO_NAME[vessel_mmsi]
        # ax.plot(longitudes, latitudes, label=label, marker="o", markersize=5, transform=projection)
        ax.plot(longitudes, latitudes, label=label, marker="o", markersize=5)

    for lat, long, title, in other_positions:
        ax.plot(long, lat, marker="o", color="black", markersize=5, transform=projection)
        ax.annotate(title, xy=(long, lat), xytext=(long - 0.0050, lat + 0.001), fontsize=10, transform=projection)
        # ax.plot(long, lat, marker="o", color="black", markersize=5)
        # ax.annotate(title, xy=(long, lat), xytext=(long - 0.0050, lat + 0.001), fontsize=10)

    # ax.set_extent([long_min, long_max, lat_min, lat_max], crs=projection)
    ax.set_extent([long_min - 0.005, long_max + 0.005, lat_min - 0.001, lat_max + 0.001])

    # Add geographical features
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.add_feature(cfeature.LAND, facecolor='lightgreen')
    ax.add_feature(cfeature.LAKES, facecolor='darkblue')
    ax.add_feature(cfeature.RIVERS, edgecolor='blue')
    ax.add_feature(cfeature.COASTLINE, edgecolor='black')

    ax.gridlines(draw_labels=True)
    ax.set_title(plot_title)
    ax.legend()

    plt.savefig(filename, dpi=300)

    return
    # time_spots = [
    #     # "06:34:00", "06:56:00", "07:06:00", "07:22:00", "07:37:00", "07:44:00"
    #     "06:30:00",
    #     "06:34:00", "06:56:00", "07:06:00",
    #     "07:44:00"
    # ]

    # plot_title = 'RV Gunnerus AIS position'
    # plot_file_name = 'plots/trondheim_map.png'
    # plot_map(data, plot_title, time_spots, other_positions, plot_file_name)

    # file = open('../../../Autonaut/red_autonaut_september_incident/flyer_position_26_09_2024.json')
    # data = json.load(file)
    #
    # time_spots = [
    #     "22:00:00",
    #     "23:59:59"
    # ]
    #
    # plot_title = 'Flyer search and rescue'
    # plot_file_name = 'plots/flyer_search_and_rescue.png'
    # plot_map(data, plot_title, time_spots, other_positions, plot_file_name)


if __name__ == "__main__":
    main()


def plot_map(data, plot_title, time_spots, other_positions, plot_file_name):

    long_min, long_max, lat_min, lat_max = get_position_boundaries(data)
    routes = [get_points(time_spots[i], time_spots[i + 1], data) for i in range(len(time_spots) - 1)]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})

    for i, route in enumerate(routes):
        latitudes, longitudes = zip(*route)
        label = "route " + str(i + 1) + " " + time_spots[i] + " - " + time_spots[i + 1]
        ax.plot(longitudes, latitudes, label=label, marker="o", markersize=5, transform=ccrs.PlateCarree())

    for lat, long, title, in other_positions:
        ax.plot(long, lat, marker="o", color="black", markersize=5, transform=ccrs.PlateCarree())
        ax.annotate(title, xy=(long, lat), xytext=(long - 0.0050, lat + 0.001),
                    fontsize=10, transform=ccrs.PlateCarree())

    ax.set_extent([long_min, long_max, lat_min, lat_max], crs=ccrs.PlateCarree())

    # Add geographical features
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')  # Ocean color
    ax.add_feature(cfeature.LAND, facecolor='lightgreen')  # Land color
    ax.add_feature(cfeature.LAKES, facecolor='darkblue')  # Lakes
    ax.add_feature(cfeature.RIVERS, edgecolor='blue')      # Rivers
    ax.add_feature(cfeature.COASTLINE, edgecolor='black')  # Coastlines

    ax.gridlines(draw_labels=True)
    ax.set_title(plot_title)
    ax.legend()

    plt.savefig(plot_file_name, dpi=300)
