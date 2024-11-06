import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timezone
from typing import Self
import warnings


class TimeSeries:
    def __init__(self, time_stamps: list[datetime], values: list[float], label: str, unit: str):
        self.time_stamps = np.array(time_stamps, dtype='datetime64[ns]')
        self.values = np.array(values, dtype=float)
        self.label = label
        self.unit = unit

    @classmethod
    def from_csv(cls, file_path: str, label: str) -> Self:
        unit = None
        time_stamps = []
        values = []
        for line in open(file_path).readlines():
            match line.split(","):
                case [date_time_raw, value_raw, unit_raw]:
                    if unit is None:
                        unit = unit_raw.strip()
                    ts = datetime.fromisoformat(date_time_raw.strip()).astimezone(timezone.utc).replace(tzinfo=None)
                    time_stamps.append(ts)
                    values.append(float(value_raw.strip()))
                case _:
                    raise ValueError("cannot deserialize line", line)
        return cls(time_stamps, values, label, unit)

    def interpolate(self, other: Self) -> None:
        all_times = np.unique(np.concatenate((self.time_stamps, other.time_stamps)))
        interpolated_self_values = np.interp(all_times.astype('datetime64[s]').astype(np.float64),
                                             self.time_stamps.astype('datetime64[s]').astype(np.float64),
                                             self.values)
        interpolated_other_values = np.interp(all_times.astype('datetime64[s]').astype(np.float64),
                                              other.time_stamps.astype('datetime64[s]').astype(np.float64),
                                              other.values)
        self.time_stamps = all_times
        self.values = interpolated_self_values
        other.time_stamps = all_times
        other.values = interpolated_other_values

    def __add__(self, other: Self) -> Self:
        if self.label is None:
            raise ValueError("current instance is missing a label")
        if self.unit != other.unit:
            raise ValueError(f"Cannot add TimeSeries with different units: {self.unit} and {other.unit}")
        self.interpolate(other)
        return TimeSeries(self.time_stamps, self.values + other.values, self.label, self.unit)

    def __sub__(self, other: Self) -> Self:
        if self.label is None:
            raise ValueError("current instance is missing a label")
        if self.unit != other.unit:
            raise ValueError(f"Cannot subtract TimeSeries with different units: {self.unit} and {other.unit}")
        self.interpolate(other)
        return TimeSeries(self.time_stamps, self.values - other.values, self.label, self.unit)

    def __mul__(self, other: Self | int) -> Self:
        if self.label is None:
            raise ValueError("current instance is missing a label")
        # if self.unit != other.unit:
        #     raise ValueError(f"Cannot multiply TimeSeries with different units: {self.unit} and {other.unit}")
        if other is Self:
            self.interpolate(other)
            return TimeSeries(self.time_stamps, self.values * other.values, self.label, self.unit)
        values = [value for value in self.values]
        return TimeSeries(self.label, values, self.label, "")


#    def __truediv__(self, other: Self) -> Self:
#        if self.label is None:
#            raise ValueError("current instance is missing a label")
#        for index, value in enumerate(other.values):
#            if value == 0:
#                other.time_stamps = np.delete(other.time_stamps, index)
#                other.values = np.delete(other.values, index)
#
#        self.interpolate(other)
#        return TimeSeries(self.time_stamps, self.values / other.values, self.label, "")

    def __repr__(self) -> str:
        if self.label is None:
            raise ValueError("current instance is missing a label")
        return f"TimeSeries(label={self.label}, unit={self.unit}, length={len(self.time_stamps)})"

    def __radd__(self, other: float) -> Self:
        if self.label is None:
            raise ValueError("current instance is missing a label")
        if isinstance(other, (int, float)) and other == 0:
            return TimeSeries(self.time_stamps.astype('datetime64[ns]').tolist(), self.values.tolist(), self.label, self.unit)
        return NotImplemented

    def __iter__(self):
        return zip(self.time_stamps, self.values)

    def transform(self, transformer, new_unit: str, other: Self = None) -> Self:
        transformed_values = []
        if other is None:
            transformed_values = [transformer(value) for value in self.values]
        else:
            self.interpolate(other)
            transformed_values = [transformer(value, other) for value in self.values]
        return TimeSeries(self.time_stamps, transformed_values, self.label, new_unit)

    def plot(self, axes: plt.Axes, label: str = None) -> None:
        label = label or self.label
        axes.plot(self.time_stamps, self.values, label=label)

    def filter_date(self, date_time_start: datetime, date_time_end: datetime) -> Self:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            filtered_data = [(time, value) for (time, value) in self
                             if np.datetime64(date_time_start) <= time <= np.datetime64(date_time_end)]

        if not filtered_data:
            return TimeSeries([], [], self.label, self.unit)

        filtered_timestamps, filtered_values = zip(*filtered_data)
        return TimeSeries(list(filtered_timestamps), list(filtered_values), self.label, self.unit)


