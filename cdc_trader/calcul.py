from decimal import Decimal, ROUND_CEILING,ROUND_FLOOR


def calculate_percentage_return(initial_quantity, final_quantity):
    return (final_quantity - initial_quantity) / abs(initial_quantity) * 100


def ceil_with_decimals(value:float, num_decimals:int)->float:
    precision = 10**num_decimals
    value_decimal = Decimal(str(value))

    # Perform the necessary operations
    value_decimal *= Decimal(precision)
    value_decimal = value_decimal.to_integral_value(rounding=ROUND_CEILING)
    value_decimal /= Decimal(precision)

    # Convert back to float if needed
    value = float(value_decimal)
    return value

def floor_with_decimals(value:float, num_decimals:int)->float:
    precision = 10**num_decimals
    value_decimal = Decimal(str(value))

    # Perform the necessary operations
    value_decimal *= Decimal(precision)
    value_decimal = value_decimal.to_integral_value(rounding=ROUND_FLOOR)
    value_decimal /= Decimal(precision)

    # Convert back to float if needed
    value = float(value_decimal)
    return value