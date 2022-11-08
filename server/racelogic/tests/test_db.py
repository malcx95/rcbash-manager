from pyfakefs.fake_filesystem_unittest import TestCase
from pathlib import Path
import unittest
import json
import server.racelogic.raceday as rd
import os


TEST_DATABASE_PATH = Path(__file__).parent / "testdata" / "testdatabases"


class DBTests(TestCase):

    test_racedays = None

    @classmethod
    def setUpClass(cls):
        cls.test_racedays = {}
        raceday_files = os.listdir(TEST_DATABASE_PATH)
        for raceday_name in raceday_files:
            path = os.path.join(TEST_DATABASE_PATH, raceday_name)
            name = raceday_name.split(".json")[0]
            with open(path) as f:
                cls.test_racedays[name] = rd._replace_with_durations(json.load(f))

    def setUp(self):
        self.setUpPyfakefs(modules_to_reload=[rd])
        rd.RESULT_FOLDER_PATH = Path("test_rcbash_results")
        rd.RESULT_FOLDER_PATH.mkdir(exist_ok=True)

    def test_roundtrip_serialize(self):
        for raceday_name, test_raceday_json in self.test_racedays.items():
            with self.subTest(raceday_name):
                raceday = rd.Raceday(rd._replace_with_durations(test_raceday_json))
                raceday._write_raceday(raceday_name + ".json")
                
                with open(rd.RESULT_FOLDER_PATH / (raceday_name + ".json")) as f:
                    saved_raceday = rd._replace_with_durations(json.load(f))

                self.assertDictEqual(rd._replace_with_durations(test_raceday_json), saved_raceday,
                                     "Saved raceday differs from loaded!")

if __name__ == "__main__":
    unittest.main()
