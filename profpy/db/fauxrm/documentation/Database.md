## Constructor
### profpy.db.fauxrm.Database ( *login_var="full_login", password_var="db_password"* )
Returns a Database object which acts as a window into the database available to the specified credentials. Database
objects have their own internal connection and cursor objects that get appropriately opened and closed if used 
within a "with-block". If not, Database objects must be explicitly closed.

Parameters:

| Name         | Description                                           | Type | Required | Default       |
|--------------|-------------------------------------------------------|------|----------|---------------|
| login_var    | environment variable containing database login string | str  | no       | "full_login"  |
| password_var | environment variable containing database password     | str  | no       | "db_password" |

Example:

```python
from profpy.db import fauxrm

# with context management
with fauxrm.Database() as database:
    pass
    
# without context management
database = fauxrm.Database()
database.close()
```

## Properties
#### name
The name of the database, akin to:

```sql
select name from v$database;
```

Example:
```python
from profpy.db import fauxrm

with fauxrm.Database() as database:
    db_name = database.name
```

### global_name
The global name of the database, akin to:
```sql
select ora_database_name from dual;
```

Example:
```python
from profpy.db import fauxrm
with fauxrm.Database() as database:
    global_name = database.global_name
```

## Methods
#### ping ( )
Does a simple "healthcheck" or "ping" query against the database.
```python
from profpy.db import fauxrm
with fauxrm.Database() as database:
    database.ping()
```
This is equivalent to:
```oracle
select 1 from dual;
```


#### model ( *owner, object_name* )
Returns either a Table or View handler object, depending on which type the object specified is. Table and View objects
are children of the Data class, and can be used to retrieve/modify data. For more information on the Table and View 
class' methods, see their documentation below.

Parameters:

| Name        | Description                                 | Type | Required |
|-------------|---------------------------------------------|------|----------|
| owner       | schema name where the table/view is located | str  | yes      |
| object_name | name of the table/view                      | str  | yes      |

Example:
```python
from profpy.db import fauxrm
with fauxrm.Database() as database:
    users = database.model(owner="owner", object_name="users")
```

---
#### execute_query ( *query, params=None, one_value=False* )
Executes any SQL query and returns a list of Row objects for easy data access. 

*Note: if an alias is not used when specifying selected columns from joined tables, or resulting columns of an aggregate 
function (i.e. "count(\*)"), then all invalid column name characters get converted to underscores for the attributes in the Row objects. For instance, 
'table2.first_name' would be accessed as row_obj.table2_first_name.*

Parameters:

| Name      | Description                                  | Type | Required | Default |
|-----------|----------------------------------------------|------|----------|---------|
| query     | A SQL query to be executed                   | str  | yes      | N/A     |
| params    | Parameters for the SQL query, if needed      | dict | no       | None    |
| one_value | Only return one result, if specified as True | bool | no       | False   |

Example:

```python
from profpy.db import fauxrm

sql = "select first_name, last_name, user_id from admin.users where last_name like :p_last"
      
params = {"p_last": "%ith"}      

with fauxrm.Database() as database:
    for row in database.execute_query(sql, params=params):
        print(row.first_name, row.user_id)
```
---
#### execute_function ( *owner, function_name, \*args* )
Executes any function available to the connection being used by the Database object.

Parameters:

| Name          | Description                              | Type  | Required | Default |
|---------------|------------------------------------------|-------|----------|---------|
| owner         | Schema that owns the function            | str   | yes      | N/A     |
| function_name | The name of the function                 | str   | yes      | N/A     |
| *args         | Any parameters to the function, in order | *args | no       | N/A     |

Example:
```python
from profpy.db import fauxrm

with fauxrm.Database as database:
    
    # say there is some function that returns the current term code for a college, with an optional offset parameter
    # to go n-terms forward or backward
    current_term_code = database.execute_function("owner", "get_term")
    last_term_code = database.execute_function("owner", "get_term", -1)
    next_term_code = database.execute_function("owner", "get_term", 1)
    
```
---
#### commit ( )
Commits any changes made to the database. See documentation on Table and View objects for more examples on this.

Example:
```python
from profpy.db import fauxrm

with fauxrm.Database() as database:
    phonebook = database.model("owner", "phonebook")
    phonebook.save(first_name="Dennis", last_name="Nedry", phone="555-555-5555") 
    database.commit()
```

---


#### rollback ( )
Rolls back any changes to the database. See documentation on Table and View objects for more examples on this.

Example:
```python
from profpy.db import fauxrm

# set all test scores associated with a list of user ids to 100
with fauxrm.Database() as database:
    test_scores = database.model("owner", "test_scores")
    user_ids = [313123123, 4442342, 1231123, 5243243]
    try:
        for user_id in user_ids:
            for record in test_scores.find(user_id=user_id):
                record.test_score = 100
                record.save()

        database.commit()
    # error found, rollback
    except:
        database.rollback()
```

---

#### close ( )
Manually closes the Database object. Not needed if using the with-block convention.

Example:
```python
from profpy.db import fauxrm

database = fauxrm.Database()
# do a bunch of stuff
database.close()
```
