""" replaces datetime """

#  import datetime
from browser import window

# ref is 1/3/2000 0h0m:0s
MY_EPOCH_YEAR = 2000
MY_EPOCH = 951868800


FOUR_YEARS_DURATION_DAYS = 4 * 365 + 1
FOUR_YEARS_DURATION_SECONDS = FOUR_YEARS_DURATION_DAYS * 24 * 60 * 60

LATEST_SECONDS = MY_EPOCH + 100 * FOUR_YEARS_DURATION_SECONDS - 1
LATEST_YEAR = MY_EPOCH_YEAR + 399

#           Mar Ap  May Jun Jul Au  Se  Oc  No  De  Ja  Fe
CALENDAR = [31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31, 28]


def totimestamp(dt_year, dt_month, dt_day, dt_hour, dt_min, dt_sec):
    """ totimestamp """

    # convert
    dt_month -= 3
    if dt_month < 0:
        dt_month += 12
        dt_year -= 1

    # check input
    assert MY_EPOCH_YEAR <= dt_year <= LATEST_YEAR

    # add time_stamps

    time_stamp = MY_EPOCH

    four_years_era = (dt_year - MY_EPOCH_YEAR) // 4
    time_stamp += four_years_era * FOUR_YEARS_DURATION_SECONDS

    year_in_era = (dt_year - MY_EPOCH_YEAR) % 4
    time_stamp += year_in_era * 365 * 24 * 60 * 60

    month = 0
    while True:

        if month >= dt_month:
            break

        time_stamp += CALENDAR[month] * 24 * 60 * 60
        month += 1

    dt_day -= 1
    time_stamp += dt_day * 24 * 60 * 60
    time_stamp += dt_hour * 60 * 60
    time_stamp += dt_min * 60
    time_stamp += dt_sec

    return time_stamp


def fromtimestamp(time_stamp):
    """ fromtimestamp """

    # check input
    assert MY_EPOCH <= time_stamp <= LATEST_SECONDS

    # convert
    rel_time_stamp = int(time_stamp) - MY_EPOCH

    # secs in day

    # calc
    secs_in_day = rel_time_stamp % 86400

    # format
    dt_sec = secs_in_day % 60
    dt_min = (secs_in_day // 60) % 60
    dt_hour = (secs_in_day // 60) // 60

    # day in time

    # calc
    days_in_date = rel_time_stamp // 86400

    four_years_era = days_in_date // FOUR_YEARS_DURATION_DAYS
    days_in_four_years = days_in_date % FOUR_YEARS_DURATION_DAYS

    year_in_four_years = days_in_four_years // 365
    days_in_year = days_in_four_years - 365 * year_in_four_years
    if year_in_four_years == 4:
        year_in_four_years -= 1
        days_in_year += 365

    dt_month = 0
    dt_day = days_in_year
    while True:
        days_in_month = CALENDAR[dt_month] + (1 if year_in_four_years == 3 and dt_month == 11 else 0)
        if dt_day < days_in_month:
            break
        dt_day -= days_in_month
        dt_month += 1

    # format
    dt_year = MY_EPOCH_YEAR + 4 * four_years_era + year_in_four_years
    dt_month += 3
    if dt_month > 12:
        dt_month -= 12
        dt_year += 1
    dt_day += 1

    # local time

    # Javascript Date constructor
    date = window.Date.new
    delta = date(time_stamp*1000).getTimezoneOffset() * 60

    rel_time_stamp_loc = rel_time_stamp - delta
    secs_in_day_local = rel_time_stamp_loc % 86400

    # format
    loc_min = (secs_in_day_local // 60) % 60
    loc_hour = (secs_in_day_local // 60) // 60

    return dt_year, dt_month, dt_day, dt_hour, dt_min, dt_sec, loc_hour, loc_min


def strftime(dt_year, dt_month, dt_day, dt_hour, dt_min, dt_sec, loc_hour, loc_min, year_first=False, day_only=False):
    """ strftime """

    if year_first:
        if day_only:
            return f"{dt_year:04}-{dt_month:02}-{dt_day:02} GMT ({loc_hour:02}:{loc_min:02})"
        return f"{dt_year:04}-{dt_month:02}-{dt_day:02} {dt_hour:02}:{dt_min:02}:{dt_sec:02} GMT ({loc_hour:02}:{loc_min:02})"
    if day_only:
        return f"{dt_day:02}-{dt_month:02}-{dt_year:04} GMT ({loc_hour:02}:{loc_min:02})"
    return f"{dt_day:02}-{dt_month:02}-{dt_year:04} {dt_hour:02}:{dt_min:02}:{dt_sec:02} GMT ({loc_hour:02}:{loc_min:02})"
