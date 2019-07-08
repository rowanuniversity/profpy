import cx_Oracle
import os
import re
import functools

short_form_regex = re.compile(r"^[a-zA-Z]+[a-zA-Z0-9_]*@[a-zA-Z_]+$")


def get_connection(login_var, password_var):

    if not all(variable in os.environ for variable in (login_var, password_var)):
        raise Exception(
            "Missing environment variables: '{0}', '{1}'".format(
                login_var, password_var
            )
        )
    else:
        return _get_connection_raw(os.environ[login_var], os.environ[password_var])


def _get_connection_raw(login, password):

    login_parts = login.split("@")

    # user@sid
    if re.match(short_form_regex, login):
        user = login_parts[0]
        dsn = login_parts[1].replace("//", "")

    # user@//host:port/service_name
    else:

        try:
            user = login_parts[0]
            server = login_parts[1]

            # parse out the port, host, and dsn
            server_parts = server.split(":")
            host = server_parts[0].replace("//", "")
            port_and_service = server_parts[1].split("/")
            port = port_and_service[0]
            service = port_and_service[1]
            dsn = cx_Oracle.makedsn(host, port, service_name=service)
        except IndexError:
            raise Exception("Invalid login string.")

    return cx_Oracle.connect(user=user, password=password, dsn=dsn)


def _cleanup_connection(in_connection):
    if in_connection:
        in_connection.rollback()
        in_connection.close()


def with_oracle_connection(
    login_var="full_login", password_var="db_password", auto_commit=False
):
    """
    Decorator that feeds a cx_Oracle connection to the wrapped function
    :param login_var:    The env. variable containing the login string (str), defaults to "full_login"
    :param password_var: The env. variable containing the password (str), defaults to "db_password"
    :param auto_commit:  Whether or not to auto-commit any changes to the database
    :return:             A wrapped function with a connection


    Example:

    @with_oracle_connection()
    def database_task(connection, query):
        cursor = connection.cursor()
        # other code
    """

    def with_connection_(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            connection = get_connection(login_var, password_var)
            result = None
            exception = None
            try:
                result = f(connection, *args, **kwargs)
            except Exception as e:
                exception = e
            else:
                if auto_commit:
                    connection.commit()
            finally:
                _cleanup_connection(connection)
                del connection
                if exception:
                    raise exception
            return result

        return wrapper

    return with_connection_
