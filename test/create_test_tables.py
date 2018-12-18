import os
import re
import cx_Oracle


def get_connection(login_var, password_var):

    if not all(variable in os.environ for variable in (login_var, password_var)):
        raise Exception("Missing environment variables: '{0}', '{1}'".format(login_var, password_var))

    login = os.environ[login_var]
    password = os.environ[password_var]

    # ex) user@//host:port/service_name
    login_parts = login.split("@")
    user = login_parts[0]
    server = login_parts[1]

    # parse out the port, host, and dsn
    server_parts = server.split(":")
    host = server_parts[0].replace("//", "")
    port_and_service = server_parts[1].split("/")
    port = port_and_service[0]
    service = port_and_service[1]

    return cx_Oracle.connect(user=user, password=password, dsn=cx_Oracle.makedsn(host, port, service_name=service))


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
