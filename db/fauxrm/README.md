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
## Basic Functionality
#### Connecting to the database
```python
from profpy.db import fauxrm

pprd = fauxrm.Database("login_environment_variable", "password_environment_variable")
database_name = pprd.name  
pprd.close()

```
OR
```python
from profpy.db import fauxrm

# if no environment variables ar specified, "full_login" and "db_password" are used
with fauxrm.Database() as pprd:
    database_name = pprd.name
```

#### Execute Raw SQL
```python
from profpy.db import fauxrm

sql = "select full_name, pidm from spvname where last_name=:last_name"
params = {"last_name": "Joe"}

# compile list of pidms
with fauxrm.Database() as pprd:
    
    pidms = []
    for record in pprd.execute_query(sql, params):
    
        # direct access to view's field names as attributes of "record"
        pidms.append(record.pidm)
```

#### Execute Oracle Functions
```python
from profpy.db import fauxrm

with fauxrm.Database() as pprd:
    current_term_code = pprd.execute_function("rowan", "f_get_term_code")
    pidm = pprd.execute_function("rowan", "id_to_pidm", 12345678)
```

## Using model objects 
#### Do basic search on a table or view
```python
from profpy.db import fauxrm

with fauxrm.Database() as pprd:

    # using views
    spvname = pprd.model("rowan", "spvname")
    john_smith_list = spvname.find(first_name="John", last_name="Smith")
    
    # using tables
    sortest = pprd.model("rowan", "sortest")
    keys = []
    
    # grab all the primary key values for the resulting rows
    for chemistry_score in sortest.find(sortest_tesc_code="CPEA"):
        keys.append(chemistry_score.key)
```

#### Modifying tables

*Inserting/Upserting*
```python
from profpy.db import fauxrm

with fauxrm.Database() as database:
    
    phonebook = database.model("owner", "phonebook")
    new_record = phonebook.save(first_name="Dennis", last_name="Nedry", phone_number="555-555-5555")

    database.commit()
```

*Deleting*
```python
from profpy.db import fauxrm

with fauxrm.Database() as database:
   phonebook = database.model("owner", "phonebook")
   phonebook.delete_from(first_name="Dennis")
   
   database.commit() 
```

*Getting at Key (only for tables)*
```python
from profpy.db import fauxrm

# say our phonebook table has a generated integer id column
with fauxrm.Database() as database:
    phonebook = database.model("owner", "phonebook")
    first_record = phonebook.get(1)
```

*Editing Values by Row*
```python
import datetime
from profpy.db import fauxrm

with fauxrm.Database() as pprd:
    sortest = pprd.model("saturn", "sortest")
    for record in sortest.find(sortest_pidm=123456):
        record.sortest_activity_date = datetime.datetime.now()
        record.sortest_test_score = "100"
        record.save()
    pprd.commit()
```

#### Query functions
The fauxrm And and Or functions are good for queries that can't be simplified down to keyword argument parameters. These
functions can be strung together and nested. 
```python
from profpy.db import fauxrm
from profpy.db.fauxrm import And, Or

with fauxrm.Database() as database:
    
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
from profpy.db import fauxrm

with fauxrm.Database() as database:

    table_with_lobs = database.model("owner", "lobs")
    clob_value = "this is a test CLOB"
    blob_value = b"test blob"
    
    table_with_lobs.save(id=1, clob_field=clob_value, blob_field=blob_value)
```

