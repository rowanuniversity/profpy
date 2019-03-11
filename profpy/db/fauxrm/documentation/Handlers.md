# fauxrm.handlers.DatabaseObjects
Table and View Objects are both children of the Data class. In a script using fauxrm, the base constructors for these
classes should not be used. Instead they should be created using a Database object and its model method.

## Instantiation
To get a Table or View handler object, you need to use the Database class' model method. This method will return
the appropriate object type. 

Example:
```python
from profpy.db import fauxrm

with fauxrm.Database() as pprd:
    spvname = pprd.model("rowan", "spvname")  # returns a View handler for the SPVNAME view
    sortest = pprd.model("saturn", "sortest") # returns a Table handler for the SORTEST table
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
from profpy.db import fauxrm

with fauxrm.Database() as database:
    table = database.model("owner", "table")
    table.mapping
    # { "first_name": {"type": <class "str">, "nullable": True, generated": False}, 
    #   "last_name" : {"type": <class "str">, "nullable": True, generated": False},
    #   "id"        : {"type", <class "int">, "nullable": False, generated: True}
    # }
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
from profpy.db import fauxrm

# print everyone's pidms
with fauxrm.Database() as pprd:
    spvname = pprd.model("rowan", "spvname")
    for record in spvname.all():
    
        # records are of type Row, and therefore allow for direct access to field names as attributes of the object.
        # "pidm" is a field name in the spvname view.
        print(record.pidm)  
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
from profpy.db import fauxrm

# get all people named Dennis
with fauxrm.Database() as pprd:
    spvname = pprd.model("rowan", "spvname")
    
    # using keyword args
    dennis_list = spvname.find(first_name="Dennis")
    
    # using raw dictionaries
    dennis_list = spvname.find({"first_name": "Dennis"})
    dennis_list = spvname.find(dict(first_name="Dennis")) 
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
from profpy.db import fauxrm

# Find all names similar to a certain Jurassic Park character
with fauxrm.Database() as pprd:
    spvname = pprd.model("rowan", "spvname")
    dennis_list = spvname.find(last_name___like="%edry", first_name___like="%ennis")
```

```python
import datetime
from profpy.db import fauxrm

# Find all test scores from people named John from the last year
with fauxrm.Database() as pprd:
    one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
    spvname = pprd.model("rowan", "spvname")
    sortest = pprd.model("saturn", "sortest")
    
    pidms = [record.pidm for record in spvname.find(first_name="John")]
    scores = sortest.find(sortest_test_date___trunc___gt=one_year_ago, sortest_pidm___in=pidms)
```

##### Using find method with Query Functions
For queries that involve using "Or", you can use the fauxrm query functions and pass them to the find method. 

```python
from profpy.db import fauxrm
from profpy.db.fauxrm import And, Or

# Find all John Smiths or Jane Does
with fauxrm.Database() as pprd:

    john_smith_query = And(first_name="John", last_name="Smith")
    jane_doe_query = And(first_name="Jane", last_name="Doe")
    query = Or(john_smith_query, jane_doe_query)
    
    spvname = pprd.model("rowan", "spvname")
    people = spvname.find(query)
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
from profpy.db import fauxrm

# find Dennis Nedry
with fauxrm.Database() as pprd:
    spvname = pprd.model("rowan", "spvname")
    dennis = spvname.find_one(first_name="Dennis", last_name="Nedry")
    print(dennis.full_name)
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
#### delete_from ( *\*\*kwargs* )
Deletes rows from a table based on keyword args. If none are specified, it deletes everything. 

Example:
```python
from profpy.db import fauxrm

# delete all test scores for certain pidms
with fauxrm.Database() as pprd:
    sortest = pprd.model("saturn", "sortest")
    pidms = [12345, 6789]
    
    sortest.delete_from(sortest_pidm___in=pidms)
    pprd.commit()
```
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
from profpy.db import fauxrm

with fauxrm.Database() as database:
    
    # say we have a table of phone numbers that has a "primary_address_id" field that corresponds to a primary key "id" field 
    # in a table of addresses
    phone_book = database.model("owner", "phonebook")
    addresses  = database.model("owner", "addresses")
    
    # find all Johns in phone book and use the foreign key to grab their primary addresses
    primary_addresses = []
    for phone_record in phone_book.find(first_name="John"):
        primary_addresses.append(addresses.get(phone_record.primary_address_id))
```

*Composite Key*
```python
import datetime
from profpy.db import fauxrm

with fauxrm.Database() as pprd:
    sortest = pprd.model("saturn", "sortest")
    one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
    
    # sortest has a composite key on sortest_test_date, sortest_pidm, and sortest_tesc_code
    # None will be returned if nothing is found that the supplied key.
    record = sortest.get(sortest_pidm=1234, sortest_test_date=one_year_ago, sortest_tesc_code="A")
```
---
#### save ( *data=None, \*\*kwargs* )
Inserts or upserts on a table, depending on whether or not a primary key is given in the specified parameters. 
Returns the new record as a Row object.

Parameters:

| Name     | Description                                     | Type     | Required                                    | Default |
|----------|-------------------------------------------------|----------|---------------------------------------------|---------|
| data     | The data to insert/upsert                       | dict     | only if no keyword arguments specified      | None    |
| **kwargs | The data to insert/upsert, as keyword arguments | **kwargs | only if no dict is passed to data parameter | N/A     |

Examples:

```python
from python.db import fauxrm

# say we have a phonebook table with a generated "id" column
with fauxrm.Database() as database:
    
    phonebook = database.model("owner", "phonebook")
    
    # insert new record
    phonebook.save(phone_number="444-444-4444", name="John Smith")
    
    # upsert on id 4
    phonebook.save(id=4, phone_number="222-222-2222")
```

##### Using Row object to modify data
An alternative to the above is modifying the attributes of Row objects and calling their save methods instead.

Example:
```python
from python.db import fauxrm

# change every test score to 100 for people named Dennis Nedry
with fauxrm.Database() as pprd:
    
    sortest = pprd.model("saturn", "sortest")
    
    for test_record in sortest.find(first_name="Dennis", last_name="Nedry"):
        test_record.sortest_test_score = "100"
        test_record.save()
```

*Note: all appropriate exceptions will be thrown if invalid values are passed to fields.*
