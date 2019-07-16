import re

COLLECTION_TYPES = (list, set, tuple)


class Query(object):
    # match regular expressions with their corresponding function objects
    __OPERATOR_REGEX = [
        (re.compile(r"[a-zA-Z_]+_{3}gt"), ">"),
        (re.compile(r"[a-zA-Z_]+_{3}te"), ">="),
        (re.compile(r"[a-zA-Z_]+_{3}lt"), "<"),
        (re.compile(r"[a-zA-Z_]+_{3}lte"), "<="),
        (re.compile(r"[a-zA-Z_]+_{3}ne"), "<>"),
        (re.compile(r"[a-zA-Z_]+_{3}in"), "in"),
        (re.compile(r"[a-zA-Z_]+_{3}nin"), "not in"),
        (re.compile(r"[a-zA-Z_]+_{3}like"), "like"),
        (re.compile(r"[a-zA-Z_]+_{3}nlike"), "not like"),
        (
            re.compile(r"[a-zA-Z_]+_{3}trunc(_{3}((gt)|(gte)|(ne)|(lt)|(lte)|(in)|(nin)))?"),
            "trunc",
        ),
    ]

    __TEXT_TO_OPERATOR = {
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "ne": "<>",
        "in": "in",
        "nin": "not in",
        "nlike": "not like",
        "like": "like",
    }

    __SQL_FUNCTIONS = ("trunc",)
    __QUERY_TYPE_ERROR_MSG = "Other object must be of type 'Query'."
    __SQL_PARSING_ERROR_MSG = "Sql Parsing Error"

    def __init__(self, *args, mapping=None, **kwargs):
        """
        Constructor
        :param args:    Other Query objects
        :param kwargs:  The fields being and'd or or'd together
        """

        if not all(isinstance(arg, Query) for arg in args):
            raise TypeError(
                "Invalid input for *args, all must be Query objects (Ands or Ors)"
            )

        # param names -> param values for parameterized query
        self.__params = {}

        # a mapping between param names and the original fields they correspond with i.e. param: [param__1, param__2]
        self.__original_fields = {}

        # a mapping between param names and the highest param name counter value. if the field is only used once, the
        # value will be zero
        #
        #  ex) if in __original_fields we have: {"first_name": ["first_name", "first_name__1", "first_name__2"]
        #      then the highest index value for "first_name" with be 2
        self.__field_to_highest_index = {}
        self.__mapping = mapping

        sql_statements = []
        same_keys = {}
        original_values = {}

        # whether or not the arguments input to the constructor will be or'd or and'd together
        and_items = (isinstance(self, And) and not isinstance(self, Or)) or type(
            self
        ) is Query

        # deal with the keyword arguments first
        for att, val in kwargs.items():

            parsed_op = self.__parse_operator(att)

            sql_function = parsed_op["sql_function"]
            key, parsed_query = (
                parsed_op["key"],
                self.__parse_sql(att, val, parsed_op["operator"], sql_function),
            )

            sql, params, new_names = (
                parsed_query["sql"],
                parsed_query["params"],
                parsed_query["new_names"],
            )
            these_original_values = []

            if new_names is not None:
                # there will only be one key in the dict
                key = list(new_names.keys())[0]
                value_list = new_names[key]

                if key in same_keys.keys():
                    same_keys[key].extend(value_list)
                else:
                    same_keys[key] = value_list

                for field, value in params.items():

                    if value is not None:
                        self.__params[field] = value
                    these_original_values.append(value)

                sql_statements.append(sql)

            elif key in same_keys.keys():
                i = 1
                new_key = key + "__" + str(i)
                while new_key in same_keys[key]:
                    i += 1
                    new_key = key + "__" + str(i)
                same_keys[key].append(new_key)
                sql = sql.replace(
                    ":{key}".format(key=key), ":{key}".format(key=new_key)
                )

                if val is not None:
                    self.__params[new_key] = val
                these_original_values.append(val)
                sql_statements.append(sql)

            else:
                same_keys[key] = [key]

                if val is not None:
                    self.__params[key] = val
                these_original_values.append(val)
                sql_statements.append(sql)

            if key in original_values.keys():
                original_values[key].extend(these_original_values)
            else:
                original_values[key] = these_original_values

        self.__original_fields = same_keys
        self.__original_values = original_values
        self.__update_latest_parameter_indexes()
        self.__is_empty = False

        # set the __sql field
        num_sql = len(sql_statements)
        if num_sql > 1:
            self.__sql = (" and " if and_items else " or ").join(sql_statements)
        elif num_sql == 0:
            self.__sql = ""
            self.__is_empty = True
        else:
            self.__sql = sql_statements[0]

        # merge with anything provided in *args
        if len(args) > 0:
            for arg in args:
                if type(self) is And:
                    self.__and(arg)
                else:
                    self.__or(arg)

    ####################################################################################################################
    # OVERRIDES
    def __and__(self, other):
        """
        Override the '&' operator
        :param other: Another Query object (Query)
        :return:      This Query, and'd with the other (Query)
        """

        if isinstance(other, Query):
            return self.__and(other)
        else:
            raise TypeError(self.__QUERY_TYPE_ERROR_MSG)

    def __or__(self, other):
        """
        Override the '|' operator
        :param other: Another Query object (Query)
        :return:      This Query, or'd with the other (Query)
        """

        if isinstance(other, Query):
            return self.__or(other)
        else:
            raise TypeError(self.__QUERY_TYPE_ERROR_MSG)

    def __str__(self):
        """
        Override __str__ for print( )
        :return: The value of the sql property for this Query object
        """

        return self.sql

    ####################################################################################################################
    # PROPERTIES
    @property
    def original_fields(self):
        """
        :return: The original field names mapped to all parameter names corresponding with them (dict str: str)
        """

        return self.__original_fields

    @property
    def original_values(self):
        """
        :return: All original field names and their corresponding values, regardless of parameter name
                (dict str: obj)
        """

        return self.__original_values

    @property
    def parameter_name_counter_dict(self):
        """
        :return: Original field names and the corresponding maximum counter value from its corresponding
                 parameter names (dict str: int)
        """

        return self.__field_to_highest_index

    @property
    def params(self):
        """
        :return: The parameter names mapped to their values (dict str: list)
        """

        return self.__params

    @property
    def sql(self):
        """
        :return: The parameterized SQL query (str)
        """

        return self.__sql

    ####################################################################################################################
    # PUBLIC METHODS

    def get_full_sql(self, table_name):
        """
        Returns a full sql query, given a table name
        :param table_name: The name of the table being queried
        :return: the sql query (str)
        """
        return "select * from {t} where {w}".format(t=table_name, w=self.sql)

    ####################################################################################################################
    # PRIVATE METHODS
    def __and(self, other):
        """
        Private wrapper method that directs the __combine method to "and" this Query and the input other
        :param other: Another Query object (Query)
        :return:      This Query, and'd with the other (Query)
        """

        if isinstance(other, Query):
            return self.__combine(other, is_and=True)
        else:
            raise TypeError(self.__QUERY_TYPE_ERROR_MSG)

    def __combine(self, other, is_and=True):
        """
        Combines this Query object with another one
        :param other:   Another Query object (Query)
        :param is_and:  Whether or not the two objects will be and'd together (bool)
        :return:        The combination of the two Query objects (Query)
        """

        if not isinstance(other, Query):
            raise TypeError(self.__QUERY_TYPE_ERROR_MSG)

        # grab the relevant properties from the other Query object
        other_originals = other.original_fields
        other_params = other.params
        other_sql = other.sql
        other_original_values = other.original_values
        other_param_indexes = other.parameter_name_counter_dict

        # update this Query objects __original_values field
        for key, value_list in other_original_values.items():
            if key in self.original_values.keys():
                self.__original_values[key].extend(value_list)
            else:
                self.__original_values[key] = value_list

        # all original field names in this Query object
        original_field_names = list(self.original_fields.keys())

        # go through the parameter names in the other Query object and look for name conflicts
        for other_original_field, other_param_name_list in other_originals.items():

            # a name conflict was detected, modify the other Query object's parameter name
            if other_original_field in original_field_names:

                # this will contain all the param-value pairs associated with this original field name
                # for instance, if we have the field "first_name" and we have parameters named "first_name",
                # "first_name__1", and "first_name__2", this dict will contain the values for all of those names
                old_params = {}

                # get the old parameter names
                for param_name in other_param_name_list:
                    try:
                        old_params[param_name] = other_params[param_name]
                    except KeyError:
                        # TODO find out why this gets triggered in nested queries sometimes, and why it has no effect
                        pattern = re.compile(":" + param_name + r"$")
                        if len(re.findall(pattern, other_sql)) > 0:
                            raise ValueError(self.__SQL_PARSING_ERROR_MSG)

                        else:
                            pass

                # this dict will contain the modified names that originated in old_params
                cleaned_params = {}

                # get the current counter value for this parameter name in this Query object
                self_param_index = self.parameter_name_counter_dict[
                    other_original_field
                ]

                # get the current counter value for this parameter name in the other Query object
                other_param_index = other_param_indexes[other_original_field]

                # set the new counter so that there will be no chance of a conflict
                if self_param_index >= other_param_index:
                    param_name_index = self_param_index + 1
                else:
                    param_name_index = self_param_index + other_param_index + 1

                # go through the parameters for this field name and modify the parameter names and the sql to reflect
                # any needed changes
                for old_param, value in old_params.items():

                    # parse together a new parameter name based on the current counter name
                    new_key = old_param.split("__")[0] + "__" + str(param_name_index)
                    cleaned_params[new_key] = value
                    self.__original_fields[other_original_field].append(new_key)
                    self.__original_values[other_original_field].append(value)
                    self.__field_to_highest_index[other_original_field] += 1

                    # what the parameters look like in the actual sql (":" prepended)
                    old_param_text, new_param_text = ":" + old_param, ":" + new_key
                    if param_name_index == 1:
                        other_sql = other_sql.replace(old_param_text, new_param_text)
                    else:

                        # parse together some regular expressions that will be used to appropriately sub out old
                        # parameter names and put in the new ones
                        regex_dict = {
                            re.compile(old_param_text + "[\s]"): new_param_text + " ",
                            re.compile(old_param_text + "$"): new_param_text,
                            re.compile(old_param_text + "[)]"): new_param_text + ")",
                            re.compile(old_param_text + "[,\s]"): new_param_text + ", ",
                        }

                        repl_text = ""
                        repl_pattern = None
                        i = 0
                        regex_dict_keys = list(regex_dict.keys())

                        # search for regex matches and do the appropriate substitution
                        while repl_pattern is None and i < len(regex_dict_keys):
                            pattern = regex_dict_keys[i]
                            text = regex_dict[pattern]

                            if len(re.findall(pattern, other_sql)) > 0:
                                repl_text = text
                                repl_pattern = pattern

                            i += 1

                        if repl_pattern is not None:
                            other_sql = re.sub(repl_pattern, repl_text, other_sql)

                        else:
                            raise ValueError(self.__SQL_PARSING_ERROR_MSG)

                    param_name_index += 1

                self.__params.update(cleaned_params)

            else:

                # there was no parameter name conflict
                self.__original_fields[other_original_field] = other_param_name_list
                other_values = []
                these_params = {}

                for param_name in other_param_name_list:
                    try:
                        other_values.append(other_params[param_name])
                        these_params[param_name] = other_params[param_name]
                    except KeyError:
                        # TODO find out why this gets triggered in nested queries sometimes, and why it has no effect
                        pattern = re.compile(":" + param_name + r"$")
                        if len(re.findall(pattern, other_sql)) > 0:
                            raise ValueError(self.__SQL_PARSING_ERROR_MSG)
                        else:
                            pass
                self.__original_values[other_original_field] = other_values
                self.__params.update(these_params)

        # reset the counters based on the new parameters
        self.__update_latest_parameter_indexes()

        # finally set the actual sql
        if self.__is_empty:
            self.__sql = other_sql
            self.__is_empty = False
        else:
            self.__sql = "({0} {1} ({2}))".format(
                self.__sql, "and" if is_and else "or", other_sql
            )

        return self

    def __get_all_reserved_param_names(self):
        """
        :return: All parameter names being used by this Query
        """
        return list(self.__params.keys())

    def __get_column_type(self, column_name):
        return self.__mapping[column_name]["type"] if self.__mapping else None

    def __or(self, other):
        """
        Private wrapper method that directs the __combine method to "or" this Query and the input other
        :param other: Another Query object (Query)
        :return:      This Query, or'd with the other (Query)
        """

        if isinstance(other, Query):
            return self.__combine(other, is_and=False)
        else:
            raise TypeError(self.__QUERY_TYPE_ERROR_MSG)

    def __parse_in_list(self, attribute, value_list, operator="in"):
        """
        Method that parses a sql "in" statement, given an attribute and a list of values
        :param attribute:  The field name
        :param value_list: The values for the in-list
        :return:           A dictionary:
                            {
                                "sql"      : the actual sql,
                                "params"   : the parameters for the query,
                                "new_names": new parameter names based on the original field i.e. field__1, field__2
                            }
        """
        in_parts = []
        out_params = {}
        new_param_names = []

        # the parameter names currently being used by this Query object
        all_reserved = self.__get_all_reserved_param_names()
        index = (
            self.__field_to_highest_index[attribute]
            if attribute in self.original_fields.keys()
            else 1
        )

        # parse together new parameter names since we are using the same field multiple times
        max_values = 1000  # oracle max for in-operator list
        num_values = len(value_list)
        num_lists = (num_values // max_values) + 1
        in_lists = []

        i = 1
        curr_in_list = []
        listed_vals = list(value_list)
        while i <= num_values:

            param_name = f"{attribute}__{index}"
            while param_name in all_reserved:
                index += 1
                param_name = f"{attribute}__{index}"
            all_reserved.append(param_name)
            new_param_names.append(param_name)

            value = listed_vals[i - 1]
            out_params[param_name] = value
            curr_in_list.append(f":{param_name}")

            if i % max_values == 0:
                in_lists.append(f"({', '.join(curr_in_list)})")
                curr_in_list = []
            i += 1
        if len(in_lists) == 0:
            in_lists.append(f"({', '.join(curr_in_list)})")

        if len(in_lists) > 1:
            out_list = f" or {attribute} {operator} ".join(in_lists)
        else:
            out_list = in_lists[0]

        return {
            "sql": out_list,
            "params": out_params,
            "new_names": {attribute: new_param_names},
        }

    def __parse_operator(self, attribute):
        """
        Parse out the operator from the keyword argument
        For example, if the user input x___gt=27 in their kwargs, this would parse out ">" as the operator and "x" as
        the key.

        :param attribute: The user-input keyword argument key (str)
        :return: A dictionary:
                {
                    "operator" : the parsed operator from the keyword key,
                    "key"      : the actual field name
                }
        """

        # some looping vars
        found = False
        num_ops = len(self.__OPERATOR_REGEX)
        i = 0
        operator = None
        parsed_key = None
        sql_function = None

        # match the input key against the regular expressions
        while not found and i < num_ops:
            for regex, this_operator in self.__OPERATOR_REGEX:

                if re.match(regex, attribute):
                    found = True

                    if this_operator in self.__SQL_FUNCTIONS:
                        parts = attribute.split("___")

                        if len(parts) > 2:
                            key = parts[len(parts) - 1]
                            try:

                                operator = self.__TEXT_TO_OPERATOR[key]
                            except KeyError:
                                raise ValueError("Invalid Operator '{0}'.".format(key))
                        else:
                            operator = "="

                        sql_function = this_operator
                        parsed_key = parts[0]

                    else:
                        parsed_key = attribute.split("___")[0]
                        operator = this_operator

                i += 1

        if operator is None:
            return {"operator": "=", "key": attribute, "sql_function": sql_function}
        else:
            # parse out the original attribute name by chopping off the operator suffix
            return {
                "operator": operator,
                "key": parsed_key,
                "sql_function": sql_function,
            }

    def __parse_sql(self, attribute, value, operator, sql_function=None):
        """
        Evaluates an attribute:value pair and creates a sql statement out of it

        :param attribute:  A field in a database table
        :param value:      The value being searched for
        :param operator:   The operator being used
        :return:           A dict that holds information about this parsed sql
                            { "sql"       : the actual sql (str),
                              "params"    : the parameters for the query (dict str: obj),
                              "new_names" : any new mapping between original field names and parameter names (str: list)
                            }
        """

        value_type = type(value)
        is_in_statement = value_type in COLLECTION_TYPES or operator in ("in", "not in")
        attribute = attribute.split("__")[0]

        new_names = None

        if value is None:
            sql = attribute + " is null"
            params = {}

        else:
            parser = FieldOperatorValue(attribute, operator, sql_function)


            # validate the types
            value_list = [value] if value_type not in COLLECTION_TYPES else value

            # special case for parsing a sql "in" statement
            if is_in_statement:
                operator = "in" if operator == "=" else operator
                parser.set_operator(operator)
                parsed_in = self.__parse_in_list(attribute, value_list, operator)
                end_sql = parsed_in["sql"]
                params = parsed_in["params"]
                new_names = parsed_in["new_names"]

            # otherwise, the parameter will simply be the field name prepended by a colon
            else:
                end_sql = ":{0}".format(attribute)
                params = {attribute: value}
            sql = parser.sql + end_sql

        return {"sql": sql, "params": params, "new_names": new_names}

    def __update_latest_parameter_indexes(self):
        """
        Iterates through the __original_fields dict and looks for the maximum counter value for the parameter names
        corresponding with each field name.
        """

        for k, field_list in self.__original_fields.items():
            num_params = len(field_list)
            current_field = (
                field_list[0] if num_params == 1 else field_list[num_params - 1]
            )
            parts = current_field.split("__")
            self.__field_to_highest_index[k] = int(parts[1]) if len(parts) > 1 else 0


class And(Query):
    """
    Extends the Query class for cases where the user wants to "and" the arguments in the constructor
    """

    def __init__(self, *args, **kwargs):
        super(And, self).__init__(*args, **kwargs)


class Or(Query):
    """
    Extends the Query class for cases where the user wants to "or" the arguments in the constructor
    """

    def __init__(self, *args, **kwargs):
        super(Or, self).__init__(*args, **kwargs)


class FieldOperatorValue(object):
    def __init__(self, field, operator, sql_function=None):
        self.__field = field
        self.__operator = operator
        self.__sql_function = sql_function

    def set_operator(self, new_operator):
        self.__operator = new_operator

    @property
    def sql(self):
        if self.__sql_function is None:
            field_text = self.__field
        else:
            field_text = "{0}({1})".format(self.__sql_function, self.__field)

        return "{0} {1} ".format(field_text, self.__operator)
