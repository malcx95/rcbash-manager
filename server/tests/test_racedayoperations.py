import unittest

from server import racedayoperations

VALID_DATE = "2023-01-01"
VALID_LOCATION = "Linkeboda"
VALID_START_LISTS = {
    "4WD": {
        "A": [
            {"number": 90, "name": "malcx95"},
            {"number": 80, "name": "someoneelse"},
        ],
        "B": [
            {"number": 91, "name": "kebab"},
            {"number": 81, "name": "annankebab"},
        ]
    },
    "2WD": {
        "A": [
            {"number": 89, "name": "hej"},
            {"number": 79, "name": "nej"},
        ],
        "B": [
            {"number": 88, "name": "va"},
            {"number": 78, "name": "tjo"},
        ]
    }
}


class RacedayOperationsTests(unittest.TestCase):

    def test_create_raceday_invalid_input(self):
        invalid_inputs = [
            ({}, "Empty"),
            ({"date": VALID_DATE, "location": "", "startLists": VALID_START_LISTS}, "Empty location"),
            ({"date": VALID_DATE, "location": VALID_LOCATION, "startLists": VALID_START_LISTS}, "Empty location"),
            ({"date": "", "location": VALID_LOCATION, "startLists": VALID_START_LISTS}, "Empty date"),
            ({"date": VALID_DATE, "location": VALID_LOCATION, "startLists": {}}, "Empty startlists"),
            ({"date": VALID_DATE, "location": VALID_LOCATION, "startLists": []}, "Wrong start list data type"),
        ]
        # TODO Add tests for valid logic, you need to have a test flask app for this
        for test_input, description in invalid_inputs:
            with self.subTest(description):
                self.assertRaises(
                    racedayoperations.RaceDayException,
                    lambda: racedayoperations.create_raceday_from_json(test_input))


if __name__ == '__main__':
    unittest.main()
