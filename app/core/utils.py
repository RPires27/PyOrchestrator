import pytz

def get_timezones():
    # Return a sorted list of common timezones
    # You can filter this list if you want to provide a smaller, more curated selection
    return sorted(pytz.all_timezones)
