# profpy.auth
## Overview
This module contains helper functions for authentication.

## How to use
Currently, the ```profpy.auth``` module contains some basic CAS authentication tools that can be easily used with Flask. 

Prior to using this module, you will want to set an environment variable that contains the URL for your CAS service. The 
default name for this environment variable in the module is ```cas_url```, but you can use others if you want to. You must
also set a ```secret_key``` for the Flask application object for this work properly. An easy way to do this is 
to simply craft a uuid, or set one in your environment.

#### Protecting an endpoint
```python
from flask import Flask
from profpy.auth import cas_required
from uuid import uuid1


app = Flask(__name__)
app.secret_key = str(uuid1())  # a secret key is required


@app.route("/someSensitivePage")
@cas_required()
def sensitive_page(cas_user, cas_attributes):
    return "<h3>You have been authenticated</h3>"
```

That's it! If the user already isn't already authenticated, they will be bounced to the CAS login page. The ```@cas_required``` decorator
must go after any routing decorators to work properly. The decorator has no required arguments. But you can optionally 
specify a CAS server url if you wish to not use the ```cas_url``` environment variable paradigm or if you wish 
to use a different CAS server for a specific endpoint.


The decorator passes the information from the validated ticket along as parameters to the decorated function. We named them ```cas_user``` and ```cas_attributes``` in this example.

If you want the ticket value itself, you can access at the ```cas-ticket``` key in the flask session object:
```python
from flask import Flask, session 
from profpy.auth import cas_required


app = Flask(__name__)
app.secret_key = "some secret value"


@app.route("/someSensitivePage")
@cas_required()
def sensitive_page(cas_user, cas_attributes):
    return f"Ticket: {session.get('cas-ticket')}"
```


#### Endpoints with parameters
Any endpoint parameters come after any CAS-parameters fed from the ```@cas_required``` decorator:
```python
@app.route("/someEndpointWithParams/<id_parameter>")
@cas_required()
def sensitive_page(cas_user, cas_attributes, id_parameter):
    return f"<h3>{cas_user} accessed page {id_parameter}</h3>"
```

#### Using another CAS url
```python
@app.route("/someSensitivePage")
@cas_required("https://some-cas-server.com")
def sensitive_page(cas_user, cas_attributes):
    return "<h3>You have been authenticated</h3>"
```

#### Logging out
You can also configure an endpoint to act as a logout redirect like so:
```python
from flask import Flask
from profpy.auth import cas_logout


app = Flask(__name__)
app.secret_key = "some secret value"


@app.route("/logout")
@cas_logout()
def logout():
    return
```

If you want to redirect them to a custom page post logout, define an endpoint for it and use the new endpoint with Flask's
```url_for``` function:
```python
from flask import Flask, url_for
from profpy.auth import cas_logout


app = Flask(__name__)
app.secret_key = "some secret value"


@app.route("/postLogout")
def after_logout():
    return "<h1>Logged out</h1>"


@app.route("/logout")
@cas_logout(after_logout="after_logout")
def logout():
    pass
```

Just as before, you can specify a different ```cas_url``` to the ```cas_logout``` decorator.
```python
@app.route("/logout")
@cas_logout("https://some-cas-server.com")
def logout():
    pass
```