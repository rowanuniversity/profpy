import unittest
import datetime
from profpy.db import fauxrm


database = fauxrm.Database()
lobs = database.model("rowan", "fauxrm_test_lobs")
test_clob = "test_clob"
test_blob = b"test_blob"


class TestLOB(unittest.TestCase):
    def test_blob_insert(self):
        new_record = lobs.new(test_blob=test_blob)
        new_record.save()
        self.assertEqual(new_record.test_blob, test_blob)

    def test_bad_blob_insert(self):

        try:
            lobs.new(test_blob="BAD DATA TYPE")
            lobs.save()
            caught = False
        except:
            caught = True
        self.assertTrue(caught)

    def test_blob_find_error(self):

        try:
            lobs.find(test_blob=b"find")
            caught = False
        except:
            caught = True
        self.assertTrue(caught)

    def test_clob_insert(self):
        new_record = lobs.new(test_clob=test_clob)
        new_record.save()
        self.assertEqual(new_record.test_clob, test_clob)

    def test_bad_clob_insert(self):
        try:
            # datetime object should trigger a fail
            lobs.new(test_clob=datetime.datetime.now())
            lobs.save()
            caught = False
        except:
            caught = True
        self.assertTrue(caught)

    def test_clob_find_error(self):
        try:
            lobs.find(test_clob=test_clob)
            caught = False
        except:
            caught = True
        self.assertTrue(caught)


if __name__ == "__main__":
    unittest.main()
    database.rollback()
    database.close()
