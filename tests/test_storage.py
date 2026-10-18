"""Tests for JSON persistence and error handling."""

import json
import os
import tempfile
import unittest

from utils.storage import load_data, save_data
from utils.validators import parse_due_date


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "sub", "data.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_missing_file_gives_empty_data(self):
        self.assertEqual(load_data(self.path), {"users": [], "projects": [], "tasks": []})

    def test_save_creates_folder_and_round_trips(self):
        payload = {"users": [{"id": 1, "name": "A"}], "projects": [], "tasks": []}
        save_data(payload, self.path)
        self.assertEqual(load_data(self.path), payload)

    def test_corrupt_json_is_backed_up(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, "w") as handle:
            handle.write("{ not json")
        data = load_data(self.path)
        self.assertEqual(data["users"], [])
        self.assertTrue(os.path.exists(self.path + ".corrupt"))

    def test_wrong_shape_is_treated_as_corrupt(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, "w") as handle:
            json.dump([1, 2, 3], handle)
        self.assertEqual(load_data(self.path)["tasks"], [])


class TestDateParsing(unittest.TestCase):
    def test_parses_various_formats(self):
        self.assertEqual(parse_due_date("2026-12-31"), "2026-12-31")
        self.assertEqual(parse_due_date("1 Dec 2026"), "2026-12-01")

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            parse_due_date("next-ish week")


if __name__ == "__main__":
    unittest.main()
