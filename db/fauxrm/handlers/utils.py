def fetch_to_dicts(in_cursor, limit=None):
    """
    Takes a cursor, post sql execution, and spits out a list of dictionaries with the keys being the field names and
    the values being the field values for each row.
    :param in_cursor: A cursor object                (cx_Oracle.Cursor)
    :param limit:     A cap on the number or results (int)
    :return:          A list of dict objects         (list)
    """
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

        if "*" in new_field:
            new_field = new_field.replace("*", "all")
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
