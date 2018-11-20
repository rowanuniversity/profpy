import cx_Oracle
import os


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


