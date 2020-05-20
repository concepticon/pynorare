def integer(number):
    if isinstance(number, str):
        if number in ['NAN', 'NA', 'NaN']:
            return number
        elif number.isdigit():
            number = float(number)
    return '{0:.0f}'.format(number)

def string(text):
    return str(text)

def types():
    return {
            'string': str,
            'integer': integer,
            'float': lambda x: '{0:.4f}'.format(float(x)) if (x and x not in ['NAN','NA','NaN']) else x
            }


