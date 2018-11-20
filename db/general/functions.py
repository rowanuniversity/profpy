def execute_sql(cursor, sql, params=None, limit=None, null_to_empty_string=False, prefix=None):
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

     :return:                     a list of dictionaries for the results of the sql query
     """

    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)

    columns = [d[0].lower() for d in cursor.description]
    if prefix:
        columns = [c[c.startswith(prefix) and len(prefix):] for c in columns]

    if limit:
        if limit == 1:
            data = [cursor.fetchone()]
        elif limit > 1:
            data = cursor.fetchmany(limit)
        else:
            data = cursor.fetchall()
    else:
        data = cursor.fetchall()

    if not data or (data == [None] and limit == 1):
        output = None if limit == 1 else []
    else:
        output = [dict(zip(columns, ["" if val is None else val for val in data_row] if null_to_empty_string else data_row))
                  for data_row in data]
        if limit == 1 and len(output) > 0:
            output = output[0]
    return output
