# profpy.db

## General Usage
One of the main goals of profpy is to limit code duplication across our scripts and projects. The profpy.db submodule
provides a group of general functions for basic data access. Some of these were directly inspired/forked from legacy code
that was found across multiple projects and CVS repositories. 
<br>
<br>

---
#### with_oracle_connection( *login_var="full_login", password_var="db_password"*)
<i>Decorator that passes a cx_Oracle connection to the wrapped function.</i>

<b>Parameters:</b>

| Name         | Description                                             | Type | Required | Default |
|--------------|---------------------------------------------------------|------|----------| ------- |
| login_var    | environment variable containing login connection string | str  | no      | full_login |
| password_var | environment variable containing database password       | str  | no      | db_password |

```python
from profpy.db import with_oracle_connection

@with_oracle_connection()
def get_person(connection, person_id):
    cursor = connection.cursor()
    cursor.execute("select * from general.people where id=:in_id", {"in_id": person_id})
    cursor.close()
    
    # alwasy explicitly commit changes when needed, connection rolls back after wrapped function is done executing.
    connection.commit()
```

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

#### execute_statement ( <i>cursor, sql, params=None</i> )
<i>Executes a SQL statement (DML/DDL) and returns nothing.</i>

<b>Parameters:</b>

| Name                 | Description                                          | Type             | Required |
|----------------------|------------------------------------------------------|------------------|----------|
| cursor               | database cursor                                      | cx_Oracle Cursor | yes      |
| sql                  | sql to be executed                                   | str              | yes      |
| params               | parameters for the sql                               | dict             | no       |


Basic usage:
```python
from profpy.db import get_connection, execute_statement

sql = "create table test (id int)"
with get_connection("full_login", "db_password") as connection:
    cursor = connection.cursor()
    execute_statement(cursor, sql)
    cursor.close()

```

<br>

---

#### execute_query ( <i>cursor, sql, params=None, limit=None, null_to_empty_string=False, prefix=None, use_generator=False</i> )
<i>Returns a list of dictionaries from a resulting SQL query. This is in contrast to the normal behavior of cx_Oracle cursor
executions which return a list of lists. This allows us to access data by column name, rather than having to keep track of indexes, leading to much more readable code. The "use_generator" parameter allows for the user to return a generator object rather than a list of dictionaries. This generator 
object will yield dictionaries as needed. This option is highly recommended for use cases involving large datasets. </i>

<b>Parameters:</b>

| Name                 | Description                                          | Type             | Required |
|----------------------|------------------------------------------------------|------------------|----------|
| cursor               | database cursor                                      | cx_Oracle Cursor | yes      |
| sql                  | sql to be executed                                   | str              | yes      |
| params               | parameters for the sql                               | dict             | no       |
| limit                | a limit on the number of rows returned               | int              | no       |
| null_to_emtpy_string | whether or not to convert nulls to empty strings     | bool             | no       |
| prefix               | a string to cut off of the front of each column name | str              | no       |
| use_generator        | whether or not to return a generator                 | bool             | no       |


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

#### sql_file_to_text( *in_file_path* )

Returns the content of a sql file as a string variable. 

Parameters:

| Name                 | Description                                          | Type             | Required | Default|
|----------------------|------------------------------------------------------|------------------|----------|--------
| in_file_path               | the path to the sql file                              | str | yes      | |
| multiple_statements | whether or not this file contains multiple lines of sql | bool | no | False |

<br>

```python
from profpy.db import sql_file_to_text
sql_str = sql_file_to_text("/tmp/some_query.sql")

# a list of statements to execute
sql_statements = sql_file_to_text("/tmp/some_sql.dml.sql", multiple_statements=True)
```

---

## Advanced Usage
The db submodule is home to the fauxrm database abstraction layer, which can be used for more complex tasks. See [the docs](./fauxrm/README.md) for more details.