class PrimaryKey(object):
    """
    A class for handling primary keys for database tables
    """

    def __init__(self, columns):
        """
        Constructor
        :param columns: A list of column names that make up this key (list)
        """

        # the columns that make up this key (a single value list if it isn't composite)
        self.columns = columns

    ####################################################################################################################
    # OVERRIDES
    def __len__(self):
        """
        Override __len__
        :return: The number of columns used by this primary key
        """

        return self.field_count

    def __str__(self):
        """
        Override __str__
        :return: A string representation of this primary key (list if composite, single value if not) (str)
        """

        return str(self.columns if self.field_count > 1 else self.columns[0])

    def __repr__(self):
        return str(self.columns)

    ####################################################################################################################
    # PROPERTIES
    @property
    def exists(self):
        """
        :return: If this primary key actually exists (isn't null or has a length of 0) (boolean)
        """

        return self.columns is not None and self.field_count > 0

    @property
    def field_count(self):
        """
        :return: The number of fields used by this primary key (int)
        """

        return len(self.columns)

    @property
    def is_composite(self):
        """
        :return: Whether or not this is a composite primary key (boolean)
        """

        return self.field_count > 1

    @property
    def sql_where_clause(self):
        """
        :return: The where clause for a parameterized query using this key (str)
        """

        statements = []
        for column in self.columns:
            statements.append("{column}=:{column}".format(column=column))
        return " and ".join(statements)

    @property
    def key_return(self):
        return "returning {0} into :out_key_string".format("||','||".join(self.columns))
