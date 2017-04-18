#!/usr/bin/env python3

import argparse
import datetime

from sensors.simulator.sample import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simulate a sensor')
    parser.add_argument('-d', '--startdate', nargs=5, type=int,
                        default=[2017, 1, 1, 0, 0],
                        help='Start date for data: YYYY MM DD HH MM')
    parser.add_argument('-i', '--dateint', type=int,
                        default=1,
                        help='Number of minutes between subsequent data')
    args = parser.parse_args()

    start_date = datetime.datetime(year=args.startdate[0], month=args.startdate[1], day=args.startdate[2],
                                   hour=args.startdate[3], minute=args.startdate[4])
    print("Start date: {0}".format(str(start_date)))

    date_interval = datetime.timedelta(minutes=args.dateint)
    print("Date interval: {0} minutes".format(str(date_interval)))

    main(start_date=start_date, date_interval=date_interval)
