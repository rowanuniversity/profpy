# profpy.auth
## Overview
This module contains helper functions for authentication.

## How to use
Currently, the ```profpy.auth``` module contains some basic CAS authentication tools that can be easily used with Flask. 

Prior to using this module, you will want to set an environment variable that contains the URL for your CAS service. The 
default name for this enviroment variable in the module is ```cas_url```, but you can use others if you want to.

#### Protecting an endpoint
```python
from flask import Flask
from profpy.auth import cas_required


app = Flask(__name__)


@app.route("/someSensitivePage")
@cas_required()
def sensitive_page():
    return "<h3>You have been authenticated</h3>"
```

That's it! If the user already isn't already authenticated, they will be bounced to the CAS login page. The ```@cas_required``` decorator
must go after any routing decorators to work properly.

#### Getting info from CAS
You can also retrieve the authenticated user and or ticket by using the decorator like so:
```python
@app.route("/someSensitivePage")
@cas_required(get_user=True, get_ticket=True)
def sensitive_page(auth_user, ticket):
    return f"<h3>{auth_user} is logged in.</h3>"
```

#### Endpoints with parameters
Any endpoint parameters come after any CAS-parameters fed from the ```@cas_required``` decorator:
```python
@app.route("/someEndpointWithParams/<id_parameter>")
@cas_required(get_user=True)
def sensitive_page(auth_user, id_parameter):
    return f"<h3>{auth_user} accessed page {id_parameter}</h3>"
```

#### Using another environment variable to store URL
```python
@app.route("/someSensitivePage")
@cas_required(cas_url_env_var="some_other_environment_variable")
def sensitive_page():
    return "<h3>You have been authenticated</h3>"
```

#### Logging out
You can also configure an endpoint to act as a logout redirect like so:
```python
from flask import Flask
from profpy.auth import cas_logout


app = Flask(__name__)


@app.route("/logout")
@cas_logout()
def logout():
    return
```
Just as before, you can specify a different environment variable using the ```cas_url_env_var``` argument to the decorator.