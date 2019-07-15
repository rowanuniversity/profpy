"""
The generic unit testing module for the fauxrm library's CRUD functionality.

Developed by Connor Hornibrook, 2018
Rowan University
"""
import random
import datetime
import unittest
import cx_Oracle
from profpy.db import fauxrm


# some constants for convenient testing
DATE_FMT = "%d-%b-%y"
TEST_PHONE = "587-272-7275"  # jur-asc-park  :-)

# You think this kind of automation is easy? Or cheap?
TEST_FIRST = "Dennis"
TEST_LAST = "Nedry"

TEST_BAND = "The Beatles"
TEST_BAND_MEMBERS = [
    dict(
        first_name="John", last_name="Lennon", instrument="Guitar", band_name=TEST_BAND
    ),
    dict(
        first_name="Paul", last_name="McCartney", instrument="Bass", band_name=TEST_BAND
    ),
    dict(
        first_name="George",
        last_name="Harrison",
        instrument="Guitar",
        band_name=TEST_BAND,
    ),
    dict(
        first_name="Ringo", last_name="Starr", instrument="Drums", band_name=TEST_BAND
    ),
]


db_handler = fauxrm.Database()
phonebook_table = db_handler.model("rowan", "fauxrm_test_phonebook")
band_member_table = db_handler.model("rowan", "fauxrm_test_band_members")
medical_table = db_handler.model("rowan", "fauxrm_test_medical")
sortest = db_handler.model("saturn", "sortest")


def create_new_band_test_record(in_handler, clear_table=False):
    if clear_table:
        in_handler.delete_where()

    test_dict = TEST_BAND_MEMBERS[0]
    in_handler.new(
        first_name=test_dict["first_name"],
        last_name=test_dict["last_name"],
        instrument=test_dict["instrument"],
        band_name=TEST_BAND,
    ).save()
    return dict(
        band_name=TEST_BAND,
        last_name=test_dict["last_name"],
        instrument=test_dict["instrument"],
    )


def create_new_phonebook_test_record(in_handler, clear_table=False):
    """
    Creates a new record in the phonebook table and returns the id (primary key) of said new record.

    :param in_handler:  The table handler object
    :param clear_table: Whether or not we want to clear/truncate the testing table prior to this action
    :return:            The id (primary key) of this new record
    """

    if clear_table:
        in_handler.delete_where()
    record = in_handler.new(
        first_name=TEST_FIRST, last_name=TEST_LAST, phone=TEST_PHONE
    )
    record.save()
    return record.key


class TestCompositeKeys(unittest.TestCase):
    """
    Test cases for composite key tables
    """

    test_member = TEST_BAND_MEMBERS[0]

    # test that the get method correctly raises an exception when not enough parts of the composite key are specified
    def test_get_key_error(self):
        caught = False
        try:
            band_member_table.get(first_name="John")
        except:
            caught = True
        self.assertTrue(caught)

    # test that the get method works on composite key with dictionary object
    def test_get_key_using_dict_obj(self):
        key = create_new_band_test_record(band_member_table, clear_table=True)
        caught = False
        try:
            band_member_table.get(key)
        except:
            caught = True
        self.assertFalse(caught)

    # test that the get method works on a composite key with kwargs
    def test_get_key_using_kwargs(self):
        key = create_new_band_test_record(band_member_table, clear_table=True)
        caught = False
        try:
            band_member_table.get(
                band_name=key["band_name"],
                last_name=key["last_name"],
                instrument=key["instrument"],
            )
        except:
            caught = True
        self.assertFalse(caught)

    # test that the get method correctly raises an exception when not enough parts of the composite key are specified
    # in a dictionary object
    def test_get_key_error_with_dict_ojb(self):
        key = create_new_band_test_record(band_member_table, clear_table=True)
        caught = False
        key.pop("band_name")  # remove necessary part of the key

        try:
            band_member_table.get(key)
        except:
            caught = True
        self.assertTrue(caught)


class TestProperties(unittest.TestCase):
    """
    Test cases for accessing ddl properties from the table handler object.
    """

    # did the handler set the columns property correctly
    def test_columns(self):
        self.assertIsNotNone(phonebook_table.columns)

    # did the handler set the column descriptions property correctly (field comments in ddl)
    def test_column_descriptions(self):
        descriptions = phonebook_table.column_descriptions
        self.assertIsNotNone(descriptions)
        self.assertTrue(all([d is not None for d in descriptions.keys()]))
        self.assertTrue(all([v is not None for v in descriptions.values()]))

    # did the handler set the table description property correctly (table comments in ddl)
    def test_table_description(self):
        self.assertIsNotNone(phonebook_table.description)

    # did the handler set the table name property correctly
    def test_table_name(self):
        self.assertIsNotNone(phonebook_table.name)

    # did the handler set the primary key field name property correctly
    def test_pk(self):
        self.assertIsNotNone(phonebook_table.primary_key)

    # did the handler set the field mappings property correctly
    def test_field_mapping(self):
        self.assertIsNotNone(phonebook_table.mapping)
        self.assertGreater(len(phonebook_table.mapping.keys()), 0)


class TestCRUD(unittest.TestCase):
    """
    Test cases for the base CRUD functionality
    """

    # test in-statements with collections of more than 1000 (Oracle's max)
    def test_giant_in(self):

        fake_names = []
        for x in range(2000):
            fake_names.append(RandomGenerators.get_random_name()[0])
        try:
            band_member_table.find(first_name___in=fake_names)
            caught = False
        except:
            caught = True

        self.assertFalse(caught)

        # "not in" statement
        try:
            band_member_table.find(first_name___nin=fake_names)
            caught = False
        except:
            caught = True
        self.assertFalse(caught)

    # test for dict-like access of data from Row objects
    def test_dict_access(self):
        test_cols = ["band_name", "last_name", "instrument", "first_name"]
        # create 10 records
        for x in range(10):
            create_new_band_test_record(band_member_table, clear_table=True)
        for record in band_member_table.find(band_name="The Beatles"):
            self.assertTrue(all(col in record.columns for col in test_cols))
            for col, value in record.items():
                self.assertTrue(col in test_cols)
                try:
                    record[col]
                    caught = False
                except KeyError:
                    caught = True
                self.assertFalse(caught)

    # can the handler clear the table correctly without a where clause
    def test_delete_where(self):
        phonebook_table.delete_where()
        self.assertEqual(phonebook_table.count, 0)

    # can the handler correctly insert one record using keyword arguments
    def test_insert_one(self):
        phonebook_table.delete_where()
        name, phone = (
            RandomGenerators.get_random_name(),
            RandomGenerators.get_random_phone_number(),
        )
        phonebook_table.new(first_name=name[0], last_name=name[1], phone=phone).save()
        self.assertEqual(phonebook_table.count, 1)

    # can the handler correctly identify a bad input keyword in a raw dictionary
    def test_bad_keywords(self):

        results = []
        for insert in (
            {"zzzz": TEST_FIRST, "last_name": TEST_LAST},
            dict(zzzz=TEST_FIRST, last_name=TEST_LAST),
        ):

            try:
                phonebook_table.new(**insert).save()
                results.append(False)
            except cx_Oracle.DatabaseError:
                results.append(True)

        self.assertTrue(all(r is True for r in results))

    # can the handler correctly insert a bunch of records (5000) using keyword arguments
    def test_insert_5000(self):

        self.test_delete_where()
        for i in range(5000):
            name, phone = (
                RandomGenerators.get_random_name(),
                RandomGenerators.get_random_phone_number(),
            )
            phonebook_table.new(
                first_name=name[0], last_name=name[1], phone=phone
            ).save()
        self.assertEqual(phonebook_table.count, 5000)

    # can the handler access records using their primary keys correctly
    def test_get(self):
        test_id = create_new_phonebook_test_record(phonebook_table, clear_table=True)
        record = phonebook_table.get(key=test_id)
        self.assertIsNotNone(record)

    # can the handler appropriately return null when the user tries to get a record that no longer exists at a key
    def test_null_id(self):
        test_id = create_new_phonebook_test_record(phonebook_table, clear_table=True)
        self.test_delete_where()
        should_be_null = phonebook_table.get(test_id)
        self.assertIsNone(should_be_null)

    # can the handler appropriately update record using keyword arguments
    def test_update(self):
        test_key = create_new_phonebook_test_record(phonebook_table, clear_table=True)
        old_version = phonebook_table.get(test_key)

        new_last_name = "Jones"
        old_version.last_name = new_last_name
        old_version.save()
        self.assertEqual(old_version.last_name, new_last_name)

    # can the handler search on null values correctly
    def test_find_on_null_value(self):
        phonebook_table.delete_where()
        new_record = phonebook_table.new(
            first_name=TEST_FIRST, last_name=TEST_LAST
        )  # phone number will be null
        new_record.save()
        results = list(phonebook_table.find(phone=None))
        num_results = len(results)

        self.assertGreater(num_results, 0)
        self.assertEqual(num_results, 1)

        record = results[0]
        self.assertEqual(record.first_name, TEST_FIRST)
        self.assertEqual(record.last_name, TEST_LAST)

    # can the handler correctly insert new data using all of the different accepted argument types
    def test_insert_types(self):
        phonebook_table.delete_where()
        success_one, success_two, success_three, success_four = True, True, True, True

        # kwargs
        try:
            phonebook_table.new(
                first_name=TEST_FIRST, last_name=TEST_LAST, phone=TEST_PHONE
            ).save()
        except:
            success_one = False
        self.assertTrue(success_one)

        # dict constructor
        try:
            phonebook_table.new(
                **dict(first_name=TEST_FIRST, last_name=TEST_LAST, phone=TEST_PHONE)
            ).save()
        except Exception as e:
            print(e)
            success_two = False
        self.assertTrue(success_two)

        # raw dict with matching case keys to the handler's fields
        try:
            phonebook_table.new(
                **{
                    "first_name": TEST_FIRST,
                    "last_name": TEST_LAST,
                    "phone": TEST_PHONE,
                }
            ).save()
        except:
            success_three = False
        self.assertTrue(success_three)

        # raw dict with upper cased keys that don't match the handler's fields (should still work)
        try:
            phonebook_table.new(
                **{
                    "FIRST_NAME": TEST_FIRST,
                    "LAST_NAME": TEST_LAST,
                    "PHONE": TEST_PHONE,
                }
            ).save()
        except:
            success_four = False
        self.assertTrue(success_four)

    # can the handler correctly prevent invalid data types being entered into fields
    def test_mapping_types(self):
        medical_table.delete_where()
        test_record = dict(
            first_name="Dennis", last_name="Nedry", visit_date=datetime.datetime.now()
        )
        test_record = medical_table.new(**test_record).save()

        # try to insert a string value into a numeric field
        caught = False
        try:
            test_record.age = "this is a string"
            test_record.save()
        except:
            caught = True
        self.assertTrue(caught)

        # try to insert a datetime into a float field
        caught = False
        try:
            test_record.weight = datetime.datetime.now()
            test_record.save()
        except:
            caught = True
        self.assertTrue(caught)

    # can the handler correctly prevent null values from being inserted into non-nullable fields
    def test_mapping_nulls(self):
        phonebook_table.delete_where()

        # try to insert a null on a non-nullable field
        caught = False
        try:
            x = phonebook_table.new(id=None)
            x.save()
        except:
            caught = True
        self.assertTrue(caught)


class TestDates(unittest.TestCase):
    """
    The date testing will use the medical test table.
    """

    test_dates = [
        datetime.datetime.strptime("18-OCT-05", DATE_FMT),
        datetime.datetime.strptime("01-DEC-05", DATE_FMT),
        datetime.datetime.strptime("04-JAN-10", DATE_FMT),
    ]
    single_test_date = datetime.datetime.strptime("18-OCT-05", DATE_FMT)
    test_value = dict(
        first_name="Dennis", last_name="Nedry", visit_date=single_test_date
    )
    test_date_fmt = "%d-%b-%y"

    # can the handler find a record using a list of possible dates
    def test_find_date_in_collection(self):

        medical_table.delete_where()
        medical_table.new(**self.test_value).save()

        results = medical_table.find(visit_date=self.test_dates)
        self.assertEqual(len(list(results)), 1)

    # can the handlers handle date strings
    def test_date_string(self):
        medical_table.delete_where()
        medical_table.new(**self.test_value).save()
        results = medical_table.find_one(
            visit_date=self.single_test_date.strftime(self.test_date_fmt)
        )
        self.assertIsNotNone(results)


class RandomGenerators(object):
    """
    Some helper methods for testing
    """

    @staticmethod
    def get_random_name():
        """
        Generates a name by randomly combining a first and last name from the two lists of Jurassic Park character
        first/last name combos
        :return: A testing name
        """

        first_names = [
            "Ian",
            "Alan",
            "Dennis",
            "John",
            "Ellie",
            "Robert",
            "Lex",
            "Ray",
            "Tim",
            "Donald",
            "Lewis",
            "Henry",
        ]
        last_names = [
            "Sattler",
            "Malcolm",
            "Grant",
            "Nedry",
            "Muldoon",
            "Hammond",
            "Wu",
            "Gennaro",
            "Dodgson",
            "Murphy",
            "Arnold",
        ]

        first_name = first_names[random.randint(0, len(first_names) - 1)]
        last_name = last_names[random.randint(0, len(last_names) - 1)]
        return first_name, last_name

    @staticmethod
    def get_random_phone_number():
        """
        Generates a random 12-character (with dashes), 10-digit phone number
        :return: A random phone number for testing with the phonebook table
        """

        phone_number = ""
        for i in range(7):
            phone_number += "-" if i == 3 else str(random.randint(0, 9))
        phone_number += "-"
        for i in range(4):
            phone_number += str(random.randint(0, 9))
        return phone_number


if __name__ == "__main__":
    unittest.main()
    db_handler.rollback()
    db_handler.close()
