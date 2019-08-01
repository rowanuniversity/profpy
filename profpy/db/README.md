# profpy.db

## General Usage
One of the main goals of profpy is to limit code duplication across our scripts and projects. The profpy.db submodule
provides a group of general functions for basic data access. Some of these were directly inspired/forked from legacy code
that was found across multiple projects and CVS repositories. 
<br>
<br>

---
#### with_cx_oracle_connection( *login=os.environ['full_login'], password=os.environ['db_password'], auto_commit=False*)
<i>Decorator that passes a cx_Oracle connection to the wrapped function. This is the suggested profpy method
for connecting to Oracle with cx_Oracle!</i>

<b>Parameters:</b>

| Name         | Description                                             | Type | Required | Default |
|--------------|---------------------------------------------------------|------|----------| ------- |
| login    | login connection string | str  | no      | full_login environment var |
| password | database password       | str  | no      | db_password environment var|
|auto_commit| commit at end of transaction? |bool|no|False

```python
from profpy.db import with_cx_oracle_connection

@with_cx_oracle_connection(auto_commit=True)
def get_person(connection, person_id):
    cursor = connection.cursor()
    cursor.execute("select * from general.people where id=:in_id", {"in_id": person_id})
    cursor.close()
```

<br>

---

#### with_sql_alchemy_oracle_session( *login=os.environ['full_login'], password=os.environ['db_password'], scoped=False, auto_commit=False, bind=None*)
<i>Decorator that passes a Sql-Alchemy session to the wrapped function. This is the suggested profpy method for 
connecting to Oracle with Sql-Alchemy!</i>

<b>Parameters:</b>

| Name         | Description                                             | Type | Required | Default |
|--------------|---------------------------------------------------------|------|----------| ------- |
| login    | login connection string | str  | no      | full_login environment var |
| password | database password       | str  | no      | db_password environment var|
| scoped | return a scoped session?       | bool  | no      | False|
| bind | optional, already-made engine to bind session to       | Sql-Alchemy Engine  | no      | None|
|auto_commit| commit changes at end of transaction? | bool | no | False

```python
from profpy.db import with_sql_alchemy_oracle_session

@with_sql_alchemy_oracle_session()
def get_person(session, person_id):
    session.execute("select * from general.people where id=:in_id", in_id=person_id)
```

<br>

---

#### with_sql_alchemy_oracle_engine( *login=os.environ['full_login'], password=os.environ['db_password']*)
<i>Decorator that passes a Sql-Alchemy engine to the wrapped function.</i>

<b>Parameters:</b>

| Name         | Description                                             | Type | Required | Default |
|--------------|---------------------------------------------------------|------|----------| ------- |
| login    | login connection string | str  | no      | full_login environment var |
| password | database password       | str  | no      | db_password environment var|

```python
from profpy.db import with_sql_alchemy_oracle_engine

@with_sql_alchemy_oracle_engine()
def get_person(engine, person_id):
    engine.execute("select * from general.people where id=:in_id", in_id=person_id)
```

<br>

---

#### with_sql_alchemy_oracle_connection( *login=os.environ['full_login'], password=os.environ['db_password'], auto_commit=False, engine=None*)
<i>Decorator that passes a Sql-Alchemy connection to the wrapped function.</i>

<b>Parameters:</b>

| Name         | Description                                             | Type | Required | Default |
|--------------|---------------------------------------------------------|------|----------| ------- |
| login    | login connection string | str  | no      | full_login environment var |
| password | database password       | str  | no      | db_password environment var|
|auto_commit| commit at end of transaction? |bool|no|False|
|engine| optional, already-made engine to use for connection | Sql-Alchemy engine | None

```python
from profpy.db import with_sql_alchemy_oracle_connection

@with_sql_alchemy_oracle_connection(auto_commit=True)
def get_person(connection, person_id):
    connection.execute("select * from general.people where id=:in_id", in_id=person_id).fetchall()
```

<br>

---


#### get_cx_oracle_connection(*login=os.environ['full_login'], password=os.environ['db_password']*)
<i>Returns cx_Oracle connection object</i>

<b>Parameters:</b>

| Name         | Description                                             | Type | Required | Default |
|--------------|---------------------------------------------------------|------|----------| ------- |
| login    | login connection string | str  | no      | full_login environment var |
| password | database password       | str  | no      | db_password environment var|

```python
from profpy.db import get_cx_oracle_connection
with get_cx_oracle_connection("login", "password") as connection:
    # do stuff
    connection.commit()
```
<br>

---

#### get_sql_alchemy_oracle_engine(*login=os.environ['full_login'], password=os.environ['db_password']*)
<i>Returns Sql-Alchemy Oracle engine</i>

<b>Parameters:</b>

| Name         | Description                                             | Type | Required | Default |
|--------------|---------------------------------------------------------|------|----------| ------- |
| login    | login connection string | str  | no      | full_login environment var |
| password | database password       | str  | no      | db_password environment var|

```python
from profpy.db import get_sql_alchemy_oracle_engine

engine = get_sql_alchemy_oracle_engine("login", "password")
engine.execute("some query")

```
<br>

---

#### get_sql_alchemy_oracle_session(*login=os.environ['full_login'], password=os.environ['db_password'], scoped=False, bind=None*)

<i>Returns Sql-Alchemy Oracle Session object</i>

<b>Parameters:</b>

| Name         | Description                                             | Type | Required | Default |
|--------------|---------------------------------------------------------|------|----------| ------- |
| login    | login connection string | str  | no      | full_login environment var |
| password | database password       | str  | no      | db_password environment var|
| scoped | return a scoped session?       | bool  | no      | False|
| bind | optional, already-made engine to bind session to       | Sql-Alchemy Engine  | no      | None|

```python
from profpy.db import get_sql_alchemy_oracle_session

session = get_sql_alchemy_oracle_session("login", "password")
session.execute("some query")

```
<br>

---

#### execute_statement ( <i>cursor, sql, params=None</i> )
<i>Executes a SQL statement (DML/DDL) with a cx_Oracle cursor and returns nothing.
This method exists for semantic consistency with ```execute_query```. The same 
functionality can be achieved by using ```cursor.execute(sql, params)``` natively with the cx_Oracle
cursor.</i>

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
<i>Returns a list of dictionaries from a resulting SQL query, using a cx_Oracle cursor. This is in contrast to the normal behavior of cx_Oracle cursor
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

#### sql_file_to_statements( *in_file_path* )

Returns the content of a sql file as a list of statements found within the file

Parameters:

| Name                 | Description                                          | Type             | Required | Default|
|----------------------|------------------------------------------------------|------------------|----------|--------
| in_file_path               | the path to the sql file                              | str | yes      | |
| as_one_string | whether or not to return the file's contents as a single string | bool | no | False |

<br>

```python
from profpy.db import sql_file_to_statements
sql_statements = sql_file_to_statements("/tmp/some_queries.sql")

```

---