import cx_Oracle
from functions import get_connection

if __name__ == "__main__":

    with get_connection("full_login", "db_password") as connection:
        cursor = connection.cursor()
        with open("./test/teardown.ddl.sql", "r") as sql:
            for drop_statement in sql.read().split(";"):
                try:
                    cursor.execute(drop_statement)
                except cx_Oracle.DatabaseError:
                    pass
        cursor.close()
        del cursor
    del connection
