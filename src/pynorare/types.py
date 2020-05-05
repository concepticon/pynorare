def integer(number):
    return '{0:.0f}'.format(number)

def string(text):
    return str(text)

def types():
    return {
            'string': str,
            'integer': lambda x: '{0:.0f}'.format(x) if x else x,
            'float': lambda x: '{0:.4f}'.format(float(x)) if x else x
            }


