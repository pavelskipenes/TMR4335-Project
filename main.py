from pathlib import Path
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import numpy as np


"""
file filters
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


def is_thruster_load(file_path):
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


def is_thruster_rpm(file_path):
    return "RPMFeedback" in str(file_path) and is_thruster(file_path)


def is_vessel_speed_over_ground(file_path):
    return "SpeedKmHr" in str(file_path)


"""
plotting
"""


def plot(x: list, y: list, unit_y: str, title: str, label: str, clear: bool, save: bool):
    # use scientific notation on y axis with the exception when using percent
    if unit_y != "%":
        plt.ticklabel_format(axis='y', style='sci', scilimits=(1, 0))
    plt.xticks(rotation=45)
    plt.locator_params(axis='y', nbins=40)
    plt.title(title)
    plt.ylabel(unit_y)
    plt.xlabel("Time")
    plt.tight_layout()
    plt.plot(x, y, label=label)
    plt.grid(True)
    plt.legend()
    if save:
        plt.savefig("plots/" + title + ".svg")
    if clear:
        plt.clf()


def plot_inidividual_and_sum(time_series, unit_y, plot_title):

    labels = time_series.keys()
    for label in labels:
        plot(time_series[label][0], time_series[label][1], "", "", label, False, False)

    all_times = sorted(set(t for label in time_series for t in time_series[label][0]))
    all_timestamps = np.array([t.timestamp() for t in all_times])
    total_sum = np.zeros(len(all_timestamps))
    for label, (times, values) in time_series.items():
        time_timestamps = np.array([t.timestamp() for t in times])
        interpolated_values = np.interp(all_timestamps, time_timestamps, values)
        total_sum += interpolated_values
    plot(all_times, total_sum, unit_y, plot_title, "Total " + plot_title.lower(), True, True)


def plot_individual(time_series, unit_y, plot_title):
    labels = time_series.keys()
    for label in labels:
        plot(time_series[label][0], time_series[label][1], unit_y, plot_title, label, False, False)
    plt.savefig("plots/" + plot_title + ".svg")
    plt.clf()


def read_and_plot(title, file_paths, filter, date_time_start, date_time_end, sum=False, new_unit: str = None, transformer=None):
    filtered_file_paths = [file_path for file_path in file_paths if filter(file_path)]
    time_series, unit_y = extract_time_series(filtered_file_paths, date_time_start, date_time_end)
    if transformer is not None:
        time_series = transform_value(time_series, transformer)
    if new_unit is not None:
        unit_y = new_unit
    if sum:
        plot_inidividual_and_sum(time_series, unit_y, title)
        return
    plot_individual(time_series, unit_y, title)


"""
deserialization
"""


def read_data(file_path: str):
    label = " ".join(file_path.parts[-2:])
    unit = None
    time = []
    value = []
    with open(file_path) as file:
        for line in file.readlines():
            match line.split(","):
                case [datetime_raw, value_raw, unit_raw]:
                    if unit is None:
                        unit = unit_raw.strip()
                    time.append(datetime.fromisoformat(datetime_raw.strip()))
                    value.append(float(value_raw.strip()))
                case _:
                    raise ValueError("cannot deserialize line", line)
    return time, value, unit, label


def extract_time_series(filtered_file_paths, date_time_start, date_time_end):
    all_values = {}

    unit = ""
    for file_path in filtered_file_paths:
        time, value, unit, label = read_data(file_path)

        if label not in all_values:
            all_values[label] = {}

        all_values[label] = (time, value)

    result = {}
    for label, (time, value) in all_values.items():
        filtered_time = [t for t in time if date_time_start <= t <= date_time_end]
        filtered_value = [value[i] for i, t in enumerate(time) if date_time_start <= t <= date_time_end]
        result[label] = (filtered_time, filtered_value)

    return result, unit


def filter_time_series(time_series, date_time_start, date_time_end):
    result = {}
    for label, (time, value) in time_series.items():
        filtered_time = [t for t in time if date_time_start <= t <= date_time_end]
        filtered_value = [value[i] for i, t in enumerate(time) if date_time_start <= t <= date_time_end]
        result[label] = (filtered_time, filtered_value)
    return result


"""
transformators changes the value in the data series
"""


def transform_value(time_series, transformer):
    new_time_series = {}
    for label, (time, values) in time_series.items():
        new_time_series[label] = (time, [transformer(value) for value in values])

    return new_time_series


def transform_specific_fuel_consumption(fuel_mass_flow, power):
    return fuel_mass_flow/power


def transform_power_efficiency(propulsion_power, load_feedback):
    return propulsion_power/load_feedback


def transform_thruster_load(thruster_load_percent):
    # max thruster power is 500kW. transform percent to SI unit
    return thruster_load_percent * 500e3


def transform_engine_load(engine_load_kw):
    # engine load is recorded in kW. transform to SI unit
    return engine_load_kw * 1e3


def transformer_km_h_to_m_s(vessel_sog):
    return vessel_sog*60/1000


def main():
    plt.figure(figsize=(30, 18))
    file_paths = list(Path("gunnerus").glob("**/*.csv"))

    # TODO: find time that splits route 1 and route 2
    date_time_start = datetime(2024, 9, 10, 6, 30, tzinfo=timezone.utc)
    date_time_end = datetime(2024, 9, 10, 7, 44, tzinfo=timezone.utc)

    single_plot_args = [
        ("Thruster load rpm", is_thruster_rpm),
        ("Thruster load percent", is_thruster_load),

        ("Engine speed", is_engine_speed),
        ("Engine boost pressure", is_engine_boost_pressure),
        ("Engine coolant temperature", is_engine_coolant_temperature),
        ("Engine exhaust temperature 1", is_engine_exhaust_temperature1),
        ("Engine exhaust temperature 2", is_engine_exhaust_temperature2),
        ("Engine fuel consumption", is_engine_fuel_consumption),
        # ("", ),
    ]

    sum_plot_args = [
        ("Thruster load watt", is_thruster_rpm, "W", transform_thruster_load),

        ("Engine fuel consumption", is_engine_fuel_consumption, None, None),
        ("Engine load", is_engine_load, None, None),
        ("Engine load watt", is_engine_load, "W", transform_engine_load),
        # ("", ),
    ]

    for title, filter in single_plot_args:
        read_and_plot(
            title=title,
            file_paths=file_paths,
            filter=filter,
            date_time_start=date_time_start,
            date_time_end=date_time_end,
            sum=False,
            new_unit=None,
            transformer=None,
        )

    for title, filter, new_unit, transformer in sum_plot_args:
        read_and_plot(
            title=title,
            file_paths=file_paths,
            filter=filter,
            date_time_start=date_time_start,
            date_time_end=date_time_end,
            sum=True,
            new_unit=new_unit,
            transformer=transformer,
        )
    read_and_plot(
        title="Speed over ground (SOG)",
        file_paths=file_paths,
        filter=is_vessel_speed_over_ground,
        date_time_start=date_time_start,
        date_time_end=date_time_end,
        sum=False,
        new_unit="m/s",
        transformer=transformer_km_h_to_m_s,
    )

    return


if __name__ == "__main__":
    main()
