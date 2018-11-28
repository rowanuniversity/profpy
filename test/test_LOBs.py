import unittest
from db import fauxrm
from db.fauxrm import And, Or


database = fauxrm.Database()


class TestLOB(unittest.TestCase):

    def test_blob_insert(self):
        pass


if __name__ == "__main__":
    unittest.main()
    database.close()
