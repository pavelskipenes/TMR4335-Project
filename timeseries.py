import numpy as np
import datetime
from typing import Self


class TimeSeries:
    def __init__(self, timestamps: list, values: list, label: str, unit: str):
        self.timestamps = np.array(timestamps)
        self.values = np.array(values)
        self.label = label
        self.unit = unit

    @classmethod
    def from_file(cls, file, label, unit) -> Self:
        unit = None
        timestamps = []
        values = []
        for line in file.readlines():
            match line.split(","):
                case [datetime_raw, value_raw, unit_raw]:
                    if unit is None:
                        unit = unit_raw.strip()
                    timestamps.append(datetime.fromisoformat(datetime_raw.strip()))
                    values.append(float(value_raw.strip()))
                case _:
                    raise ValueError("cannot deserialize line", line)
        return cls(timestamps, values, label, unit)

    def interpolate(self, new_timestamps):
        interpolated_values = np.interp(new_timestamps, self.timestamps, self.values)
        return TimeSeries(new_timestamps, interpolated_values)

    def __add__(self, other):
        # Interpolate both to a common time grid
        all_times = np.unique(np.concatenate((self.timestamps, other.timestamps)))
        interpolated_self = self.interpolate(all_times)
        interpolated_other = other.interpolate(all_times)

        return TimeSeries(all_times, interpolated_self.values + interpolated_other.values)

    def __mul__(self, other):
        # interpolate both to a common time grid
        all_times = np.unique(np.concatenate((self.timestamps, other.timestamps)))
        interpolated_self = self.interpolate(all_times)
        interpolated_other = other.interpolate(all_times)

        return TimeSeries(all_times, interpolated_self.values * interpolated_other.values)

    def transform(self, transformer):
        self.values = [transformer(value) for value in self.values]
