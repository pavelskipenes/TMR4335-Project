def is_engine2(file_path: str) -> bool:
    return "Engine2" in str(file_path)


def get_engine_id(file_path):
    "data/gunnerus/RVG_mqtt/Engine1"
    return int(str(file_path)[29])

# exclude plotting engine 2 which was not being used


def is_engine(file_path: str) -> bool:
    return "Engine" in str(file_path) and not is_engine2(file_path)


def is_thruster(file_path: str) -> bool:
    return "hcx" in str(file_path)


def is_thruster_load(file_path):
    return "LoadFeedback" in str(file_path) and is_thruster(file_path)


def is_thruster_rpm(file_path):
    return "RPMFeedback" in str(file_path) and is_thruster(file_path)


def is_engine_load(file_path):
    return "engine_load" in str(file_path) and is_engine(file_path)


def is_engine_speed(file_path):
    return "engine_speed" in str(file_path) and is_engine(file_path)


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


def is_vessel_speed_over_ground(file_path):
    return "SpeedKmHr" in str(file_path)
