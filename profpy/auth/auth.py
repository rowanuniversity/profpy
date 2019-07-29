import os
import caslib
import functools
from flask import request, redirect, url_for, session


_default_cas_url_var = "cas_url"


def cas_required(after_login_endpoint, cas_url_env_var=_default_cas_url_var):
    def _cas_required(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if "cas-user" not in session:
                session["cas-after-login"] = after_login_endpoint
                response = login(cas_url_env_var)
            else:
                response = f(session.pop("cas-user"), session.pop("cas-attributes"), *args, **kwargs)
            return response
        return wrapper
    return _cas_required


def login(cas_url_env_var):
    """
    Business logic for CAS login
    :param cas_url_env_var: The environment variable containing the CAS server url
    :return:                An appropriate redirect url
    """

    if cas_url_env_var not in os.environ:
        raise Exception(f"Environment variable \"{cas_url_env_var}\" must be set.")

    cas_url = os.environ[cas_url_env_var]
    out_params = request.args.copy()
    if "ticket" in request.args:
        ticket_value = request.args["ticket"]
        app_url = request.url.replace(f"?ticket={ticket_value}", "").replace(f"&ticket={ticket_value}", "")
        del out_params["ticket"]
    else:
        app_url = request.url

    redirect_url = f"{cas_url}/cas/login?service={app_url}"
    if "ticket" in request.args:
        session["cas-ticket"] = request.args["ticket"]

    if "cas-ticket" in session:

        client = caslib.SAMLClient(cas_url, app_url)
        cas_response = client.saml_serviceValidate(session["cas-ticket"])
        if cas_response.success:
            session["cas-user"] = cas_response.user
            session["cas-attributes"] = cas_response.attributes
            redirect_url = url_for(session.pop("cas-after-login"), **out_params)
        else:
            del session["cas-ticket"]
    return redirect(redirect_url)


def cas_logout(cas_url_env_var=_default_cas_url_var, after_logout=None):
    """
    Decorator for Flask that handles logging out of CAS
    :param cas_url_env_var: The environment variable containing the CAS url (default: "cas_url")
    :param after_logout:    Url for the post logout redirection, if none specified, user goes to CAS logout endpoint
    :return:                A redirect to the CAS logout page
    """
    def _logout(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            if cas_url_env_var not in os.environ:
                raise Exception(f"Environment variable \"{cas_url_env_var}\" must be set.")
            logout_url = f"{os.environ[cas_url_env_var]}/cas/logout"
            if after_logout:
                logout_url += f"?service={url_for(after_logout, _external=True)}"
            response = redirect(logout_url)
            return response
        return inner
    return _logout
