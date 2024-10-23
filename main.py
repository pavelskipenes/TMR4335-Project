from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt


def plot(x: list, y: list, title: str, label: str, clear: bool = True):
    plt.plot(x, y, label=label)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.title(title)
    plt.legend()
    plt.plot()
    plt.savefig("plots/" + label.replace(".csv", ".svg"))
    if clear:
        plt.clf()


def extract_data(file_path: str):
    with open(file_path) as file:
        unit = ""
        time = []
        value = []
        for line in file.readlines():
            elements = line.split(",")
            if len(unit) == 0:
                unit = elements[2]
            time.append(datetime.fromisoformat(elements[0]))
            value.append(round(float(elements[1]), 2))
        return time, value, unit


def is_engine(file_path: str) -> bool:
    return "Engine" in str(file_path)


def is_thruster(file_path: str) -> bool:
    return "hcx" in str(file_path)


def extract_label(file_path):
    return " ".join(file_path.parts[-2:])


def is_engine_load(file_path):
    return "engine_load" in str(file_path)


def transform_time():
    pass


def is_engine2(file_path: str) -> bool:
    return "Engine2" in str(file_path)


def main():
    file_paths = Path("gunnerus").glob("**/*.csv")
    filtered_file_paths = [file_path for file_path in file_paths if is_engine(file_path) and is_engine_load(file_path)]

    all_data = {}

    for file_path in filtered_file_paths:
        if is_engine2(file_path):
            continue
        label = extract_label(file_path)
        time, data, unit = extract_data(file_path)
        plot(time, data, "Individual Engine Loads", label, False)

        for t, d in zip(time, data):
            all_data[t] = all_data.get(t, 0) + d

    all_time = sorted(all_data.keys())
    all_sum = [all_data[t] for t in all_time]

    plot(all_time, all_sum, "Total Engine Load", "Total Load", False)


if __name__ == "__main__":
    main()
