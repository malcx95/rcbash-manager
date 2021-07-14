from duration import Duration
from functools import reduce
from htmlparsing import RCMHtmlParser

import filelocation
import numpy as np
import matplotlib.pyplot as plt


def get_total_times(parser):
    return {(number, driver): reduce(lambda a, b: a + b, laptimes, Duration(0))
            for (number, driver), laptimes in parser.result.items()}


def get_num_laps_driven(parser):
    return {(number, driver): max(0, len(laptimes) - 1)
            for (number, driver), laptimes in parser.result.items()}


def get_positions(total_times, num_laps_driven):
    orderings = []
    for (number, driver), num_laps_driven in num_laps_driven.items():
        orderings.append(((number, driver), num_laps_driven, total_times[(number, driver)]))

    orderings_sorted = sorted(orderings, key=lambda k: (k[1], -k[2].milliseconds), reverse=True)

    return [(number, driver) for (number, driver), _, _ in orderings_sorted]


def get_best_laptimes(parser):
    return {(number, driver): min(laptimes[1:], key=lambda lt: lt.milliseconds) if len(laptimes) > 1 else None
            for (number, driver), laptimes in parser.result.items()}


def get_average_laptimes(total_times, num_laps_driven):
    average_laptimes = {}
    for (number, driver), total_time in total_times.items():
        laps_driven = num_laps_driven[(number, driver)]
        if laps_driven == 0:
            average_laptimes[(number, driver)] = None
        else:
            average_laptimes[(number, driver)] = Duration(total_time.milliseconds // laps_driven)

    return average_laptimes


def main():
    parser = RCMHtmlParser()

    html_file_contents = filelocation.find_and_read_latest_html_file()

    parser.parse_data(html_file_contents)
    
    print()
    total_times = get_total_times(parser)
    print(total_times)
    print()

    num_laps_driven = get_num_laps_driven(parser)
    print(num_laps_driven)
    print()

    positions = get_positions(total_times, num_laps_driven)
    print(positions)
    print()

    best_laptimes = get_best_laptimes(parser)
    print(best_laptimes)
    print()

    average_laptimes = get_average_laptimes(total_times, num_laps_driven)
    print(average_laptimes)
    print()



if __name__ == "__main__":
    main()
