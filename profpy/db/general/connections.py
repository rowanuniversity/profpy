import cx_Oracle
import os
import re
import functools
from sqlalchemy import create_engine, MetaData
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


def _cx_oracle_wrapper_logic(f, login, password, auto_commit, *args, **kwargs):
    """
    Common logic between Oracle connection decorators. This was made to avoid duplicate code and to avoid making
    breaking changes to the library for people using it
    :param f:            the function being wrapped
    :param login:        Oracle login string
    :param password:     Oracle password
    :param auto_commit:  Whether or not to auto-commit at the end of the transaction
    :param args:         Additional args from the decorated function
    :param kwargs:       Additional kwargs from the decorated function
    :return:             Decorated function
    """
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


def with_cx_oracle_connection(login=os.environ.get("full_login"), password=os.environ.get("db_password"),
                              auto_commit=False):
    """
    Decorator that feeds a cx_Oracle connection to the wrapped function
    :param login:        the login string (str), defaults to "full_login" env variable
    :param password:     The password (str), defaults to "db_password" env variable
    :param auto_commit:  Whether or not to auto-commit any changes to the database
    :return:             A wrapped function with a connection


    Example:

    @with_cx_oracle_connection()
    def database_task(connection, query):
        cursor = connection.cursor()
        # other code
    """
    def with_connection_(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return _cx_oracle_wrapper_logic(f, login, password, auto_commit, *args, **kwargs)
        return wrapper
    return with_connection_


def with_sql_alchemy_model(engine, owner, object_name):
    """
    Decorator that feeds a Sql-Alchemy model to the decorated function
    :param engine:       A Sql-Alchemy engine
    :param owner:        The schema/owner of the table/view
    :param object_name:  The name of the table/view
    :return:
    """
    def with_sql_alchemy_model_(f):
        @functools.wraps(f)
        def wrap(*args, **kwargs):
            md = MetaData(engine, schema=owner)
            md.reflect(only=[object_name], views=True)
            model = None
            for tbl_name, tbl_obj in md.tables.items():
                if tbl_name == f"{owner}.{object_name}":
                    model = tbl_obj
            return f(model, *args, **kwargs)
        return wrap
    return with_sql_alchemy_model_


def with_oracle_connection(login=os.environ.get("full_login"), password=os.environ.get("db_password"),
                           auto_commit=False):
    """
    DEPRECATED

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
            return _cx_oracle_wrapper_logic(f, login, password, auto_commit, *args, **kwargs)
        return wrapper
    return with_connection_


def with_sql_alchemy_oracle_session(login=os.environ.get("full_login"), password=os.environ.get("db_password"),
                                    scoped=False, auto_commit=False, bind=None):
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
                session.close()
                if exception:
                    raise exception
            return result
        return wrap
    return with_oracle_session_


def with_sql_alchemy_oracle_engine(login=os.environ.get("full_login"), password=os.environ.get("db_password")):
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


def with_sql_alchemy_oracle_connection(login=os.environ.get("full_login"), password=os.environ.get("db_password"),
                                       auto_commit=False, engine=None):
    """
    Decorator that passes in a sqlalchemy connection the decorated function
    :param login:       the database login
    :param password:    the database password
    :param auto_commit: whether or not to commit the transaction after usage
    :param engine:      an optional engine to use for this connection
    :return:            a decorated function with a sqlalchemy connection passed in as the first argument
    """
    def with_sql_alchemy_connection_(f):
        @functools.wraps(f)
        def wrap(*args, **kwargs):
            in_engine = engine if engine else OracleConnectionHelper(login, password).get_sql_alchemy_engine()
            connection = in_engine.connect()
            transaction = connection.begin()
            result = None
            exception = None
            try:
                result = f(connection, *args, **kwargs)
            except Exception as e:
                exception = e
            else:
                if auto_commit and connection and transaction:
                    transaction.commit()
            finally:
                if transaction:
                    transaction.rollback()
                    transaction.close()
                if connection:
                    connection.close()
                if exception:
                    raise exception
            return result
        return wrap
    return with_sql_alchemy_connection_


def get_sql_alchemy_oracle_model(engine, object_owner, object_name, return_relationships=False):
    """
    Returns an auto-generated Sql-Alchemy model based on the given parameters.
    :param engine: The Sql-Alchemy engine being used to create this class
    :param object_owner:         The owner of the table/view in the database.
    :param object_name:          The name of the table/view
    :param return_relationships: Whether or not to return all auto-generated models. If a table with a foreign key
                                 is modeled, that source tables for the key are also modeled.
    :return:                     A model or list of models, depending on the parameters
    """
    md = MetaData(engine, schema=object_owner)
    md.reflect(only=[object_name], views=True)

    if return_relationships:
        return md.tables.items()
    else:
        model = None
        for tbl_name, tbl_obj in md.tables.items():
            if tbl_name == f"{object_owner}.{object_name}":
                model = tbl_obj
        return model


def get_sql_alchemy_oracle_session(login=os.environ.get("full_login"), password=os.environ.get("db_password"),
                                   scoped=False, bind=None):
    """
    Returns an Oracle sqlalchemy Session object
    :param login:    the database login string
    :param password: the database password
    :param scoped:   whether or not to return a scoped session
    :param bind:        the engine to bind to, a new one gets created if this is left null
    :return:         a Session object
    """
    return OracleConnectionHelper(login, password).get_sql_alchemy_session(scoped=scoped, bind=bind)


def get_sql_alchemy_oracle_engine(login=os.environ.get("full_login"), password=os.environ.get("db_password")):
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
