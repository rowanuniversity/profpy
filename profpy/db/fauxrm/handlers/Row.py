"""
Row.py
Abstracts a row from a sql query result so that you can access the fields of the row as this object's attributes.

For instance, if there is a table called "phonebook" with a column for "area_code", you could access the data in that
column using the .find method, which returns these Row objects:

    with fauxrm.Database() as database:
        phonebook = database.model("owner", "phonebook")
        area_codes = []
        for row in phonebook.find(first_name="Joe"):
            area_codes.append(row.area_code)

You can also update data using these objects, if they belong to a table handler:
    with fauxrm.Database() as database:
        phonebook = database.model("owner", "phonebook")
        for row in phonebook.find(first_name="Joe"):
            row.area_code = "555"
            row.save()
        phonebook.commit()
"""
import cx_Oracle


class Row(object):

    __TYPE_ERROR_MSG = "Invalid type input for '{0}', {1} required but {2} given"
    __NULL_ERROR_MSG = "Field '{0}' cannot be null"
    __INVALID_FIELD_NAME_MSG = "Invalid field name specified"
    __KEY_ATTR = "key"
    __MAPPING_TYPE_KEY = "type"
    __MAPPING_NULLABLE_KEY = "nullable"
    __RESERVED_ATTRS = ("_Row__data", "_Row__mapping", "_Row__key", "_Row__handler", "_Row__original_values")

    def __init__(self, data, handler):
        """
        Constructor
        :param data:       The data for this row (dict)
        :param handler:    The handler object (fauxrm)
        """

        self.__data = data
        self.__original_values = data
        self.__mapping = handler.mapping if handler else {}
        self.__handler = handler
        self.__key = {}

        for field, value in self.__data.items():
            if isinstance(value, cx_Oracle.LOB):
                self.__data[field] = value.read()

        if handler.has_key:
            for field in handler.primary_key.columns:
                self.__key[field] = self.__data[field]

    ####################################################################################################################
    # OVERRIDES
    def __eq__(self, other):
        """
        Override "==" operator
        :param other: Another object (Record)
        :return: Are the two objects equal (bool)
        """

        return isinstance(other, type(self)) and self.key == other.key

    def __getattr__(self, field):
        """
        Allow the caller to access data from the row as an attribute i.e. row.first_name
        :param field: The field to be accessed (str)
        :return:      The value located in that field (obj)
        """

        if field in self.__data.keys():
            return self.__data[field]
        elif field == self.__KEY_ATTR:
            return self.key
        else:
            raise AttributeError(self.__INVALID_FIELD_NAME_MSG)

    def __getitem__(self, field):
        """
        Allow the caller to access data from the row like a dict object i.e. row["first_name"]
        :param field: The field to be accessed (str)
        :return:      The value located in that field (obj)
        """
        if field in self.__data.keys():
            return self.__data[field]
        else:
            raise KeyError(self.__INVALID_FIELD_NAME_MSG)

    def __ne__(self, other):
        """
        Override the "!=" operator
        :param other: The object being compared to this Row (obj)
        :return:      Whether or not the other object is not equal to this Row (bool)
        """
        return not self == other

    def __setattr__(self, field, value):
        """
        Allow the caller to set field values using attribute access i.e. row.first_name = "Dennis"
        :param field: The field to be set (str)
        :param value: The value to be input to the field (obj)
        :return:
        """

        if field in self.__RESERVED_ATTRS:
            super(Row, self).__setattr__(field, value)
        else:
            self.__set_data(field, value)

    def __setitem__(self, field, value):
        """
        Allow the caller to set field values using dictionary key access i.e. row["first_name"] = "Dennis"
        :param field: The field to be set (str)
        :param value: The value being input (obj)
        :return:
        """

        if field in self.__data.keys():
            self.__set_data(field, value)
        else:
            raise KeyError(self.__INVALID_FIELD_NAME_MSG)

    def __str__(self):
        """
        Override str( ) to always show a string representation of the __data property
        :return:
        """
        return str(self.__data)

    def __repr__(self):
        return str(self.data)
    ####################################################################################################################
    # PROPERTIES

    @property
    def data(self):
        """
        :return: The data in this Row (dict)
        """
        return self.__data

    @property
    def key(self):
        """
        :return: The value of this Row's primary key (dict)
        """
        return self.__key

    ####################################################################################################################
    # PUBLIC METHODS
    def save(self):
        """
        Saves this Row to the database, if the table handler still exists
        :return:
        """
        if self.__handler is None:
            raise AttributeError("Cannot save this record to the database.")
        else:

            if self.__handler.is_table:
                if not self.__handler.has_key:
                    raise Exception("Cannot perform 'update' operation without primary key.")
                self.__handler.save(**self.__data)
                new_object = self.__handler.get(self.key)
                if self.__state_changed():
                    self.__handler.delete_from(**self.__original_values)
                self.__dict__.update(new_object.__dict__)
            else:
                raise Exception("Can only perform 'save' on a record in a table.")

    ####################################################################################################################
    # PRIVATE METHODS
    def __state_changed(self):
        """
        :return: Whether or not the original values from this row have been altered (bool)
        """
        return any(self.__original_values[key] != self.__data[key] for key in self.__data)

    def __is_valid_type(self, field, value):
        """
        Validates caller-input values for fields in this row
        :param field:   The field in which the new data is being input (str)
        :param value:   The value (obj)
        :return:        a dictionary: {"valid": Whether or not the value is valid for this field (bool),
                                       "message": an error message, if needed}
        """

        # get the required and input types
        in_type = type(value)
        mapping = self.__mapping[field]
        required_type = mapping[self.__MAPPING_TYPE_KEY]

        # check for nullability
        is_nullable = self.__mapping[field][self.__MAPPING_NULLABLE_KEY]
        if is_nullable:
            null_valid = True
        else:
            null_valid = value is not None

        valid_types = in_type == required_type
        if in_type in (bytes, str) and required_type in (cx_Oracle.CLOB, cx_Oracle.BLOB):
            valid_types = True

        if is_nullable and value is None:
            valid_types = True

        # parse together an error message, if needed
        if not null_valid:
            message = self.__NULL_ERROR_MSG.format(field)
        elif not valid_types:
            message = self.__TYPE_ERROR_MSG.format(field, required_type, in_type)
        else:
            message = ""

        return {"valid": valid_types and null_valid,
                "message": message}

    def __set_data(self, field, value):
        """
        Sets the value of a field to the input value parameter after validation
        :param field:  The field to be set (str)
        :param value:  The input value (obj)
        :return:
        """
        validity = self.__is_valid_type(field, value)
        if validity["valid"]:
            self.__data[field] = value
        else:
            raise TypeError(validity["message"])
