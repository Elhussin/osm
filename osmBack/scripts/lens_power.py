LENS_POWERS = [(f"{x:+.2f}", f"{x:+.2f}") for x in [i / 4 for i in range(-120, 121)]]

spherical_lens_powersMunis = [(f"-{abs(x):05.2f}", f"-{abs(x):05.2f}") for x in [i / 4 for i in range(-120, 1)]]
spherical_lens_powersPlus = [(f"+{abs(x):05.2f}", f"+{abs(x):05.2f}") for x in [i / 4 for i in range(1, 121)]]
cylinder_lens_powers = [(f"-{abs(x):05.2f}", f"-{abs(x):05.2f}") for x in [i / 4 for i in range(-60, 1)]]
additional_lens_powers = [(f"+{abs(x):05.2f}", f"+{abs(x):05.2f}") for x in [i / 4 for i in range(1, 25)]]

# دمج الموجب والسالب للـ spherical
spherical_lens_powers = spherical_lens_powersMunis + spherical_lens_powersPlus



def format_decimal(value, width=6, decimals=2):
    if value is None:
        return "—"
    return f"{(value):+0{width}.{decimals}f}"

# print(format_decimal(1.456))
# print(format_decimal(-15.456))
