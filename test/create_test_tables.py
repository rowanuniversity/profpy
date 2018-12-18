import os
import cx_Oracle
import re
from profpy.db import get_connection

if __name__ == "__main__":

    path = "./test/ddls"
    connection = get_connection("full_login", "db_password")
    cursor = connection.cursor()

    ddls = list(filter(lambda file_name: re.match(re.compile(r"[a-zA-Z_1-9]+\.ddl\.sql$"), file_name),
                       os.listdir(path)))

    for file in ddls:
        with open(os.path.join(path, file), "r") as sql:
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
