import cx_Oracle
import os
import re


def get_connection_parts_short_form(login, password):

    # ex) user@service
    login_parts = login.split("@")
    user, service = login_parts[0], login_parts[1]

    return {"user": user, "password": password, "dsn": service}


def get_connection_parts_long_form(login, password):

    # ex) user@//host:port/service_name
    login_parts = login.split("@")
    user, server = login_parts[0], login_parts[1]

    # split the port and the host, strip the leading "//"
    server_parts = server.split(":")
    host = server_parts[0].replace("//", "")

    # parse out the service name, create the dsn string
    port_and_service_name = server_parts[1].split("/")
    port, service_name = port_and_service_name[0], port_and_service_name[1]

    dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
    return {"user": user, "password": password, "dsn": dsn}


def get_connection(login_var, password_var):

    patterns = (
        {"pattern": re.compile(r"[a-zA-Z]+@[a-zA-Z]+"), "function": get_connection_parts_short_form},
        {"pattern": re.compile(r"^[a-zA-Z]+([a-zA-Z]|\d)*@//([a-zA-Z]|\d|\.)+:\d{4}/[a-zA-Z]+([a-zA-Z]|\d|\.)*$"),
         "function": get_connection_parts_long_form}
    )

    env_vars = os.environ.keys()
    if not (login_var in env_vars and password_var in env_vars):
        raise ValueError("Environment variables not found on this server.")

    else:
        connection_string = os.environ[login_var]
        num_patterns = len(patterns)
        i = 0

        func = None
        while func is None and i < num_patterns:
            pair = patterns[i]
            pattern = pair["pattern"]

            if re.match(pattern, connection_string):
                func = pair["function"]

            i += 1

        if func is None:
            raise ValueError("Invalid connection string.")

        else:

            login_parts = func(connection_string, os.environ[password_var])
            user, password, dsn = login_parts["user"], login_parts["password"], login_parts["dsn"]
            return cx_Oracle.connect(user=user, password=password, dsn=dsn)
