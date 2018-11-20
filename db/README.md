# profpy.db

## General Usage
One of the main goals of profpy is to limit code duplication across our scripts and projects. The profpy.db submodule
provides a group of general functions for basic data access. Some of these were directly inspired/forked from legacy code
that was found across multiple projects and CVS repositories. 

#### get_connection
<i>Returns cx_Oracle connection object based on given environment variable names. Often "full_login" and "db_password"</i>.
```python
from profpy.db import get_connection
with get_connection("full_login", "db_password") as connection:
    # do stuff
    connection.commit()
```

#### execute_sql
<i>Returns a list of dictionaries from a resulting SQL query. This is in contrast to the normal behavior of cx_Oracle cursor
executions which return a list of lists. This allows us to access data by column name, rather than index, leading to much more readable code.</i>
```python
from profpy.db import get_connection, execute_sql

sql = "select phone_number, first_name, last_name from phonebook where last_name=:last_name and first_name=:first_name"

with get_connection("full_login", "db_password") as connection:
    cursor = connection.cursor()
    parameters = {"first_name": "Jane", "last_name": "Doe"}
    for row in execute_sql(cursor, sql, parameters):
        print(row["phone_number"])  # rather than row[0]
```