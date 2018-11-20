import os
import re
import cx_Oracle
from db.connections import get_connection

if __name__ == "__main__":
    connection = get_connection("host_pprd", "db_password")
    cursor = connection.cursor()

    ddls = list(filter(lambda file_name: re.match(re.compile(r"[a-zA-Z_1-9]+_ddl.sql$"), file_name), os.listdir(".")))

    concat_sql = ""
    for file in ddls:
        with open(file, "r") as sql:
            statements = sql.read().split(";")
            for statement in statements:
                statement = statement.lstrip().rstrip()
                if statement != "" and statement is not None:
                    try:
                        cursor.execute(statement)
                    except cx_Oracle.DatabaseError as db_error:
                        print("######################################################################")
                        print("Could not execute the following SQL:")
                        print(statement)
                        print()
                        connection.rollback()

    cursor.close()
    connection.close()
    del cursor, connection
