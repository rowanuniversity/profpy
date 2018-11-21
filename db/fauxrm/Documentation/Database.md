# profpy.db.fauxrm - Technical Documentation

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


#### Methods
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
    spvname = database.model("rowan", "spvname")
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

sql = "select n.first_name as first_name, n.last_name as last_name, n.pidm as pidm, t.sortest_test_score as score " \
      "from sortest t left join spvname n on t.sortest_pidm=n.pidm " \
      "where t.sortest_pidm=:p_pidm"
      
params = {"p_pidm": 123456789}      

with fauxrm.Database() as database:
    for row in database.execute_query(sql, params=params):
        print(row.pidm, row.first_name, row.last_name)
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
    current_term_code = database.execute_function("rowan", "f_get_term_code")
    last_term_code = database.execute_function("rowan", "f_get_term_code", -1)
```
---
#### commit ( )
Commits any changes made to the database. See documentation on Table and View objects for more examples on this.

Example:
```python
from profpy.db import fauxrm

with fauxrm.Database() as database:
    phonebook = database.model("rowan", "phonebook")
    phonebook.save(first_name="Dennis", last_name="Nedry", phone="555-555-5555") 
    database.commit()
```

---
#### rollback ( )
Rolls back any changes to the database. See documentation on Table and View objects for more examples on this.

Example:
```python
from profpy.db import fauxrm

# set all test scores associated with a list of banners to 100
with fauxrm.Database() as database:
    sortest = database.model("saturn", "sortest")
    banners = [313123123, 4442342, 1231123, 5243243]
    try:
        for banner_id in banners:
            pidm = database.execute_function("rowan", "id_to_pidm", banner_id)
            for record in sortest.find(sortest_pidm=pidm):
                record.sortest_test_score = "100"
                record.save()

        database.commit()
    
    # error found, rollback
    except:
        database.rollback()

```