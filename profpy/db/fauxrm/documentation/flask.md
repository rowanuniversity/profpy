## fauxrm with Flask
One of the benefits of fauxrm's decorator functions, is that they can be easily integrated into web applications and microservices. 
These functions were designed with usage with Flask in mind, but they could be potentially integrated with any Python web framework.

## App-context Handlers
Flask's g-object allows us to store data at the application-level during a request. Using "g", we can store fauxrm Database-handlers or
models within the application "context" for our endpoints to use. 

```python
from flask import Flask, g, jsonify
from profpy.db import fauxrm

app = Flask(__name__)


def get_handler():
    if "db" not in g:
        g.db = fauxrm.Database()
    return g.db
    
@app.route("/rest/person/<id_number>")
def person(id_number):
    handler = get_handler()
    model = handler.model("table_owner", "people")
    return jsonify(model.find(id=id_number))
```

#### What did this do? 
When a user hits this application, specifically "/rest/person/<id_number>" in this case, a fauxrm database handler is 
either created or retrieved (if it already exists) to be used for the endpoint's operation.

## Using the with_model decorator
We also could use the fauxrm.with_model decorator to have some cleaner, more "pythonic" code. The with_model function 
takes in a database handler, the owner of the table/view, and the name of the owner/view as parameters.

```python
from flask import Flask, g, jsonify
from profpy.db import fauxrm

app = Flask(__name__)


def get_handler():
    if "db" not in g:
        g.db = fauxrm.Database()
    return g.db
    

@fauxrm.with_model(get_handler(), "table_owner", "people")    
@app.route("/rest/person/<id_number>")
def person(id_number, model):
    return jsonify(model.find(id=id_number))
```

We can string decorators together if we need to use multiple models:
```python
@fauxrm.with_model(get_handler(), "table_owner", "people")    
@fauxrm.with_model(get_handler(), "table_owner", "phonebook")
@app.route("/rest/person/<id_number>")
def person(id_number, phonebook_model, people_model):
    return jsonify(dict(biographic=people_model.find(id=id_number), phone=phonebook_model.find(id=id_number)))
```

### Further Reading
For more information on Flask, [read their docs](http://flask.pocoo.org/).

   