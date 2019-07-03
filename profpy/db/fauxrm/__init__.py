# init file
import functools
from .handlers.Database import Database
from .queries.query import And, Or


def with_fauxrm(login_var="full_login", password_var="db_password"):
    def with_fauxrm_(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            database = Database(login_var, password_var)
            result = f(database, *args, **kwargs)
            database.close()
            return result
        return wrapper
    return with_fauxrm_


def with_model(handler, owner_name, object_name):
    def with_model_(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(handler.model(owner_name, object_name), *args, **kwargs)
        return wrapper
    return with_model_
