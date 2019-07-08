import unittest
import random
import types
from profpy.db import get_connection, execute_query

# db stuff
connection = get_connection("full_login", "db_password")
cursor = connection.cursor()

# some values to use for testing
first_names = ["Dennis", "Ian", "Alan", "John"]
last_names = ["Nedry", "Malcolm", "Grant", "Hammond"]
query = "select * from rowan.fauxrm_test_general_names where id < 10"
break_num = 11  # query should only grab 11 results

# populate the table with 100 random people
first_name_last_index = len(first_names) - 1
last_name_last_index = len(last_names) - 1
sql = "insert into rowan.fauxrm_test_general_names (first_name, last_name) values (:first_name, :last_name)"
for i in range(100):
    first_name = first_names[random.randint(0, first_name_last_index)]
    last_name = last_names[random.randint(0, last_name_last_index)]
    cursor.execute(sql, {"first_name": first_name, "last_name": last_name})


class TestGenerator(unittest.TestCase):
    def test_query(self):
        results = execute_query(cursor, query, use_generator=True)
        self.assertTrue(isinstance(results, types.GeneratorType))

        results = execute_query(cursor, query)
        self.assertFalse(isinstance(results, types.GeneratorType))

    def test_stop_iteration(self):
        results = execute_query(cursor, query, use_generator=True)
        caught = False
        for counter in range(break_num):
            try:
                next(results)
            except StopIteration:
                caught = True
        self.assertTrue(caught)


if __name__ == "__main__":

    unittest.main()
    connection.rollback()
    cursor.close()
    connection.close()
    del cursor
    del connection
