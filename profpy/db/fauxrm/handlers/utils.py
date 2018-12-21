from .Row import Row


def results_to_objs(in_cursor, table_object=None, limit=None, get_row_objs=False):
    field_names = clean_field_names([d[0].lower() for d in in_cursor.description])
    results = in_cursor.fetchmany(limit) if limit else in_cursor.fetchall()
    return to_row_objs(results, field_names, table_object) if get_row_objs else to_dict_objs(results, field_names)


def to_row_objs(in_data, in_fields, table_object):
    return [Row(dict(zip(in_fields, row)), table_object) for row in in_data]


def to_dict_objs(in_data, in_fields):
    return [dict(zip(in_fields, row)) for row in in_data]


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


