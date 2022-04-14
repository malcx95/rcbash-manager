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

    def setup_fake_input(self, entered_inputs):
        resultcalculation._input = mock.Mock(side_effect=entered_inputs)

    def to_list_of_lists(self, list_of_tuples):
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

    def _assert_correct_results_added(self, expected, actual):
        for heat, results in expected.items():
            for rcclass, class_results in results.items():
                actual_class_results = actual[heat][rcclass]
                if not class_results:
                    self.assertEqual(
                        actual_class_results, {},
                        f"Expected {rcclass} {heat} heat to not have been added!")
                else:
                    for group, group_results in class_results.items():
                        self.assertIn(group, actual_class_results,
                                      f"Expected group {group} to have been added to {rcclass} {heat}!")
                        actual_group_results = actual_class_results[group]
                        if not group_results:
                            self.assertEqual(
                                actual_group_results, {},
                                f"Expected {rcclass} group {group} {heat} heat to not have been added!")
                        else:
                            self.assertListEqual(
                                group_results["positions"],
                                actual_group_results["positions"],
                                f"Incorrect positions in {rcclass} {heat} {group}"
                            )
                            self.assertDictEqual(
                                group_results["num_laps_driven"],
                                actual_group_results["num_laps_driven"],
                                f"Incorrect positions in {rcclass} {heat} {group}"
                            )
                            self.assertDictEqual(
                                group_results["total_times"],
                                actual_group_results["total_times"],
                                f"Incorrect total times in {rcclass} {heat} {group}"
                            )
                            self.assertListEqual(
                                group_results["best_laptimes"],
                                actual_group_results["best_laptimes"],
                                f"Incorrect best laptimes in {rcclass} {heat} {group}"
                            )
                            self.assertListEqual(
                                group_results["average_laptimes"],
                                actual_group_results["average_laptimes"],
                                f"Incorrect average laptimes in {rcclass} {heat} {group}"
                            )
                            self.assertEqual(
                                group_results["manual"],
                                actual_group_results["manual"],
                                f"Incorrect manual flag in {rcclass} {heat} {group}"
                            )
        self.assertDictEqual(expected, actual, "Something unexpected is wrong with the results!")


    def test_create_qualifiers(self):
        participants_entered = [
            "90", "90", "89", "1", "11", "", "y", # 2WD A
            "90", "90", "12", "27", "29", "", "y", # 2WD B
            "90", "90", "21", "22", "26", "", "y", # 2WD C
            "90", "90", "35", "49", "51", "", "y", # 4WD A
            "90", "90", "67", "68", "36", "", "y", # 4WD B
            "", "y"
        ]
        self.setup_fake_input(participants_entered)
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
        list_of_initial_start_lists = [
            { # normal 2WD qualifier
                "Kval": {
                    "2WD": {"A": [90, 89, 11, 47], "B": [12, 27, 29], "C": [21, 22, 26]},
                    "4WD": {"A": [35, 49, 51], "B": [67, 68, 36]},
                }
            },
            {  # normal 4WD qualifier
                "Kval": {
                    "2WD": {"A": [90, 89, 11, 47], "B": [12, 27, 29], "C": [21, 22, 26]},
                    "4WD": {"A": [35, 49, 51], "B": [67, 68, 36]},
                }
            },
        ]
        list_of_total_times = [
            { # normal 2WD qualifier
                89: Duration(minutes=21),
                90: Duration(minutes=20),
                47: Duration(minutes=18, milliseconds=1),
                11: Duration(minutes=19, milliseconds=1),
            },
            { # normal 4WD qualifier
                67: Duration(minutes=21),
                68: Duration(minutes=20),
                36: Duration(minutes=18, milliseconds=1),
            },
        ]
        list_of_num_laps_driven = [
            { 90: 20, 89: 20, 11: 21, 47: 19 }, # normal 2WD qualifier
            { 67: 20, 68: 21, 36: 19 }, # normal 4WD qualifier
        ]
        list_of_best_laptimes = [
            [ # normal 2WD qualifier
                (89, Duration(minutes=1)),
                (90, Duration(seconds=30)),
                (47, Duration(seconds=31, milliseconds=1)),
                (11, Duration(seconds=19, milliseconds=1)),
            ],
            [ # normal 4WD qualifier
                (67, Duration(seconds=30)),
                (68, Duration(seconds=31, milliseconds=1)),
                (36, Duration(seconds=19, milliseconds=1)),
            ],
        ]

        list_of_expected_positions = [
            [11, 90, 89, 47],  # normal 2WD qualifier
            [68, 67, 36],  # normal 4WD qualifier
        ]

        list_of_expected_groups = [
            "A",  # normal 2WD qualifier
            "B",  # normal 4WD qualifier
        ]

        list_of_expected_classes = [
            "2WD",  # normal 2WD qualifier
            "4WD",  # normal 4WD qualifier
        ]

        list_of_descriptions = [
            "Normal 2WD qualifier",
            "Normal 4WD qualifier",
        ]

        for (initial_start_lists,
             total_times,
             num_laps_driven,
             best_laptimes,
             expected_positions,
             expected_group,
             expected_class,
             description,
            ) in zip(
                 list_of_initial_start_lists,
                 list_of_total_times,
                 list_of_num_laps_driven,
                 list_of_best_laptimes,
                 list_of_expected_positions,
                 list_of_expected_groups,
                 list_of_expected_classes,
                 list_of_descriptions,
            ):

            self.setup_fake_input(["y"])
            self.setup_database_state(initial_start_lists, {}, 0)
            self.setup_fake_html_parsing(total_times, num_laps_driven, best_laptimes)

            not_class = {"4WD": "2WD", "2WD": "4WD"}[expected_class]
            expected_average = self.to_list_of_lists(
                htmlparsing.get_average_laptimes(total_times, num_laps_driven))

            expected_results = {
                QUALIFIERS_NAME: {
                    expected_class: {
                        expected_group: {
                            "positions": expected_positions,
                            "num_laps_driven": num_laps_driven,
                            "total_times": total_times,
                            "best_laptimes": self.to_list_of_lists(best_laptimes),
                            "average_laptimes": expected_average,
                            "manual": False
                        }
                    },
                    not_class: {}
                }
            }

            with self.subTest(description):

                resultcalculation.add_new_result()
                database = resultcalculation._get_database()
                self._assert_correct_results_added(expected_results, database[RESULTS_KEY])
                self.assertDictEqual(database[START_LISTS_KEY], initial_start_lists,
                                     "Start lists were changed!")
                self.assertEqual(database[CURRENT_HEAT_KEY], 0, "Current heat was changed!")
