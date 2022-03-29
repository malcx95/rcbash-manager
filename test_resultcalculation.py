import resultcalculation
from pathlib import Path
from pyfakefs.fake_filesystem_unittest import TestCase
import unittest.mock as mock


class ResultCalculationTests(TestCase):

    def setUp(self):
        self.setUpPyfakefs(modules_to_reload=[resultcalculation])
        resultcalculation.RESULT_FOLDER_PATH = Path("test_rcbash_results")

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

