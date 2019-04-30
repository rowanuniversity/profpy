# init file
from .handlers.Database import Database
from .queries.query import And, Or


def with_fauxrm(login_var="full_login", password_var="db_password"):
    def with_fauxrm_(f):
        import functools

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            from .handlers.Database import Database
            database = Database(login_var, password_var)
            result = f(database, *args, **kwargs)
            database.close()
            return result
        return wrapper
    return with_fauxrm_
