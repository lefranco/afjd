#!/usr/bin/env python3

""" tu """


import time
import datetime
import argparse
import sys
import typing

SPEED_MOVES = 48
SPEED_RETREATS = 24
SPEED_ADJUSTMENTS = 24

CURRENT_ADVANCEMENT = 5


class Game:
    """ Class for handling a game """

    def __init__(self, archive: bool, fast: bool, play_weekend: bool, deadline_sync: bool, deadline_hour: int):

        self._archive = archive
        self._fast = fast
        self._play_weekend = play_weekend
        self._deadline_sync = deadline_sync
        self._deadline_hour = deadline_hour

        self._speed_moves = SPEED_MOVES
        self._speed_retreats = SPEED_RETREATS
        self._speed_adjustments = SPEED_ADJUSTMENTS

        self._current_advancement = CURRENT_ADVANCEMENT

        self._deadline = 0

    def push_deadline(self, forced_timestamp: typing.Optional[float] = None) -> None:
        """ push_deadline """

        # do not touch deadline if game is archive
        if self._archive:
            return

        # set start deadline from where we start

        if forced_timestamp is not None:
            now = forced_timestamp
            print(f"Forcing time now as {datetime.datetime.fromtimestamp(now, datetime.timezone.utc)} GMT")
        else:
            now = time.time()

        if self._fast:
            # round it to next minute
            self._deadline = (int(now) // 60) * 60 + 60
            # increment is one minute
            deadline_increment = 60
        else:
            # round it to next hour
            self._deadline = (int(now) // 3600) * 3600 + 3600
            # increment is one hour
            deadline_increment = 3600

        print(f"Step 1 : after rounding deadline is {datetime.datetime.fromtimestamp(self._deadline, datetime.timezone.utc)} GMT")

        # increment deadline

        # what is the season next to play ?
        if self._current_advancement % 5 in [0, 2]:
            hours_or_minute_add = self._speed_moves
            print("Next is move")
        elif self._current_advancement % 5 in [1, 3]:
            hours_or_minute_add = self._speed_retreats
            print("Next is retreat")
        else:
            hours_or_minute_add = self._speed_adjustments
            print("Next is adj")

        # increment deadline
        self._deadline += hours_or_minute_add * deadline_increment

        print(f"Step 2 after increment : deadline is {datetime.datetime.fromtimestamp(self._deadline, datetime.timezone.utc)} GMT")

        # if fast we are done
        if self._fast:
            return

        # pass the week end if applicable
        if not self._play_weekend:

            print("applying avoid weekend")

            # keep passing a day until out of week end
            while True:

                # extract deadline to datetime
                datetime_deadline_extracted = datetime.datetime.fromtimestamp(self._deadline, datetime.timezone.utc)

                # datetime to date
                deadline_day = datetime_deadline_extracted.date()

                # accept if we are out of the weekend
                if not deadline_day.weekday() in [5, 6]:
                    break

                # pass a day
                self._deadline += 24 * 3600
                print("pushed one day through week end")

        print(f"Step 3 : after avoiding weekends : deadline is {datetime.datetime.fromtimestamp(self._deadline, datetime.timezone.utc)} GMT")

        # eventually sync the deadline to the proper hour of a day
        if self._deadline_sync:

            # time in day of deadline so far
            current_deadline_time_in_day = int(self._deadline) % (24 * 3600)

            # time in day of deadline wished
            wished_deadline_time_in_day = self._deadline_hour * 3600

            print(f"{current_deadline_time_in_day=} {wished_deadline_time_in_day=}")

            # increment or decrement (depending on which is later)
            if wished_deadline_time_in_day > current_deadline_time_in_day:
                # expected deadline time is later in day :  we set our deadline accordingly
                self._deadline += wished_deadline_time_in_day - current_deadline_time_in_day
                print("option A")
            elif wished_deadline_time_in_day < current_deadline_time_in_day:
                # expected deadline time is earlier in day :  we set our deadline next day
                self._deadline += 24 * 3600 + wished_deadline_time_in_day - current_deadline_time_in_day
                print("option B")

        print(f"Step 4 : after setting to sync : deadline is {datetime.datetime.fromtimestamp(self._deadline, datetime.timezone.utc)}")

    def show_deadline(self) -> None:
        """ show_deadline """
        datetime_deadline_extracted = datetime.datetime.fromtimestamp(self._deadline, datetime.timezone.utc)
        print(f"deadline is {datetime_deadline_extracted}")

    def __str__(self) -> str:
        return f"archive={self._archive} fast={self._fast} play_weekend={self._play_weekend} deadline_sync={self._deadline_sync} deadline_hour={self._deadline_hour}"


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--now", required=True, type=lambda d: datetime.datetime.strptime(d, '%Y%m%d%H%M%z'), help="Date in the format yyyymmddHHMM+0100 (+0200 in summer)")
    parser.add_argument('-a', '--archive', required=False, action="store_true", help='Game is archive')
    parser.add_argument('-f', '--fast', required=False, action="store_true", help='Game is fast')
    parser.add_argument('-w', '--play_weekend', required=False, action="store_true", help='Game plays weekends')
    parser.add_argument('-S', '--deadline_sync', required=False, action="store_true", help='Game wants deadline sync.')
    parser.add_argument('-H', '--deadline_hour', required=False, type=int, default=0, help='Game wants deadline sync at this time')
    args = parser.parse_args()

    print(f"Using time now as {args.now}")

    if not 0 <= args.deadline_hour <= 23:
        print("Please revise deadline hour")
        sys.exit(1)

    game = Game(args.archive, args.fast, args.play_weekend, args.deadline_sync, args.deadline_hour)
    print(game)

    forced_timestamp = args.now.timestamp()
    game.push_deadline(forced_timestamp)

    print("After : ", end='')
    game.show_deadline()


if __name__ == '__main__':
    main()