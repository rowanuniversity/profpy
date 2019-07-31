import cx_Oracle
import os
import re
import functools
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

short_form_regex = re.compile(r"^[a-zA-Z]+[a-zA-Z0-9_]*@[a-zA-Z_]+$")


class OracleConnectionHelper(object):
    """
    Oracle connection string handling/parsing class. This class handles all of the common logic for connecting to
    Oracle databases with both cx_Oracle and sqlalchemy
    """
    def __init__(self, login, password):
        """
        Constructor, chops up login string into individual parts to be used to create connections.
        :param login:    the database login string
        :param password: the database password
        """
        login_parts = login.split("@")

        if re.match(short_form_regex, login):
            username = login_parts[0]
            dsn = login_parts[1]
        else:
            try:
                # parse out the port, host, and dsn
                username = login_parts[0]
                server = login_parts[1]
                server_parts = server.split(":")
                host = server_parts[0].replace("//", "")
                port_and_service = server_parts[1].split("/")
                port = port_and_service[0]
                service = port_and_service[1]
                dsn = cx_Oracle.makedsn(host, port, service_name=service)
            except IndexError:
                raise Exception("Invalid login string.")

        self.__username = username
        self.__password = password
        self.__dsn = dsn
        self.__engine_string = f"oracle://{username}:{password}@{dsn}"

    def get_cx_oracle_connection(self):
        """
        :return: A cx_Oracle connection object
        """
        return cx_Oracle.connect(user=self.__username, password=self.__password, dsn=self.__dsn)

    def get_sql_alchemy_engine(self):
        """
        :return: A sqlalchemy engine object
        """
        return create_engine(self.__engine_string)

    def get_sql_alchemy_session(self, scoped=False, bind=None):
        """
        :param scoped: whether or not to return a scoped session
        :param bind:   an engine to bind the session to, if not specified it defaults to the in-house one
        :return:       a sqlalchemy session object
        """
        session = sessionmaker(bind=bind if bind else self.get_sql_alchemy_engine())
        return scoped_session(session)() if scoped else session()


def with_oracle_connection(login=os.environ.get("full_login"), password=os.environ.get("db_password"),
                           auto_commit=False):
    """
    Decorator that feeds a cx_Oracle connection to the wrapped function
    :param login:        the login string (str), defaults to "full_login" env variable
    :param password:     The password (str), defaults to "db_password" env variable
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
            connection = OracleConnectionHelper(login, password).get_cx_oracle_connection()
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
                if connection:
                    connection.rollback()
                    connection.close()
                del connection
                if exception:
                    raise exception
            return result
        return wrapper
    return with_connection_


def with_oracle_session(login=os.environ.get("full_login"), password=os.environ.get("db_password"), scoped=False,
                        auto_commit=False, bind=None):
    """
    Decorator that passes an Oracle sqlalchemy session to the decorated function
    :param login:       the database login string
    :param password:    the database password
    :param scoped:      whether or not to return a scoped session
    :param auto_commit: whether or not to auto commit after usage
    :param bind:        the engine to bind to, a new one gets created if this is left null
    :return:            a decorated function with an Oracle sqlalchemy session as the first argument
    """
    def with_oracle_session_(f):
        @functools.wraps(f)
        def wrap(*args, **kwargs):
            session = OracleConnectionHelper(login, password).get_sql_alchemy_session(scoped=scoped, bind=bind)
            result = None
            exception = None
            try:
                result = f(session, *args, **kwargs)
            except Exception as e:
                exception = e
            else:
                if auto_commit:
                    session.commit()
            finally:
                session.rollback()
                session.remove()
                if exception:
                    raise exception
            return result
        return wrap
    return with_oracle_session_


def with_oracle_engine(login=os.environ.get("full_login"), password=os.environ.get("db_password")):
    """
    Decorator that passes an Oracle sqlalchemy engine to the decorated function
    :param login:    the database login string
    :param password: the database password
    :return:
    """
    def with_oracle_engine_(f):
        @functools.wraps(f)
        def wrap(*args, **kwargs):
            return f(OracleConnectionHelper(login, password).get_sql_alchemy_engine(), *args, **kwargs)
        return wrap
    return with_oracle_engine_


def get_oracle_session(login=os.environ.get("full_login"), password=os.environ.get("db_password"), scoped=False,
                       bind=None):
    """
    Returns an Oracle sqlalchemy Session object
    :param login:    the database login string
    :param password: the database password
    :param scoped:   whether or not to return a scoped session
    :param bind:        the engine to bind to, a new one gets created if this is left null
    :return:         a Session object
    """
    return OracleConnectionHelper(login, password).get_sql_alchemy_session(scoped=scoped, bind=bind)


def get_oracle_engine(login=os.environ.get("full_login"), password=os.environ.get("db_password")):
    """
    Returns an Oracle sqlalchemy engine
    :param login:    the database login string
    :param password: the database password
    :return:         a sqlalchemy engine
    """
    return OracleConnectionHelper(login, password).get_sql_alchemy_engine()


def get_cx_oracle_connection(login=os.environ.get("full_login"), password=os.environ.get("db_password")):
    """
    Returns a cx_Oracle connection object
    :param login:    the database login string
    :param password: the database password
    :return:         a cx_Oracle connection object
    """
    return OracleConnectionHelper(login, password).get_cx_oracle_connection()


def get_connection(login_var, password_var):
    """
    DEPRECATED

    Returns a cx_Oracle connection object. This is from a legacy version, and it being kept here to avoid making
    a breaking change for users of profpy.
    :param login_var:    the env variable containing the login string
    :param password_var: the env variable containing the password
    :return:             a cx_Oracle connection object
    """
    return get_cx_oracle_connection(os.environ[login_var], os.environ[password_var])
