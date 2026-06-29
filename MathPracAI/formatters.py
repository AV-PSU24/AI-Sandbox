def signed(value):
    return f"- {abs(value)}" if value < 0 else f"+ {value}"


def superscript_number(value):
    digits = str(value)
    superscripts = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
    return digits.translate(superscripts)


def polynomial_term(coefficient, exponent, is_first):
    sign = "-" if coefficient < 0 else "+"
    absolute = abs(coefficient)

    if exponent == 0:
        body = str(absolute)
    elif exponent == 1:
        body = "x" if absolute == 1 else f"{absolute}x"
    else:
        body = f"x{superscript_number(exponent)}" if absolute == 1 else f"{absolute}x{superscript_number(exponent)}"

    if is_first:
        return f"-{body}" if sign == "-" else body
    return f" {sign} {body}"


def format_function_equation(coefficients):
    degree = len(coefficients) - 1
    terms = []
    for index, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        terms.append(polynomial_term(coefficient, degree - index, not terms))
    return f"f(x) = {''.join(terms) if terms else '0'}"


def format_function_substitution(coefficients, x):
    degree = len(coefficients) - 1
    pieces = []
    for index, coefficient in enumerate(coefficients):
        exponent = degree - index
        if coefficient == 0:
            continue

        absolute = abs(coefficient)
        if exponent == 0:
            body = str(absolute)
        elif exponent == 1:
            body = f"{absolute}({x})"
        else:
            body = f"{absolute}({x}){superscript_number(exponent)}"

        if not pieces:
            pieces.append(f"-{body}" if coefficient < 0 else body)
        else:
            pieces.append(f" {'-' if coefficient < 0 else '+'} {body}")
    return "".join(pieces) if pieces else "0"
