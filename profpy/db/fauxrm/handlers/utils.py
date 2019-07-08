"""
handlers/utils.py
A collection of utility functions for the various handler classes to use.
"""
from .Row import Row


def validate_params(in_params):
    """
    Validates input parameters for parameterized sql
    :param in_params: The parameters (dict, or None)
    :return:          The parameters, if valid
    """
    if in_params:
        if isinstance(in_params, dict):
            return in_params
        else:
            raise TypeError("Parameters must be of type 'dict'")
    else:
        return {}


def results_to_objs(in_cursor, table_object=None, limit=None, get_row_objs=False):
    """
    Takes in a cursor (post execution) and spits out results as a list of dict objects or Row objects
    :param in_cursor:    The cx_Oracle cursor                            (cx_Oracle.Cursor)
    :param table_object: The handler object                              (profpy.db.fauxrm.handlers.Data)
    :param limit:        A limit on the number of results to be returned (int)
    :param get_row_objs: Whether or not to return Row objects            (bool)
    :return:             The list of results                             (list)
    """
    field_names = clean_field_names([d[0].lower() for d in in_cursor.description])
    results = in_cursor.fetchmany(limit) if limit else in_cursor.fetchall()
    return (
        to_row_objs(results, field_names, table_object)
        if get_row_objs
        else to_dict_objs(results, field_names)
    )


def to_row_objs(in_data, in_fields, table_object):
    """
    Takes a list of tuples and a list of column names to spit out a nice result set of Row objects.
    :param in_data:      The results of a sql query execution        (list)
    :param in_fields:    The column names of the query result        (list)
    :param table_object: The handler object linked to the Row object (profpy.db.fauxrm.handlers.Data)
    :return:             A list of Row objects                       (list)
    """
    return [Row(dict(zip(in_fields, row)), table_object) for row in in_data]


def to_dict_objs(in_data, in_fields):
    """
    Takes a list of tuples and a list of column names to spit out a nice result set of dict objects.
    :param in_data:   The results of a sql query execution (list)
    :param in_fields: The column names of the query result (list)
    :return:          A list of dict objects               (list)
    """
    return [dict(zip(in_fields, row)) for row in in_data]


def clean_field_names(in_field_names, bad_chars=(".", "(", ")")):
    """
    Removes characters from fields that would not be valid for Python object attribute names. This method is used
    when renaming the resulting field names from aggregate functions, joins, etc.
    :param in_field_names: The field names to be checked/cleaned               (list)
    :param bad_chars:      The collection of characters to look for and remove (tup)
    :return:               The cleaned list of fields                          (list)
    """
    clean_fields = []
    for fn in in_field_names:
        new_field = fn

        if "*" in new_field:
            new_field = new_field.replace("*", "all")
        for bc in bad_chars:
            new_field = new_field.replace(bc, "_")
        count_chars = len(new_field)
        if new_field[count_chars - 1] == "_":
            new_field = new_field[:-1]
        clean_fields.append(new_field)
    return in_field_names
