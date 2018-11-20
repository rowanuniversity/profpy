import cx_Oracle
import datetime
from . import Table, View
from . import Row
from db.connections import get_connection
FULL_LOGIN = "full_login"
DB_PASSWORD = "db_password"


class Database(object):

    def __init__(self, user_var=FULL_LOGIN, password_var=DB_PASSWORD):

        self.__connection = get_connection(user_var, password_var)
        self.__cursor     = self.__connection.cursor()
        self.user         = self.__get_current_user()
        self.tables       = {}
        self.views        = {}

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
    ####################################################################################################################

    def model(self, owner, object_name):
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
        view = View(owner, view_name, self)
        if owner in list(self.views.keys()):
            self.views[owner][view_name] = view
        else:
            self.views[owner] = {
                view_name: view
            }
        return view

    def __model_table(self, owner, table_name):

        table = Table(owner, table_name, self)
        if owner in list(self.tables.keys()):
            self.tables[owner][table_name] = table
        else:
            self.tables[owner] = {
                table_name: table
            }
        return table

    def execute_query(self, query, params=None, one_value=False):
        if params:
            self.__cursor.execute(query, params)
        else:
            self.__cursor.execute(query)
        data = fetch_to_dicts(self.__cursor)
        rows = []
        if isinstance(data, dict):
            data = [data]
        for record in data:
            rows.append(Row(record, [], {}, None))

        if one_value and len(rows) == 0:
            return None
        elif one_value:
            return rows[0]
        else:
            return rows

    def execute_function(self, owner, function_name, *args, one_value=False):
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
            self.__cursor.execute(sql, params)
            rows = self.__cursor.fetchall()
            if one_value and len(rows) > 0:
                result = rows[0][0]
            elif len(rows) > 0:
                result = rows
            else:
                result = None
            return result
        else:
            raise Exception("Function does not exist.")

    def commit(self):
        self.__connection.commit()

    def rollback(self):
        self.__connection.rollback()

    def close(self):
        """
        Closes this handler and its corresponding connection and cursor objects
        :return:
        """
        try:

            self.__connection.rollback()
            self.__cursor.close()
            self.__connection.close()
            self.__cursor = None
            self.__connection = None

        except AttributeError:
            # TODO write some better handling here, should not be triggered, but need to find best practice
            return True

    @property
    def name(self):
        self.__cursor.execute("select ora_database_name from dual")
        return self.__cursor.fetchone()[0]

    def __get_object_type(self, in_owner, in_object_name):
        sql = "select lower(object_type) from all_objects where lower(owner)=:in_owner " \
              "and lower(object_name)=:in_object_name"
        params = {"in_owner": in_owner.lower(), "in_object_name": in_object_name.lower()}
        self.__cursor.execute(sql, params)
        return self.__cursor.fetchone()[0]

    def __object_exists(self, in_owner, in_object_name, in_object_type=None):
        sql = "select * from all_objects where lower(owner)=:in_owner and lower(object_name)=:in_object_name"
        params = {"in_owner": in_owner.lower(), "in_object_name": in_object_name.lower()}
        if in_object_type:
            sql += " and lower(object_type)=:in_object_type"
            params["in_object_type"] = in_object_type.lower()
        self.__cursor.execute(sql, params)
        return self.__cursor.fetchone()

    def __get_current_user(self):
        """
        :return: The user logged in under this schema
        """
        self.__cursor.execute("select lower(user) from dual")
        return self.__cursor.fetchone()[0]

    def execute_sql(self, sql, table_object, get_data=False, params=None, get_record_objects=False, limit=None):
        """
        Executes a given sql statement
        :param sql:                  The sql statement/query to be executed (str)
        :param get_data:             Whether or not data should be returned (i.e. fetchall) (boolean)
        :param params:               For parameterization (dict)
        :param get_record_objects    Whether or not the caller wants a list of Record objects (boolean)
        :return:                     A list of Record objects, if get_record_objects is set to True (list)
        """
        try:
            if params is None:
                self.__cursor.execute(sql)
            else:
                self.__cursor.execute(sql, params)

            if get_data:
                if get_record_objects:
                    rows = []
                    fetched = fetch_to_dicts(self.__cursor, limit)
                    if isinstance(fetched, dict):
                        fetched = [fetched]

                    for row in fetched:
                        new_record = {}

                        for col in table_object.columns:
                            new_record[col] = row[col]

                        pk_cols = getattr(table_object, "_Table__primary_key_object").columns \
                            if isinstance(table_object, Table) else []
                        rows.append(Row(new_record, pk_cols, table_object.mapping, table_object))

                else:
                    rows = fetch_to_dicts(self.__cursor, limit)

                return rows

        except cx_Oracle.IntegrityError:
            self.__connection.rollback()
            raise cx_Oracle.IntegrityError("Key constraint violated.")

        except cx_Oracle.DatabaseError:
            self.__connection.rollback()
            raise cx_Oracle.DatabaseError("Database error with following statement: {0}".format(sql))


def fetch_to_dicts(in_cursor, limit=None):
    bad_chars = [".", "(", ")"]
    if limit:
        if limit == 1:
            results = in_cursor.fetchone()
            if results is None:
                results = []
            else:
                results = [results]
        else:
            results = in_cursor.fetchmany(limit)
    else:
        results = in_cursor.fetchall()

    field_names = [d[0].lower() for d in in_cursor.description]
    clean_fields = []
    for fn in field_names:
        new_field = fn
        for bc in bad_chars:
            new_field = new_field.replace(bc, "_")
        count_chars = len(new_field)
        if new_field[count_chars - 1] == "_":
            new_field = new_field[:-1]
        clean_fields.append(new_field)

    output = [dict(zip(clean_fields, row)) for row in results]
    if limit and len(output) > 0:
        output = output[0] if limit == 1 else output[0:limit]
    return output

