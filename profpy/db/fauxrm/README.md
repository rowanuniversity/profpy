# profpy.db.fauxrm
<i>This is a brief quick start guide, for more information, see the [technical documentation](./documentation/).</i>


fauxrm is a lightweight Oracle database abstraction layer for Python that provides a lot of the
functionality of traditional ORM's without the usual step of writing domain/model classes.
This library is meant to hopefully simplify tasks that involve basic record creation/modification,
whether it be an ETL batch job or a simple web application.

### Dependencies
The only non-native Python library needed to run fauxrm is [cx_Oracle](https://oracle.github.io/python-cx_Oracle/).
Information on installing this library can be found [here](http://cx-oracle.readthedocs.io/en/latest/installation.html).

Note: The [Oracle Instant Client](http://www.oracle.com/technetwork/database/database-technologies/instant-client/overview/index.html)
will need to be installed.<br><br><br>

# Quick Start
For a quick reference on using this tool to develop Flask applications, see [this documentation](./documentation/flask.md). However, it is recommended that you read this page first. 
## Basic Functionality
#### Connecting to the database
```python
from profpy.db import fauxrm

database = fauxrm.Database("login_environment_variable", "password_environment_variable")
database_name = database.name  
database.close()

```
OR
```python
from profpy.db import fauxrm

# if no environment variables ar specified, "full_login" and "db_password" are used
with fauxrm.Database() as database:
    database_name = database.name
```

OR

```python
from profpy.db.fauxrm import with_fauxrm

@with_fauxrm("full_login", "db_password")  # again, these are defaults
def some_function(database):
    database_name = database.name

```

#### Execute Raw SQL
```python
from profpy.db.fauxrm import with_fauxrm

# compile list of user ids
@with_fauxrm()
def get_ids(database):

    sql = "select full_name, user_id from users where last_name=:last_name"
    params = {"last_name": "Joe"}
    user_ids = []
    for record in database.execute_query(sql, params):
        user_ids.append(record.user_id)
```

#### Execute Oracle Functions
```python
from profpy.db.fauxrm import with_fauxrm

@with_fauxrm()
def main(database):
    current_term_code = database.execute_function("owner", "get_term_code")
```

## Using model objects 
#### Do basic search on a table or view
```python
from profpy.db.fauxrm import with_fauxrm

@with_fauxrm()
def demo(database):

    # using views
    users = database.model("owner", "users")
    john_smith_list = users.find(first_name="John", last_name="Smith")
    
    # using tables
    test_scores = database.model("owner", "test_scores")
    keys = []
    
    # grab all the primary key values for the resulting rows
    for sat_score in test_scores.find(test_code="SAT"):
        keys.append(sat_score.key)
```

#### Using the with_model decorator
The fauxrm module also supports a with_model decorator that could be useful in streamlining code.
```python
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, owner_name="table_owner", object_name="phonebook")
def get_phone_number(phonebook, name):
    return phonebook.find(name=name)
    
if __name__ == "__main__":
    get_phone_number("Dennis Nedry")
    database.close()

```

You can string them together to use multiple models in one function:
```python
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, owner_name="table_owner", object_name="phonebook")
@with_model(database, owner_name="table_owner", object_name="addresses")
def get_user_info(addresses, phonebook, name):
    phone_info = phonebook.find(name=name)
    address_info = addresses.find(name=name)
    return dict(addresses=address_info, phones=phone_info)
    
if __name__ == "__main__":
    get_user_info("Dennis Nedry")
    database.close()
```

#### Querying with Other SQL Operators
The [technical docs](./documentation/Handlers.md#find--datanone-limitnone-rawfalse-kwargs-) for the find method have examples using other sql operators such as LIKE and IN. 

#### Modifying tables

*Saving*
```python
from profpy.db.fauxrm import with_fauxrm

@with_fauxrm()
def add_phone(database):
    phonebook = database.model("owner", "phonebook")
    new_record = phonebook.new(first_name="Dennis", last_name="Nedry", phone_number="555-555-5555")
    new_record.save()
    database.commit()
```

*Deleting*
```python
from profpy.db.fauxrm import with_fauxrm

@with_fauxrm()
def demo(database):
   phonebook = database.model("owner", "phonebook")
   phonebook.delete_where(first_name="Dennis")
   database.commit() 
```

*Getting at Key (only for tables)*
```python
from profpy.db.fauxrm import with_fauxrm

# say our phonebook table has a generated integer id column
@with_fauxrm()
def demo(database):
    phonebook = database.model("owner", "phonebook")
    first_record = phonebook.get(1)
```

*Editing Values by Row*
```python
import datetime
from profpy.db.fauxrm import with_fauxrm

@with_fauxrm()
def edit_test_scores(database):
    test_scores = database.model("owner", "test_score")
    for record in test_scores.find(user_id=123456):
        record.activity_date = datetime.datetime.now()
        record.test_score = 100
        record.save()
    database.commit()
```

#### Query functions
The fauxrm And and Or functions are good for queries that can't be simplified down to keyword argument parameters. These
functions can be strung together and nested. 
```python
from profpy.db.fauxrm import And, Or, with_fauxrm

@with_fauxrm()
def query_demo(database):  
    # select all john smiths and jane does from the phonebook (an or statement)
    john_smith = And(first_name="John", last_name="Smith")
    jane_doe = And(first_name="Jane", last_name="Doe")
    query = Or(john_smith, jane_doe)
    
    phonebook = database.model("owner", "phonebook")
    results = phonebook.find(query)
```

#### LOBs
fauxrm supports the reading and writing BLOBS and CLOBS. However, it does not currently support searching on these data types.
```python
from profpy.db.fauxrm import with_fauxrm

@with_fauxrm()
def lob_demo(database):
    table_with_lobs = database.model("owner", "lobs")
    clob_value = "this is a test CLOB"
    blob_value = b"test blob"
    table_with_lobs.new(
        id=1,
        clob_field=clob_value,
        blob_field=blob_value
    )
    table_with_lobs.save()
```

