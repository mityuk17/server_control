import dateutil.parser as dparser


def transform_time(time_str):
    time = dparser.parse(time_str, fuzzy=True)
    return time.strftime('%d.%m.%Y %H:%M:%S')