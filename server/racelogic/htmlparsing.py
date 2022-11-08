from html.parser import HTMLParser
from functools import reduce
from collections import defaultdict
from typing import List, Tuple, Dict

from server.racelogic.duration import Duration


class HeaderRow:

    def __init__(self):
        self.pos = None
        self.nr = None
        self.driver = None
        self.omg = None
        self.definitive_time = None
        self.best_time = None
        self.average_time = None
        self.stddev = None


class RCMHtmlParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.header = defaultdict(HeaderRow)
        self.result_header = []
        self.result = defaultdict(list)
        self._parsing_header = True
        self._parsing_table = False
        self._parsing_table_row = False
        self._parsing_data = False
        self._parsing_bold_time = False
        self._parsing_result_header = False
        self._driver_index = 0
        self._result_header_index_start = 0

    def parse_data(self, contents):
        self.feed(contents)
        for number_name in self.result_header:
            if number_name not in self.result:
                self.result[number_name] = []

    @staticmethod
    def _is_start_of_table(tag, attrs):
        return tag == "tr" and attrs == [("valign", "top")]

    def _there_are_tables_after_this(self, tag, attrs):
        return (not self._parsing_table) and len(self.result_header) > 0 and tag == "td" and ("class", "tableborder") in attrs

    def _is_useful_table_row(self, tag, attrs):
        return self._parsing_table and tag == "tr" and attrs == []

    def _is_useful_table_data(self, tag, attrs):
        return self._parsing_table_row and tag == "td"

    def _is_end_of_result_header(self, tag, attrs):
        return tag == "tr" and self._parsing_result_header and attrs == []

    def _handle_table_parsing(self, tag, attrs):
        if self._is_end_of_result_header(tag, attrs):
            # HACK: For some reason, the end of the table headers is a start "tr"-tag, which is why
            #       this is handled here. It renders properly in the browser though as it converts the
            #       start tag to an end tag.
            self._parsing_result_header = False
        elif self._is_useful_table_row(tag, attrs):
            self._parsing_table_row = True
        elif self._is_useful_table_data(tag, attrs):
            self._parsing_data = True

    @staticmethod
    def _is_start_of_laptime_row(data):
        return data.strip().isdigit()

    @staticmethod
    def _is_laptime_empty_due_to_time_being_bold(data):
        # When the current lap time is the best time, the document puts the time
        # in <b>-tags, but not the '(0)' part. Since I'm not sure if '(0)' always
        # is present, I think it's safer to check whether there is an actual laptime
        # in the data string, which is what this tests. The replace-function is used
        # since isnumeric() doesn't regard floats as numeric.
        return (data.strip() != "") and (not data.strip().split(' ')[-1].replace('.', '').replace(':', '').isnumeric())

    def _handle_laptime_row(self, data):
        num_drivers = len(self.result_header)
        if self._driver_index >= num_drivers and data.strip() == "":
            # we have a bunch of empty cells we need to skip
            return

        if self._is_start_of_laptime_row(data):
            # to handle multiple tables, we don't reset it to 0 but to where we started
            self._driver_index = self._result_header_index_start
        else:
            number, name = self.result_header[self._driver_index]
            if self._is_laptime_empty_due_to_time_being_bold(data):
                # skip since we are parsing the best laptime, the time will exist in the next tag.
                self._parsing_bold_time = True
                return
            elif data.strip() == "":
                if not self._parsing_bold_time:
                    # we have an empty cell, move to the next
                    self._driver_index += 1
                else:
                    self._parsing_bold_time = False
                return

            time_string = data.strip().split(' ')[-1]
            time_string_split = time_string.split(':')

            minutes = int(time_string_split[0]) if len(time_string_split) > 1 else 0
            seconds_string, milliseconds_string = time_string_split[-1].split('.')

            seconds = int(seconds_string)
            milliseconds = int(milliseconds_string)

            duration = Duration(milliseconds=milliseconds, seconds=seconds, minutes=minutes)

            self.result[(number, name)].append(duration)

            self._driver_index += 1

    def handle_starttag(self, tag, attrs):
        if self._parsing_table:
            self._handle_table_parsing(tag, attrs)

        elif self._is_start_of_table(tag, attrs):
            self._parsing_table = True

        elif self._there_are_tables_after_this(tag, attrs):
            self._result_header_index_start = len(self.result_header)

    def handle_endtag(self, tag):
        if tag == "table":
            if self._parsing_table and (self._parsing_header or len(self.result_header) > 0):
                # We should turn on parsing result header mode either if we just got finished
                # parsing the header, or if we have already processed rows prior to this.
                self._parsing_header = False
                self._parsing_result_header = True
            self._parsing_table = False
        elif tag == "tr":
            self._parsing_table_row = False
        elif tag == "td":
            self._parsing_data = False

    def handle_data(self, data):
        if self._parsing_data:
            if not self._parsing_header:
                self._handle_laptime_row(data)

        elif self._parsing_result_header and self._parsing_table:
            if data.strip() != "" and "# nr" not in data.lower():
                data_split = data.strip().split(" ")

                number = data_split[0]
                name = " ".join(data_split[1:])
                self.result_header.append((int(number), name))


def get_total_times(parser) -> Dict[int, Duration]:
    return {int(number): reduce(lambda a, b: a + b, laptimes, Duration(0))
            for (number, _), laptimes in parser.result.items()}


def get_race_participants(parser) -> List[int]:
    return [int(number) for number, _ in parser.result]


def get_num_laps_driven(parser) -> Dict[int, int]:
    return {int(number): max(0, len(laptimes) - 1)
            for (number, _), laptimes in parser.result.items()}


def get_positions(total_times, num_laps_driven) -> List[int]:
    orderings = []
    for number, num_laps_driven in num_laps_driven.items():
        orderings.append((int(number), num_laps_driven, total_times[number]))

    orderings_sorted = sorted(orderings, key=lambda k: (k[1], -k[2].milliseconds), reverse=True)

    return [number for number, _, _ in orderings_sorted]


def get_best_laptimes(parser) -> List[Tuple[int, Duration]]:
    best_times = [(int(number), min(laptimes[1:], key=lambda lt: lt.milliseconds))
                  for (number, _), laptimes in parser.result.items() if len(laptimes) > 1]
    return sorted(best_times, key=lambda k: k[1])


def get_average_laptimes(total_times, num_laps_driven) -> List[Tuple[int, Duration]]:
    average_laptimes = []
    for number, total_time in total_times.items():
        laps_driven = num_laps_driven[number]
        if laps_driven > 0:
            average_laptimes.append((number, Duration(total_time.milliseconds // laps_driven)))

    return average_laptimes
