from html.parser import HTMLParser
from collections import defaultdict
from duration import Duration


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
        self._parsing_result_header = False
        self._driver_index = 0

    def _is_start_of_table(self, tag, attrs):
        return tag == "tr" and attrs == [("valign", "top")]

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

    def _is_start_of_laptime_row(self, data):
        return data.strip().isdigit()

    def _is_laptime_empty_due_to_time_being_bold(self, data):
        # When the current lap time is the best time, the document puts the time
        # in <b>-tags, but not the '(0)' part. Since I'm not sure if '(0)' always
        # is present, I think it's safer to check whether there is an actual laptime
        # in the data string, which is what this tests. The replace-function is used
        # since isnumeric() doesn't regard floats as numeric.
        return not data.strip().split(' ')[-1].replace('.', '').replace(':', '').isnumeric()

    def _handle_laptime_row(self, data):
        if self._is_start_of_laptime_row(data):
            self._driver_index = 0
            print(f"Start of row! Lap {data}")
        else:
            number, name = self.result_header[self._driver_index]
            if self._is_laptime_empty_due_to_time_being_bold(data):
                # skip since we are parsing the best laptime, the time will exist in the next
                # tag.
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
            print("\nStarting table!\n")
            self._parsing_table = True

    def handle_endtag(self, tag):
        if tag == "table":
            if self._parsing_table and self._parsing_header:
                self._parsing_header = False
                self._parsing_result_header = True
            self._parsing_table = False
        elif tag == "tr":
            self._parsing_table_row = False
        elif tag == "td":
            self._parsing_data = False

    def handle_data(self, data):
        if self._parsing_data:
            if data.strip() != "":
                #print(f"Useful data: {data}, {self._parsing_header}")
                if not self._parsing_header:
                    self._handle_laptime_row(data)
                
        elif self._parsing_result_header and self._parsing_table:
            if data.strip() != "" and "# nr" not in data.lower():
                number, name = data.strip().split(" ")
                self.result_header.append((int(number), name))
                print(f"Result header: {data}!")


def test():
    parser = RCMHtmlParser()

    with open("../20210703_840511/18_22_49.html", encoding='utf-16-le') as f:
        contents = f.read()

    parser.feed(contents)
    print(parser.result_header)
    import pprint
    pprint.pprint(parser.result)

    for (number, driver), laps in parser.result.items():
        total = Duration(0)
        for duration in laps:
            total += duration

        print(f"Driver {driver} total: {total}")
