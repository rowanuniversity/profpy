import datetime
import cx_Oracle
from .KeyHandler import PrimaryKey
from .utils import results_to_objs, validate_params
from ..queries import Query


class Data(object):
    """
    A class for accessing/altering a table in an Oracle database
    """

    __PK_ERROR_MSG = "This table does not have a primary key."
    __GENERATED_PK_MSG = "Cannot insert primary key on table where it is generated."
    __REQUIRED_FIELDS_MSG = "Did not enter required fields. Required: {0}"

    __TYPE_MAPPING = {
        "VARCHAR2":             str,
        "VARCHAR":              str,
        "NCHAR":                str,
        "NVARCHAR":             str,
        "RAW":                  str,
        "NUMBER":               int,
        "INTEGER":              int,
        "INT":                  int,
        "SMALLINT":             int,
        "REAL":                 int,
        "NUMERIC":              int,
        "LONG":                 int,
        "FLOAT":                float,
        "DEC":                  float,
        "DECIMAL":              float,
        "DOUBLE PRECISION":     float,
        "DATE":                 datetime.datetime,
        "TIMESTAMP":            datetime.datetime,
        "CLOB":                 cx_Oracle.CLOB,
        "BLOB":                 cx_Oracle.BLOB
    }
    __DB_TRUE = ("Y", "y", "YES", "yes")
    __DB_FALSE = ("N", "n", "NO", "no")

    def __init__(self, owner, name, db):
        """
        Constructor
        :param name:             The name of the table, ex) "OWNER.TABLE_NAME", "TABLE_NAME" (str)
        """

        self._db = db
        self.__owner = owner.lower()
        self.__table_name = name.lower()
        self.__full_name = "{0}.{1}".format(owner, name)
        self.__field_names = self.__get_field_names()
        self.__field_definitions = self.__get_field_definitions()

    ####################################################################################################################
    # PROPERTIES
    @property
    def column_descriptions(self):
        """
        :return: A dict of column comments from the table
        """

        return self.__get_field_comments()

    @property
    def columns(self):
        """
        :return: A list of columns from this table
        """

        return self.__field_names

    @property
    def count(self):
        """
        :return: The number of records in the table
        """

        return self.__get_count()

    @property
    def description(self):
        """
        :return: The comments from the table, defined in the ddl
        """

        return self.__get_table_comments()

    @property
    def is_table(self):
        """
        :return: Whether or not this object is a table
        """

        return isinstance(self, Table)

    @property
    def lob_fields(self):
        """
        :return: Any LOB-type field
        """
        sql = "select lower(column_name) as column_name from all_tab_cols " \
              "where lower(owner)=:in_owner and lower(table_name)=:in_table and data_type in ('CLOB', 'BLOB')"

        params = {"in_owner": self.owner, "in_table": self.table_name}
        results = self._db.execute_query(sql, params=params)
        return [row["column_name"] for row in results]

    @property
    def mapping(self):
        """
        :return: The field definitions of this table (dictionary)
        """

        return self.__field_definitions

    @property
    def mapping_pretty(self):
        """
        :return: Read-friendly string of the mapping
        """
        string = ""
        for field, mapping in self.mapping.items():
            string += field + "\n\tType:\t\t{0}\n".format(mapping["type"].__name__)
            string += "\tNullable:\t{0}\n\tGenerated:\t{1}\n\n".format(mapping["nullable"], mapping["generated"])
        return string

    @property
    def name(self):
        """
        :return: The table's full name
        """

        return self.__full_name

    @property
    def owner(self):
        """
        :return: The owner of the table
        """
        return self.__owner

    @property
    def non_nullable_fields(self):
        """
        :return: The fields in this table that are required (non-nullable)
        """

        required_fields = []
        for field, definition in self.mapping.items():
            is_nullable = definition["nullable"]
            if not is_nullable:
                required_fields.append(field)
        return required_fields

    @property
    def table_name(self):
        """
        :return: The table name, sans any owner
        """

        return self.__table_name

    ####################################################################################################################
    # PUBLIC METHODS
    def all(self):
        """
        :return: All the records from the table (list of Record objects)
        """

        sql = "select * from {table}".format(table=self.name)
        return self._execute_sql(sql, get_data=True, get_row_objects=True)

    def find(self, data=None, limit=None, get_row_objects=True, **kwargs):
        """
        Finds records based on field values. User may provide as many fields as he/she wants to continue to filter
        the resulting set.
        :param data:            Fields to search on as field-value pairs in a dictionary (dict)
        :param limit:           A limit on the number of records returned (int)
        :param get_row_objects: Whether or not to return Row objects, as opposed to dicts (bool)
        :param kwargs:          Fields to search on, i.e. first_name="Joe" (used instead of "data" arg)
        :return:                A result set from the database (list of Result objects)
        """

        if data is None and len(kwargs) == 0:
            raise Exception("Did not specify anything for query.")

        if isinstance(data, Query):
            result = self.__query(data, limit)

        else:
            use_this = kwargs if data is None else data
            prepared_kwargs = self._prepare_kwargs(use_this, "select {0}".format(", ".join(self.columns)))
            result = self._execute_sql(prepared_kwargs["sql"], get_data=True, params=prepared_kwargs["params"],
                                       get_row_objects=get_row_objects, limit=limit)

        return result

    def find_one(self, data=None, get_row_objects=True, **kwargs):
        """
        Same as find, but it returns only the first record in the resulting list.

        :param data:            Fields to search on as field-value pairs in a dictionary (dict)
        :param get_row_objects: Whether or not to return Row objects, as opposed to dicts (bool)
        :param kwargs:          Optionally, the caller can specify field-value pairs as keyword arguments
        :return:                If it exists, the Record found at the specified field-value pairs.
        """

        results = self.find(data=data, limit=1, get_row_objects=get_row_objects, **kwargs)
        return results[0] if results else None

    ####################################################################################################################
    # PROTECTED METHODS

    def _execute_sql(self, sql, get_data=False, params=None, get_row_objects=False, limit=None):
        """
        Executes a given sql statement
        :param sql:                  The sql statement/query to be executed (str)
        :param get_data:             Whether or not data should be returned (i.e. fetchall) (boolean)
        :param params:               For parameterization (dict)
        :param get_row_objects    Whether or not the caller wants a list of Record objects (boolean)
        :return:                     A list of Record objects, if get_record_objects is set to True (list)
        """
        try:
            self._db.cursor.execute(sql, validate_params(params))
            if get_data:
                rows = results_to_objs(self._db.cursor, self, limit, get_row_objs=get_row_objects)
                return rows
        except cx_Oracle.IntegrityError:
            raise cx_Oracle.IntegrityError("Key constraint violated.")

        except cx_Oracle.DatabaseError:
            raise cx_Oracle.DatabaseError("Database error with following statement: {0}".format(sql))

    def _fix_field_casing(self, data):
        """
        Replaces all keys in a dictionary of column-value pairs with the correct column names. This is useful for if
        users input "first_name" but the database table has the column as "FIRST_NAME" or vice versa.
        :param data: The input dictionary
        :return: The cleaned data, or None if the data is found to be invalid, e.g. columns were completely wrong
        """

        cleaned_data = {}
        bad_data = False
        for key, value in data.items():
            new_key = self.__validate_input_key(key)

            if new_key is None:
                bad_data = True
                break
            else:
                cleaned_data[new_key] = value

        return None if bad_data else cleaned_data

    def _prepare_kwargs(self, in_kwargs, sql_prefix, is_change=False):
        """
        Converts kwargs inputs to sql and packages it with a corresponding parameter dictionary
        :param in_kwargs:   user-input kwargs
        :param sql_prefix:  the beginning of the sql statement (likely either "select *" or "delete"
        :return:            a dictionary containing the sql and its corresponding parameters (also a dict)
        """

        if is_change:

            in_kwargs = self._fix_field_casing(in_kwargs)
            if in_kwargs is None:
                raise ValueError("Invalid field.")

            validated_type_results = self.__validate_arg_types(in_kwargs)
            if not validated_type_results["validity"]:
                raise TypeError(validated_type_results["message"])

            params = {}
            for column, value in in_kwargs.items():

                this_mapping = self.mapping[column]
                acceptable_type = this_mapping["type"]

                # handle CLOBs and BLOBs
                if column in self.lob_fields:
                    value_type = type(value)
                    if value_type is not str and acceptable_type is cx_Oracle.CLOB:
                        raise Exception("Invalid insert/update on CLOB field '{0}'".format(column))
                    elif value_type is not bytes and acceptable_type is cx_Oracle.BLOB:
                        raise Exception("Invalid insert/update on BLOB field '{0}'".format(column))
                    else:
                        params[column] = value
                else:
                    params[column] = value

            column_list = []
            params_list = []
            for column in in_kwargs.keys():
                column_list.append(column)
                param_list_sql = ":" + column
                mapping = self.mapping[column]

                if mapping["type"] is cx_Oracle.BLOB:
                    param_list_sql = "to_blob(" + param_list_sql + ")"
                elif mapping["type"] is cx_Oracle.CLOB:
                    param_list_sql = "to_clob(" + param_list_sql + ")"

                params_list.append(param_list_sql)
            column_list = ", ".join(column_list)
            params_list = ", ".join(params_list)

            # parse parameterized query ex) "INSERT INTO OWNER.TABLE (NAME, ADDRESS) VALUES (:NAME, :ADDRESS)"
            sql = "insert into {0} ({1}) values ({2})".format(self.name, column_list, params_list)

        else:
            if any(self.mapping[k.split("___")[0]]["type"] in [cx_Oracle.BLOB, cx_Oracle.CLOB] for k in list(in_kwargs.keys())):

                raise Exception("Cannot query on LOB fields.")

            q = Query(**in_kwargs)
            sql = "{prefix} from {table} where {w}".format(prefix=sql_prefix, table=self.name, w=q.sql)
            params = q.params

            validated_type_results = self.__validate_arg_types(q.original_values)
            if not validated_type_results["validity"]:
                raise TypeError(validated_type_results["message"])

        return {"sql": sql, "params": params}

    ####################################################################################################################
    # PRIVATE METHODS
    def __get_count(self):
        """
        :return: The total number of records in the table
        """

        sql = "select count(*) as total from {0}".format(self.name)
        return self._execute_sql(sql, get_data=True, limit=1)[0]["total"]

    def __get_field_comments(self):
        """
        Gets the field comments that were specified in the ddl
        :return: A dictionary -> key: field, value: comment
        """

        sql = "select lower(column_name) as c_name, comments from all_col_comments " \
              "where lower(table_name)=:in_table_name and lower(owner)=:in_owner"
        params = {"in_table_name": self.table_name, "in_owner": self.owner}
        raw_comments = self._execute_sql(sql, get_data=True, params=params)
        comment_dict = {}
        for row in raw_comments:
            comment_dict[row["c_name"]] = row["comments"]
        return comment_dict

    def __get_field_definitions(self):
        """
        Gets the field definitions from the table, i.e. nullability, data types, etc.
        :return: The field definitions as a dictionary set up the following way:
                    Key (field name):
                        "type" : the required data type for this field
                        "nullable" : whether or not this field is nullable
                        "generated" (only for keys) : whether or not a primary key field is generated by the database
        """
        sql = "select lower(column_name) as c_name, data_type, nullable, identity_column from all_tab_columns " \
              "where lower(table_name)=:in_table_name and lower(owner)=:in_owner"
        params = {"in_table_name": self.table_name, "in_owner": self.owner}
        result = self._execute_sql(sql, get_data=True, params=params)
        definitions = {}
        for row in result:
            type_value = row["data_type"]
            nullable_value = row["nullable"] in self.__DB_TRUE
            is_generated = row["identity_column"] in self.__DB_TRUE

            if "(" in type_value:  # remove memory or length specifiers i.e. VARCHAR2(100)
                type_value = type_value.split("(")
                type_value = type_value[0]

            column_name = row["c_name"]
            definition = {"type": self.__TYPE_MAPPING[type_value], "nullable": nullable_value,
                          "generated": is_generated}
            pk_attr = "_Table__primary_key_object"
            if hasattr(self, pk_attr) and column_name in getattr(self, pk_attr).columns:
                definition["generated"] = is_generated

            definitions[column_name] = definition

        return definitions

    def __get_field_names(self):
        """
        Gets the fields names from the table associated with this TableHandler instance
        :return: The field names (list)
        """

        sql = "select lower(column_name) as field_name from all_tab_columns where lower(owner)=:in_owner and " \
              "lower(table_name)=:in_table"
        params = {"in_owner": self.__owner.lower(), "in_table": self.__table_name.lower()}
        result = self._execute_sql(sql, get_data=True, params=params)
        return [row["field_name"] for row in result]

    def __get_table_comments(self):
        """
        Gets the table comment that was specified in the ddl
        :return: The table comment (str)
        """

        sql = "select comments from all_tab_comments where lower(table_name)=:in_table_name and lower(owner)=:in_owner"
        params = {"in_table_name": self.table_name, "in_owner": self.owner}
        result = self._execute_sql(sql, get_data=True, params=params)
        if result:
            return result[0]["comments"]  # result will be a one-item list with a single dict
        else:
            return ""

    def __query(self, query, limit=None):
        """
        Executes a sql query using Query objects
        :param query:   A Query query object
        :return:        A list of Record objects based on this query
        """

        if not isinstance(query, Query):
            raise TypeError("Invalid query.")
        else:

            original_fields = query.original_fields

            # entered fields that aren't in the table
            if not any(field in self.columns for field in original_fields.keys()):
                raise ValueError("Invalid field specified in query.")

            # elif not self.__entered_required_fields(original_fields):
            #     raise Exception("Missing required fields.")

            else:

                validation = self.__validate_arg_types(query.original_values)
                has_valid_args, message = validation["validity"], validation["message"]
                if has_valid_args:
                    return self._execute_sql(query.get_full_sql(self.name), get_data=True, params=query.params,
                                             get_row_objects=True, limit=limit)
                else:
                    raise TypeError(message)

    def __validate_arg_types(self, in_kwargs):
        """
        Checks to see if the user input valid argument types, based on the tables field definitions/mapping.
        If a conflict is found, an appropriate error message is crafted and passed on to the method that is calling
        this one, as well as a boolean flag.

        :param in_kwargs: The arguments being tested
        :return:          A dictionary containing two keys:
                            "validity" -> was this a valid input based on the type from the database (bool)
                            "message"  -> an error message detailing the specific type or nullablity conflict
        """

        keys = list(in_kwargs)
        num_args = len(keys)
        i = 0

        # check if all required fields are present
        has_valid_args = True
        message = "" if has_valid_args else "Missing required fields."
        while i < num_args and has_valid_args:
            this_key = keys[i]
            mapping = self.mapping[this_key.lower()]
            accepted_type, is_nullable = mapping["type"], mapping["nullable"]

            this_entry = in_kwargs[this_key]
            values = [this_entry] if type(this_entry) not in (list, tuple, set) else this_entry
            type_error_message = "Invalid type: '{0}' for field '{1}', {2} required but {3} was given."
            for value in values:

                msg = type_error_message.format(value, this_key, str(accepted_type), str(type(value)))

                # null value was attempted for non-nullable field
                if value is None and not is_nullable:
                    message = "Invalid type for field '{0}', NULL values are not allowed for this field.".format(this_key)
                    has_valid_args = False

                # invalid type was found for this field
                elif not isinstance(value, accepted_type) and value is not None:
                    value_type = type(value)

                    # check if a list or tuple of values was entered
                    if value_type in (list, tuple, set) and len(value) > 0:

                        # all values in this collection must be valid to proceed
                        if not all(isinstance(this_value, accepted_type) or this_value is None for this_value in value):
                            message = msg
                            has_valid_args = False

                    elif value_type is bytes and accepted_type is cx_Oracle.BLOB:
                        pass

                    elif value_type is str and accepted_type is cx_Oracle.CLOB:
                        pass

                    # value had the wrong type
                    else:
                        message = msg
                        has_valid_args = False
                i += 1

        return {
            "validity": has_valid_args,
            "message": message
        }

    def __validate_input_key(self, key):
        """
        Checks to see if a column name exists in the table, in the provided form or in a similar form (capitalized or
        in lowercase form). The correct version is returned.
        :param key: An input column name, often from a dictionary key
        :return: The corrected column name, or None if the column name does not exist in the table
        """

        if key in self.columns:
            return key
        elif key.upper() in self.columns:
            return key.upper()

        elif key.lower() in self.columns:
            return key.lower()
        else:
            return None


class Table(Data):

    def __init__(self, owner, name, db):

        super().__init__(owner=owner, name=name, db=db)
        self.__primary_key_object = self.__get_primary_key_object()

    @property
    def primary_key(self):
        """
        :return: The primary key object that holds info about the primary key
        """

        return self.__primary_key_object

    @property
    def generated_fields(self):
        """
        :return: All generated fields from the table
        """
        generated_fields = []
        for field, mapping in self.mapping.items():
            if "generated" in list(mapping.keys()):
                if mapping["generated"] is True:
                    generated_fields.append(field)
        return generated_fields

    @property
    def has_key(self):
        return self.__primary_key_object.exists

    def delete_from(self, **kwargs):
        """
        Truncates the table associated with this Table instance
        :return:
        """

        if len(kwargs.keys()) > 0:
            prepared_kwargs = self._prepare_kwargs(kwargs, "delete")
            self._execute_sql(prepared_kwargs["sql"], params=prepared_kwargs["params"])
        else:
            self._execute_sql("delete from {table}".format(table=self.name))

    def get(self, key=None, **kwargs):
        """
        Retrieve a Record by supplying its primary key.
        :param key:     Either a single value (single key) or a dictionary of values (composite key)
        :param kwargs:  Individual key-value pairs, this can be used instead of the key arg, if desired
        :return:        If it exists, the Record found at that key, else null (type Record)
        """
        if not self.has_key:
            raise Exception("Cannot perform 'get' operation on table with no primary key.")

        # key validation
        cleaned_key = None

        # is the user searching by a single key value or a composite key
        searching_by_single_key = key is not None

        # did the user input a dictionary type for the "key" argument, signalling a composite key (rather than use
        # kwargs)
        in_key_is_dict = type(key) is dict

        # if they input a dictionary object, align the key casings with the casing of our fields names in the handler
        # and specify that we are NOT searching by a single key value
        if in_key_is_dict:
            cleaned_key = self._fix_field_casing(key)
            searching_by_single_key = False

        # use the kwargs object if our clean_key variable is never set
        use_this = cleaned_key if in_key_is_dict else kwargs
        num_args = len(use_this.keys())

        # # this should no longer be needed since we enforce keys in the constructor
        # if self.primary_key is None:
        #     raise Exception("No primary key set for this table.")

        if searching_by_single_key:

            # check that the caller didn't try to search a single value against a composite primary key
            if self.primary_key.field_count != 1:
                raise Exception("Not enough values supplied for this primary key.")

            # if not, we can simply utilize the find_one method
            else:
                return self.find_one(data={self.primary_key.columns[0]: key})

        else:

            # make sure that the caller supplied the correct number of fields for the composite field
            if self.primary_key.field_count != num_args:
                raise Exception("Not enough values supplied for this primary key.")

            else:

                # make sure that the caller supplied the correct field names for the composite field
                if not all(in_field in self.primary_key.columns for in_field in use_this.keys()):
                    raise Exception("Invalid composite key fields specified.")

                # since the composite key utilizes a combination of fields, we can utilize the find method to retrieve
                # the unique record
                else:
                    results = list(self.find(**use_this))
                    num_results = len(results)

                    # returned no results
                    if num_results == 0:
                        return None
                    elif num_results > 1:
                        # TODO: explore better options here
                        raise Exception("Invalid key, more than one result returned")
                    else:
                        return results[0]

    def save(self, data=None, **kwargs):
        """
        Inserts or updates a record, depending on if a primary key is given
        :param data     A Record in the form of a dictionary object (dict)
        :param kwargs:  If data is not used, the caller can specify individual field-value pairs as keyword arguments
        :return:        The Record object that was saved to the table (Record)
        """

        use_this = kwargs
        if data is not None:
            use_this = data

        if self.__pk_in_kwargs(use_this):
            if self.__record_exists_in_table(use_this):
                result = self.__update(**use_this)
            else:
                result = self.__insert(**use_this)
        else:
            result = self.__insert(**use_this)
        return result

    def __insert(self, **kwargs):
        """
        Inserts a row of values into the table associated with this TableHandler instance using parameterized sql
        :param values: The values to be inserted (dict)
        :return:
        """
        components = self._prepare_kwargs(kwargs, sql_prefix=None, is_change=True)
        params = components["params"]
        try:

            self._execute_sql(components["sql"], params=params)

            if self.has_key:

                return_sql = self.__get_key_sql_and_params(params)
                params = return_sql["params"]
                return_sql = return_sql["sql"]

            else:
                return_sql = "select * from {0} where ".format(self.name)
                params_sql = []
                for p in params:
                    params_sql.append(":{0}={0}".format(p))
                params_sql = " and ".join(params_sql)
                return_sql += params_sql

            results = self._execute_sql(return_sql, params=params, get_data=True, get_row_objects=True, limit=1)
            return results[0] if self.has_key else results

        except cx_Oracle.DatabaseError as db_error:
            raise db_error

    def __update(self, **kwargs):
        """
        Updates a record at the given primary key
        :param primary_key: The key corresponding with record to update
        :param kwargs:      Keyword arguments corresponding to field value updates, e.g. last_name="Smith"
        :return:
        """
        if self.primary_key is None:
            raise Exception(self.__PK_ERROR_MSG)
        else:

            params = self._prepare_kwargs(kwargs, "", is_change=True)["params"]
            update_sql = "update {table} set ".format(table=self.name)

            keys = params.keys()
            param_sql = []
            for i, param in enumerate(keys):
                if param not in self.primary_key.columns:
                    param_sql.append("{param}=:{param}".format(param=param))
            param_sql = ", ".join(param_sql)

            update_sql += param_sql + " where " + self.primary_key.sql_where_clause
            return_sql_code_and_params = self.__get_key_sql_and_params(params)
            key_params = return_sql_code_and_params["params"]
            return_sql = return_sql_code_and_params["sql"]

            # lock the record for update
            lock_sql = "select * from {0} where {1} for update".format(self.name, self.primary_key.sql_where_clause)
            self._execute_sql(lock_sql, params=key_params)

            # update the record
            self._execute_sql(update_sql, params=params)

            # return the updated Record object back to the caller
            try:
                return self._execute_sql(return_sql, params=key_params, get_data=True, get_row_objects=True)[0]
            except IndexError:
                return

    def __record_exists_in_table(self, in_args):
        """
        Checks to see if a record exists in the table, based on a given dictionary of arguments
        :param in_args: The arguments used to find the record (dict)
        :return:        Whether or not the record exists (boolean)
        """

        params = {}
        params_sql = ""
        for i, column in enumerate(self.primary_key.columns):
            params[column] = in_args[column]
            params_sql += "{column}=:{column}".format(column=column)

            if i < self.primary_key.field_count - 1:
                params_sql += " and "

        sql = "select * from {table} where ".format(table=self.name) + params_sql
        try:
            x = self._execute_sql(sql, get_data=True, params=params)[0]
            return True
        except IndexError:
            return False

    def __pk_in_kwargs(self, in_kwargs):
        """
        Determines whether or not the primary key is present in a keyword dictionary. This covers composite keys.
        :param in_kwargs: The input keywords (dict)
        :return:          Whether or not the primary key is present (boolean)
        """

        if self.primary_key:
            return all(f in in_kwargs.keys() for f in self.primary_key.columns)
        else:
            return False

    def __get_key_sql_and_params(self, parameters):
        """
        Used to parse sql and params to find newly created table entries.
        :param parameters:  Parameters that were used to create the table entry
        :return:            A dictionary containing sql to retrieve the new entry and the parameters for the query
        """

        key_params = {}
        gen_field_sql = None
        if len(self.generated_fields) > 0:
            gen_field_statements = []
            for gf in self.generated_fields:

                sql = "select max({field}) as gen_col from {table}".format(field=gf, table=self.name)
                value = self._execute_sql(sql, get_data=True, limit=1)[0]["gen_col"]
                key_params[gf] = value
                gen_field_statements.append("{field}=:{field}".format(field=gf))

            gen_field_sql = " and ".join(gen_field_statements)

        sql = "select * from {table} where ".format(table=self.name) + self.primary_key.sql_where_clause
        if gen_field_sql and (gen_field_sql != self.primary_key.sql_where_clause):
            sql += " and " + gen_field_sql

        for field in self.primary_key.columns:

            # if the field was not already handled by the generated key check above, deal with it here
            if field not in key_params.keys():
                key_params[field] = parameters[field]
        return {"sql": sql, "params": key_params}

    def __get_primary_key_object(self):
        """
        Creates a PrimaryKey object using constraint table information from the database.
        :return: a PrimaryKey object for this table
        """

        sql = "select lower(column_name) as column_name from all_cons_columns where " \
              "constraint_name = (select constraint_name from all_constraints where " \
              "lower(table_name)=:in_table and lower(owner)=:in_owner and constraint_type=:in_type)"
        parameters = {"in_table": self.table_name.lower(), "in_type": "P", "in_owner": self.owner}

        try:
            pk = [row["column_name"] for row in self._execute_sql(sql, get_data=True, params=parameters)]
        except IndexError:
            # no primary key found for the table
            pk = None
        return PrimaryKey(pk)


class View(Data):
    def __init__(self, owner, name, db):
        super().__init__(owner=owner, name=name, db=db)

    @property
    def has_key(self):
        return False
