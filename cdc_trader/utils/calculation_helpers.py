from decimal import Decimal, ROUND_CEILING,ROUND_FLOOR


def calculate_percentage_return(initial_quantity, final_quantity):
    return (final_quantity - initial_quantity) / abs(initial_quantity) * 100


def ceil_with_decimals(value: float, num_decimals: int) -> float:
    precision = 10**num_decimals
    value_decimal = Decimal(str(value))

    # Perform the necessary operations
    value_decimal *= Decimal(precision)
    value_decimal = value_decimal.to_integral_value(rounding=ROUND_CEILING)
    value_decimal /= Decimal(precision)

    # Check if the result has null decimal values
    if value_decimal % 1 == 0:
        return int(value_decimal)
    else:
        return float(value_decimal)

def floor_with_decimals(value: float, num_decimals: int) -> float:
    precision = 10**num_decimals
    value_decimal = Decimal(str(value))

    # Perform the necessary operations
    value_decimal *= precision
    value_decimal = value_decimal.to_integral_value(rounding=ROUND_FLOOR)
    value_decimal /= Decimal(precision)

    # Check if the result has null decimal values
    if value_decimal % 1 == 0:
        return int(value_decimal)
    else:
        return float(value_decimal)


# def count_decimal_places(number):
#     decimal_number = Decimal(str(number))
#     return abs(decimal_number.as_tuple().exponent)

def count_decimal_places(min_quantity):
    # Convert the minimum quantity to a string to handle scientific notation
    min_quantity_str = str(min_quantity)

    # Remove trailing zeros after the decimal point
    min_quantity_str = min_quantity_str.rstrip('0')

    # Find the position of the decimal point
    decimal_position = min_quantity_str.find('.')

    # Count the number of decimal places
    if decimal_position == -1:
        return 0
    else:
        return len(min_quantity_str) - decimal_position - 1

