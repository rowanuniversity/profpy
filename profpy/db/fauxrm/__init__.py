# init file
import functools
import re
import threading
import time
from flask import Flask
from .handlers.Database import Database
from .queries.query import And, Or


def with_fauxrm(login_var="full_login", password_var="db_password"):
    """
    Decorator that passes in a fauxrm.Database object to the decorated function
    :param login_var:    The environment variable containing the login string
    :param password_var: The environment variable containing the password string
    :return:             The decorated function, with a fauxrm.Database object as its first argument value
    """

    def with_fauxrm_(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            database = Database(login_var, password_var)
            result = f(database, *args, **kwargs)
            database.close()
            return result

        return wrapper

    return with_fauxrm_


def with_model(database_handler, owner_name, object_name):
    """
    Decorator that passes in a fauxrm model to the decorated function
    :param database_handler: the fauxrm.Database object being used in this application
    :param owner_name:       the owner of the table/view
    :param object_name:      the name of the table/view
    :return:                 a decorated function with the created fauxrm model as its first argument value
    """

    def with_model_(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(database_handler.model(owner_name, object_name), *args, **kwargs)

        return wrapper

    return with_model_


class ModelAttribute(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


class FauxrmApp(Flask):
    """
    Child of the Flask application object that helps with using fauxrm models with web apps. Database objects are
    supplied at initialization and the models are created with the startup of the app. This way, new models don't have
    to be created outside of the app's scope/context, and shouldn't affect the performance of individual endpoints.
    """

    def __init__(
        self,
        module_name,
        db_objects,
        login_var="full_login",
        password_var="db_password",
        keep_alive_interval=20
    ):
        """
        Constructor
        :param module_name:        The name of the module (most likely will always be __name__)
        :param db_objects:         A list of database objects following the [owner.table, owner.table, ...] format.
        :param login_var:          Environment variable containing db login string
        :param password_var:       Environment variable containing db password string
        :param keep_alive_interval The number of seconds between database connection "keep alive" calls
        """
        if not FauxrmApp.valid_db_object_list(db_objects):
            raise ValueError("Invalid list of database objects given.")
        super().__init__(module_name)
        self.__login_var = login_var
        self.__password_var = password_var
        self.db = Database(login_var, password_var)
        self.teardown_appcontext = self.teardown

        for db_obj in FauxrmApp.split_db_object_names(db_objects):
            owner = db_obj["owner"]
            if not hasattr(self, owner):
                setattr(self, owner, ModelAttribute())
            getattr(self, owner)[db_obj["object_name"]] = self.db.model(**db_obj)

        # start up a daemon that continuously pings the database this application is using to avoid a timeout
        self.__keep_alive_interval = keep_alive_interval
        self.__keep_up = threading.Thread(target=self.__keep_alive, args=(), daemon=True)
        self.__keep_up.start()

    def __keep_alive(self):
        """
        Function used by the self.__keep_up daemon to ping the database
        :return:
        """
        while True:
            self.db.ping()
            time.sleep(self.__keep_alive_interval)

    def teardown(self, exception):
        """
        Close Database object at app teardown, this is just an extra layer of protection as this step should be handled
        by garbage collection in the Database class' __del__ method.
        :param exception: Any exception from the app teardown
        :return:
        """
        self.db.close()

    @staticmethod
    def valid_db_object_list(in_list):
        """
        Validator method for the input list of database object names.
        :param in_list: The list of object names
        :return:        Whether or not all of the object names are valid
        """
        regex = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z][a-zA-Z0-9_]*$")
        return all(re.match(regex, obj) for obj in in_list)

    @staticmethod
    def split_db_object_names(in_list):
        """
        Splits the database objects input into owner and name combinations that can be used to create fauxrm models.
        :param in_list: The list of input database objects
        :return:        The list of parsed owner-name pairs
        """
        out_names = []
        for obj in in_list:
            parts = obj.split(".")
            out_names.append(dict(owner=parts[0], object_name=parts[1]))
        return out_names
