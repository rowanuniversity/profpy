import os
import re
from flask import Flask, jsonify
from uuid import uuid1
from sqlalchemy import MetaData, Table
from datetime import datetime, date, time
from ..db import get_sql_alchemy_oracle_session, get_sql_alchemy_oracle_engine


_table_regex = re.compile(r"^\w+\.\w+$")


class Schema(object):
    def __init__(self, in_tables):
        for table_str, table_obj in in_tables.items():
            setattr(self, table_obj.name, table_obj)


class OracleFlaskApp(Flask):
    def __init__(self, context, name, in_tables=None, login=os.environ.get("full_login"),
                 password=os.environ.get("db_password")):
        super().__init__(context)

        schema_to_table = dict()

        if in_tables:
            if not all(re.match(_table_regex, table) for table in in_tables):
                raise ValueError("Invalid table entered. Must be a schema-qualified name: <schema>.<table>")

            for t in set(in_tables):
                parts = t.split(".")
                schema = parts[0]
                table = parts[1]
                if schema in schema_to_table:
                    schema_to_table[schema].append(table)
                else:
                    schema_to_table[schema] = [table]

        engine = get_sql_alchemy_oracle_engine(login, password)
        self.db = get_sql_alchemy_oracle_session(login, password, engine)

        # bake in a healthcheck route
        for rule in ["healthcheck", "health", "ping"]:
            self.add_url_rule(f"/{rule}", view_func=self.__healthcheck)

        if in_tables:
            for schema, tables in schema_to_table.items():
                md = MetaData(engine, schema=schema)
                md.reflect(only=tables, views=True)
                setattr(self, schema, Schema(md.tables))

        self.tables = in_tables
        self.application_name = name
        self.url_map.strict_slashes = False
        self.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
        self.secret_key = str(uuid1())

    def teardown(self, exception):
        self.db.close()

    def __healthcheck(self):
        self.db.execute("select 1 from dual")
        return jsonify(dict(message="Healthy", application=self.application_name, status=200)), 200


def _serialize(self, result_set, as_http_response=False, iso_dates=True):
    out_results = []
    return_one = type(result_set).__name__ == "result"
    if return_one:
        result_set = [result_set]
    for in_result in result_set:
        this_result = dict()
        for column in self.columns:
            value = getattr(in_result, column.name)
            if isinstance(value, (datetime, date, time)) and iso_dates:
                value = value.isoformat()
            this_result[column.name] = value
        out_results.append(this_result)
    out_results = (out_results[0] if out_results else []) if return_one else out_results
    return jsonify(out_results) if as_http_response else out_results


Table.as_json = _serialize
