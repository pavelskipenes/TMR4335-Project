from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np


def plot(x: list, y: list, title: str, label: str, clear: bool = True, save: bool = True):
    plt.plot(x, y, label=label)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.title(title)
    plt.legend()
    plt.plot()
    if save:
        plt.savefig("plots/" + label.replace(".csv", ".svg"))
    if clear:
        plt.clf()


def extract_data(file_path: str):
    label = " ".join(file_path.parts[-2:])
    unit = ""
    time = []
    value = []
    with open(file_path) as file:
        for line in file.readlines():
            elements = line.split(",")
            if len(unit) == 0:
                unit = elements[2]
            time.append(datetime.fromisoformat(elements[0]))
            value.append(round(float(elements[1]), 2))
    return time, value, unit, label


def is_engine(file_path: str) -> bool:
    return "Engine" in str(file_path)


def is_thruster(file_path: str) -> bool:
    return "hcx" in str(file_path)


def is_engine_load(file_path):
    return "engine_load" in str(file_path)


def is_engine_fuel_consumption(file_path):
    return "fuel_consumption" in str(file_path)


def is_engine2(file_path: str) -> bool:
    return "Engine2" in str(file_path)


def specific_fuel_consumption(fuel_mass_flow, power):
    return fuel_mass_flow/power


def extract_time_series(filtered_file_paths):
    all_data = {}

    unit = ""
    for file_path in filtered_file_paths:
        time, data, unit, label = extract_data(file_path)
        all_data[label] = (time, data)
    return all_data, unit


def complete_plot(filtered_file_paths, plot_title):
    time_series, unit = extract_time_series(filtered_file_paths)
    labels = time_series.keys()
    for label in labels:
        (time, data) = time_series[label]
        plot(time, data, "", label, False, False)
    all_times = sorted(set(t for time, _ in time_series.values() for t in time))
    all_timestamps = np.array([t.timestamp() for t in all_times])
    total_sum = np.zeros(len(all_timestamps))
    for time, data in time_series.values():
        time_timestamps = np.array([t.timestamp() for t in time])
        interpolated_data = np.interp(all_timestamps, time_timestamps, data)
        total_sum += interpolated_data
    plot(all_times, total_sum, plot_title, "Total " + plot_title.lower(), True, True)


def main():
    plt.figure(figsize=(24, 12))
    file_paths = Path("gunnerus").glob("**/*.csv")
    filtered_file_paths = [file_path for file_path in file_paths if is_engine(file_path) and is_engine_load(file_path)]
    complete_plot(filtered_file_paths, "Engine load")
    file_paths = Path("gunnerus").glob("**/*.csv")
    filtered_file_paths = [file_path for file_path in file_paths if is_engine(
        file_path) and is_engine_fuel_consumption(file_path)]
    complete_plot(filtered_file_paths, "Fuel consumption")


if __name__ == "__main__":
    main()
