from pathlib import Path
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import filter as f
from timeseries import TimeSeries
import transform


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
            return f"engine {index} load"
        case _:
            raise NotImplementedError(f"{source}")


def get_thruster_label(side: str, source: str) -> str:
    match source:
        case 'RPMFeedback.csv':
            return f"thruster {side} RPM feedback"
        case 'LoadFeedback.csv':
            return f"thruster {side} load feedback"
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


def read_and_plot(title, file_paths, filter, date_time_start, date_time_end, sum_plots=False, new_unit: str = None, transformer=None):
    filtered_file_paths = [file_path for file_path in file_paths if filter(file_path)]

    time_series = [TimeSeries.from_csv(file_path, label=construct_label(file_path))
                   for file_path in filtered_file_paths]

    if date_time_start is not None and date_time_end is not None:
        time_series = [ts.filter_date(date_time_start, date_time_end) for ts in time_series]

    if transformer is not None:
        time_series = [time_serie.transform(transformer, new_unit) for time_serie in time_series]

    unit = time_series[0].unit

    figure, ax = plt.subplots(figsize=(30, 18))

    if unit != "%":
        ax.ticklabel_format(axis='y', style='sci', scilimits=(1, 0))

    ax.tick_params(axis='x', rotation=45)
    ax.locator_params(axis='y', nbins=40)
    ax.set_ylabel(unit)
    ax.set_xlabel("Time")
    ax.set_title(title)
    ax.grid(True)

    for ts in time_series:
        ts.plot(ax)

    if sum_plots:
        summed_series = sum(time_series)
        summed_series.label = f"{title.lower()} total"
        summed_series.plot(ax)

    ax.legend()
    figure.tight_layout()
    figure.savefig(f"plots/{title}.svg")
    figure.clf()


def main():
    file_paths = list(Path("data/gunnerus/").glob("**/*.csv"))

    # TODO: find date time range (route) for:
    # thruster rpm control
    # thruster load control
    # idle / no speed
    # TODO: subtract engine load and thurster load to get idealized hotel load assumed to be constant
    # TODO: plot shit separated by routes
    # TODO: plot map data using the same routes

    date_time_start = datetime(2024, 9, 10, 6, 30, tzinfo=timezone.utc)
    routes = [
        ("thruster load control", datetime(2024, 9, 10, 6, 40, tzinfo=timezone.utc),
         datetime(2024, 9, 10, 6, 57, tzinfo=timezone.utc)),
        ("thruster rpm control", datetime(2024, 9, 10, 6, 57, tzinfo=timezone.utc),
         datetime(2024, 9, 10, 7, 5, 45, tzinfo=timezone.utc)),
    ]

    date_time_end = datetime(2024, 9, 10, 7, 44, tzinfo=timezone.utc)

    single_plot_args = [
        ("Thruster load rpm", f.is_thruster_rpm),
        ("Thruster load percent", f.is_thruster_load),

        ("Engine speed", f.is_engine_speed),
        ("Engine boost pressure", f.is_engine_boost_pressure),
        ("Engine coolant temperature", f.is_engine_coolant_temperature),
        ("Engine exhaust temperature 1", f.is_engine_exhaust_temperature1),
        ("Engine exhaust temperature 2", f.is_engine_exhaust_temperature2),
        ("Engine fuel consumption", f.is_engine_fuel_consumption),
        # ("", ),
    ]

    sum_plot_args = [
        ("Thruster load watt", f.is_thruster_rpm, "W", transform.thruster_load),

        ("Engine fuel consumption", f.is_engine_fuel_consumption, None, None),
        ("Engine load", f.is_engine_load, None, None),
        ("Engine load watt", f.is_engine_load, "W", transform.engine_load),
        # ("", ),
    ]

    for title, filter in single_plot_args:
        read_and_plot(
            title=title,
            file_paths=file_paths,
            filter=filter,
            date_time_start=date_time_start,
            date_time_end=date_time_end,
            sum_plots=False,
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
            sum_plots=True,
            new_unit=new_unit,
            transformer=transformer,
        )
        read_and_plot(
            title="Speed over ground (SOG)",
            file_paths=file_paths,
            filter=f.is_vessel_speed_over_ground,
            date_time_start=date_time_start,
            date_time_end=date_time_end,
            sum_plots=False,
            new_unit="m/s",
            transformer=transform.km_h_to_m_s,
        )

        return


if __name__ == "__main__":
    main()
