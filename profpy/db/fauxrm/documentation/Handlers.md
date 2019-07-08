# fauxrm.handlers.DatabaseObjects
Table and View Objects are both children of the Data class. In a script using fauxrm, the base constructors for these
classes should not be used. Instead they should be created using a Database object and its model method.

## Instantiation
To get a Table or View handler object, you need to create a Database object first. Then, it is suggested that you used either
the Database object's .model() method or the with_model decorator. You can also use the with_fauxrm decorator that simply passes a 
Database object into the decorated function. The last suggested method is using the Database object's own context manager, but this
is likely the least likely to be used option. 

All of these conventions give you flexibility with how you use this tool. For our documentation, we will mostly use the 
with_model convention, as it is the most succinct. However, this may not *always* be the best design choice if you are 
using the same models repeatedly in your code. Examples of the different conventions can be found below:

Using the with_fauxrm decorator:
```python
from profpy.db.fauxrm import with_fauxrm

# the arguments to with_fauxrm are optional and default to "full_login" and "db_password", respectively. 
# they are the names of the environment variables containing your connection string and password.
@with_fauxrm(login_var="login_env_var", password_var="password_env_var")
def find_user(database, user_id):
    users = database.model("owner", "users")
    return users.get(user_id)
```


Using the Database object and or with_model decorator: 
```python
from profpy.db.fauxrm import with_model, Database

# instantiate Database object, like with the with_fauxrm decorator these default to "full_login" and "db_password"
database = Database(login_var="login_env_var", password_var="password_env_var")

# using the .model() convention:
def find_user_1(user_id):
    user_table = database.model("owner", "users")
    return user_table.get(user_id)

# using the with_model convention:
@with_model(database, "owner", "users")
def find_user_2(user_table, user_id):
    return user_table.get(user_id)
```

Using native Database object context manager:
```python
from profpy.db.fauxrm import Database

def find_user(user_id):
    with Database() as database:
        users = database.model("owner", "users")
        return users.find(user_id=user_id)
```


## Properties

#### columns
A list of columns in this Table or View

---
#### column_descriptions
A dictionary of column comments for this Table or View, with keys being the column names and values being the comments.

---
#### count
The number of rows in this Table or View

---
#### description
The comment/description for this Table or View, defined in the DDL.

---
#### mapping
The field definitions for each field. 

```python
from profpy.db.fauxrm import Database

database = Database()
table = database.model("owner", "table")
print(table.mapping)
```

This should output something like this (if the table had these fields):
```text
 { "first_name": {"type": <class "str">, "nullable": True, generated": False}, 
   "last_name" : {"type": <class "str">, "nullable": True, generated": False},
   "id"        : {"type", <class "int">, "nullable": False, generated: True}
 }
```

---
#### name
The Table/View's full name (owner.name)

---
#### owner
The Table/View's owner

---
#### required_fields
The non-nullable fields in this Table or View

---
#### table_name
The name of the table (no owner name included)

## Methods
When a method is said to return "Row" objects, this is referring to the fauxrm.handlers.Row class. These objects 
allow users to access data from a result set from a query by field name as attributes of an object rather than 
indexes in a list or keys in a dict. This concept will be explored in various methods below.

#### all ( )
Returns all records from the table

Example:
```python
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "owner", "users")
def print_user_ids(users):
    for record in users.all():
        print(record.user_id)
```

---
#### find ( *data=None, limit=None, raw=False, \*\*kwargs* )
The find method allows us to query on a table based on its field names using python's keyword arguments parameter type, or using
fauxrm's Query functions (for more complex queries)

Parameters: 

| Name     | Description                                                       | Type     | Required                                    | Default |
|----------|-------------------------------------------------------------------|----------|---------------------------------------------|---------|
| data     | A dictionary to use as search terms                               | dict     | only if no keyword arguments specified      | None    |
| limit    | A cap on the number of returned results                           | int      | no                                          | None    |
| raw      | Whether or not to return a list of dicts (instead of Row objects) | bool     | no                                          | False   |
| **kwargs | Field=value search terms on the table/view                        | **kwargs | only if no dict is passed to data parameter | N/A     |


Examples:
```python
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "owner", "users")
def example(users):
    # get all people named Dennis
    # using keyword args
    dennis_list = users.find(first_name="Dennis")
    
    # using raw dictionaries
    dennis_list = users.find({"first_name": "Dennis"})
    dennis_list = users.find(dict(first_name="Dennis")) 
```
<br>

##### Using find method with SQL Operators
Similar to Django's ORM functionality, some SQL operators and functions are available for use in the find method's keyword arguments 
with the usage of underscores.

Currently supported operators/functions:

| Operator      | Description                                       |
|---------------|---------------------------------------------------|
| =             | field=value                                       |
| <>            | field___ne=value                                  |
| >             | field___gt=value                                  |
| >=            | field___gte=value                                 |
| <             | field___lt=value                                  |
| <=            | field___lte=value                                 |
| LIKE          | field___like=value                                |
| TRUNC(<date>) | field___trunc=value, field___trunc___lt=value, etc. |
| IN            | field___in=values, field=\[values\], field={values}   |


```python
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "park_admin", "users")
def find_nedry(users):
    return users.find(last_name___like="%edry", first_name___like="%ennis")
```

```python
import datetime
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "owner", "office_visits")
def doctor_example(office_visits):

    visits = office_visits.find(visit_date___gt=datetime.date(2019, 3, 1))
    
    # you can also use valid oracle date strings
    visits = office_visits.find(visit_date___gt="01-MAR-19") 
```

##### Using find method with Query Functions
For queries that involve using "Or", you can use the fauxrm query functions and pass them to the find method. 

```python
from profpy.db.fauxrm import And, Or, with_model, Database

database = Database()

@with_model(database, "owner", "users")
def example(users):
    john_smith_query = And(first_name="John", last_name="Smith")
    jane_doe_query = And(first_name="Jane", last_name="Doe")
    query = Or(john_smith_query, jane_doe_query)
    return users.find(query)
```

---

#### find_one ( *data=None, \*\*kwargs* )
Same as find method, but it only returns the first result. 

Parameters: 

| Name     | Description                                                       | Type     | Required                                    | Default |
|----------|-------------------------------------------------------------------|----------|---------------------------------------------|---------|
| data     | A dictionary to use as search terms                               | dict     | only if no keyword arguments specified      | None    |
| raw      | Whether or not to return a dicts (instead of a Row object) | bool     | no                                          | False   |
| **kwargs | Field=value search terms on the table/view                        | **kwargs | only if no dict is passed to data parameter | N/A     |

Example:

```python
from profpy.db.fauxrm import Database, with_model

database = Database()

@with_model(database, "owner", "users")
def example(users):
    return users.find_one(first_name="Dennis", last_name="Nedry")
```

## Table Objects
Both Table and View objects have access to *all* of the functionality outlined in the preceding documentation. The following
properties and methods are only available to table objects. 

### Table-exclusive Properties
#### primary_key
Returns the primary key object for this table, if one is set. 

---
#### generated_fields
Returns all generated fields for this table

---
#### has_key
Returns whether or not this table has a primary key

### Table-exclusive methods
#### delete_where ( commit=False, *\*\*kwargs* )
Deletes rows from a table based on keyword args. If none are specified, it deletes everything. 

Example:
```python
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "owner", "test_scores")
def example(test_scores):

    ids = [12345, 6789]
    
    # commit in place, this argument is optional
    test_scores.delete_where(commit=True, user_id___in=ids)
```
---
#### new (\*\*kwargs)
Creates a new record that is un-persisted to the database until saved. This method is how we create
new data with fauxrm. 

Parameters:

| Name     | Description                                       | Type     | Required                                    | Default |
|----------|---------------------------------------------------|----------|---------------------------------------------|---------|
| **kwargs | key_field=value for each field | **kwargs | no | N/A     | 


Example:
```python
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "owner", "test_scores")
def add_test_score(model, user_id, score):
    new_score = model.new(
        id=user_id,
        score=score
    )
    
    # the commit argument is optional, if not specified, 
    # nothing will be committed until database.commit()
    # is called at some point
    new_score.save(commit=True)
```
The above example will save the new record to the test_scores table, unless any database errors are thrown. 

---
#### get ( *key=None, \*\*kwargs* )
Retrieve a record by supplying its primary key. Table must have a primary key set for this to not throw an exception.
This functionality should handle composite keys. If nothing is found at that key, None is returned. Exceptions are 
appropriately raised for improper field types, improper number of key fields supplied, and improper field names.

Parameters:

| Name     | Description                                       | Type     | Required                                    | Default |
|----------|---------------------------------------------------|----------|---------------------------------------------|---------|
| key      | The value to search for on the primary key        | any      | only if no keyword arguments specified      | None    |
| **kwargs | key_field=value for each field in the primary key | **kwargs | only if no dict is passed to data parameter | N/A     |

Examples:

*Normal Primary Key*
```python
from profpy.db.fauxrm import Database, with_model

database = Database()

# say we have a table of phone numbers that has a "primary_address_id" field that corresponds to a primary key "id" field 
# in a table of addresses
@with_model(database, "owner", "phonebook")
@with_model(database, "owner", "addresses")
def example(addresses, phonebook):
    # find all Johns in phone book and use the foreign key to grab their primary addresses
    primary_addresses = []
    for phone_record in phonebook.find(first_name="John"):
        primary_addresses.append(addresses.get(phone_record.primary_address_id))
    return primary_addresses
```

*Composite Key*
```python
import datetime
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "owner", "test_scores")
def example(test_scores):
    one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
    
    # select a test score based on a composite key of user id, date, and test code
    return test_scores.get(user_id=1234, test_date=one_year_ago, test_code="A")
```