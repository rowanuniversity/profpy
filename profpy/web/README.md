# profpy.web
## Overview
The ```web``` submodule contains some helper classes to make Flask app development even easier than it already was. 

Contained in this submodule is the ```OracleFlaskApp``` extension of the ```Flask``` class that enables easy access to 
Oracle tables/views with Sql-Alchemy without the need for explicitly writing models.

Also in this submodule are the ```@cas_required``` and ```@cas_logout``` CAS authentication decorators, which can 
be accessed like so: ```from profpy.web.auth import cas_required, cas_logout```. These decorators will work with *any* 
Flask application, not just our ```OracleFlaskApp``` class.


### Creating an Application
The ```OracleFlaskApp``` class allows us to access auto-generated Sql-Alchemy models of any table or view 
as attributes of the application. All you have to do is provide schema-qualified table/view names in a list to
the constructor.

All instances of this class have a baked-in healthcheck endpoint. This can be reached at ```/health```,
 ```/healthcheck```, or ```/ping```.

```python
from profpy.web import OracleFlaskApp
from flask import jsonify

app = OracleFlaskApp(__name__, "My Oracle Web App", ["general.people", "contact.addresses"], "login", "password")

# get models by attribute access
people = app.general.people
addresses = app.contact.addresses


@app.route("/person/id/<person_id>")
def search(person_id):
    return people.as_json(
        app.db.query(people).filter_by(
            id=person_id
        ).first(),
        as_http_response=True
    )
    
# you can also execute sql rather than use the models. However, you may need to 
# implement some custom json formatting (not shown here)
@app.route("/person/name/<name>")
def name_search(name):
    return jsonify(app.db.execute("select * from general.people where name like :p_name || '%'", p_name=name))
``` 

As you can see from above, we called the model's ```as_json``` method and passed in a Sql-Alchemy query. The ```as_json```
method also allows us to specify if we just want the json as a python ```dict``` object or as a "jsonified" Flask response.
Having this option eliminates the need for repeated calls to ```flask.jsonify``` across an application with json endpoints. 

Go [here](./technical.md) for technical documentation on the ```OracleFlaskApp``` class.


### Protecting endpoints with CAS
The ```auth``` decorators in this submodule allow us to easily protect endpoints with CAS. 
Prior to using this module, you may want to set an environment variable that contains the URL for your CAS service. The name for this environment variable in the module is ```cas_url```. Alternatively, you can pass a url into the decorators each time you use them.

If you 
are using a ```Flask``` object (not ```OracleFlaskApp```), you will then have to set a ```secret_key``` for this work properly. An easy way to do this is 
to simply craft a uuid, or set one in your environment.


```python
from profpy.web import auth, OracleFlaskApp


app = OracleFlaskApp(__name__, "My App", ["schema.table"], "login", "password")

@app.route("/")
@auth.cas_required()
def home(cas_user, cas_attributes):
    return f"<h1>{cas_user} Authenticated!"
```

As seen above, the ```cas_required``` decorator passes the authenticated user and attributes on to the 
decorated endpoint. When the endpoint is hit, the user will either get bounced to the CAS server for authentication, or 
they will reach their destination without interruption. Once authenticated, they get bounced to the endpoint's intended 
location. 

#### Logging out
You can also use the ```auth.cas_logout``` decorator to log a user out of CAS. You can provide an optional ```after_logout```
parameter that specifies where the user goes once they are logged out. If not, they go to the default CAS logout page for the 
given server. 

```python
from profpy.web import auth, OracleFlaskApp


app = OracleFlaskApp(__name__, "My App", ["schema.table"], "login", "password")

@app.route("/unauth")
def post_logout():
    return "<h1>Logged out</h1>"


@app.route("/logout")
@auth.cas_logout(after_logout="post_logout")
def logout():
    pass
```


#### Specifying CAS Server in decorator
If you don't decide to store the CAS server url in the ```cas_url``` environment variable, you can pass 
the url into the decorators.

```python
from profpy.web import auth, OracleFlaskApp


app = OracleFlaskApp(__name__, "My App", ["schema.table"], "login", "password")
cas_url = "https://some-cas-server.com"


@app.route("/")
@auth.cas_required(cas_server_url=cas_url)
def home(cas_user, cas_attributes):
    return f"<h1>{cas_user} Authenticated!"


@app.route("/unauth")
def post_logout():
    return "<h1>Logged out</h1>"


@app.route("/logout")
@auth.cas_logout(cas_server_url=cas_url, after_logout="post_logout")
def logout():
    pass
```

#### With pure Flask app
All previous examples used our OracleFlaskApp class. There may be an instance where you don't need to connect
to Oracle or want to use some other database platform to back your app. For this reason, the ```auth``` decorators
work with "vanilla" Flask applications as well. 
```python
from profpy.web import auth
from flask import Flask
from uuid import uuid1


app = Flask(__name__)
app.secret_key = str(uuid1())

@app.route("/")
@auth.cas_required()
def home(cas_user, cas_attributes):
    return f"<h1>{cas_user} Authenticated!"


@app.route("/unauth")
def post_logout():
    return "<h1>Logged out</h1>"


@app.route("/logout")
@auth.cas_logout(after_logout="post_logout")
def logout():
    pass
```