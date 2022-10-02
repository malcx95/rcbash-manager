from pyfakefs.fake_filesystem_unittest import TestCase
from pathlib import Path
import unittest
import json
import db
import os


TEST_DATABASE_PATH = "./testdata/testdatabases"


class DBTests(TestCase):

    test_databases = None

    @classmethod
    def setUpClass(cls):
        cls.test_databases = {}
        database_files = os.listdir(TEST_DATABASE_PATH)
        for database in database_files:
            path = os.path.join(TEST_DATABASE_PATH, database)
            name = database.split(".json")[0]
            with open(path) as f:
                cls.test_databases[name] = db._replace_with_durations(json.load(f))

    def setUp(self):
        self.setUpPyfakefs(modules_to_reload=[db])
        db.RESULT_FOLDER_PATH = Path("test_rcbash_results")
        db.RESULT_FOLDER_PATH.mkdir(exist_ok=True)

    def test_roundtrip_serialize(self):
        for db_name, test_db_json in self.test_databases.items():
            with self.subTest(db_name):
                database = db.Database(db._replace_with_durations(test_db_json))
                database._write_database(db_name + ".json")
                
                with open(db.RESULT_FOLDER_PATH / (db_name + ".json")) as f:
                    saved_db = db._replace_with_durations(json.load(f))

                self.assertDictEqual(db._replace_with_durations(test_db_json), saved_db,
                                     "Saved database differs from loaded!")

if __name__ == "__main__":
    unittest.main()
