from .Row import Row


def fetch_to_dicts(in_cursor, limit=None):
    """
    Takes a cursor, post sql execution, and spits out a list of dictionaries with the keys being the field names and
    the values being the field values for each row.
    :param in_cursor: A cursor object                (cx_Oracle.Cursor)
    :param limit:     A cap on the number or results (int)
    :return:          A list of dict objects         (list)
    """

    field_names = clean_field_names([d[0].lower() for d in in_cursor.description])

    if limit:
        results = execution_iterator(in_cursor, field_names, limit)
        if limit == 1:
            try:
                results = next(results)
            except StopIteration:
                results = None
    else:
        results = execution_iterator(in_cursor, field_names)

    return results


def fetch_to_row_objs(in_cursor, key_fields, mapping, table_object, limit=None):

    field_names = clean_field_names([d[0].lower() for d in in_cursor.description])
    if limit:
        results = row_obj_iterator(in_cursor, field_names, key_fields, mapping, table_object, limit)
        if limit == 1:
            try:
                results = next(results)
            except StopIteration:
                results = None
    else:
        results = row_obj_iterator(in_cursor, field_names, key_fields, mapping, table_object)
    return results


def clean_field_names(in_field_names, bad_chars=(".", "(", ")")):
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


def row_obj_iterator(cursor, field_names, key_fields, mapping, table_object, array_size=1000):
    while True:
        results = cursor.fetchmany(array_size)
        if not results:
            break
        else:
            for result in results:
                yield Row(dict(zip(field_names, result)), key_fields, mapping, table_object)


def execution_iterator(cursor, field_names, array_size=1000):
    while True:
        results = cursor.fetchmany(array_size)
        if not results:
            break
        for result in results:
            yield dict(zip(field_names, result))
