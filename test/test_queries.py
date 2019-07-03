"""
The unit testing module for the fauxrm's library's query functionality.

Developed by Connor Hornibrook, 2018
Rowan University
"""
import unittest
import datetime

from profpy.db.fauxrm import Database
from profpy.db.fauxrm.queries import And, Or, Query

db_handler = Database()
medical = db_handler.model("rowan", "fauxrm_test_medical")
TEST_WEIGHT = 300.0
TEST_AGE = 40
TEST_DATE = datetime.datetime(2004, 1, 1, 1, 4, 5, 3)
TEST_FIRST = "Dennis"
TEST_LAST = "Nedry"


def create_new_medical_test_record(in_handler, clear_table=False):
    """
    Creates a new record in the phonebook table and returns the id (primary key) of said new record.

    :param in_handler:  The table handler object
    :param clear_table: Whether or not we want to clear/truncate the testing table prior to this action
    :return:            The id (primary key) of this new record
    """

    if clear_table:
        in_handler.delete_where()
    obj = in_handler.new(
        first_name=TEST_FIRST,
        last_name=TEST_LAST,
        age=TEST_AGE,
        weight=TEST_WEIGHT,
        visit_date=TEST_DATE,
    )
    obj.save()
    return obj


class TestQueryObjects(unittest.TestCase):
    """
    Unit testing for actions related to the Query class and its children And & Or
    """

    def test_args_type_in_constructor(self):

        bad_arg = "foo"
        try:
            Query(bad_arg)
            caught = False
        except TypeError:
            caught = True

        self.assertTrue(caught)

        try:
            Query(And(bad_arg, x="10"), y=11)
            caught = False
        except TypeError:
            caught = True

        self.assertTrue(caught)

        try:
            Query(bad_arg, y=11)
            caught = False
        except TypeError:
            caught = True

        self.assertTrue(caught)

    def test_base(self):

        record = create_new_medical_test_record(medical, clear_table=True)

        # and
        and_ = Query(first_name=TEST_FIRST, last_name=TEST_LAST)

        # or
        or_ = Query(first_name=TEST_FIRST, last_name="zzzz")

        and_result = medical.find_one(and_)
        or_result = medical.find_one(or_)

        self.assertEqual(record, and_result, or_result)

    def test_and(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        and_ = medical.find_one(
            And(first_name=TEST_FIRST, last_name=TEST_LAST, visit_date=TEST_DATE)
        )
        bad = medical.find_one(And(first_name=TEST_FIRST, last_name="x"))

        self.assertEqual(record, and_)
        self.assertIsNone(bad)

    def test_or(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        or_ = medical.find_one(Or(first_name=TEST_FIRST, last_name=TEST_LAST))
        or_2 = medical.find_one(Or(first_name=TEST_FIRST, last_name="x"))
        bad = medical.find_one(Or(first_name="x", last_name="x"))

        self.assertEqual(record, or_, or_2)
        self.assertIsNone(bad)

    def test_and_override(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        and_1 = And(first_name=TEST_FIRST, last_name=TEST_LAST)
        and_2 = And(first_name=TEST_FIRST, visit_date=TEST_DATE)

        # these two should give us the same result
        and_3 = and_1 & and_2
        and_4 = And(first_name=TEST_FIRST, last_name=TEST_LAST, visit_date=TEST_DATE)

        result_1 = medical.find_one(and_3)
        result_2 = medical.find_one(and_4)

        self.assertEqual(record, result_1, result_2)

    def test_or_override(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        statement_1 = And(first_name=TEST_FIRST, last_name=TEST_LAST)
        statement_2 = And(first_name="x", last_name="x")

        # these two should give the same result
        or_1 = statement_1 | statement_2
        or_2 = Or(statement_1, statement_2)

        result_1 = medical.find_one(or_1)
        result_2 = medical.find_one(or_2)
        self.assertEqual(record, result_1, result_2)

    def test_logic_stringing(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        statement_1 = And(first_name=TEST_FIRST, last_name=TEST_LAST)  # True
        statement_2 = And(first_name=TEST_FIRST, last_name="x")  # False
        statement_3 = Or(first_name=TEST_FIRST, last_name="x")  # True
        statement_4 = Or(first_name="x", last_name___like="x%")  # False

        # should give us our test record
        q = And(Or(statement_1, statement_2), Or(statement_3, statement_4))

        result = medical.find_one(q)
        self.assertEqual(record, result)

    def test_deeply_nested_query(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        statement_1 = And(first_name=TEST_FIRST, last_name=TEST_LAST)  # True
        statement_2 = And(first_name=TEST_FIRST, last_name="x")  # False
        statement_3 = And(
            first_name=TEST_FIRST, last_name=TEST_LAST, visit_date=TEST_DATE
        )  # True

        q = Or(
            Or(
                Or(
                    Or(
                        Or(And(statement_1, statement_3), statement_1, statement_2),
                        statement_2,
                    ),
                    statement_2,
                ),
                statement_2,
            ),
            statement_2,
        )
        self.assertEqual(record, medical.find_one(q))

        q = And(
            And(
                And(And(And(statement_1, statement_3), statement_1), statement_1),
                statement_1,
            ),
            statement_1,
        )

        self.assertEqual(record, medical.find_one(q))


class TestOperators(unittest.TestCase):
    def test_gt(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        good = medical.find_one(age___gt=0)
        bad = medical.find_one(age___gt=TEST_AGE)

        self.assertEqual(record, good)
        self.assertIsNone(bad)

    def test_gte(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        good_1 = medical.find_one(age___gte=0)
        good_2 = medical.find_one(age___gte=TEST_AGE)
        bad = medical.find_one(age___gte=TEST_AGE + 1)

        self.assertEqual(record, good_1, good_2)
        self.assertIsNone(bad)

    def test_lt(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        good = medical.find_one(age___lt=TEST_AGE + 1)
        bad = medical.find_one(age___lt=0)

        self.assertEqual(record, good)
        self.assertIsNone(bad)

    def test_lte(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        good_1 = medical.find_one(age___lte=TEST_AGE)
        good_2 = medical.find_one(age___lte=TEST_AGE + 1)
        bad = medical.find_one(age___lte=0)

        self.assertEqual(record, good_1, good_2)
        self.assertIsNone(bad)

    def test_ne(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        good = medical.find_one(age___ne=0)
        bad = medical.find_one(age___ne=TEST_AGE)

        self.assertEqual(record, good)
        self.assertIsNone(bad)

    def test_like(self):

        good_wilds = ("%nis", "Den%", "%nn%")
        bad_wilds = ("%zx", "Al%", "%zzz%")
        good_results, bad_results = [], []
        record = create_new_medical_test_record(medical, clear_table=True)

        for wild in good_wilds:
            good_results.append(medical.find_one(first_name___like=wild))
        for wild in bad_wilds:
            bad_results.append(medical.find_one(first_name___like=wild))

        good = all(r == record for r in good_results)
        bad = all(r is None for r in bad_results)

        self.assertTrue(good)
        self.assertTrue(bad)

    def test_in(self):

        record = create_new_medical_test_record(medical, clear_table=True)

        # try the three different collection types for both positive and negative test cases
        good_tuple = (1, 2, 3, TEST_AGE)
        good_list = [1, 2, 3, TEST_AGE]
        good_set = {1, 2, 3, TEST_AGE}
        bad_tuple = (1, 2, 3)
        bad_list = [1, 2, 3]
        bad_set = {1, 2, 3}

        good_collections = (good_tuple, good_list, good_set)
        bad_collections = (bad_tuple, bad_list, bad_set)

        good_results = []
        bad_results = []

        for collection in good_collections:

            # try both methods
            good_results.append(medical.find_one(age=collection))
            good_results.append(medical.find_one(age___in=collection))

        for collection in bad_collections:

            # try both methods
            bad_results.append(medical.find_one(age=collection))
            bad_results.append(medical.find_one(age___in=collection))

        good = all(r == record for r in good_results)
        bad = all(r is None for r in bad_results)

        self.assertTrue(good)
        self.assertTrue(bad)

    def test_trunc_date(self):

        record = create_new_medical_test_record(medical, clear_table=True)
        truncated_datetime = datetime.datetime.strptime(
            TEST_DATE.strftime("%Y-%m-%d"), "%Y-%m-%d"
        )

        good_1 = medical.find_one(visit_date=TEST_DATE)
        good_2 = medical.find_one(visit_date___trunc=truncated_datetime)
        bad = medical.find_one(visit_date=truncated_datetime)

        self.assertEqual(record, good_1, good_2)
        self.assertIsNone(bad)


if __name__ == "__main__":
    unittest.main()
    db_handler.rollback()
    db_handler.close()
