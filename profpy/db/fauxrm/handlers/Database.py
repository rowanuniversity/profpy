import cx_Oracle
import datetime
from .DatabaseObjects import Table, View
from .utils import results_to_objs, validate_params
from ... import get_connection

FULL_LOGIN = "full_login"
DB_PASSWORD = "db_password"


class Database(object):

    __IO_ERROR_MSG = "Cannot open the file that was given."

    def __init__(self, login_var=FULL_LOGIN, password_var=DB_PASSWORD):
        """
        Constructor
        :param login_var:     An environment variable containing an Oracle connection string
        :param password_var: An environment variable containing an Oracle password
        """

        self.__connection = get_connection(login_var, password_var)
        self.cursor = self.__connection.cursor()  # a cursor for internal sql calls
        self.__ping_cursor = self.__connection.cursor()
        self.user = self.__get_current_user()
        self.tables = {}
        self.views = {}

    ####################################################################################################################
    # OVERRIDES
    def __enter__(self):
        """
        Context management for object instantiation
        :return:
        """
        return self

    def __exit__(self, exception_type, exception_val, trace):
        """
        Context management for object destruction
        :param exception_type:
        :param exception_val:
        :param trace:
        :return:
        """
        self.close()

    def __del__(self):
        self.close()

    ####################################################################################################################
    def ping(self):
        """
        Simple connection keep-alive/healthcheck method
        :return:
        """
        self.__ping_cursor.execute("select 1 from dual")

    def model(self, owner, object_name):
        """
        Returns a Table or View object based on the given parameters.
        :param owner:       The object's owner   (str)
        :param object_name: The object's name    (str)
        :return:            The object           (Object - Table or View)
        """
        if self.__object_exists(owner, object_name):
            object_type = self.__get_object_type(owner, object_name)
            if object_type == "view":
                model = self.__model_view(owner, object_name)
            elif object_type == "table":
                model = self.__model_table(owner, object_name)
            else:
                raise Exception("Invalid object type. Must be table or view.")
            return model
        else:
            raise Exception("Specified table or view does not exist.")

    def __model_view(self, owner, view_name):
        """
        Returns a view object based on the given info
        :param owner:     The owner of the view (str)
        :param view_name: The name of the view  (str)
        :return:          A View object         (View)
        """
        view = View(owner, view_name, self)
        if owner in list(self.views.keys()):
            self.views[owner][view_name] = view
        else:
            self.views[owner] = {view_name: view}
        return view

    def __model_table(self, owner, table_name):
        """
        Returns a Table object based on the given info
        :param owner:      The owner of the Table (str)
        :param table_name: The name of the table  (str)
        :return:           A Table object         (Table)
        """

        table = Table(owner, table_name, self)
        if owner in list(self.tables.keys()):
            self.tables[owner][table_name] = table
        else:
            self.tables[owner] = {table_name: table}
        return table

    def execute_query(self, query, params=None, limit=None):
        """
        Executes a sql query and returns the results
        :param query:    The sql query to be executed                       (str)
        :param params:   The parameters for the query                       (dict)
        :param limit:    A cap on the number of rows returned               (int)
        :return:         A list of Row objects from the result of the query (list)
        """

        if limit is not None and limit < 1:
            raise ValueError("Limit must be greater than 0.")
        self.cursor.execute(query, validate_params(params))
        return results_to_objs(self.cursor, get_row_objs=True)

    def execute_function(self, owner, function_name, *args):
        """
        Executes an Oracle function
        :param owner:         The schema owner of the function       (str)
        :param function_name: The name of the function               (str)
        :param args:          Any ordered parameters to the function (*args)
        :return:              The value returned by the function     ( any )
        """
        if self.__object_exists(owner, function_name, "function"):
            function_concat = owner + "." + function_name
            params = {}
            for i, a in enumerate(args):
                good_arg = a
                if isinstance(a, str):
                    if a.lower() == "sysdate":
                        good_arg = datetime.datetime.now()
                params["a_{0}".format(i)] = good_arg
            params_sql = ", ".join(":{0}".format(k) for k in list(params.keys()))
            sql = "select {0}({1}) from dual".format(function_concat, params_sql)
            self.cursor.execute(sql, params)
            rows = self.cursor.fetchone()
            return rows[0] if rows else None
        else:
            raise Exception("Function does not exist.")

    def execute_sql_from_file(self, in_file):
        """
        Executes sql from a .sql file using the current connection
        :param in_file: The path to a .sql file (str)
        :return:
        """
        with open(in_file, "r") as sql_file:
            data = None
            try:
                self.cursor.execute(sql_file.read())
                data = results_to_objs(self.cursor)
            except cx_Oracle.DatabaseError:
                pass
            finally:
                return data

    def execute_sql(self, sql, params=None):
        """
        Executes a general sql statement, doesn't return anything.
        :param sql:    The sql to be executed (str)
        :param params: The parameters         (dict)
        :return:       Nothing
        """
        self.cursor.execute(sql, validate_params(params))

    def commit(self):
        """
        Commit changes to the database
        :return:
        """
        self.__connection.commit()

    def rollback(self):
        """
        Rollback database changes
        :return:
        """
        self.__connection.rollback()

    def close(self):
        """
        Closes this handler and its corresponding connection and cursor objects
        :return:
        """
        try:
            self.__connection.rollback()
        except cx_Oracle.DatabaseError:
            pass

        for field in [self.__ping_cursor, self.cursor, self.__connection]:
            try:
                field.close()
                field = None

            # these exceptions are thrown if the connection or cursor are no longer open, respectively
            except cx_Oracle.DatabaseError:
                pass
            except cx_Oracle.InterfaceError:
                pass

        return True

    @property
    def name(self):
        """
        :return: The name of the database
        """
        self.cursor.execute("select name from v$database")
        return self.cursor.fetchone()[0]

    @property
    def global_name(self):
        """
        :return: The global name of the database
        """
        self.cursor.execute("select ora_database_name from dual")
        return self.cursor.fetchone()[0]

    def __get_object_type(self, in_owner, in_object_name):
        """
        Gets the type of a database object
        :param in_owner:       The object's owner (str)
        :param in_object_name: The object's name  (str)
        :return:               The object's type  (str)
        """
        sql = (
            "select lower(object_type) from all_objects where lower(owner)=:in_owner "
            "and lower(object_name)=:in_object_name"
        )
        params = {
            "in_owner": in_owner.lower(),
            "in_object_name": in_object_name.lower(),
        }
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()[0]

    def __object_exists(self, in_owner, in_object_name, in_object_type=None):
        """
        Searches for an object (Table, View, Function, etc.) to see if it exists in the database
        :param in_owner:       The owner of the object          (str)
        :param in_object_name: The name of the object           (str)
        :param in_object_type: The type of the object           (str)
        :return:               Whether or not the object exists (bool)
        """
        sql = "select * from all_objects where lower(owner)=:in_owner and lower(object_name)=:in_object_name"
        params = {
            "in_owner": in_owner.lower(),
            "in_object_name": in_object_name.lower(),
        }
        if in_object_type:
            sql += " and lower(object_type)=:in_object_type"
            params["in_object_type"] = in_object_type.lower()
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()

    def __get_current_user(self):
        """
        :return: The user logged in under this schema
        """
        self.cursor.execute("select lower(user) from dual")
        return self.cursor.fetchone()[0]
