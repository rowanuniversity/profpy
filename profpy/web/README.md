# profpy.web
## Overview
The ```web``` submodule contains an extension of the Flask wsgi object called ```SecuredFlaskApp``` which allows
us to make role and CAS-secured Flask apps with minimal overhead. 

#### Creating an Application
The ```SecureFlaskApp``` class allows us to access auto-generated Sql-Alchemy models of any table or view 
as attributes of the application. All you have to do is provide schema-qualified table/view names in a list to
the constructor.

All instances of this class have a baked-in healthcheck endpoint. This can be reached at ```/health```,
 ```/healthcheck```, or ```/ping```.

```python
from profpy.web import SecureFlaskApp
from profpy.db import get_sql_alchemy_oracle_engine

engine = get_sql_alchemy_oracle_engine()
app = SecureFlaskApp(__name__, "My Web App", engine, ["general.people", "contact.addresses"])

# get models by attribute access
people = app.general.people
addresses = app.contact.addresses


@app.route("/")
@app.secured()
def home():
    return "<h1>Home Page</h1>"

@app.route("/person/id/<person_id>")
def search(person_id):
    return people.as_json(
        app.db.query(people).filter_by(
            id=person_id
        ).first(),
        as_http_response=True
    )
  
``` 

In the above example, we created a basic home page with the ```home``` route function. Using the ```@app.secured``` 
decorator, we added CAS-protection to the endpoint (more on CAS configuration later). The ```search``` function gives an
example of the auto-generated Sql-Alchemy models being used directly as properties of the application.


#### Using the CAS user
What if you want to use information from the authenticated CAS user? This is possible by specifying ```True``` for
the optional ```get_cas_user``` argument to the ```@app.secured``` decorator. Doing this will pass the 
user object along to the decorated function. This object will have all of the CAS attributes as class attributes, 
as well as any roles the user may have from role-based security (if used).

```python
@app.route("/")
@app.secured(get_cas_user=True)
def home(cas_user):

    # access to authenticated CAS attributes
    cas_user.sAMAccountName
    cas_user.displayName
    
    return f"<h1>Welcome {cas_user.user}</h1>"
```

#### Role-based protection
Once configured (see configuration section at bottom), you can also use role-based protection for endpoints. The ```SecureFlaskApp```
class looks for and then validates this configuration. If no configuration is specified, role-based security is ignored. If an invalid
configuration is specified, role-based security will be ignored, but the app's logger will notify you of what 
values need to be fixed. 


When relying on environment variable-based configuration, you don't have to change anything in your setup for Flask.
```python
from profpy.web import SecureFlaskApp
from profpy.db import get_sql_alchemy_oracle_engine

engine = get_sql_alchemy_oracle_engine()
app = SecureFlaskApp(__name__, "My App", engine, ["general.people", "contact.addresses"])
```

Alternatively, you can specify role-based security configuration values to the constructor itself. This is also shown in the configuration section at the end of this README. 
```python
from profpy.web import SecureFlaskApp
from profpy.db import get_sql_alchemy_oracle_engine

engine = get_sql_alchemy_oracle_engine()
app = SecureFlaskApp(__name__, "My App", engine, ["general.people", "contact.addresses"], security_schema="security", role_table="app_role", user_table="app_user", user_role_table="app_user_app_role")
```

---

Restricting access to users who have any of the given roles:
```python
app = SecureFlaskApp(__name__, "My Web App", engine, ["general.people", "contact.addresses"])

@app.route("/mainSecurityGrid")
@app.secured(any_roles=["ROLE_NEDRY"])
def main_security():
    return "<h1>Welcome, to Jurassic Park</h1>"
```

You can also do the inverse and have a list of roles to block access from. 
```python
app = SecureFlaskApp(__name__, "My Web App", engine, ["general.people", "contact.addresses"])

@app.route("/mainSecurityGrid")
@app.secured(not_roles=["ROLE_NEDRY"])
def main_security():
    return "<h1>Welcome, to Jurassic Park</h1>"
```

Restricting access to users who have ALL of the given roles:
```python
app = SecureFlaskApp(__name__, "My Web App", engine, ["general.people", "contact.addresses"])

@app.route("/mainSecurityGrid")
@app.secured(all_roles=["ROLE_NEDRY", "ROLE_HAMMOND"])
def main_security():
    return "<h1>Welcome, to Jurassic Park</h1>"
```

Role Security Arguments:

| Argument                | Description                                                        |
|--------------------------|--------------------------------------------------------------------|
| any_roles          | User that has any of these roles can access endpoint       |
| not_roles      | User with any of these roles can NOT access the endpoint                    |
| all_roles      | User with all of these roles can access the endpoint                    |


The CAS user will also have a list of all of their roles as an attribute:
```python
@app.route("/mainSecurityGrid")
@app.secured(all_roles=["ROLE_NEDRY", "ROLE_HAMMOND"], get_cas_user=True)
def main_security(user):
    roles = user.roles
    return f"<h1>Welcome, to Jurassic Park. You have these roles: {', '.join(roles)}</h1>"
```

Correct configuration of role-based security will allow you access to any fields from your security user table as 
part of the CAS user object. Let's assume there is a ```display_name``` field in your user table in the data base; you 
can access it this way:

```python
app = SecureFlaskApp(__name__, "My Web App", engine, ["general.people", "contact.addresses"])

@app.route("/mainSecurityGrid")
@app.secured(all_roles=["ROLE_NEDRY", "ROLE_HAMMOND"], get_cas_user=True)
def main_security(cas_user):
    return f"<h1>Hello {cas_user.display_name}! Welcome, to Jurassic Park</h1>"
```


#### Custom 403 Page
By default the app will just render a basic "Unauthorized" json response. You can override this by specifying
a template name in the constructor for the ```SecureFlaskApp```.
```python
app = SecureFlaskApp(__name__, "My Web App", engine, ["general.people", "contact.addresses"], custom_403_template="403.html")
```

#### CAS logout
By default, the ```SecureFlaskApp``` comes with a ```/logout``` endpoint that will use the CAS server to log the current user
out. Once logged out, the user will be sent to the CAS server's default logout page. 

However, you can specify an after logout location specific to your app via the ```SecureFlaskApp```'s constructor.
```python
app = SecureFlaskApp(__name__, "My Web App", engine, post_logout_view_function="post_logout")


@app.route("/afterLogout")
def post_logout():
    return "<h1>User logged out</h1>"
```

Note that this argument is the name of the routing function that you define in your code, not the endpoint itself.


You can also override the logout endpoint to be something other than ```/logout```.
```python
app = SecureFlaskApp(__name__, "My Web App", engine, logout_endpoint="/otherLogout", post_logout_view_function="post_logout")
```

#### Session Cookie-based Protection
There may also be scenarios in which you want to protect endpoints using a combination of session cookies and HTTP basic auth. 

A good use case here would be an admin-like page that utilizes AJAX. To clamp down these kinds of endpoints to only 
be accessible from certain pages, you can use the ```@app.set_session_cookie``` and ```@app.requires_session_cookie``` decorators.

The ```@app.set_session_cookie``` decorator simply sets a Flask session cookie to a specified value when you hit the decorated route. 

The ```@app.requires_session_cookie``` decorator only allows users to use the decorated route function if the
specified cookie is present *or* if they provide suitable HTTP basic auth credentials. 

This gives us flexibility to design secure AJAX methods that can be used both by the web app and *authorized* users outside of the web app using cURL or some similar tool.

```python
from profpy.db import get_sql_alchemy_oracle_engine
from profpy.web import SecureFlaskApp
from flask import request

engine = get_sql_alchemy_oracle_engine()
app = SecureFlaskApp(__name__, "My Web App", engine, ["general.people", "contact.addresses"])

@app.route("/admin")
@app.set_session_cookie("admin-session")
@app.secured()
def admin():
    return "<h1>admin page</h1>"


@app.route("/createUser", methods=["POST"])
@app.requires_session_cookie("admin-session")
def create():
    app.db.execute(
        app.general.people.insert().values(
            first_name=request.args.first_name,
            last_name=request.args.last_name
        )
    )
    app.db.commit()
```

##### What did that do?
When the user hits the ```/admin``` endpoint, a cookie called "admin-session" gets 
set in the encrypted Flask session object. As long as this is set, they can use the 
```/createUser``` endpoint. If they tried hitting ```curl host:port/createUser``` from the command
line, they would get a 401 error. If http basic auth is set up in the environment (see configuration section below), 
the endpoint *is* accessible from outside of the application if valid credentials are supplied. 

##### What is the cookie value? 
By default, ```@app.set_session_cookie``` sets the session cookie to a random uuid. However, 
you can override this default behavior.
```python
@app.route("/admin")
@app.set_session_cookie("admin-session", cookie_value="some-alternative-value")
@app.secured()
def admin():
    return "<h1>admin page</h1>"
```

## Configuration
The ```SecureFlaskApp``` requires some very basic configuration for CAS, and some additional configuration for role-based
security (if used). 

#### CAS
For CAS to work correctly, you just need to set an environment variable called ```cas_url``` that stores 
the CAS server url. Alternatively, you could specify this url when you create the application.
```python
app = SecureFlaskApp(__name__, "My Web App", engine, cas_url="https://some-cas-server.com")
``` 

#### Role-based security
To use role-based security, set the following environment variables:

| Env Var                  | Description                                                        |
|--------------------------|--------------------------------------------------------------------|
| security_schema          | The database schema containing your security tables/views          |
| security_role_table      | The database table/view containing role info                       |
| security_user_table      | The database table/view containing user info                       |
| security_user_role_table | The database table/view containing the user to role crosswalk info |

Additionally, these tables/views are required to follow some basic structural rules:

- The role and user tables must both have unique key fields called ```id```. 

- The crosswalk table must have identifiers called ```app_user_id``` and ```app_role_id``` to link back to the other tables. 

- The actual role names in the role table/view must be stored in a field called ```authority```.

- The user table must have a column called ```username``` that corresponds to authenticated CAS users' usernames found in the CAS attributes. 

Instead of setting environment variables, you can also specify these configuration values in the app's constructor:
```python
app = SecureFlaskApp(__name__, "My Web App", engine, security_schema="security", role_table="roles", user_table="users", user_role_table="user_roles")
```

#### Session Cookie Protection
The only configuration needed for session cookie-based endpoint protection would be to set 
the following environment variables:

| Env Var                  | Description                                                        |
|--------------------------|--------------------------------------------------------------------|
| http_basic_auth_user          | username          |
| http_basic_auth_password     | password |

## app-init CLI
Upon installation of profpy (2.3.0 or higher), you will get the command line tool "app-init" as well. This tool
allows you to quickly create and configure Dockerized web applications with the ```profpy.web``` tools.

```shell script
app-init -h
```
