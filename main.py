from pathlib import Path
from itertools import accumulate
import matplotlib.pyplot as plt
import filter as f
from timeseries import TimeSeries
import transform
import os
import routes

extension = ".png"


def get_new_plot():
    return plt.subplots(figsize=(12, 6), dpi=300)


def save_plot(figure, title, route):
    figure.tight_layout()
    try:
        os.mkdir(f"plots/{route[0]}/")
    except FileExistsError:
        pass
    figure.savefig(f"plots/{route[0]}/{title}{extension}")


def filter_array(array, filter_func):
    return [element for element in array if filter_func(element)]


def filter_date_time(time_series, route):
    date_time_start = route[1]
    date_time_end = route[2]
    if date_time_start is not None and date_time_end is not None:
        if time_series is list:
            return [ts.filter_date(date_time_start, date_time_end) for ts in time_series]
        else:
            return time_series.filter_date(date_time_start, date_time_end)


def get_engine_label(index: int, source: str) -> str:
    match source:
        case 'boost_pressure.csv':
            return f"engine {index} boost pressure"
        case 'coolant_temperature.csv':
            return f"engine {index} coolant temperature"
        case 'exhaust_temperature1.csv' | 'exhaust_temperature2.csv':
            return f"engine {index} exhaust temperature"
        case 'fuel_consumption.csv':
            return f"engine {index} fuel consumption"
        case 'engine_speed.csv':
            return f"engine {index} speed"
        case 'engine_load.csv':
            return f"engine {index} power"
        case _:
            raise NotImplementedError(f"{source}")


def get_thruster_label(side: str, source: str) -> str:
    match source:
        case 'RPMFeedback.csv':
            return f"thruster {side} RPM"
        case 'LoadFeedback.csv':
            return f"thruster {side} load"
        case _:
            raise NotImplementedError(f"{source}")


def construct_label(file_path: str) -> str:
    match file_path.parts[-2:]:
        case [top_level, second_level]:
            match top_level:
                case "Engine1":
                    return get_engine_label(1, second_level)
                case "Engine3":
                    return get_engine_label(3, second_level)
                case "hcx_stbd_mp":
                    return get_thruster_label("starboard", second_level)
                case "hcx_port_mp":
                    return get_thruster_label("port", second_level)
                case "SeapathGPSVtg":
                    return "SOG"
                case _:
                    raise NotImplementedError(f"{top_level, second_level}")
        case top_level:
            raise NotImplementedError(f"{top_level}")


def total_power_engines(title, route, file_paths):
    file_paths_engine_load = filter_array(file_paths, f.is_engine_load)
    file_paths_engine_fuel_consumption = filter_array(file_paths, f.is_engine_fuel_consumption)
    # this is in KW
    time_series_engine_load = [TimeSeries.from_csv(file_path, label=construct_label(file_path))
                               for file_path in file_paths_engine_load]
    # this is in liters per hour
    time_series_fuel_consumption = [TimeSeries.from_csv(file_path, label=construct_label(file_path))
                                    for file_path in file_paths_engine_fuel_consumption]

    time_series_engine_load = [filter_date_time(ts, route) for ts in time_series_engine_load]
    time_series_fuel_consumption = [filter_date_time(ts, route) for ts in time_series_fuel_consumption]

    # interpolate
    for ts_load, ts_engine in zip(time_series_engine_load, time_series_fuel_consumption):
        ts_load.interpolate(ts_engine)
        ts_engine.interpolate(ts_load)

    for ts_load, ts_fuel in zip(time_series_engine_load, time_series_fuel_consumption):
        new_values = []
        for value_load, value_fuel in zip(ts_load.values, ts_fuel.values):
            new_values.append(value_load / value_fuel * 3600 / (820 * 45.4) * 100)
        ts_load.values = new_values
        ts_load.label = "Engine thermal efficiency " + ts_load.label[7]
        ts_load.unit = "%"

    time_series_thermal_efficiency = time_series_engine_load

    figure, ax = get_new_plot()

    for ts in time_series_thermal_efficiency:
        ts.plot(ax, title, route)

    save_plot(figure, title, route)
    plt.close()


def theoretical_fuel_consumption(title, route, file_paths):
    figure, ax = get_new_plot()

    file_paths_thruster_load = filter_array(file_paths, f.is_thruster_load)

    ts_thrusters_percent = [TimeSeries.from_csv(
        file_path, label=construct_label(file_path)) for file_path in file_paths_thruster_load]

    ts_thrusters_percent = [filter_date_time(ts, route) for ts in ts_thrusters_percent]

    ts_thrusters_power = sum([ts.transform(transform.thruster_load, "W") for ts in ts_thrusters_percent])

    new_values = []
    efficiency_switchboard = 0.99
    efficiency_frequency_converter = 0.97
    efficiency_generator = 0.96
    for thrust in ts_thrusters_power.values:
        new_values.append(thrust / (efficiency_frequency_converter * efficiency_switchboard * efficiency_generator))

    engine_power = TimeSeries(ts_thrusters_power.time_stamps, new_values, "theoretical thermal efficiency", "")

    engine_load = engine_power.transform(transform.engine_power_to_total_load, "%")
    engine_efficiency = engine_load.transform(transform.engine_efficiency_emperical, "%")
    engine_efficiency = engine_efficiency.transform(transform.from_percent_to_fraction, "")

    time_diffs = ts_thrusters_power.get_time_diff()

    thruster_time_diffs = [thruster.get_time_diff() for thruster in ts_thrusters_percent][0]
    electrical_eff = 0.922

    time_stamps = ts_thrusters_power.time_stamps
    ts_thrusters_power.label = "Thrusters power"

    engines_power_values = []
    efficiency_switchboard = 0.99
    efficiency_frequency_converter = 0.97
    efficiency_generator = 0.96

    for value in ts_thrusters_power.values:
        engines_power_values.append(value / (efficiency_frequency_converter *
                                             efficiency_switchboard * efficiency_generator))

    ts_engines_power = TimeSeries(
        time_stamps, engines_power_values, "Theoretical power engines", "W")
    ts_engines_load = ts_engines_power.transform(transform.engine_power_to_total_load, "%")
    ts_engines_efficiency = ts_engines_load.transform(transform.engine_efficiency_emperical, "")
    ts_engines_efficiency.label = "Theoretical eninges efficiency"

    diesel_heating_value = 45.4 * 10**6

    def to_energy_usage(
            delta_time: float,
            thrust: float,
            electrical_efficiency: float,
            fuel_energy_density: float,
            efficiency: float):
        # ints are saturated => float conversion
        # time diff is in nano seconds
        nominator = (10**(-9) * float(delta_time) * float(thrust))
        denominator = (electrical_efficiency * fuel_energy_density * float(efficiency))
        return nominator/denominator

    energy_usage = [to_energy_usage(diff, thrust, electrical_eff, diesel_heating_value, eff)
                    for diff, thrust, eff in zip(time_diffs, ts_thrusters_power.values, engine_efficiency.values)]
    energy_usage_cumulative = list(accumulate(energy_usage))

    fuel_usage = TimeSeries(ts_thrusters_power.time_stamps[:-1],
                            energy_usage_cumulative, "Engines fuel consumption", "kg")

    fuel_usage.plot(ax, title, route)

    save_plot(figure, title, route)
    plt.close()


def theoretical_engine_thermal_efficiency(title, route, file_paths):
    file_paths_thruster_load = filter_array(file_paths, f.is_thruster_load)

    ts_thrusters_load_ind = [TimeSeries.from_csv(
        file_path, label=construct_label(file_path)) for file_path in file_paths_thruster_load]

    ts_thrusters_load_ind = [filter_date_time(ts, route) for ts in ts_thrusters_load_ind]

    ts_thrusters_power = sum([ts.transform(transform.thruster_load, "W") for ts in ts_thrusters_load_ind])

    time_stamps = ts_thrusters_power.time_stamps

    efficiency_switchboard = 0.99
    efficiency_frequency_converter = 0.97
    efficiency_generator = 0.96
    efficiency_power_trail = efficiency_frequency_converter * efficiency_switchboard * efficiency_generator

    engines_power_values = [power/efficiency_power_trail for power in ts_thrusters_power.values]
    ts_engines_power = TimeSeries(time_stamps, engines_power_values, "Theoretical power engines", "W")

    ts_engines_power = ts_engines_power.transform(transform.engine_power_to_total_load, "%")
    ts_engines_power = ts_engines_power.transform(transform.engine_efficiency_emperical, "%")

    ts_engines_power.label = "Theoretical thermal efficiency engines"
    ts_engines_power.unit = "%"

    figure, ax = get_new_plot()
    ts_engines_power.plot(ax, title, route)
    save_plot(figure, title, route)
    plt.close()


def read_and_plot(title, file_paths, filter, route, sum_plots=False, new_unit: str = None, transformer=None):
    filtered_file_paths = filter_array(file_paths, filter)
    time_series = [TimeSeries.from_csv(file_path, label=construct_label(file_path))
                   for file_path in filtered_file_paths]

    time_series = [filter_date_time(ts, route) for ts in time_series]

    if transformer is not None:
        time_series = [time_serie.transform(transformer, new_unit) for time_serie in time_series]

    figure, ax = get_new_plot()

    for ts in time_series:
        ts.plot(ax, title, route)

    if sum_plots:
        summed_series = sum(time_series)
        summed_series.label = f"total {title.lower()}"
        summed_series.plot(ax, title, route)

    save_plot(figure, title, route)
    plt.close()


def power_efficiency_engine_to_thruster_emperical(title, route, file_paths):

    time_series_engine_load_ind = [TimeSeries.from_csv(file_path, construct_label(
        file_path))for file_path in file_paths if f.is_engine_load(file_path)]

    number_of_engines = len(time_series_engine_load_ind)

    time_series_engine_load = [filter_date_time(ts, route) for ts in time_series_engine_load_ind]

    time_series_engine_load_total = sum(time_series_engine_load)

    def to_percent_load(total_engine_load):
        max_engine_power = 450
        max_total_engine_power = number_of_engines * max_engine_power
        result = (total_engine_load / max_total_engine_power) * 100
        return result

    time_series_engine_load_total = time_series_engine_load_total.transform(to_percent_load, "%")
    time_series_engine_load_total = time_series_engine_load_total.transform(
        transform.engine_power_efficiency_emperical_to_thruster, "%")

    time_series_engine_load_total.label = "total power efficiency from engines to thrusters"

    # average = sum(time_series_engine_load_total.values) / len(time_series_engine_load_total.values)
    # print(f"{route[0]} average power efficiency from engine to thruster {average}")

    figure, ax = get_new_plot()
    time_series_engine_load_total.plot(ax, title, route)
    save_plot(figure, title, route)
    plt.close()


def engine_load_minus_thruster_load(title, route, file_paths):

    file_paths_engine_power_ind = filter_array(file_paths, f.is_engine_load)
    file_paths_thruster_load_ind = filter_array(file_paths, f.is_thruster_load)

    time_series_engine_power_ind = [TimeSeries.from_csv(
        file_path, construct_label(file_path)) for file_path in file_paths_engine_power_ind]
    time_series_thruster_load_ind = [TimeSeries.from_csv(
        file_path, construct_label(file_path)) for file_path in file_paths_thruster_load_ind]

    time_series_engine_power_ind = [ts.transform(transform.engine_load, "W") for ts in time_series_engine_power_ind]
    time_series_thruster_power_ind = [ts.transform(transform.thruster_load, "W")
                                      for ts in time_series_thruster_load_ind]

    time_series_engines_power = sum(time_series_engine_power_ind)
    time_series_thrusters_power = sum(time_series_thruster_power_ind)
    time_series_difference_power = time_series_engines_power - time_series_thrusters_power

    time_series_engines_power = filter_date_time(time_series_engines_power, route)
    time_series_thrusters_power = filter_date_time(time_series_thrusters_power, route)
    time_series_difference_power = filter_date_time(time_series_difference_power, route)

    time_series_engines_power.label = "Engines power"
    time_series_thrusters_power.label = "Thrusters power"
    time_series_difference_power.label = "Difference"

    figure, ax = get_new_plot()

    time_series_difference_power.plot(ax, title, route)
    time_series_engines_power.plot(ax, title, route)
    time_series_thrusters_power.plot(ax, title, route)

    save_plot(figure, title, route)
    plt.close()


def main():
    file_paths = list(Path("data/gunnerus/").glob("**/*.csv"))

    # TODO: subtract engine load and thurster load to get idealized hotel load assumed to be constant
    # TODO: plot shit separated by routes
    # TODO: plot map data using the same routes

    for route in routes.routes:
        single_plot_args = [
            ("Thruster rpm", f.is_thruster_rpm),
            ("Thruster load", f.is_thruster_load),

            ("Engine speed", f.is_engine_speed),
            ("Engine boost pressure", f.is_engine_boost_pressure),
            ("Engine coolant temperature", f.is_engine_coolant_temperature),
            ("Engine exhaust temperature 1", f.is_engine_exhaust_temperature1),
            ("Engine exhaust temperature 2", f.is_engine_exhaust_temperature2),
            ("Engine fuel flow rate", f.is_engine_fuel_consumption),
            # ("", ),
        ]

        for title, filter in single_plot_args:
            read_and_plot(
                title=title,
                file_paths=file_paths,
                filter=filter,
                route=route,
                sum_plots=False,
                new_unit=None,
                transformer=None,
            )

        sum_plot_args = [
            ("Thruster power", f.is_thruster_load, "W", transform.thruster_load),

            ("Engine fuel flow rate", f.is_engine_fuel_consumption, None, None),
            ("Engine fuel flow rate kg_m³", f.is_engine_fuel_consumption,
             "kg/m³", transform.engine_fuel_consumption_liter_per_h_to_kg_per_h),
            ("Engine power kilowatt", f.is_engine_load, None, None),
            ("Engine power", f.is_engine_load, "W", transform.engine_load),
            # ("", ),
        ]
        for title, filter, new_unit, transformer in sum_plot_args:
            read_and_plot(
                title=title,
                file_paths=file_paths,
                filter=filter,
                route=route,
                sum_plots=True,
                new_unit=new_unit,
                transformer=transformer,
            )

        read_and_plot(
            title="Speed over ground",
            file_paths=file_paths,
            filter=f.is_vessel_speed_over_ground,
            route=route,
            sum_plots=False,
            new_unit="m/s",
            transformer=transform.km_h_to_m_s,
        )
        engine_load_minus_thruster_load("Difference engine and thruster power", route, file_paths)
        power_efficiency_engine_to_thruster_emperical("power efficiency from engines to thrusters", route, file_paths)
        theoretical_engine_thermal_efficiency("Theoretical engine thermal efficiency", route, file_paths)
        total_power_engines("Theoretical fuel consumption", route, file_paths)
        theoretical_fuel_consumption("Theoretical fuel consumption", route, file_paths)


if __name__ == "__main__":
    main()
