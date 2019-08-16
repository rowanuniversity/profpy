"""
profpy.web

Easy-to-use Flask extension for CAS and role-based security with Oracle-backed Flask Apps
"""
import os
import re
import functools
import caslib
from flask import Flask, jsonify, session, request, redirect, url_for
from urllib.parse import quote
from uuid import uuid1
from sqlalchemy import MetaData, Table
from datetime import datetime, date, time
from ..db import get_sql_alchemy_oracle_session, get_sql_alchemy_oracle_engine


# some constants
_table_regex = re.compile(r"^\w+\.\w+$")
_default_cas_url_var = "cas_url"
_schema_var = "security_schema"
_role_var = "security_role_table"
_user_var = "security_user_table"
_user_role_var = "security_user_role_table"


class CasUser(object):
    """
    Helper class that simply makes accessing CAS attributes more straight forward
    """
    def __init__(self, cas_user, cas_attributes, roles=None):
        """
        Constructor
        :param cas_user:       A validated CAS user
        :param cas_attributes: A validated CAS user's attribute dictionary
        """

        self.__attributes = cas_attributes
        self.__user = cas_user
        self.roles = roles if roles else []

    def __getattr__(self, item):
        if item == "user":
            result = self.__user
        else:
            result = self.__attributes.get(item)
            if result:
                result = result[0] if len(result) == 1 else result
        return result

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __str__(self):
        return self.__user

    def __repr__(self):
        return self.__str__()

    def serialize(self):
        return dict(user=self.__user, attributes=self.__attributes)


class Schema(object):
    """
    Helper class for simply storing Table objects with their appropriate schema
    """
    def __init__(self, in_tables):
        for table_str, table_obj in in_tables.items():
            setattr(self, table_obj.name, table_obj)


class OracleFlaskApp(Flask):
    """
    A CAS-secured, Sql-Alchemy Oracle-backed Flask application.
    """
    def __init__(self, context, name, in_tables=None, login=os.environ.get("full_login"),
                 password=os.environ.get("db_password"), role_security=True,
                 cas_url=os.environ.get(_default_cas_url_var), logout_endpoint="logout",
                 post_logout_view_function=None):
        """
        Constructor
        :param context:                    WSGI object name (__name__)
        :param name:                       The descriptive name of the web app
        :param in_tables:                  A list of schema-qualified database tables/views for the app to use
        :param login:                      Oracle DB login
        :param password:                   Oracle password
        :param role_security:              Whether or not to enable role-based security
        :param cas_url:                    The CAS server url
        :param logout_endpoint:            The endpoint for the CAS logout
        :param post_logout_view_function:  The page to drop a user at after they have logged out
        """
        super().__init__(context)

        # organize tables by schema
        schema_to_table = dict()
        if in_tables:
            if not all(re.match(_table_regex, table) for table in in_tables):
                raise ValueError("Invalid table entered. Must be a schema-qualified name: <schema>.<table>")
            schema_to_table = _explode_full_table_names(in_tables)

        # connect to oracle
        engine = get_sql_alchemy_oracle_engine(login, password)
        self.db = get_sql_alchemy_oracle_session(login, password, engine)

        # bake in a healthcheck route
        for rule in ["healthcheck", "health", "ping"]:
            self.add_url_rule(f"/{rule}", view_func=self.__healthcheck)
        self.add_url_rule(f"/{logout_endpoint}", view_func=self.__logout)

        # create table object attributes of the app (e.g. app.query(app.schema.table).all())
        if in_tables:
            for schema, tables in schema_to_table.items():
                setattr(self, schema, Schema(_create_table_objects(engine, schema, tables)))

        # configure the optional role-based security
        self.roles = None
        self.users = None
        self.user_roles = None
        self.__after_logout = post_logout_view_function
        self.__cas_server_url = cas_url

        required_security_vars = [_role_var, _user_var, _user_role_var, _schema_var]
        security_vals = {_role_var: os.environ.get(_role_var), _user_var: os.environ.get(_user_var),
                         _user_role_var: os.environ.get(_user_role_var)}
        security_schema = os.environ.get(_schema_var)
        if role_security:

            # check configuration in environment vars
            if not all(ev in os.environ for ev in required_security_vars):
                raise Exception(f"Security environment variables must be set: {', '.join(required_security_vars)}")

            # if valid, create sqlalchemy table objects for role security
            else:
                # shown above, the order of the the security config list is role, user, user_role (0, 1, 2 indexes)
                self.roles = _get_single_table(engine, security_schema, security_vals[_role_var])
                self.users = _get_single_table(engine, security_schema, security_vals[_user_var])
                self.user_roles = _get_single_table(engine, security_schema, security_vals[_user_role_var])

        # other fields
        self.tables = in_tables
        self.application_name = name
        self.url_map.strict_slashes = False
        self.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
        self.secret_key = str(uuid1())

    def __healthcheck(self):
        """
        Baked in app health check
        :return: a json response
        """
        try:
            self.db.execute("select 1 from dual")
            response = jsonify(dict(message="Healthy", application=self.application_name, status=200)), 200
        except Exception as e:
            response = jsonify(dict(message=f"Unhealthy: {str(e)}", application=self.application_name, status=500)), 500
        return response

    def __logout(self):
        """
        :return: A redirect for a CAS logout
        """
        logout_url = f"{self.__cas_server_url}/cas/logout"
        if self.__after_logout:
            logout_url += f"?service={url_for(self.__after_logout, _external=True)}"
        return redirect(logout_url)

    def secured(self, roles=None, get_cas_user=False):
        """
        Use CAS to secure an endpoint, alternatively specify any roles to restrict access to the endpoint to as well
        :param roles:        A list of roles for security
        :param get_cas_user: Whether or not to return an object representing an authenticated CAS user
        :return:             the decorated function
        """
        def _secured(f):
            @functools.wraps(f)
            def wrap(*args, **kwargs):
                if not self.__cas_server_url:
                    raise Exception("No CAS URL set in environment or specified in decorator.")
                else:
                    response = jsonify(dict(message="Unauthorized")), 403
                    session["cas-after-login"] = f"{request.path}{_parse_query_string(quoted=False)}"
                    if "cas-object" not in session:
                        response = _login(self.__cas_server_url)
                    else:
                        raw_cas = session.get("cas-object")
                        cas = CasUser(raw_cas["user"], raw_cas["attributes"])
                        auths = self.db.query(self.users, self.roles.c.authority) \
                            .outerjoin(self.user_roles, self.users.c.id == self.user_roles.c.app_user_id) \
                            .outerjoin(self.roles, self.user_roles.c.app_role_id == self.roles.c.id) \
                            .filter(self.users.c.username == cas.user).all()
                        cas.roles = [a.authority for a in auths]

                        # role-based auth. if roles are specified and the user doesn't meet the requirement, keep the
                        # default 403 response
                        if roles and not any(role in roles for role in cas.roles):
                            pass

                        # else, they authenticated fully (both CAS and role-base if specified)
                        else:
                            session.pop("cas-object")
                            response = f(cas, *args, **kwargs) if get_cas_user else f(*args, **kwargs)
                return response
            return wrap
        return _secured


def _explode_full_table_names(in_tables):
    """
    Takes a list of schema-qualified names and creates a schema-key, table_list-value dict
    :param in_tables: A list of schema-qualified table/view names
    :return:          schema-key, table_list-value dict
    """
    schema_to_table = dict()
    for t in set(in_tables):
        parts = t.split(".")
        schema = parts[0]
        table = parts[1]
        if schema in schema_to_table:
            schema_to_table[schema].append(table)
        else:
            schema_to_table[schema] = [table]
    return schema_to_table


def _get_single_table(engine, in_schema, in_table):
    """
    Create a single table object
    :param engine:    sqlalchemy engine
    :param in_schema: the db schema
    :param in_table:  the table
    :return:          sqlalchemy table object
    """
    md = MetaData(engine, schema=in_schema)
    md.reflect(only=[in_table], views=True)
    return md.tables[f"{in_schema}.{in_table}"] if md.tables else None


def _create_table_objects(engine, schema, tables):
    """
    Create multiple table objects for one schema
    :param engine: sqlalchemy engine
    :param schema: db schema
    :param tables: the tables
    :return:       sqlalchemy table objects in a dict
    """
    md = MetaData(engine, schema=schema)
    md.reflect(only=tables, views=True)
    return md.tables


def _serialize_table_object(self, result_set, as_http_response=False, iso_dates=True):
    """
    Serializer for results of a sqlalchemy query from Table object
    :param self:              the object
    :param result_set:        the result
    :param as_http_response:  whether or not to return an actual json "response" or just a dict
    :param iso_dates:         whether or not to use iso dates
    :return:                  json for a sqlalchemy query result
    """
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


def _parse_query_string(quoted=False):
    """
    Appropriately parses query string from current request object
    :param quoted: Whether or not to use url quoting (necessary when setting CAS service parameter)
    :return:       A parsed query string from the current request object
    """
    qs = "?"
    arg_list = []
    for k, v in request.args.items():
        if k != "ticket":
            arg_list.append(f"{k}={v}")

    qs += "&".join(arg_list)
    return (quote(qs) if quoted else qs) if qs != "?" else ""


def _login(in_cas_url):
    """
    Business logic for CAS login
    :param in_cas_url:      The CAS server url
    :return:                An appropriate redirect url
    """
    app_url = f"{request.base_url}{_parse_query_string(quoted=True)}"
    redirect_url = f"{in_cas_url}/cas/login?service={app_url}"
    if "ticket" in request.args:
        session["cas-ticket"] = request.args["ticket"]

    if "cas-ticket" in session:

        client = caslib.SAMLClient(in_cas_url, app_url)
        cas_response = client.saml_serviceValidate(session["cas-ticket"])
        if cas_response.success:
            session["cas-object"] = CasUser(cas_response.user, cas_response.attributes).serialize()
            redirect_url = session.pop("cas-after-login")
        else:
            del session["cas-ticket"]
    return redirect(redirect_url)


# implement serializer
Table.as_json = _serialize_table_object
