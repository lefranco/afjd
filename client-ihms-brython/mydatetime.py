
import time
import datetime

# ref is 1/3/2000 0h0m:0s
MY_EPOCH_YEAR = 2000
MY_EPOCH = 951868800


LATEST = MY_EPOCH + 400 * 365 * 24 * 60 * 60
FOUR_YEARS_DURATION = 4 * 365 + 1
          # Mar Ap  May Jun Jul Au  Se  Oc  No  De  Ja  Fe
CALENDAR = [31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31, 28]

def fromtimestamp(time_stamp):

    # check input
    assert MY_EPOCH <= time_stamp <= LATEST

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

    four_years_era = days_in_date // FOUR_YEARS_DURATION
    days_in_four_years = days_in_date % FOUR_YEARS_DURATION

    year_in_four_years = days_in_four_years // 365
    days_in_year = days_in_four_years - 365 * year_in_four_years
    if year_in_four_years == 4:
        year_in_four_years -= 1
        days_in_year += 365

    dt_month = 0
    dt_day = days_in_year
    while True:
        days_in_month =  CALENDAR[dt_month] + (1 if year_in_four_years == 3 and dt_month == 11 else 0)
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

    return dt_year, dt_month, dt_day, dt_hour, dt_min, dt_sec

def strftime(dt_year, dt_month, dt_day, dt_hour, dt_min, dt_sec):
    return f"{dt_day:02}-{dt_month:02}-{dt_year:04} {dt_hour:02}:{dt_min:02}:{dt_sec:02} GMT"

def check_time_stamp(timestamp):

    date_now_gmt = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
    date_now_gmt_str_ref = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")

    dt_year, dt_month, dt_day, dt_hour, dt_min, dt_sec = fromtimestamp(timestamp)
    date_now_gmt_str_retr = strftime(dt_year, dt_month, dt_day, dt_hour, dt_min, dt_sec)

    assert date_now_gmt_str_retr == date_now_gmt_str_ref, f"Error for {timestamp}  yield {date_now_gmt_str_retr=} but {date_now_gmt_str_ref=}"


def main():


    #check_time_stamp(1078012800)
    #return

    timestamp = MY_EPOCH
    before = 0

    while True:

        check_time_stamp(timestamp)
        timestamp += 100

        disp = 10000000

        if timestamp // disp != before:
            date_now_gmt = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
            date_now_gmt_str_ref = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
            print(date_now_gmt_str_ref)
            before = timestamp // disp


if __name__ == '__main__':
    main()


