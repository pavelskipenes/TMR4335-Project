from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np


"""
filters
"""


def is_engine2(file_path: str) -> bool:
    return "Engine2" in str(file_path)


# exclude plotting engine 2 which was not being used
def is_engine(file_path: str) -> bool:
    return "Engine" in str(file_path) and not is_engine2(file_path)


def is_thruster(file_path: str) -> bool:
    return "hcx" in str(file_path)


def is_engine_load(file_path):
    return "engine_load" in str(file_path) and is_engine(file_path)


def is_engine_speed(file_path):
    return "engine_speed" in str(file_path) and is_engine(file_path)


def is_thruster_load_feedback(file_path):
    return "LoadFeedback" in str(file_path) and is_thruster(file_path)


def is_engine_exhaust_temperature1(file_path):
    return "exhaust_temperature1" in str(file_path) and is_engine(file_path)


def is_engine_exhaust_temperature2(file_path):
    return "exhaust_temperature2" in str(file_path) and is_engine(file_path)


def is_exhaust_temperature2(file_path):
    return "exhaust_temperature2" in str(file_path) and is_engine(file_path)


def is_engine_coolant_temperature(file_path):
    return "coolant_temperature" in str(file_path) and is_engine(file_path)


def is_engine_boost_pressure(file_path):
    return "boost_pressure" in str(file_path) and is_engine(file_path)


def is_engine_fuel_consumption(file_path):
    return "fuel_consumption" in str(file_path) and is_engine(file_path)


"""
plots
"""


def plot(x: list, y: list, unit_y: str, title: str, label: str, clear: bool, save: bool):
    plt.plot(x, y, label=label)
    plt.xticks(rotation=45)
    plt.title(title)
    plt.ylabel(unit_y)
    plt.xlabel("time")
    plt.legend()
    plt.tight_layout()
    plt.plot()
    if save:
        plt.savefig("plots/" + title + ".svg")
    if clear:
        plt.clf()


def plot_inidividual_and_sum(filtered_file_paths, plot_title):
    time_series, unit_y = extract_time_series(filtered_file_paths)
    labels = time_series.keys()
    for label in labels:
        (time, data) = time_series[label]
        plot(time, data, "", "", label, False, False)
    all_times = sorted(set(t for time, _ in time_series.values() for t in time))
    all_timestamps = np.array([t.timestamp() for t in all_times])
    total_sum = np.zeros(len(all_timestamps))
    for time, data in time_series.values():
        time_timestamps = np.array([t.timestamp() for t in time])
        interpolated_data = np.interp(all_timestamps, time_timestamps, data)
        total_sum += interpolated_data
    plot(all_times, total_sum, unit_y, plot_title, "Total " + plot_title.lower(), True, True)


def plot_individual(filtered_file_paths, plot_title):
    time_series, unit_y = extract_time_series(filtered_file_paths)
    labels = time_series.keys()
    for label in labels:
        (time, data) = time_series[label]
        plot(time, data, unit_y, plot_title, label, False, False)
    plt.savefig("plots/" + plot_title + ".svg")
    plt.clf()


"""
data processing
"""


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


def extract_time_series(filtered_file_paths):
    all_data = {}

    unit = ""
    for file_path in filtered_file_paths:
        time, data, unit, label = extract_data(file_path)
        all_data[label] = (time, data)
    return all_data, unit


"""
calculations
"""


def specific_fuel_consumption(fuel_mass_flow, power):
    return fuel_mass_flow/power


def main():
    plt.figure(figsize=(24, 12))
    file_paths = list(Path("gunnerus").glob("**/*.csv"))

    filtered_file_paths = [file_path for file_path in file_paths if is_engine_load(file_path)]
    plot_inidividual_and_sum(filtered_file_paths, "Engine load")

    filtered_file_paths = [file_path for file_path in file_paths if is_engine_fuel_consumption(file_path)]
    plot_inidividual_and_sum(filtered_file_paths, "Fuel consumption")

    filtered_file_paths = [file_path for file_path in file_paths if is_thruster_load_feedback(file_path)]
    plot_individual(filtered_file_paths, "Load feedback")

    filtered_file_paths = [file_path for file_path in file_paths if is_engine_speed(file_path)]
    plot_individual(filtered_file_paths, "Engine speed")

    filtered_file_paths = [file_path for file_path in file_paths if is_engine_boost_pressure(file_path)]
    plot_individual(filtered_file_paths, "Engine boost pressure")

    filtered_file_paths = [file_path for file_path in file_paths if is_engine_coolant_temperature(file_path)]
    plot_individual(filtered_file_paths, "Engine coolant temperature")

    filtered_file_paths = [file_path for file_path in file_paths if is_engine_exhaust_temperature1(file_path)]
    plot_individual(filtered_file_paths, "Engine coolant temperature 1")

    filtered_file_paths = [file_path for file_path in file_paths if is_engine_exhaust_temperature2(file_path)]
    plot_individual(filtered_file_paths, "Engine coolant temperature 2")


if __name__ == "__main__":
    main()
