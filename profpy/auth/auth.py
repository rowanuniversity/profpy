import os
import caslib
import functools
from flask import request, redirect

_default_cas_url_var = "cas_url"


def cas_required(get_user=False, get_ticket=False, cas_url_env_var=_default_cas_url_var, override_http=False):
    """
    Decorator for Flask that handles CAS authentication for the routing function it is decorating
    :param get_user:        Whether or not to return the authenticated user object
    :param get_ticket:      Whether or not to return the authenticated ticket object
    :param cas_url_env_var: The environment variable containing the CAS url (default: "cas_url")
    :param override_http:   Switch to https for your service in the CAS service argument
    :return:                Either a redirect response to CAS auth page, or the desired dest., if already logged in
    """
    def _cas_required(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if cas_url_env_var not in os.environ:
                raise ValueError(f"Environment variable \"{cas_url_env_var}\" not found.")
            else:
                cas_url = os.environ[cas_url_env_var]
            redirect_url = request.url
            if override_http and redirect_url[:5] != "https":
                redirect_url = redirect_url.replace("http", "https")
            response = redirect(f"{cas_url}/cas/login?service={redirect_url}")
            if "ticket" in request.args:
                ticket = caslib.SAMLClient(cas_url, request.base_url).saml_serviceValidate(request.args["ticket"])
                if ticket.success:
                    if get_ticket or get_user:
                        if get_ticket and get_user:
                            response = f(ticket.user, ticket.attributes, *args, **kwargs)
                        elif get_user:
                            response = f(ticket.user, *args, **kwargs)
                        else:
                            response = f(ticket.attributes, *args, **kwargs)
                    else:
                        response = f(*args, **kwargs)
            return response
        return wrapper
    return _cas_required


def cas_logout(cas_url_env_var=_default_cas_url_var):
    """
    Decorator for Flask that handles logging out of CAS
    :param cas_url_env_var: The environment variable containing the CAS url (default: "cas_url")
    :return:                A redirect to the CAS logout page
    """
    def _logout(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            return redirect(f"{os.environ[cas_url_env_var]}/cas/logout")
        return inner
    return _logout
