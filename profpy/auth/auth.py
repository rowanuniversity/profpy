import os
import caslib
from flask import request, redirect

_default_cas_url_var = "cas_url"


def cas_required(get_user=False, get_ticket=False, cas_url_env_var=_default_cas_url_var):
    """
    Decorator for Flask that handles CAS authentication for the routing function it is decorating
    :param get_user:        Whether or not to return the authenticated user object
    :param get_ticket:      Whether or not to return the authenticated ticket object
    :param cas_url_env_var: The environment variable containing the CAS url (default: "cas_url")
    :return:                Either a redirect response to CAS auth page, or the desired dest., if already logged in
    """
    def _cas_required(f):
        def wrapper(*args, **kwargs):
            if cas_url_env_var not in os.environ:
                raise ValueError(f"Environment variable \"{cas_url_env_var}\" not found.")
            else:
                cas_url = os.environ[cas_url_env_var]
            response = redirect(f"{cas_url}/cas/login?service={request.base_url}")
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
                else:
                    raise Exception("Invalid ticket.")
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
        def inner(*args, **kwargs):
            return redirect(f"{os.environ[cas_url_env_var]}/cas/logout")
        return inner
    return _logout
