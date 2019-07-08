import os
import cx_Oracle
import re

DEFAULT_ARRAY_SIZE = 1000


def execute_statement(cursor, sql, params=None):
    """
    Executes a dml or ddl statement.
    If the input statement is not dml/ddl, then the statement is executed and nothing is returned.
    :param cursor: The input cursor.
    :param sql:    The sql to be executed
    :param params: The parameters
    :return:
    """

    cursor.execute(sql, params if params else {})


def execute_query(
    cursor,
    sql,
    params=None,
    limit=None,
    null_to_empty_string=False,
    prefix=None,
    use_generator=False,
):
    """
     Executes a sql query, and outputs the results as a list of dictionaries, rather than a list of lists. This allows
     us to access data by column name rather than index, resulting in much more readable code.

     For example, a normal cx_Oracle cursor execution for "select first_name, last_name from names" would result
     in:
        [ ["john", "smith"], ["jane", "doe"], ... ]

     This functional will instead return:
        [ {"first_name": "john", "last_name": "smith"}, {"first_name": "jane", "last_name": "doe"} ... ]


     :param cursor:               a cx_Oracle cursor object         (cx_Oracle Cursor) -- required
     :param sql:                  a sql statement                   (str)              -- required
     :param params:               parameters for the sql statement  (dict)             -- optional
     :param limit:                a limit on the number of results  (int)              -- optional
     :param null_to_empty_string: convert Nones to empty strings    (bool)             -- optional
     :param prefix:               remove this prefix from dict keys (str)              -- optional


     :param use_generator:        whether or not to return data as
                                  a generator rather than a list    (bool)             -- optional

     :return:                     a list of dictionaries for the results of the sql query
     """

    cursor.execute(sql, params if params else {})
    columns = [d[0].lower() for d in cursor.description]
    if prefix:
        columns = [c[c.startswith(prefix) and len(prefix) :] for c in columns]

    if use_generator:
        output = results_to_generator(cursor, columns, null_to_empty_string, limit)
    else:
        data = cursor.fetchmany(limit) if limit else cursor.fetchall()

        if not data:
            output = []
        else:
            output = [
                row_to_dict(columns, data_row, null_to_empty_string)
                for data_row in data
            ]

    return output


def results_to_generator(
    in_cursor,
    field_names,
    null_to_empty_string=False,
    limit=None,
    array_size=DEFAULT_ARRAY_SIZE,
):
    """
    Returns a generator as the result of a sql query. Each item yielded is a dictionary, with keys being the column
    names of row result.

    :param in_cursor:            The cursor object                                (cx_Oracle.Cursor)
    :param field_names:          The field names for the result set               (list)
    :param null_to_empty_string: Whether or not to convert nulls to empty strings (bool)
    :param limit:                A cap on the results returned                    (int)
    :param array_size:           An array size for the cursor fetch               (int)
    :return:                     A result set from the sql query                  (generator)
    """

    try:
        if limit:
            found_records = 0
            while found_records <= limit:
                results = in_cursor.fetchmany(limit)
                if not results:
                    break
                else:
                    for result in results:
                        if found_records < limit:
                            yield row_to_dict(field_names, result, null_to_empty_string)
                            found_records += 1
                        else:
                            raise StopIteration
        else:
            while True:
                results = in_cursor.fetchmany(array_size)
                if not results:
                    break
                else:
                    for result in results:
                        yield row_to_dict(field_names, result, null_to_empty_string)

    except GeneratorExit as ge:
        try:
            in_cursor.close()
            del in_cursor
        except cx_Oracle.InterfaceError:
            pass  # cursor already closed
        raise ge


def row_to_dict(field_names, data, null_to_empty_string=False):
    """
    Converts a tuple result of a cx_Oracle cursor execution to a dict, with the keys being the column names
    :param field_names:          The names of the columns in the result set       (list)
    :param data:                 The data in this row                             (tup)
    :param null_to_empty_string: Whether or not to convert nulls to empty strings (bool)
    :return:                     A row of results                                 (dict)
    """
    clean_data = (
        ["" if val is None else val for val in data] if null_to_empty_string else data
    )
    return dict(zip(field_names, clean_data))


def parse_multiline_sql(in_str):
    """
    Separates sql string composed of multiple statements into a list of strings
    :param in_str: The sql str
    :return:       A list of sql statements
    """
    regex = re.compile(r"""((?:[^;"']|"[^"]*"|'[^']*')+)""")
    results = []
    bad = ["", "/"]

    for p in regex.split(in_str)[1::2]:
        if p.strip() in bad:
            pass
        else:
            if p[0] == "\n":
                results.append(p[1:])
            elif p[:2] == "\r\n":
                results.append(p[2:])
            elif p[-1:] == "\n":
                results.append(p[:-1])
            elif p[-2:] == "\r\n":
                results.append(p[:-2])
            else:
                results.append(p)
    return results


def sql_file_to_statements(in_file_path, as_one_string=False):
    """
    Reads in a sql file and returns it as a string
    :param in_file_path:        The file path
    :param as_one_string:       Returns the content of the file as a string
    :return:                    The contents of the file as a str object (or list of str objs if multiple statements)
    """
    if os.path.isfile(in_file_path):
        parts = in_file_path.split(".")

        try:
            if parts[len(parts) - 1] != "sql":
                raise Exception("Invalid file type: Must be .sql file.")
            else:
                with open(in_file_path, "r") as sql:
                    sql_str = sql.read()
                    return sql_str if as_one_string else parse_multiline_sql(sql_str)
        except IndexError:
            raise Exception("Invalid file type: Must be .sql file.")
    else:
        raise Exception("File does not exist.")
