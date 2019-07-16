## fauxrm with Flask
The fauxrm library comes with a handy helper class for Flask called FauxrmApp, which is a child of the flask.Flask class. 
This class allows us to specify any tables or views that we may need in our application when creating the app object.


#### How is this helpful? 
By doing it this way, we can actually access table and view models as properties of the application directly without
having to do any additional set up. This means that our code can be clean and concise. 


```python
from profpy.db.fauxrm import FauxrmApp
from flask import jsonify

tables = ["admin.users", "admin.roles", "payroll.timesheets"]
app = FauxrmApp(__name__, db_objects=tables, login_var="login_env_var", password_var="password_env_var")

    
@app.route("/rest/person/<id_number>")
def person(id_number):
    return jsonify(dict(results=app.admin.users.find(id=id_number, as_json=True)))
```

Notice that we simply called `app.admin.users` as a property of the application. The FauxrmApp is smart enough
to create higher-level properties for owners and sub-properties for object names so you can access them like you would 
with SQL syntax. This also helps avoid any issues with duplicate table/view names under different owners. 

The `login_var` and `password_var` arguments are optional, and default to "full_login" and "db_password", respectively.
App instantiation can be as simple as this:
```python
app = FauxrmApp(__name__, ["admin.users", "admin.roles", "payroll.timesheets"])
```

#### Timeout handling
Keeping a database connection open for too long without usage can cause a timeout and crash your application when users
try to hit various endpoints. To remedy this, the FauxrmApp class has a built-in daemon that periodically "pings" 
the database. The interval between the pings is defaulted to 20 seconds, but this can be configured at initialization.
```python
# ping database every 10 seconds
app = FauxrmApp(__name__, ["admin.users", "admin.roles"], keep_alive_interval=10)
```



   