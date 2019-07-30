import os
import caslib
import functools
from flask import request, redirect, url_for, session
from urllib.parse import quote


_default_cas_url_var = "cas_url"


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


def cas_required(cas_server_url=os.environ.get(_default_cas_url_var)):
    """
    Decorator that forces CAS authentication for the decorated endpoint.
    :param cas_server_url: An optional alternative CAS server url
    :return:               A decorated, CAS-protected endpoint
    """
    def _cas_required(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            session["cas-after-login"] = f"{request.path}{_parse_query_string(quoted=False)}"
            if "cas-user" not in session:
                response = login(cas_server_url)
            else:
                response = f(session.pop("cas-user"), session.pop("cas-attributes"), *args, **kwargs)
            return response
        return wrapper
    return _cas_required


def login(in_cas_url):
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
            session["cas-user"] = cas_response.user
            session["cas-attributes"] = cas_response.attributes
            redirect_url = session.pop("cas-after-login")
        else:
            del session["cas-ticket"]
    return redirect(redirect_url)


def cas_logout(cas_server_url=os.environ.get(_default_cas_url_var), after_logout=None):
    """
    Decorator for Flask that handles logging out of CAS
    :param cas_server_url:  The CAS server url
    :param after_logout:    Url for the post logout redirection, if none specified, user goes to CAS logout endpoint
    :return:                A redirect to the CAS logout page
    """
    def _logout(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            logout_url = f"{os.environ[cas_server_url]}/cas/logout"
            if after_logout:
                logout_url += f"?service={url_for(after_logout, _external=True)}"
            response = redirect(logout_url)
            return response
        return inner
    return _logout
