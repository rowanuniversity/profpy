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
```
*Note: We don't have to do an explicit call to database.close(), this is handled by garbage collection.  

#### Using the Row object like a dict 
You can also iterate through the columns in a row in a couple of different ways. 

##### Using the ```.items()``` method
```python
@with_model(database, "admin", "user_table")
def print_people_named_dennis(user_table):
    for user in user_table.find(first_name="Dennis"):
        for col_name, value in user.items():
            print(f"{col_name}:\t{value}")
```

##### Using the ```.columns``` property of model
```python
@with_model(database, "admin", "user_table")
def print_people_named_dennis(user_table):
    for user in user_table.find(first_name="Dennis"):
        for col_name in user_table.columns:
            print(f"{col_name}\t{user[col_name]}")
```
*Note: Row objects also have ```.columns``` as  a property

##### Additional dict-like syntax
In addition to ```.items()```, ```.values()```, ```.get()```, and ```.keys()``` are also supported for dict-like access.
```python
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "admin", "users")
def demo(users):
    for user in users.find(last_name="Nedry"):
        
        # get keys and values
        keys = user.keys()  # user.columns returns the same thing
        vals = user.values()
        
        # dict-like iteration
        for key, value in user.items():
            print(key, value)
        
        # dict-like get
        first_name = user.get("first_name")
        
        # .get() with fallback value
        some_value = user.get("field_that_does_not_exist", "fallback value")
```

#### Querying with Other SQL Operators
Fauxrm currently supports some other SQL operators, similar to the way that Django does. The syntax follows the pattern \<field\>___\<operator\>=\<value\>. 
This syntax is applied as keyword arguments just like normal queries. 
```python
import datetime
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "owner", "movies")
def movie_stats(movies):

    # <, >, <=, >=, <>, like, not like, in, not in
    movies.find(runtime___lt=127)
    movies.find(runtime___gt=127)
    movies.find(runtime___lte=127)
    movies.find(runtime___gte=127)
    movies.find(runtime___ne=127)
    movies.find(title___like="Jurassic%")
    movies.find(title___nlike="%World")
    movies.find(title___in=["Forrest Gump", "Jurassic Park"])
    movies.find(title___nin=["Ernest Scared Stupid"])

    # truncate date
    movies.find(release_date___trunc=datetime.date(year=1993, month=6, day=11))
    
    # truncate date with other operator
    # sql: 
    #      select * from owner.movies where trunc(release_date) > '1993-11-06'
    movies.find(release_date___trunc___gt=datetime.date(year=1993, month=6, day=11))


@with_model(database, "owner", "movie_characters")
def movie_characters(movie_characters):
    
    # LIKE operator
    movie_characters.find(first_name___like="Denn%")
    
    # IN operator, either syntax works
    movie_characters.find(first_name___in=["Dennis", "Alan", "John", "Tim"])
    movie_characters.find(first_name=["Dennis", "Alan", "John", "Tim"])
      
```

#### Query functions
The fauxrm And and Or functions are good for queries that can't be simplified down to keyword argument parameters. These
functions can be strung together and nested. 
```python
from profpy.db.fauxrm import And, Or, with_model, Database

database = Database()

@with_model(database, "owner", "phonebook")
def query_demo(phonebook):  
    # select all john smiths and jane does from the phonebook (an or statement)
    john_smith = And(first_name="John", last_name="Smith")
    jane_doe = And(first_name="Jane", last_name="Doe")
    query = Or(john_smith, jane_doe)
    results = phonebook.find(query)
```

What would this have looked like with SQL? 
```oracle
select * 
from   owner.phonebook
where (first_name='John' and last_name='Smith') or (first_name='Jane' and last_name='Doe');
```

Additionally, you can use the keyword operators from the previous section inside of these logical operator functions.
This snippet of fauxrm code...
```python
from profpy.db.fauxrm import Or, with_model, Database

database = Database()

@with_model(database, "owner", "phonebook")
def query_demo(phonebook):
    phonebook.find(Or(first_name___like="Denn%", last_name="Grant"))
```

... would look like this in SQL:
```oracle 
select *
from   owner.phonebook
where  first_name like 'Denn%' or last_name='Grant';
```

#### Modifying tables

*Saving*
The save method allows you to commit "in place" like so: 
```python
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "owner", "phonebook")
def add_phone(phonebook):
    new_record = phonebook.new(first_name="Dennis", last_name="Nedry", phone_number="555-555-5555")
    new_record.save(commit=True)
```

This eliminates the need for an explicit call to database.commit(). 

Alternatively, the database handler's commit method is best used 
after a string of .save() calls or a loop. 
```python
for phone_number in ["555-555-5555", "555-555-5556", "555-555-5557"]:
    phonebook.new(phone_number=phone_number).save()
database.commit()
```

*Deleting*
```python
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "owner", "phonebook")
def demo(phonebook):
   phonebook.delete_where(first_name="Dennis", commit=True)
```

*Getting at Key (only for tables)*
```python
from profpy.db.fauxrm import with_model, Database

database = Database()

# say our phonebook table has a generated integer id column
@with_model(database, "owner", "phonebook")
def demo(phonebook):
    first_record = phonebook.get(1)
```

*Editing Values by Row*
```python
import datetime
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "owner", "test_score")
def edit_test_scores(test_scores):
    for record in test_scores.find(user_id=123456):
        record.activity_date = datetime.datetime.now()
        record.test_score = 100
        record.save()
    database.commit()
```

#### LOBs
fauxrm supports the reading and writing BLOBS and CLOBS. However, it does not currently support searching on these data types.
```python
from profpy.db.fauxrm import with_model, Database

database = Database()

@with_model(database, "owner", "lobs")
def lob_demo(table_with_lobs):
    clob_value = "this is a test CLOB"
    blob_value = b"test blob"
    table_with_lobs.new(
        id=1,
        clob_field=clob_value,
        blob_field=blob_value
    ).save(commit=True)
```

