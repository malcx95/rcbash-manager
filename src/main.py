from duration import Duration
from functools import reduce
from htmlparsing import RCMHtmlParser


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
    pass


def get_average_laptimes(parser):
    pass


def get_std_deviations(parser):
    pass


def main():
    parser = RCMHtmlParser()

    with open("../20210703_840511/17_11_39.html", encoding='utf-16-le') as f:
        contents = f.read()

    parser.parse_data(contents)

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


if __name__ == "__main__":
    main()
