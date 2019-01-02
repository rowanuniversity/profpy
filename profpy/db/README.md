# profpy.db

## General Usage
One of the main goals of profpy is to limit code duplication across our scripts and projects. The profpy.db submodule
provides a group of general functions for basic data access. Some of these were directly inspired/forked from legacy code
that was found across multiple projects and CVS repositories. 
<br>
<br>

---

#### get_connection(<i> login_var, password_var </i>)
<i>Returns cx_Oracle connection object based on given environment variable names. Often "full_login" and "db_password"</i>.

<b>Parameters:</b>

| Name         | Description                                             | Type | Required |
|--------------|---------------------------------------------------------|------|----------|
| login_var    | environment variable containing login connection string | str  | yes      |
| password_var | environment variable containing database password       | str  | yes      |

```python
from profpy.db import get_connection
with get_connection("full_login", "db_password") as connection:
    # do stuff
    connection.commit()
```
<br>

---

#### execute_sql ( <i>cursor, sql, params=None, limit=None, null_to_empty_string=False, prefix=None</i> )
<i>Returns a list of dictionaries from a resulting SQL query. This is in contrast to the normal behavior of cx_Oracle cursor
executions which return a list of lists. This allows us to access data by column name, rather than having to keep track of indexes, leading to much more readable code.</i>

<b>Parameters:</b>

| Name                 | Description                                          | Type             | Required |
|----------------------|------------------------------------------------------|------------------|----------|
| cursor               | database cursor                                      | cx_Oracle Cursor | yes      |
| sql                  | sql to be executed                                   | str              | yes      |
| params               | parameters for the sql                               | dict             | no       |
| limit                | a limit on the number of rows returned               | int              | no       |
| null_to_emtpy_string | whether or not to convert nulls to empty strings     | bool             | no       |
| prefix               | a string to cut off of the front of each column name | str              | no       |


Basic usage:
```python
from profpy.db import get_connection, execute_query

sql = "select phone_number, first_name, last_name from phonebook where last_name=:last_name and first_name=:first_name"

with get_connection("full_login", "db_password") as connection:
    cursor = connection.cursor()
    parameters = {"first_name": "Jane", "last_name": "Doe"}
    
    for row in execute_query(cursor, sql, parameters):
        print(row["first_name"])  # rather than row[1]
    
    cursor.close()
```

Chopping off prefix:
```python
from profpy.db import get_connection, execute_query

sql = "select * from sortest where sortest_pidm=:pidm"

with get_connection("full_login", "db_password") as connection:
    cursor = connection.cursor()
    for row in execute_query(cursor, sql, {"pidm", "123456"}, prefix="sortest_"):
        print(row["tesc_code"])  # rather than "sortest_tesc_code
        
    cursor.close()
```
<br>

---

## Advanced Usage
The db submodule is home to the fauxrm database abstraction layer, which can be used for more complex tasks. See [the docs](./fauxrm/README.md) for more details.