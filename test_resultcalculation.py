import resultcalculation
from resultcalculation import QUALIFIERS_NAME, START_LISTS_KEY, RESULTS_KEY, \
    CURRENT_HEAT_KEY, ALL_PARTICIPANTS_KEY
import htmlparsing
from duration import Duration
from pathlib import Path
from pyfakefs.fake_filesystem_unittest import TestCase
import unittest.mock as mock


class ResultCalculationTests(TestCase):

    def setUp(self):
        self.clipboard = None
        def fake_clipboard_copy(obj):
            self.clipboard = obj

        resultcalculation.clipboard.copy = fake_clipboard_copy
        self.setUpPyfakefs(modules_to_reload=[resultcalculation])
        resultcalculation.RESULT_FOLDER_PATH = Path("test_rcbash_results")
        resultcalculation.RESULT_FOLDER_PATH.mkdir(exist_ok=True)

    def _to_list_of_lists(self, list_of_tuples):
        return [list(t) for t in list_of_tuples]

    def setup_fake_html_parsing(self, total_times, num_laps_driven, best_laptimes):
        htmlparsing.get_total_times = mock.Mock(return_value=total_times)
        htmlparsing.get_num_laps_driven = mock.Mock(return_value=num_laps_driven)
        htmlparsing.get_best_laptimes = mock.Mock(return_value=best_laptimes)
        htmlparsing.get_race_participants = mock.Mock(return_value=[num for num in total_times])
        resultcalculation._read_results = mock.Mock(return_value=None)

    def setup_database_state(self, start_lists, results, current_heat):
        database = {START_LISTS_KEY: start_lists}
        all_participants = list(set(num
                                    for rcclass in start_lists[QUALIFIERS_NAME].values()
                                    for group in rcclass.values()
                                    for num in group))
        database[ALL_PARTICIPANTS_KEY] = all_participants
        database[RESULTS_KEY] = results
        database[CURRENT_HEAT_KEY] = current_heat
        resultcalculation._save_database(database)

    def test_create_qualifiers(self):
        participants_entered = [
            "90", "90", "89", "1", "11", "", "y", # 2WD A
            "90", "90", "12", "27", "29", "", "y", # 2WD B
            "90", "90", "21", "22", "26", "", "y", # 2WD C
            "90", "90", "35", "49", "51", "", "y", # 4WD A
            "90", "90", "67", "68", "36", "", "y", # 4WD B
            "", "y"
        ]
        resultcalculation._input = mock.Mock(side_effect=participants_entered)
        resultcalculation.create_qualifiers()
        database = resultcalculation._get_database()

        expected_all_participants = {90, 89, 11, 12, 27, 29, 21, 22, 26, 35, 49, 51, 67, 68, 36}
        expected_start_lists = {
            "Kval": {
                "2WD": {"A": [90, 89, 11], "B": [12, 27, 29], "C": [21, 22, 26]},
                "4WD": {"A": [35, 49, 51], "B": [67, 68, 36]},
            }
        }
        self.assertSetEqual(set(database["all_participants"]), expected_all_participants)
        self.assertDictEqual(database["start_lists"], expected_start_lists)
        self.assertDictEqual(database["results"], {})
        self.assertEqual(database["current_heat"], 0)

    def test_add_new_result_qualifiers(self):
        initial_start_lists = {
            "Kval": {
                "2WD": {"A": [90, 89, 11, 47], "B": [12, 27, 29], "C": [21, 22, 26]},
                "4WD": {"A": [35, 49, 51], "B": [67, 68, 36]},
            }
        }
        self.setup_database_state(initial_start_lists, {}, 0)
        total_times = {
            89: Duration(minutes=21),
            90: Duration(minutes=20),
            47: Duration(minutes=18, milliseconds=1),
            11: Duration(minutes=19, milliseconds=1),
        }
        num_laps_driven = { 90: 20, 89: 20, 11: 21, 47: 19 }
        best_laptimes = [
            (89, Duration(minutes=1)),
            (90, Duration(seconds=30)),
            (47, Duration(seconds=31, milliseconds=1)),
            (11, Duration(seconds=19, milliseconds=1)),
        ]
        self.setup_fake_html_parsing(total_times, num_laps_driven, best_laptimes)

        expected_average = self._to_list_of_lists(
            htmlparsing.get_average_laptimes(total_times, num_laps_driven))
        expected_results = {
            QUALIFIERS_NAME: {
                "2WD": {
                    "A": {
                        "positions": [11, 90, 89, 47],
                        "num_laps_driven": num_laps_driven,
                        "total_times": total_times,
                        "best_laptimes": self._to_list_of_lists(best_laptimes),
                        "average_laptimes": expected_average,
                        "manual": False
                    }
                },
                "4WD": {}
            }
        }
        resultcalculation.add_new_result()
        database = resultcalculation._get_database()
        self.assertDictEqual(database[RESULTS_KEY], expected_results,
                             "Results were not added correctly!")
        self.assertDictEqual(database[START_LISTS_KEY], initial_start_lists,
                             "Start lists were changed!")
        self.assertEqual(database[CURRENT_HEAT_KEY], 0, "Current heat was changed!")
