def transform_value(time_series, transformer):
    new_time_series = {}
    for label, (time, values) in time_series.items():
        new_time_series[label] = (time, [transformer(value) for value in values])

    return new_time_series


def specific_fuel_consumption(fuel_mass_flow, power):
    return fuel_mass_flow / power


def power_efficiency(propulsion_power, load_feedback):
    return propulsion_power / load_feedback


def thruster_load(thruster_load_percent):
    # max thruster power is 500kW. transform percent to SI unit
    return thruster_load_percent * 5e3


def engine_load(engine_load_kw):
    # engine load is recorded in kW. transform to SI unit
    return engine_load_kw * 1e3


def engine_power_to_total_load(engine_load_kw):
    number_of_engines = 2
    max_power_engine = 450e3
    return engine_load_kw / (number_of_engines * max_power_engine) * 100


def from_percent_to_fraction(value):
    return value / 100


def km_h_to_m_s(vessel_sog):
    return vessel_sog * 60 / 1000


# input: 0-100 
# output: 0-100
def engine_efficiency_emperical(engine_power_percent):
    return -0.0024 * engine_power_percent**2 + 0.402 * engine_power_percent + 27.4382


def engine_power_efficiency_emperical_to_thruster(engine_efficiency):
    synchronous_generator_efficency = 0.96
    frequency_converter_efficiency = 0.97
    switchboard_efficiency = 0.99
    propulsion_motor_efficiency = 0.97
    return engine_efficiency * synchronous_generator_efficency * frequency_converter_efficiency * switchboard_efficiency * propulsion_motor_efficiency


def engine_fuel_consumption_liter_per_h_to_kg_per_h(fuel_flow):
    DENCITY_DIESEL = 820
    LITER_TO_M3_PER_H = 0.001
    return fuel_flow * LITER_TO_M3_PER_H * DENCITY_DIESEL


# value is the engine power in kw divided by fuel flow rate in liters per hour
# returns caclulated thermal efficiency in percent
def engine_thermal_efficiency(value):
    to_percent = 100
    return value * ((36e3) / (820 * 454) * to_percent)


def bmep(power_diesel_engine):
    displaced_volume = 0.001
    number_of_cylinders = 8
    revolutions_per_stroke = 1

    return (power_diesel_engine * revolutions_per_stroke) / (displaced_volume * number_of_cylinders)
