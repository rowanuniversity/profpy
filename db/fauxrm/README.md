# profpy.db.fauxrm
fauxrm is a lightweight Oracle database abstraction layer for Python that provides a lot of the
functionality of traditional ORM's without the usual step of writing domain/model classes.
This library is meant to hopefully simplify tasks that involve basic record creation/modification,
whether it be an ETL batch job or a simple web application.

### Dependencies
The only non-native Python library needed to run fauxrm is [cx_Oracle](https://oracle.github.io/python-cx_Oracle/).
Information on installing this library can be found [here](http://cx-oracle.readthedocs.io/en/latest/installation.html).

Note: The [Oracle Instant Client](http://www.oracle.com/technetwork/database/database-technologies/instant-client/overview/index.html)
will need to be installed.<br><br><br>

## General Usage
For the purposes of these examples, let's assume there is a table in our database called "phonebook" that looks like this:

id | first_name | last_name | phone
---| ---------- | --------- | ------
1|Dennis|Nedry|555-555-5555
2|Ian|Malcolm|222-222-2222

<i>Note: Our id column is the primary key, and is a generated integer value.</i><br>

### Handler objects
fauxrm revolves around the usage of Database objects, which are easily instantiated using environment variable names that house database login info.
By default, these get set to "full_login" and "db_password" if you do not set them explicitly

```python
from profpy.db import fauxrm

# create a handler using a table name and environment variable strings. 
with fauxrm.Database("oracle_connection_string_environment_variable", "oracle_password_environment_variable") as db:
    # ... do stuff ...
    
    # commit changes, if you want
    db.commit()

```
<br>

### Exploring handler object's properties
When a handler is created, you have access to all of that database's tables, views and functions.
```python
from profpy.db import fauxrm

# use default "full_login" and "db_password"
with fauxrm.Database() as database:
    phonebook = database.model(owner="rowan", table_name="phonebook")
    phonebook.mapping
    # returns:
    # {'phone': {'generated': False, 'type': <type 'str'>, 'nullable': True},
    #  'first_name': {'generated': False, 'type': <type 'str'>, 'nullable': True},
    #  'last_name': {'generated': False, 'type': <type 'str'>, 'nullable': True},
    #  'id': {'generated': True, 'type': <type 'int'>, 'nullable': False}}
    
    phonebook.primary_key
    # returns "id"
    
    phonebook.columns
    # returns ['id', 'first_name', 'last_name', 'phone']
    
    phonebook.column_descriptions
    # returns:
    # {'phone': 'The phone number for this entry',
    #  'first_name': 'The first name of the person for this entry',
    #  'last_name': 'The last name of the person for this entry',
    #  'id': 'Auto generated primary key for phonebook entries'}
    
    phonebook.description
    # returns "A Test table for the fauxrm library"

```

We can also access several objects at once using the same handler.
```python
from profpy.db import fauxrm
with fauxrm.Database() as database:
    current_term_code = database.execute_function(owner="rowan", function_name="f_get_term_code")
    sortest = database.model("saturn", "sortest")
    spvname = database.model("rowan", "spvname")
```
<br>
<br>

### Retrieving data

##### Get
There are a couple of different ways to retrieve data from tables using handlers. The simplest way is the "get" method. The
get method takes a key value as a parameter and returns the single record that corresponds with it. This will work for
composite keys as well as single field keys.
```python
from profpy.db import fauxrm
with fauxrm.Database() as database:
    
    phonebook = database.model("rowan", "phonebook")
    
    # we know that Dennis' key value from the table was 1.
    record = phonebook.get(1)

    # our new record variable now has access to the fields in the table as attributes of the object.
    print(record.first_name)  # Dennis
    print(record.last_name)   # Nedry
    
    # we can also access the fields like dictionary keys
    print(record["first_name"])
    print(record["last_name"])
    
    # FauxRM's model-less design allows us to quickly switch tables and access those fields as attributes as well.
    library = database.model("rowan", "library")
    record = library.get(1)
    print(record.author)
    print(record.title)
```
<br>
<br>

##### Find
The find method allows the user to query the table in a few different ways. The first way is to
utilize keyword arguments or dictionaries:
```python
# All of these will have equivalent behavior
records = table.find(first_name="Dennis", last_name="Nedry")
records = table.find(dict(first_name="Dennis", last_name="Nedry"))
records = table.find({"first_name": "Dennis", "last_name": "Nedry"})
```
<br>
<br>

##### Query Classes
Keyword arguments are good for simple searches on a few fields. However, they can only replicate a big AND statement in the database.
For more complex queries we can use the fauxrm query classes.
```python
from profpy.db.fauxrm.queries import And, Or
from profpy.fauxrm import Database

# select * from phonebook
#    where first_name='Dennis' and
#          last_name='Nedry' and
#          (phone='555-555-5555' or last_name='Malcolm')

with Database() as database:
    phonebook = database.model("rowan", "phonebook")
    or_statement = Or(phone="555-555-5555", last_name="Malcom")
    q = And(or_statement, first_name="Dennis", last_name="Nedry")
    records = phonebook.find(q)
```
<br>
<br>

##### Other operators
What if we want to use other operators other than "="? Using a syntax similar to the one used by Django, users can construct
queries using the other arithmetic operators, as well as other SQL functions and operators such as LIKE. For this example, let's assume we have a table
called "addresses" that looks like this:


 first_name | last_name | age | address
----------- | --------- | --- | --------
John|Doe|55|11 W. 1st St
Jane|Doe|23|33 N 12th St


```python
from profpy.fauxrm import Database
from profpy.fauxrm.queries import And, Or
with Database() as database:
    addresses = database.model("rowan", "address")

    # select * from addresses where last_name like 'Do%' and age > 23 and (first_name = 'John' or last_name='Doe')
    q = And(
            Or(first_name="John", last_name="Doe"),
            last_name___like="Do%",
            age___gt=23
    )
    results = addresses.find(q)
```
<br>

###### Currently Supported Operators and Functions
Operator/Function | Examples
:------: | :----:
=   | field=value
<>|field___ne=value
\>|field___gt=value
\>=|field___gte=value
\<|field___lt=value
\<=|field___lte=value
LIKE|field___like=value
TRUNC (dates)|field___trunc=value<br>field___trunc___lt=value<br>field___trunc___gte=value
IN|field___in=\[values\]<br>field=\[values\]<br>field={values}

##### Query concatenation and nesting
We can also use the "&" and "|" operators to concatenate query parts.
```python
from profpy.db import fauxrm
from profpy.db.fauxrm.queries import And, Or

with fauxrm.Database() as database:
    addresses = database.model("rowan", "addresse")

    and_1 = And(first_name="John", last_name="Doe")
    or_1 = Or(first_name="John", age=22)
    and_2 = And(last_name___like="%e", age___gt=33)

    # "and" them all together
    query = and_1 & or_1 & and_2

    results = addresses.find(query)
```
As shown in the previous example, queries can be input as arguments to other queries. The below query would likely not return anything, but it demonstrates this nesting behavior.
```python
from profpy.db.fauxrm.queries import Or, And
query = Or(
            Or(first_name="Jane", last_name="Doe"),
            And(age___gt=55, birthday=datetime.datetime(1990, 2, 3),
            Or(first_name="Dennis", last_name___like="Ned%"),
            last_name="Smith,
            age___lt=100
)
```
<br>
<br>

### Creating/Updating Data

#### Inserting

Using our phonebook table from before, lets insert some new data into the table.
```python
from profpy.db import fauxrm

with fauxrm.Database() as database:
    phonebook = database.model("rowan", "phonebook")
    new_record = phonebook.save(first_name="Dennis", last_name="Nedry", phone="555-555-5555")

    # just like before, we can access the fields of the table as attributes of the object
    first_name = new_record.first_name
    last_name = new_record.last_name
    phone = new_record.phone

    # the record's new key
    new_record.key
    database.commit()
```
<br>
<br>

#### Updating
We can also use the save function to update data, if we specify the key in our input
```python
from profpy.db import fauxrm

with fauxrm.Database() as database:

    # let's say we know there is a record with an id of 1
    # this would grab the record at that key and update the first name field
    phonebook = database.model("rowan", "phonebook")
    updated_record = phonebook.save(id=1, first_name="Ian")
    database.commit()

```

But what if we don't know the key? For instance, what if we needed to update a timestamp field with the current date/time for multiple records?
Luckily, the returned records also have a save method that can be invoked after we alter their attributes.
```python
import datetime
from profpy.db import fauxrm

# let's say we have a table called "timesheet" which has a timestamp field called "time_in"
# let's update the "time_in" field for all the records for "John Smith" to be the current date/time

with fauxrm.Database() as database:

    timesheet = database.model("rowan", "timesheet")
    current_date_time = datetime.datetime.now()
    work_days = timesheet.find(first_name="John", last_name="Smith")
    for record in work_days:

        record.time_in = current_date_time
        record.save()

    database.commit()
```
Any attribute change goes through validation that will not allow a user to enter improper data types or null values where they are not allowed.
