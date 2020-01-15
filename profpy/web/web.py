"""
profpy.web

Easy-to-use Flask extension for CAS and role-based security with database-backed Flask Apps
"""
import os
import re
import functools
import caslib
from flask import Flask, jsonify, session, request, redirect, url_for, render_template
from urllib.parse import quote
from uuid import uuid1
from sqlalchemy import MetaData, Table
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime, date, time


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
    def __init__(self, cas_user, cas_attributes, db_session=None, user_table=None):
        """
        Constructor
        :param cas_user:       A validated CAS user
        :param cas_attributes: A validated CAS user's attribute dictionary
        """

        self.__attributes = cas_attributes
        self.__user = cas_user
        self.roles = []

        if db_session is not None and user_table is not None:
            db_user = db_session.query(user_table).filter_by(username=self.__user).first()
            for field in db_user.keys():
                setattr(self, field, getattr(db_user, field))

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


class SecureFlaskApp(Flask):
    """
    A CAS-secured, Sql-Alchemy Database-backed Flask application. This class also allows for role-based security.
    """
    def __init__(self, context, name, engine, in_tables=None,
                 cas_url=os.environ.get(_default_cas_url_var), logout_endpoint="logout",
                 post_logout_view_function=None, custom_403_template=None, security_schema=os.environ.get(_schema_var),
                 role_table=os.environ.get(_role_var), user_table=os.environ.get(_user_var),
                 user_role_table=os.environ.get(_user_role_var), **configs):
        """
        Constructor
        :param context:                    WSGI object name (__name__)
        :param name:                       The descriptive name of the web app
        :param engine:                     A sqlalchemy engine for the database
        :param in_tables:                  A list of schema-qualified database tables/views for the app to use
        :param cas_url:                    The CAS server url
        :param logout_endpoint:            The endpoint for the CAS logout
        :param post_logout_view_function:  The page to drop a user at after they have logged out
        :param custom_403_template:        A custom 403 html page template
        :param security_schema:            The db schema containing security tables
        :param role_table                  Table containing security roles
        :param user_table                  Table containing security users
        :param user_role_table             Crosswalk table for security roles and users
        :param configs                     Any additional Flask configs to set/override.
        """
        super().__init__(context)

        if cas_url is None:
            raise Exception("CAS url not configured.")

        # strip trailing slash, if it is present
        elif cas_url[len(cas_url) - 1] == "/":
            cas_url = cas_url[:-1]

        # organize tables by schema
        schema_to_table = dict()
        if in_tables:
            if not all(re.match(_table_regex, table) for table in in_tables):
                raise ValueError("Invalid table entered. Must be a schema-qualified name: <schema>.<table>")
            schema_to_table = _explode_full_table_names(in_tables)

        # connect to db
        self.db = scoped_session(sessionmaker(bind=engine))()
        self.__custom_403 = custom_403_template

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
        self.__role_security_configured = False

        required_security = [role_table, user_table, user_role_table, security_schema]

        # set up role-based security if the user configured it
        if any(required_security):

            # if valid, create sqlalchemy table objects for role security
            if all(required_security):
                # shown above, the order of the the security config list is role, user, user_role (0, 1, 2 indexes)
                self.roles = _get_single_table(engine, security_schema, role_table)
                self.users = _get_single_table(engine, security_schema, user_table)
                self.user_roles = _get_single_table(engine, security_schema, user_role_table)

                # validate the required columns
                missing = {}
                for obj, required_fields in {self.roles: ["id", "authority"], self.users: ["id"],
                                             self.user_roles: ["app_role_id", "app_user_id"]}.items():
                    this_table_missing = []
                    raw = _raw_columns(obj)
                    for rf in required_fields:
                        if rf not in raw:
                            this_table_missing.append(rf)
                    if this_table_missing:
                        missing[obj.name] = this_table_missing

                if missing:
                    for k, v in missing.items():
                        self.logger.warning(f"Security table {k} missing the following required fields: {', '.join(v)}")
                else:
                    self.__role_security_configured = True

            # user specified some of the required security configs, but not all. log a warning
            else:
                missing = []
                for k, v in {"role table": role_table, "user table": user_table,
                             "user role crosswalk table": user_role_table, "security schema": security_schema}.items():
                    if not v:
                        missing.append(k)
                self.logger.warning(f"Role-based security not configured correctly. Invalid/missing values: {', '.join(missing)}")

        # other fields
        self.tables = in_tables
        self.application_name = name
        self.url_map.strict_slashes = False
        self.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
        self.config["TEMPLATES_AUTO_RELOAD"] = True
        self.jinja_env.auto_reload = True
        self.secret_key = str(uuid1())
        self.config["TEMPLATES_AUTO_RELOAD"] = True
        self.jinja_env.auto_reload = True

        # set any user-provided configs
        for key, value in configs.items():
            self.config[key] = value

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
        session.pop("cas-object", None)
        return redirect(logout_url)

    def set_session_cookie(self, cookie_name, cookie_value=uuid1()):
        """
        Sets a specified session cookie to a specified value
        :param cookie_name:  the name of the session cookie to be set
        :param cookie_value: the value to set the session cookie to
        :return:             the decorated function
        """
        def _set_cookie_hash(f):
            @functools.wraps(f)
            def wrap(*args, **kwargs):
                session[cookie_name] = cookie_value
                return f(*args, **kwargs)
            return wrap
        return _set_cookie_hash

    def requires_session_cookie(self, cookie_name, http_user=os.environ.get("http_basic_auth_user"),
                                http_password=os.environ.get("http_basic_auth_password")):
        """
        Requires a session cookie for the decorated endpoint to be accessed. This is particularly useful for protecting
        admin-related AJAX endpoints from outside use.
        :param cookie_name:     A cookie name
        :param http_user:       Basic auth user
        :param http_password:   Basic auth password
        :return:                An http response
        """
        def _requires_cookie(f):
            @functools.wraps(f)
            def wrap(*args, **kwargs):
                if session.get(cookie_name):
                    response = f(*args, **kwargs)
                elif request.authorization:
                    if request.authorization.username == http_user \
                            and request.authorization.password == http_password:
                        response = f(*args, **kwargs)
                    else:
                        response = jsonify(dict(message="Invalid credentials")), 403
                else:
                    response = jsonify(dict(message="Missing credentials.")), 401
                return response
            return wrap
        return _requires_cookie

    def secured(self, any_roles=None, not_roles=None, all_roles=None, get_cas_user=False):
        """
        Use CAS to secure an endpoint, alternatively specify any roles to restrict access to the endpoint to as well
        :param any_roles:    A list of roles to allow to see the form
        :param get_cas_user: Whether or not to return an object representing an authenticated CAS user
        :param not_roles:    A list of roles to NOT allow to see the form
        :param all_roles:    User must be in ALL of these roles to see page
        :return:             the decorated function
        """
        def _secured(f):
            @functools.wraps(f)
            def wrap(*args, **kwargs):

                # set response to "unauthorized" by default, this will get changed if the user is allowed to hit
                # the decorated route function
                response = render_template(self.__custom_403) if self.__custom_403 \
                               else jsonify(dict(message="Unauthorized")), 403
                session["cas-after-login"] = f"{request.path}{_parse_query_string(quoted=False)}"
                if "cas-object" not in session:
                    response = _login(self.__cas_server_url)
                else:
                    raw_cas = session.get("cas-object")
                    cas = CasUser(raw_cas["user"], raw_cas["attributes"], db_session=self.db, user_table=self.users)

                    # do role-based security, if it was configured
                    if self.__role_security_configured:
                        auths = self.db.query(self.users, self.roles.c.authority) \
                            .outerjoin(self.user_roles, self.users.c.id == self.user_roles.c.app_user_id) \
                            .outerjoin(self.roles, self.user_roles.c.app_role_id == self.roles.c.id) \
                            .filter(self.users.c.username == cas.user).all()
                        cas.roles = [a.authority for a in auths]

                        # all_roles was set, and the authenticated user doesn't have all of the roles in the
                        # in the list, block their access
                        valid = True
                        if all_roles and not all(role in cas.roles for role in all_roles):
                            valid = False
                        if not_roles and any(role in not_roles for role in cas.roles):
                            valid = False
                        if any_roles and not any(role in any_roles for role in cas.roles):
                            valid = False
                        if valid:
                            response = f(cas, *args, **kwargs) if get_cas_user else f(*args, **kwargs)

                    # no role-based security configured, just do CAS
                    else:
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


def _login(in_cas_url, db_session=None, security_user_table=None):
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
            session["cas-object"] = CasUser(cas_response.user, cas_response.attributes, db_session,
                                            security_user_table).serialize()
            redirect_url = session.pop("cas-after-login")
        else:
            del session["cas-ticket"]
    return redirect(redirect_url)


def _raw_columns(table_obj):
    return [str(col).replace(f"{table_obj.name}.", "") for col in table_obj.columns]


# implement serializer
Table.as_json = _serialize_table_object
