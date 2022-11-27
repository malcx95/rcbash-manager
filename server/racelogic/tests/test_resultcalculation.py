from typing import Dict, List

import server.racelogic.raceday as rd
import server.racelogic.htmlparsing as htmlparsing
import server.racelogic.resultcalculation as resultcalculation
from server.racelogic.duration import Duration
from server.racelogic.raceday import QUALIFIERS_NAME, START_LISTS_KEY, RESULTS_KEY, \
    ALL_PARTICIPANTS_KEY, QUARTER_FINAL_NAME, FINALS_NAME, CURRENT_HEAT_KEY

import os
from pathlib import Path
from pyfakefs.fake_filesystem_unittest import TestCase
import unittest.mock as mock


TEST_DATABASE_PATH = Path(__file__).parent / "testdata" / "testdatabases"


class ResultCalculationTests(TestCase):

    test_racedays: Dict[str, rd.Raceday] = {}

    @classmethod
    def setUpClass(cls):
        raceday_files = os.listdir(TEST_DATABASE_PATH)
        for raceday in raceday_files:
            path = os.path.join(TEST_DATABASE_PATH, raceday)
            name = raceday.split(".json")[0]
            cls.test_racedays[name] = rd.load_and_deserialize_raceday(path)

    def setUp(self):
        self.clipboard = None

        def fake_clipboard_copy(obj):
            self.clipboard = obj

        resultcalculation.clipboard.copy = fake_clipboard_copy
        self.setUpPyfakefs(modules_to_reload=[rd, resultcalculation])
        rd.RESULT_FOLDER_PATH = Path("test_rcbash_results")
        resultcalculation.rd.RESULT_FOLDER_PATH = Path("test_rcbash_results")
        rd.RESULT_FOLDER_PATH.mkdir(exist_ok=True)

    def tearDown(self):
        # TODO make this a parameter
        resultcalculation.MAX_NUM_PARTICIPANTS_PER_GROUP = 6

    def setup_fake_input(self, entered_inputs):
        resultcalculation._input = mock.Mock(side_effect=entered_inputs)

    def to_list_of_lists(self, list_of_tuples):
        return [list(t) for t in list_of_tuples]

    def setup_fake_html_parsing(self, total_times, num_laps_driven, best_laptimes):
        resultcalculation.htmlparsing.get_total_times = mock.Mock(return_value=total_times)
        resultcalculation.htmlparsing.get_num_laps_driven = mock.Mock(return_value=num_laps_driven)
        resultcalculation.htmlparsing.get_best_laptimes = mock.Mock(return_value=best_laptimes)
        resultcalculation.htmlparsing.get_race_participants = mock.Mock(return_value=[num for num in total_times])
        resultcalculation._read_results = mock.Mock(return_value=None)

    def setup_raceday_state(self, start_lists, results, current_heat):
        json_raceday = {START_LISTS_KEY: start_lists}
        all_participants = list(set(num
                                    for rcclass in start_lists[QUALIFIERS_NAME].values()
                                    for group in rcclass.values()
                                    for num in group))
        json_raceday[ALL_PARTICIPANTS_KEY] = all_participants
        json_raceday[RESULTS_KEY] = results
        json_raceday[CURRENT_HEAT_KEY] = current_heat
        raceday = rd.Raceday(json_raceday)
        raceday.save()

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
            "90", "90", "89", "1", "11", "", "y",  # 2WD A
            "90", "90", "12", "27", "29", "", "y",  # 2WD B
            "90", "90", "21", "22", "26", "", "y",  # 2WD C
            "90", "90", "35", "49", "51", "", "y",  # 4WD A
            "90", "90", "67", "68", "36", "", "y",  # 4WD B
            "", "y"
        ]
        self.setup_fake_input(participants_entered)
        resultcalculation.create_qualifiers()
        raceday = rd.get_raceday()

        expected_all_participants = {
            rd.Driver(num) for num in {90, 89, 11, 12, 27, 29, 21, 22, 26, 35, 49, 51, 67, 68, 36}
        }
        expected_start_lists = {
            "Kval": {
                "2WD": {"A": [90, 89, 11], "B": [12, 27, 29], "C": [21, 22, 26]},
                "4WD": {"A": [35, 49, 51], "B": [67, 68, 36]},
            }
        }
        self.assertSetEqual(set(raceday.all_participants), expected_all_participants)
        self.assertDictEqual(raceday.get_start_lists_dict(), expected_start_lists)
        self.assertDictEqual(raceday.get_results_dict(), {})
        self.assertEqual(raceday.get_current_heat(), rd.QUALIFIERS_NAME)

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
            {  # 2WD dns
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
            { # 2WD dns
                89: Duration(minutes=21),
                90: Duration(minutes=20),
                11: Duration(minutes=19, milliseconds=1),
            },
        ]
        list_of_num_laps_driven = [
            { 90: 20, 89: 20, 11: 21, 47: 19 }, # normal 2WD qualifier
            { 67: 20, 68: 21, 36: 19 }, # normal 4WD qualifier
            { 90: 20, 89: 20, 11: 21 }, # 2WD dns
        ]
        list_of_best_laptimes = [
            [ # normal 2WD qualifier
                (11, Duration(seconds=19, milliseconds=1)),
                (90, Duration(seconds=30)),
                (47, Duration(seconds=31, milliseconds=1)),
                (89, Duration(minutes=1)),
            ],
            [ # normal 4WD qualifier
                (36, Duration(seconds=19, milliseconds=1)),
                (67, Duration(seconds=30)),
                (68, Duration(seconds=31, milliseconds=1)),
            ],
            [ # 2WD dns
                (11, Duration(seconds=19, milliseconds=1)),
                (90, Duration(seconds=30)),
                (89, Duration(minutes=1)),
            ]
        ]

        list_of_expected_positions = [
            [11, 90, 89, 47],  # normal 2WD qualifier
            [68, 67, 36],  # normal 4WD qualifier
            [11, 90, 89, 47],  # 2WD dns
        ]

        list_of_expected_groups = [
            "A",  # normal 2WD qualifier
            "B",  # normal 4WD qualifier
            "A",  # 2WD dns
        ]

        list_of_expected_classes = [
            "2WD",  # normal 2WD qualifier
            "4WD",  # normal 4WD qualifier
            "2WD",  # 2WD dns
        ]

        list_of_descriptions = [
            "Normal 2WD qualifier",
            "Normal 4WD qualifier",
            "2WD DNS",
        ]

        list_of_expected_dns = [
            None,  # normal 2WD qualifier
            None,  # normal 4WD qualifier
            [47],  # 2WD dns
        ]

        for (initial_start_lists,
             total_times,
             num_laps_driven,
             best_laptimes,
             expected_positions,
             expected_group,
             expected_class,
             expected_dns,
             description,
            ) in zip(
                 list_of_initial_start_lists,
                 list_of_total_times,
                 list_of_num_laps_driven,
                 list_of_best_laptimes,
                 list_of_expected_positions,
                 list_of_expected_groups,
                 list_of_expected_classes,
                 list_of_expected_dns,
                 list_of_descriptions,
            ):

            self.setup_fake_input(["y"])
            self.setup_raceday_state(initial_start_lists, {}, 0)
            self.setup_fake_html_parsing(total_times, num_laps_driven, best_laptimes)

            not_class = {"4WD": "2WD", "2WD": "4WD"}[expected_class]
            expected_average = self.to_list_of_lists(
                htmlparsing.get_average_laptimes(total_times, num_laps_driven))

            expected_group_results = {
                "positions": expected_positions,
                "num_laps_driven": num_laps_driven,
                "total_times": total_times,
                "best_laptimes": self.to_list_of_lists(best_laptimes),
                "average_laptimes": expected_average,
                "manual": False
            }

            if expected_dns is not None:
                expected_group_results["dns"] = expected_dns

            expected_results = {
                QUALIFIERS_NAME: {
                    expected_class: {
                        expected_group: expected_group_results
                    },
                    not_class: {}
                }
            }

            with self.subTest(description):

                resultcalculation.add_new_result()
                raceday = rd.get_raceday()
                actual_results = raceday.get_results_dict(convert_from_durations=False)
                self._assert_correct_results_added(expected_results, actual_results)
                self.assertDictEqual(raceday.get_start_lists_dict(), initial_start_lists,
                                     "Start lists were changed!")
                self.assertEqual(raceday.current_heat, 0, "Current heat was changed!")

    def test_start_new_race_round_qualifiers_normal(self):
        raceday = self.test_racedays["test_start_new_race_round_qualifiers_normal"]
        raceday.save()
        self.setup_fake_input(["y"])

        resultcalculation.start_new_race_round()

        expected_new_start_lists = {
            "2WD": {
                "A": [37, 22, 27, 41, 71],
                "B": [19, 88, 62, 65]
            },
            "4WD": {
                "A": [11, 90, 77, 75, 36],
                "B": [89, 45, 82, 39, 67],
                "C": [83, 46, 60, 64]
            }
        }
        new_raceday = rd.get_raceday()
        self.assertDictEqual(new_raceday.get_start_lists_dict()[rd.EIGHTH_FINAL_NAME],
                             expected_new_start_lists,
                             "Start lists were incorrectly made from qualifiers!")

    def test_start_new_race_round_qualifiers_dns(self):
        raceday = self.test_racedays["test_start_new_race_round_qualifiers_dns"]
        raceday.save()
        self.setup_fake_input(["y"])

        resultcalculation.start_new_race_round()

        expected_new_start_lists = {
            "2WD": {
                "A": [37, 22, 27, 19, 71],
                "B": [62, 88, 41, 65]
            },
            "4WD": {
                "A": [90, 77, 75, 36, 89],
                "B": [45, 82, 39, 67, 83],
                "C": [46, 11, 64, 60]
            }
        }
        new_raceday = rd.get_raceday()
        self.assertDictEqual(new_raceday.get_start_lists_dict()[rd.EIGHTH_FINAL_NAME],
                             expected_new_start_lists,
                             "Start lists were incorrectly made from qualifiers!")

    def test_start_new_race_round_qualifiers_merge_groups(self):
        raceday = self.test_racedays["test_start_new_race_round_qualifiers_normal"]
        raceday.save()
        self.setup_fake_input([
            "n",  # don't use current groups
            "A",  # merge all 2WD to A
            "B",  # merge 4WD to B
            "y"   # accept
        ])

        resultcalculation.start_new_race_round()

        expected_new_start_lists = {
            "2WD": {
                "A": [37, 22, 27, 41, 71, 19, 88, 62, 65],
            },
            "4WD": {
                "A": [11, 90, 77, 75, 36, 89, 45],
                "B": [82, 39, 67, 83, 46, 60, 64],
            }
        }
        new_raceday = rd.get_raceday()
        self.assertDictEqual(new_raceday.get_start_lists_dict()[rd.EIGHTH_FINAL_NAME],
                             expected_new_start_lists,
                             "Start lists were incorrectly made from qualifiers!")

    def test_start_new_race_round_qualifiers_merge_groups_dns(self):
        raceday = self.test_racedays["test_start_new_race_round_qualifiers_dns"]
        raceday.save()
        self.setup_fake_input([
            "n",  # don't use current groups
            "A",  # merge all 2WD to A
            "B",  # merge 4WD to B
            "y"   # accept
        ])

        resultcalculation.start_new_race_round()

        expected_new_start_lists = {
            "2WD": {
                "A": [37, 22, 27, 19, 71, 62, 88, 41, 65],
            },
            "4WD": {
                "A": [90, 77, 75, 36, 89, 45, 82],
                "B": [39, 67, 83, 46, 11, 64, 60],
            }
        }
        new_raceday = rd.get_raceday()
        self.assertDictEqual(new_raceday.get_start_lists_dict()[rd.EIGHTH_FINAL_NAME],
                             expected_new_start_lists,
                             "Start lists were incorrectly made from qualifiers!")

    def test_start_new_race_round_finals_normal(self):
        raceday = self.test_racedays["test_start_new_race_round_finals_normal"]
        raceday.save()

        # TODO make this a parameter
        resultcalculation.MAX_NUM_PARTICIPANTS_PER_GROUP = 6

        resultcalculation.start_new_race_round()

        # TODO validate these
        expected_new_start_lists = {
            "2WD": {
                "A": [37, 22, 88, 27, 41],  # 1 person will be missing from each higher heat
                "B": [65, 62, 19, 71]
            },
            "4WD": {
                "A": [11, 77, 90, 36, 75],
                "B": [45, 39, 46, 89, 82],
                "C": [67, 83, 60, 64]
            }
        }
        new_raceday = rd.get_raceday()
        self.assertDictEqual(new_raceday.get_start_lists_dict()[FINALS_NAME],
                             expected_new_start_lists,
                             "Start lists were incorrectly made for finals!")

    def test_start_new_race_round_finals_many_people_per_heat(self):
        raceday = self.test_racedays["test_start_new_race_round_finals_normal"]

        # TODO make this a parameter
        resultcalculation.MAX_NUM_PARTICIPANTS_PER_GROUP = 9

        raceday.save()

        resultcalculation.start_new_race_round()

        # TODO validate these
        expected_new_start_lists = {
            "2WD": {
                "A": [37, 22, 88, 27, 41, 65, 62, 19, 71],
            },
            "4WD": {
                "A": [11, 77, 90, 36, 75, 45, 39, 46],
                "B": [89, 82, 67, 83, 60, 64],
            }
        }
        new_raceday = rd.get_raceday()
        self.assertDictEqual(new_raceday.get_start_lists_dict()[FINALS_NAME],
                             expected_new_start_lists,
                             "Start lists were incorrectly made for finals!")

    def test_start_new_race_round_intermediate_normal(self):
        raceday = self.test_racedays["test_start_new_race_round_intermediate_normal"]
        raceday.save()

        resultcalculation.start_new_race_round()

        expected_new_start_lists = {
            "2WD": {
                "A": [37, 22, 27, 88, 65],
                "B": [41, 71, 19, 62],
            },
            "4WD": {
                "A": [11, 77, 90, 39, 45],
                "B": [36, 75, 89, 46, 60],
                "C": [67, 82, 64, 83]
            }
        }
        new_raceday = rd.get_raceday()
        self.assertDictEqual(new_raceday.get_start_lists_dict()[QUARTER_FINAL_NAME],
                             expected_new_start_lists,
                             "Start lists were incorrectly made for eight finals!")
        self.assertEqual(new_raceday.current_heat, 2, "Heat was not incremented!")

    def test_start_new_race_round_intermediate_only_A_heat(self):
        raceday = self.test_racedays["test_start_new_race_round_intermediate_one_heat"]
        raceday.save()

        resultcalculation.start_new_race_round()

        expected_new_start_lists = {
            "2WD": {
                "A": [88, 65, 19, 62, 37, 22, 27, 41, 71],
            },
            "4WD": {
                "A": [11, 77, 90, 39, 45],
                "B": [36, 75, 89, 46, 60],
                "C": [67, 82, 64, 83]
            }
        }
        new_raceday = rd.get_raceday()
        self.assertDictEqual(new_raceday.get_start_lists_dict()[QUARTER_FINAL_NAME],
                             expected_new_start_lists,
                             "Start lists were incorrectly made for eight finals!")
        self.assertEqual(new_raceday.current_heat, 2, "Heat was not incremented!")

    def test_calculate_cup_points(self):
        raceday = self.test_racedays["test_calculate_cup_points"]
        raceday.save()
        raceday = rd.get_raceday()

        points, points_per_race = resultcalculation._calculate_cup_points(raceday)

        expected_total_points = {
            rd.Driver(37): 100,
            rd.Driver(22): 92,
            rd.Driver(88): 93,
            rd.Driver(41): 81,
            rd.Driver(27): 77,
            rd.Driver(35): 65,
            rd.Driver(19): 64,
            rd.Driver(65): 64,
            rd.Driver(29): 61,
            rd.Driver(71): 78,
            rd.Driver(11): 90,
            rd.Driver(90): 86,
            rd.Driver(77): 58,
            rd.Driver(45): 70,
            rd.Driver(36): 85,
            rd.Driver(21): 87,
            rd.Driver(89): 47,
            rd.Driver(75): 70,
            rd.Driver(82): 91,
            rd.Driver(46): 64,
            rd.Driver(26): 52
        }
        self.assertDictEqual(points, expected_total_points,
                             "Points were calculated incorrectly!")

        expected_points_per_race = {
            "2WD": {
                rd.Driver(37): [20, 20, 20, 40],
                rd.Driver(22): [19, 19, 18, 36],
                rd.Driver(88): [18, 18, 19, 38],
                rd.Driver(27): [14, 16, 15, 32],
                rd.Driver(35): [15, 17, 11, 22],
                rd.Driver(29): [12, 11, 12, 26],
                rd.Driver(19): [11, 12, 13, 28],
                rd.Driver(41): [16, 14, 17, 34],
                rd.Driver(71): [17, 15, 16, 30],
                rd.Driver(65): [13, 13, 14, 24],
            },
            "4WD": {
                rd.Driver(11): [16, 14, 20, 40],
                rd.Driver(90): [17, 18, 17, 34],
                rd.Driver(45): [13, 19, 16, 22],
                rd.Driver(36): [19, 16, 14, 36],
                rd.Driver(77): [0, 13, 15, 30],
                rd.Driver(89): [0, 11, 10, 26],
                rd.Driver(46): [12, 12, 12, 28],
                rd.Driver(82): [14, 20, 19, 38],
                rd.Driver(21): [20, 17, 18, 32],
                rd.Driver(75): [18, 15, 13, 24],
                rd.Driver(26): [11, 10, 11, 20]
            }
        }
        for rcclass in expected_points_per_race:
            for num, expected_points_list in expected_points_per_race[rcclass].items():
                self.assertListEqual(points_per_race[rcclass][num], expected_points_list,
                                     f"Points per race for driver {num} in {rcclass} was incorrect!")
        self.assertDictEqual(points_per_race, expected_points_per_race,
                             "Points per race was incorrectly calculated! Extra drivers?")

    def test_calculate_season_points(self):
        raceday_1 = self.test_racedays["test_raceday1"]  # full attendance
        raceday_2 = self.test_racedays["test_raceday2"]  # driver 22 missing
        raceday_3 = self.test_racedays["test_raceday3"]  # driver 77 went from 2WD -> 4WD and dns

        locations: List[str] = ["Linköping", "Sandhem", "Slottsbron"]

        racedays = [raceday_1, raceday_2, raceday_3]
        season_points = resultcalculation.calculate_season_points(racedays, locations)

        expected_2wd = resultcalculation.SeasonPoints()
        expected_2wd.points_per_race = {
            rd.Driver(22): [100, 0, 100],
            rd.Driver(88): [95, 95, 95],
            rd.Driver(41): [90, 90, 90],

            rd.Driver(19): [85, 85, 85],
            rd.Driver(38): [80, 80, 80],
            rd.Driver(77): [75, 75, 0],
        }
        expected_2wd.total_points = {
            rd.Driver(22): 200,
            rd.Driver(88): 285,
            rd.Driver(41): 270,

            rd.Driver(19): 255,
            rd.Driver(38): 240,
            rd.Driver(77): 150,
        }
        expected_2wd.total_points_with_drop_race = {
            rd.Driver(22): 200,
            rd.Driver(88): 190,
            rd.Driver(41): 180,

            rd.Driver(19): 170,
            rd.Driver(38): 160,
            rd.Driver(77): 150,
        }
        expected_2wd.drop_race_indices = {
            rd.Driver(22): 1,
            rd.Driver(88): 0,
            rd.Driver(41): 0,

            rd.Driver(19): 0,
            rd.Driver(38): 0,
            rd.Driver(77): 2,
        }
        expected_2wd.race_locations = locations
        expected_2wd.race_participation = {
            rd.Driver(90): [True, False, True],
            rd.Driver(45): [True, True, True],
            rd.Driver(36): [True, True, True],

            rd.Driver(75): [True, True, True],
            rd.Driver(46): [True, True, True],
            rd.Driver(11): [True, True, True],
            rd.Driver(77): [True, True, False],
        }
        expected_4wd = resultcalculation.SeasonPoints()
        expected_4wd.points_per_race = {
            rd.Driver(90): [100, 100, 100],
            rd.Driver(45): [95, 95, 95],
            rd.Driver(36): [90, 90, 90],

            rd.Driver(75): [85, 85, 85],
            rd.Driver(46): [80, 80, 80],
            rd.Driver(11): [75, 75, 75],
            rd.Driver(77): [0, 0, 75],
        }
        expected_4wd.total_points = {
            rd.Driver(90): 300,
            rd.Driver(45): 285,
            rd.Driver(36): 270,

            rd.Driver(75): 255,
            rd.Driver(46): 240,
            rd.Driver(11): 225,
            rd.Driver(77): 75,
        }
        expected_4wd.total_points_with_drop_race = {
            rd.Driver(90): 200,
            rd.Driver(45): 190,
            rd.Driver(36): 180,

            rd.Driver(75): 170,
            rd.Driver(46): 160,
            rd.Driver(11): 150,
            rd.Driver(77): 75,
        }
        expected_4wd.drop_race_indices = {
            rd.Driver(90): 0,
            rd.Driver(45): 0,
            rd.Driver(36): 0,

            rd.Driver(75): 0,
            rd.Driver(46): 0,
            rd.Driver(11): 0,
            rd.Driver(77): 0,
        }
        expected_4wd.race_participation = {
            rd.Driver(90): [True, True, True],
            rd.Driver(45): [True, True, True],
            rd.Driver(36): [True, True, True],

            rd.Driver(75): [True, True, True],
            rd.Driver(46): [True, True, True],
            rd.Driver(11): [True, True, True],
            rd.Driver(77): [False, False, True],
        }
        expected_4wd.race_locations = locations

        racedays = [raceday_1, raceday_2, raceday_3]
        season_points = resultcalculation.calculate_season_points(racedays, locations)

        self.assertEqual(len(season_points), 2)
        self.assertDictEqual(season_points["2WD"].points_per_race,
                             expected_2wd.points_per_race)
        # TODO du är här
