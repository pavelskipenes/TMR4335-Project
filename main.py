from scipy.signal import butter, filtfilt
from pathlib import Path
from itertools import accumulate
import matplotlib.pyplot as plt
import filter as f
from timeseries import TimeSeries
import transform
import os
import routes

extension = ".png"


def difference_engine_load(title, route, file_paths):

    file_paths_engines = filter_array(file_paths, f.is_engine_load)
    ts_engine_emperical = sum([TimeSeries.from_csv(fp, construct_label(fp)) for fp in file_paths_engines])
    ts_engine_theoretical = get_theoretical_engine_power(title, route, file_paths)

    ts_engine_emperical = filter_date_time(ts_engine_emperical, route)
    ts_engine_theoretical = filter_date_time(ts_engine_theoretical, route)

    ts_engine_emperical.interpolate(ts_engine_theoretical)

    ts_engine_emperical.unit = "kW"
    ts_engine_theoretical.unit = "kW"
    ts_engine_theoretical.values = [value/1000 for value in ts_engine_theoretical.values]

    ts_engine_difference = ts_engine_emperical - ts_engine_theoretical

    mean_difference = sum(ts_engine_difference.values) / len(ts_engine_difference.values)
    mean_theoretical = sum(ts_engine_theoretical.values) / len(ts_engine_theoretical.values)
    mean_emperical = sum(ts_engine_emperical.values) / len(ts_engine_emperical.values)

    ts_engine_difference.label = f"Engine load difference. mean: {round(mean_difference, 2)} kW"
    ts_engine_emperical.label = f"Engine load emperical. mean: {round(mean_emperical, 2)} kW"
    ts_engine_theoretical.label = f"Engine load theoretical mean: {round(mean_theoretical, 2)} kW"

    figure, ax = get_new_plot()
    ts_engine_difference.plot(ax, title, route)
    ts_engine_theoretical.plot(ax, title, route)
    ts_engine_emperical.plot(ax, title, route)
    save_plot(figure, title, route)
    plt.close()


def get_theoretical_engine_power(title, route, file_paths):
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
    return ts_engines_power


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


def theoretical_total_power_engines(title, route, file_paths):
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


def theoretical_engine_power_efficiency(title, route, file_paths):
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

    mean = round(sum(ts_engines_power.values)/len(ts_engines_power.values), 2)
    ts_engines_power.label = f"Theoretical power efficiency. mean: {mean}%"
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

    if new_unit is not None:
        for ts in time_series:
            ts.unit = new_unit

    figure, ax = get_new_plot()

    for ts in time_series:
        ts.plot(ax, title, route)

    if sum_plots:
        summed_series = sum(time_series)
        summed_series.label = f"total {title.lower()}"
        summed_series.plot(ax, title, route)

    save_plot(figure, title, route)
    plt.close()


def energy_efficiency_fuel_to_genset(title, route, file_paths):
    file_paths_fuel_consumption = filter_array(file_paths, f.is_engine_fuel_consumption)
    file_paths_engine_load = filter_array(file_paths, f.is_engine_load)

    engine_ids = [f.get_engine_id(file_path) for file_path in file_paths_fuel_consumption]
    ts_fuel_consumption_ind = [TimeSeries.from_csv(fp, construct_label(fp)) for fp in file_paths_fuel_consumption]
    ts_engine_load_ind = [TimeSeries.from_csv(fp, construct_label(fp)) for fp in file_paths_engine_load]

    ts_fuel_consumption_ind = [filter_date_time(ts, route) for ts in ts_fuel_consumption_ind]
    ts_engine_load_ind = [filter_date_time(ts, route) for ts in ts_engine_load_ind]

    ts_fuel_consumption_ind = [ts.transform(transform.engine_fuel_consumption_liter_per_h_to_kg_per_s, "kg/s")
                               for ts in ts_fuel_consumption_ind]
    ts_engine_power_ind = [ts.transform(transform.engine_load, "W") for ts in ts_engine_load_ind]

    def low_pass_filter(data, cutoff, fs, order=4):
        nyquist = 0.5 * fs
        normal_cutoff = cutoff / nyquist
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return filtfilt(b, a, data)

    diesel_heating_value = 45.4*10**(6)
    figure, ax = get_new_plot()
    for fuel, power, engine_id in zip(ts_fuel_consumption_ind, ts_engine_power_ind, engine_ids):
        fuel.interpolate(power)
        time_stamps = fuel.time_stamps[:-1]

        time_diffs_fuel = fuel.get_time_diff()
        fuel_values = fuel.values[:-1]
        fuel_values = [1e-6 if val < 1e-9 else val for val in fuel_values]
        energy_in = [1e3*diesel_heating_value * float(mass_flow_rate) * float(diff) * 10**(-9)
                     for diff, mass_flow_rate in zip(time_diffs_fuel, fuel_values)]

        time_diffs_engine = power.get_time_diff()
        engine_power_values = power.values[:-1]
        energy_out = [float(diff)*float(engine_power) * 10**(-9)
                      for diff, engine_power in zip(time_diffs_engine, engine_power_values)]

        energy_efficiency = [e_out/e_in * 100 for e_out, e_in in zip(energy_out, energy_in)]
        ts = TimeSeries(time_stamps, energy_efficiency, "Energy efficiency from fuel to generator output", "%")

        ts.values = low_pass_filter(ts.values, cutoff=0.6, fs=10)
        label = f"engine {engine_id} efficiency.\nmean: {
            round(sum(ts.values)/len(ts.values), 2)}, min: {round(min(ts.values), 2)}, max: {round(max(ts.values), 2)}\n"
        ts.plot(ax, title, route, label)

    save_plot(figure, title, route)
    plt.close()


def energy_efficiency_engine_to_thruster(title, route, file_paths):
    file_paths_fuel_consumption = filter_array(file_paths, f.is_engine_fuel_consumption)
    file_paths_thruster_load = filter_array(file_paths, f.is_thruster_load)

    ts_fuel_consumption_ind = [TimeSeries.from_csv(fp, construct_label(fp)) for fp in file_paths_fuel_consumption]
    ts_thruster_load_ind = [TimeSeries.from_csv(fp, construct_label(fp)) for fp in file_paths_thruster_load]

    ts_fuel_consumption_ind = [filter_date_time(ts, route) for ts in ts_fuel_consumption_ind]
    ts_thruster_load_ind = [filter_date_time(ts, route) for ts in ts_thruster_load_ind]

    ts_fuel_consumption_ind = [ts.transform(transform.engine_fuel_consumption_liter_per_h_to_kg_per_s, "kg/s")
                               for ts in ts_fuel_consumption_ind]
    ts_thruster_power_ind = [ts.transform(transform.thruster_load, "W") for ts in ts_thruster_load_ind]

    ts_fuel_consumption = sum(ts_fuel_consumption_ind)
    ts_thruster_power = sum(ts_thruster_power_ind)

    ts_fuel_consumption.interpolate(ts_thruster_power)
    time_stamps = ts_fuel_consumption.time_stamps[:-1]

    diesel_heating_value = 45.4*10**(6)

    time_diffs_fuel = ts_fuel_consumption.get_time_diff()
    fuel_values = ts_fuel_consumption.values[:-1]
    energy_in = [diesel_heating_value * float(value) * float(diff) * 10**(-9)
                 for diff, value in zip(time_diffs_fuel, fuel_values)]

    time_diffs_thruster = ts_thruster_power.get_time_diff()
    thruster_values = ts_thruster_power.values[:-1]
    energy_out = [float(diff)*float(value) * 10**(-9) for diff, value in zip(time_diffs_thruster, thruster_values)]

    # TODO: scaling below 0.1 should not be there but is nesessary.
    energy_efficiency = [e_out/e_in * 0.1 for e_out, e_in in zip(energy_out, energy_in)]
    mean = round(sum(energy_efficiency)/len(energy_efficiency), 2)
    ts = TimeSeries(time_stamps, energy_efficiency, f"Energy efficiency from fuel to thrusters. mean:{mean}%", "%")

    figure, ax = get_new_plot()
    ts.plot(ax, title, route)
    save_plot(figure, title, route)
    plt.close()


def cumulative_fuel_consumption(title, route, file_paths):
    file_paths_fuel_consumption = filter_array(file_paths, f.is_engine_fuel_consumption)
    ts_fuel_consumption_ind = [TimeSeries.from_csv(file_path, construct_label(file_path))
                               for file_path in file_paths_fuel_consumption]

    ts_fuel_consumption_ind = [filter_date_time(ts, route) for ts in ts_fuel_consumption_ind]

    ts_fuel_consumption = sum(ts_fuel_consumption_ind)
    ts_fuel_consumption.label = "total fuel consumption"
    time_stamps = ts_fuel_consumption.time_stamps

    fuel_density_diesel = 820

    def to_kg_s(diff, value):
        return float(0.001/3600) * float(value) * float(fuel_density_diesel) * float(diff) * float(10**(-9))

    fuel_rates = [to_kg_s(diff, value) for diff, value
                  in zip(ts_fuel_consumption.get_time_diff(), ts_fuel_consumption.values)]

    ts_fuel_consumption_cumulative = TimeSeries(
        time_stamps[:-1], list(accumulate(fuel_rates)), "Cumulative fuel consumption", "kg")

    figure, ax = get_new_plot()
    ts_fuel_consumption_cumulative.plot(ax, title, route)
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
            # ("Engine boost pressure", f.is_engine_boost_pressure),
            # ("Engine coolant temperature", f.is_engine_coolant_temperature),
            # ("Engine exhaust temperature 1", f.is_engine_exhaust_temperature1),
            # ("Engine exhaust temperature 2", f.is_engine_exhaust_temperature2),
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
            # ("Thruster power", f.is_thruster_load, "W", transform.thruster_load),
            ("Thruster power kW", f.is_thruster_load, "kW", transform.to_thruster_power_kw),

            # ("Engine fuel flow rate", f.is_engine_fuel_consumption, None, None),
            ("Engine fuel flow rate kg per h", f.is_engine_fuel_consumption,
             "kg/h", transform.engine_fuel_consumption_liter_per_h_to_kg_per_h),
            ("Engine fuel flow rate kg per m³", f.is_engine_fuel_consumption,
             "kg/m³", transform.engine_fuel_consumption_liter_per_h_to_kg_per_h),
            # ("Engine power kilowatt", f.is_engine_load, None, None),
            # ("Engine power kW", f.is_engine_load, "kW", None),
            # ("Engine power", f.is_engine_load, "W", transform.engine_load),
            ("Engine power kW", f.is_engine_load, "kW", None),
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
        # emperical data
        energy_efficiency_engine_to_thruster("power efficiency from engines to thrusters", route, file_paths)
        cumulative_fuel_consumption("Cumulative fuel consumption", route, file_paths)
        energy_efficiency_fuel_to_genset("Thermal efficiency from fuel to generator output", route, file_paths)
        # theoretical
        theoretical_total_power_engines("Theoretical engine power", route, file_paths)
        theoretical_fuel_consumption("Theoretical fuel consumption", route, file_paths)
        theoretical_engine_power_efficiency("Theoretical power efficiency", route, file_paths)
        # difference
        difference_engine_load("Difference engine emperical and theoretical", route, file_paths)


if __name__ == "__main__":
    main()
