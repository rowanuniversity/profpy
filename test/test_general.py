import unittest
import random
import types
from profpy.db import get_connection, execute_sql, sql_file_to_text, results_to_generator

connection = get_connection("full_login", "db_password")
cursor     = connection.cursor()

first_names = ["Dennis", "Ian", "Alan", "John"]
last_names  = ["Nedry", "Malcolm", "Grant", "Hammond"]


first_name_last_index = len(first_names) - 1
last_name_last_index  = len(last_names) - 1
sql = "insert into rowan.fauxrm_test_general_names (first_name, last_name) values (:first_name, :last_name)"
for i in range(100):
    first_name = first_names[random.randint(0, first_name_last_index)]
    last_name  = last_names[random.randint(0, last_name_last_index)]
    cursor.execute(sql, {"first_name": first_name, "last_name": last_name})


class TestGenerator(unittest.TestCase):

    def test_query(self):
        query = "select * from rowan.fauxrm_test_general_names where id < 10"
        results = execute_sql(cursor, query, use_generator=True)
        self.assertTrue(isinstance(results, types.GeneratorType))

        results = execute_sql(cursor, query)
        self.assertFalse(isinstance(results, types.GeneratorType))


if __name__ == "__main__":

    unittest.main()
    connection.rollback()
    cursor.close()
    connection.close()
    del cursor
    del connection
