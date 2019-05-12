
mass_unit = {
    "none": (1.00, "Kg"),
    "kilogram": (1.00, "Kg"),
    "kg": (1.00, "Kg"),
    "gram": (0.001, "gm"),
    "gm": (0.001, "gm"),
    "pound": (0.45359237, "lb"),
    "lb": (0.45359237, "lb"),
    "ounce": (0.028349523, "lb"),
    "oz": (0.028349523, "lb"),
}

len_unit = {
    "none": (1.00, "m"),
    "meter": (1.00, "m"),
    "m": (1.00, "m"),
    "decimeter": (0.10, "dm"),
    "dm": (0.01, "dm"),
    "centimeter": (0.01, "cm"),
    "cm": (0.01, "cm"),
    "millimeter": (0.001, "mm"),
    "mm": (0.001, "mm"),
    "feet": (0.3048, "ft"),
    "foot": (0.3048, "ft"),
    "ft": (0.3048, "ft"),
    "inch": (0.0254, "in"),
    "in": (0.0254, "in"),
}

temp_unit = {
    "none": (1.00, "K"),
    "kelvin": (1.00, "K"),
    "k": (1.00, "K"),
    "farenheit": (1.00, "F"),
    "f": (1.00, "F"),
    "celcius": (1.00, "C"),
    "centigrade": (1.00, "C"),
    "c": (1.00, "C"),
    "rankine": (1.00, "R"),
    "r": (1.00, "R"),
}

press_unit = {
    "none": (1.00, "inHg"),
    "pascals": (1.00, "Pa"),
    "pa": (1.00, "Pa"),
    "inch-mercury": (3386.386725364, "inHg"),
    "inches-mercury": (3386.386725364, "inHg"),
    "ins-hg": (3386.386725364, "inHg"),
    "in-hgs": (3386.386725364, "inHg"),
    "inhg": (3386.386725364, "inHg"),
    "inmercury": (3386.386725364, "inHg"),
    "millimeter": (133.3223120222, "mmHg"),
    "mms-hg": (133.3223120222, "mmHg"),
    "mm-hgs": (133.3223120222, "mmHg"),
    "mms": (133.3223120222, "mmHg"),
    "torrs": (133.3223120222, "mmHg"),
    "millibar": (100.00, "mb"),
    "mbar": (100.00, "mb"),
    "kilopascal": (1000.00, "KPa"),
    "kpa": (1000.00, "KPa"),
    "pounds": (6894.744825494, "PSI"),
    "psi": (6894.744825494, "PSI"),
    "lbs": (6894.744825494, "PSI"),
}

time_unit = {
    "none": (1.00, "sec"),
    "seconds": (1.00, "sec"),
    "sec": (1.00, "sec"),
    "ss": (1.00, "sec"),
    "milliseconds": (0.001, "msec"),
    "msec": (0.001, "msec"),
    "ms": (0.001, "msec"),
    "microsecond": (0.000001, "usec"),
    "usec": (0.000001, "usec"),
    "us": (0.000001, "usec"),
    "minutes": (60.0, "min"),
    "min": (60.0, "min"),
    "hours": (3600.0, "hr"),
    "hr": (3600.0, "hr"),
}

angle_unit = {
    "none": (1.00, "rad"),
    "radians": (1.00, "rad"),
    "rads": (1.00, "rad"),
    "rad": (1.00, "rad"),
    "degrees": (0.01745329251994, "deg"),
    "degs": (0.01745329251994, "deg"),
    "deg": (0.01745329251994, "deg"),
    "gradians": (0.01570796326795, "grad"),
    "grads": (0.01570796326795, "grad")
}


units_error_tab = [
    "no error",
    "unknown unit type",
    "unknown unit tag",
]


def get_unit(unit_type, unit):
    """ look up unit params """
    if unit_type == "temp":
        return temp_unit[unit.lower()]
    elif unit_type == "mass":
        return mass_unit[unit.lower()]
    elif unit_type == "length":
        return len_unit[unit.lower()]
    elif unit_type == "time":
        return time_unit[unit.lower()]
    elif unit_type == "press":
        return press_unit[unit.lower()]
    elif unit_type == "angle":
        return angle_unit[unit.lower()]
    else:
        return 1.0, None


def conv_unit(unit_type, val, in_unit, out_unit=None):
    
    factor, unit = get_unit(unit_type, in_unit)
    if unit_type == 'temp':
        if unit == "C":
            number = 273.15 + val
        elif unit == 'F':
            number = 273.15 + (val - 32.0) * 5 / 9
        elif unit == 'R':
            number = val * 5 / 9
    else:
        number = val * factor

    if out_unit:
        factor, unit = get_unit(unit_type, out_unit)
        if unit_type == "temp":
            if unit == "C":
                number = number - 273.15
            elif unit == "F":
                number = (number - 273.15) * 9 / 5 + 32.0
            elif unit == "R":
                number = number * 9 / 5
        else:
            if factor == 0:
                number = 0
            else:
                number /= factor

    return number


def unit_label(unit_type, unit):
    try:
        rec = get_unit(unit_type, unit)
    except KeyError as ex:
        if unit.endswith('s'):
            rec = get_unit(unit_type, unit[:-1])

    if rec:
        return rec[1]
    else:
        return ""


def main():
    print(unit_label("time", "secs"))
    print(unit_label("temp", "celsius"))
    print(unit_label("length", "feet"))
    print(unit_label("mass", "lbs"))

    print()
    print(conv_unit("time", 10, "sec"))
    print(conv_unit("time", 10, "hr"))
        
    
if __name__ == "__main__":
    main()
