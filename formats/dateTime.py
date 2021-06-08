from datetime import datetime as dt

def datetime_format(datetime_arg) -> str:
    return dt.strftime(datetime_arg, "%Y-%m-%d %H:%M:%S")