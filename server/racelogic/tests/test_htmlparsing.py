import unittest
import os
from pathlib import Path

import server.racelogic.htmlparsing as htmlparsing

from server.racelogic.duration import Duration


EXPECTED_RESULTS = {
    "normal.html": [
        # driver, num laps, total time
        (37, 33, Duration(minutes=20, seconds=0,  milliseconds=723)),
        (88, 32, Duration(minutes=19, seconds=33, milliseconds=647)),
        (22, 31, Duration(minutes=19, seconds=40, milliseconds=105)),
        (41, 29, Duration(minutes=19, seconds=48, milliseconds=252)),
        (27, 28, Duration(minutes=19, seconds=22, milliseconds=623)),
        (71, 2,  Duration(minutes=1,  seconds=25, milliseconds=388)),
    ],
    "corrupt.html": [
        # driver, num laps, total time
        (11, 14, Duration(minutes=8, seconds=7,  milliseconds=89)),
        (82, 14, Duration(minutes=8, seconds=10, milliseconds=362)),
        (21, 13, Duration(minutes=7, seconds=38, milliseconds=168)),
        (90, 13, Duration(minutes=8, seconds=0,  milliseconds=965)),
        (45, 12, Duration(minutes=7, seconds=52, milliseconds=792)),
        (77, 7,  Duration(minutes=4, seconds=30, milliseconds=71)),
    ],
    "dns.html": [
        # driver, num laps, total time
        (37, 14, Duration(minutes=8, seconds=3,  milliseconds=498)),
        (71, 13, Duration(minutes=8, seconds=2,  milliseconds=867)),
        (27, 12, Duration(minutes=7, seconds=59, milliseconds=216)),
        (65, 11, Duration(minutes=7, seconds=31, milliseconds=489)),
        (35, 0,  Duration(minutes=0, seconds=0,  milliseconds=0)),
    ]
}

BEST_LAPTIMES = {
    "normal.html": [
        (37, Duration(minutes=0, seconds=33, milliseconds=919)),
        (88, Duration(minutes=0, seconds=33, milliseconds=875)),
        (22, Duration(minutes=0, seconds=35, milliseconds=701)),
        (41, Duration(minutes=0, seconds=36, milliseconds=724)),
        (27, Duration(minutes=0, seconds=37, milliseconds=447)),
        (71, Duration(minutes=0, seconds=37, milliseconds=20))
    ],
    "corrupt.html": [
        (11, Duration(minutes=0, seconds=32, milliseconds=796)),
        (21, Duration(minutes=0, seconds=31, milliseconds=398)),
        (45, Duration(minutes=0, seconds=34, milliseconds=218)),
        (77, Duration(minutes=0, seconds=32, milliseconds=983)),
        (82, Duration(minutes=0, seconds=31, milliseconds=660)),
        (90, Duration(minutes=0, seconds=31, milliseconds=571)),
    ],
    "dns.html": [
        (37, Duration(minutes=0, seconds=33, milliseconds=0)),
        (71, Duration(minutes=0, seconds=33, milliseconds=517)),
        (27, Duration(minutes=0, seconds=34, milliseconds=534)),
        (65, Duration(minutes=0, seconds=34, milliseconds=581))
    ],
}

AVERAGE_LAPTIMES = {
    "normal.html": [
        (37, Duration(minutes=0, seconds=36, milliseconds=385)),
        (88, Duration(minutes=0, seconds=36, milliseconds=676)),
        (22, Duration(minutes=0, seconds=38, milliseconds=67)),
        (41, Duration(minutes=0, seconds=40, milliseconds=974)),
        (27, Duration(minutes=0, seconds=41, milliseconds=522)),
        (71, Duration(minutes=0, seconds=42, milliseconds=694))
    ],
    "corrupt.html": [
        (11, Duration(minutes=0, seconds=34, milliseconds=792)),
        (21, Duration(minutes=0, seconds=35, milliseconds=243)),
        (45, Duration(minutes=0, seconds=39, milliseconds=399)),
        (77, Duration(minutes=0, seconds=38, milliseconds=581)),
        (82, Duration(minutes=0, seconds=35, milliseconds=25)),
        (90, Duration(minutes=0, seconds=36, milliseconds=997)),
    ],
    "dns.html": [
        (37, Duration(minutes=0, seconds=34, milliseconds=535)),
        (71, Duration(minutes=0, seconds=37, milliseconds=143)),
        (27, Duration(minutes=0, seconds=39, milliseconds=934)),
        (65, Duration(minutes=0, seconds=41, milliseconds=44))
    ],
}


class HtmlParsingTests(unittest.TestCase):

    def test_parser_correctly_calculates_everything(self):

        for test_file, expected_results in EXPECTED_RESULTS.items():
            with self.subTest(f"Test file {test_file}"):
                filepath = Path(__file__).parent / "testdata" / test_file

                with open(filepath, encoding="utf-16-le") as f:
                    contents = f.read()

                parser = htmlparsing.RCMHtmlParser()
                parser.parse_data(contents)

                total_times = htmlparsing.get_total_times(parser)
                num_laps_driven = htmlparsing.get_num_laps_driven(parser)
                positions = htmlparsing.get_positions(total_times, num_laps_driven)

                for i, (driver, num_laps, total_time) in enumerate(expected_results):
                    self.assertEqual(total_time, total_times[driver],
                                     f"Expected driver {driver} to total time {total_time}!")
                    self.assertEqual(num_laps, num_laps_driven[driver],
                                     f"Expected driver {driver} to get {num_laps} laps!")
                    self.assertEqual(driver, positions[i],
                                     f"Position of driver {driver} is incorrect! "
                                     f"Expected driver to finish in position {i + 1}, "
                                     f"got positions {positions}!")

                expected_best_times = BEST_LAPTIMES[test_file]
                expected_average_times = AVERAGE_LAPTIMES[test_file]

                best_laptimes = htmlparsing.get_best_laptimes(parser)
                average_laptimes = htmlparsing.get_average_laptimes(total_times, num_laps_driven)

                self.assertSetEqual(set(best_laptimes), set(expected_best_times),
                                    "Best laptimes were incorrect!")
                self.assertSetEqual(set(average_laptimes), set(expected_average_times),
                                    "Average laptimes were incorrect!")
